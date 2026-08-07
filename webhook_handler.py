import hmac
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import HTTPException, status
from fake_platform_server import WEBHOOK_SECRET
from scheduler import store

logger = logging.getLogger("WebhookHandler")

def process_social_delivery_webhook_raw(raw_body: bytes, signature_header: str) -> Dict[str, Any]:
    """
    Verifies delivery webhook HMAC-SHA256 signature and updates campaign post status.
    - Missing or invalid signature returns HTTP 400 Bad Request.
    - Valid signature flips status to 'published' or 'failed'.
    """
    if not signature_header or "sha256=" not in signature_header:
        logger.warning("❌ Delivery Webhook missing or invalid X-Hub-Signature-256 header. Rejecting with HTTP 400.")
        raise HTTPException(status_code=400, detail="Missing or invalid X-Hub-Signature-256 header.")

    # 1. Signature Verification (HMAC-SHA256)
    expected_sig = f"sha256={hmac.new(WEBHOOK_SECRET.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()}"
    
    if not hmac.compare_digest(signature_header, expected_sig):
        logger.warning("❌ Forged/Modified Delivery Webhook Signature Detected! Rejected with HTTP 400.")
        raise HTTPException(status_code=400, detail="Invalid webhook signature. Request rejected.")

    # 2. Parse Valid Webhook Payload
    try:
        payload_dict = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON webhook payload.")

    idempotency_key = payload_dict.get("idempotency_key")
    event_status = payload_dict.get("status", "published")

    # 3. Find and Update Campaign Post Entry
    post_entry = store.get_post_by_idempotency_key(idempotency_key)
    if not post_entry:
        logger.warning(f"⚠️ Post for idempotency key '{idempotency_key}' not found in store.")
        return {"status": "POST_NOT_FOUND", "idempotency_key": idempotency_key}

    # Update status only after verified webhook! (Status is trust)
    post_entry.status = "published" if event_status == "published" else "failed"
    post_entry.published_at = datetime.utcnow()
    
    logger.info(f"✅ Verified Webhook Processed! Post '{post_entry.id}' status flipped to '{post_entry.status}'.")

    # Check if full campaign is finished
    campaign = store.get_campaign(post_entry.campaign_id)
    if campaign:
        if all(p.status == "published" for p in campaign.posts.values()):
            campaign.status = "published"

    return {
        "status": "PROCESSED_VERIFIED",
        "post_id": post_entry.id,
        "new_status": post_entry.status
    }
