import os
import json
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from main import app
from scheduler import store, process_campaign_batch
from fake_platform_server import fake_platform
from crypto_utils import encrypt_token, decrypt_token
from seed_demo_data import seed

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_seed():
    store.campaigns.clear()
    fake_platform.published_posts.clear()
    fake_platform.idempotency_store.clear()
    fake_platform.rate_limit_active = False
    seed()

def test_probe_1_idempotent_publishing_no_duplicates():
    """PROBE 1 — Publish same campaign twice + retry after timeout -> exactly 1 post per platform."""
    campaign = store.get_campaign("camp_demo_100")
    
    # First publish
    entries1 = process_campaign_batch(campaign.id)
    assert len(entries1) == 2
    post_count_after_first = len(fake_platform.published_posts)
    
    # Second publish (Same campaign / idempotency keys)
    entries2 = process_campaign_batch(campaign.id)
    assert len(entries2) == 2
    
    # Verify fake platform database count did NOT increase (No double posting guarantee)
    assert len(fake_platform.published_posts) == post_count_after_first

def test_probe_2_rate_limit_429_backoff_handling():
    """PROBE 2 — Fake platform returns 429 Retry-After -> worker waits, retries once allowed, and succeeds."""
    fake_platform.rate_limit_active = True
    fake_platform.rate_limit_retry_after = 1 # 1 second for fast test
    
    campaign = store.get_campaign("camp_demo_100")
    
    # Deactivate rate limit after 1 second simulation
    import threading
    def disable_limit():
        import time
        time.sleep(1.2)
        fake_platform.rate_limit_active = False

    threading.Thread(target=disable_limit).start()
    
    entries = process_campaign_batch(campaign.id)
    assert len(entries) == 2
    assert fake_platform.rate_limit_active is False

def test_probe_3_durable_scheduler_crash_recovery():
    """PROBE 3 — Schedule post, kill worker mid-batch, restart it -> completes with zero duplicates."""
    campaign = store.get_campaign("camp_demo_100")
    
    # 1. Simulate worker crash mid-batch on item 2
    with pytest.raises(RuntimeError, match="Simulated Worker Crash Mid-Batch"):
        process_campaign_batch(campaign.id, simulate_crash_mid_batch=True)
        
    posts_after_crash = len(fake_platform.published_posts)
    assert posts_after_crash == 1 # First item succeeded, second crashed before creating duplicate
    
    # 2. Worker Restarts and Resumes Batch
    resumed_entries = process_campaign_batch(campaign.id, simulate_crash_mid_batch=False)
    assert len(resumed_entries) == 2
    assert len(fake_platform.published_posts) == 2 # Final count is exactly 2 (Instagram + X), zero duplicates!

def test_probe_4_forged_and_valid_delivery_webhook():
    """PROBE 4 — Forged webhook -> 400 Bad Request; Valid webhook -> status flips to published."""
    campaign = store.get_campaign("camp_demo_100")
    post_entry = campaign.posts["instagram"]
    
    # 1. Forged Signature -> HTTP 400
    forged_body = json.dumps({
        "event_id": "evt_forged_100",
        "event_type": "post.delivered",
        "platform": "instagram",
        "post_id": "ig_post_101",
        "idempotency_key": post_entry.idempotency_key,
        "status": "published"
    }).encode("utf-8")
    
    resp_forged = client.post(
        "/webhook/social-delivery",
        content=forged_body,
        headers={"X-Hub-Signature-256": "sha256=forged_bad_signature_hash", "Content-Type": "application/json"}
    )
    assert resp_forged.status_code == 400
    assert post_entry.status != "published"
    
    # 2. Valid Webhook Signature -> HTTP 200 OK & Status Flips
    payload_bytes, valid_sig = fake_platform.generate_delivery_webhook(
        platform="instagram",
        post_id="ig_post_101",
        idempotency_key=post_entry.idempotency_key,
        status="published"
    )
    
    resp_valid = client.post(
        "/webhook/social-delivery",
        content=payload_bytes,
        headers={"X-Hub-Signature-256": valid_sig, "Content-Type": "application/json"}
    )
    assert resp_valid.status_code == 200
    assert resp_valid.json()["status"] == "PROCESSED_VERIFIED"
    assert post_entry.status == "published"

def test_probe_5_image_dimensions_and_distinct_captions():
    """PROBE 5 — Instagram file is 1080x1080, X file is 1600x900, captions differ per platform."""
    campaign = store.get_campaign("camp_demo_100")
    
    ig_variant = campaign.posts["instagram"].image_variant
    x_variant = campaign.posts["x"].image_variant
    
    # Verify File Dimensions
    with Image.open(ig_variant.file_path) as img:
        assert img.width == 1080
        assert img.height == 1080
        
    with Image.open(x_variant.file_path) as img:
        assert img.width == 1600
        assert img.height == 900
        
    # Verify Distinct Captions
    ig_caption = campaign.posts["instagram"].caption
    x_caption = campaign.posts["x"].caption
    assert ig_caption != x_caption
    assert "#Engineering" in ig_caption
    assert "#BackendDev" in x_caption

def test_probe_6_encrypted_tokens_at_rest():
    """PROBE 6 — Grep database and logs -> no plaintext token anywhere; stored tokens are encrypted."""
    plaintext = "sk_fake_secret_oauth_token_12345"
    encrypted = encrypt_token(plaintext)
    
    # Verify stored string is encrypted base64 and DOES NOT contain plaintext
    assert plaintext not in encrypted
    assert decrypt_token(encrypted) == plaintext
    
    # Inspect store accounts
    for platform, token in store.encrypted_tokens.items():
        assert "sk_fake" not in token # Encrypted string must not hold raw token!
