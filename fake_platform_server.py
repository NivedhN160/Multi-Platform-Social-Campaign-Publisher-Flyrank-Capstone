import hmac
import hashlib
import json
import logging
from typing import Dict, Any
from models import DeliveryWebhookPayload

logger = logging.getLogger("FakePlatformServer")

WEBHOOK_SECRET = "whsec_social_delivery_secret_999"

def compute_webhook_signature(payload_bytes: bytes, secret: str = WEBHOOK_SECRET) -> str:
    """Computes HMAC-SHA256 signature header format: sha256=<hex>."""
    sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={sig}"

class FakeSocialPlatformServer:
    """
    Simulates real social platform APIs (Instagram & X/Twitter):
    - Validates OAuth Bearer Tokens
    - Deduplicates requests by Idempotency-Key
    - Simulates Rate Limit 429 & Retry-After behavior
    - Dispatches HMAC-SHA256 signed delivery webhooks
    """
    def __init__(self):
        self.published_posts: Dict[str, Dict[str, Any]] = {}
        self.idempotency_store: Dict[str, Dict[str, Any]] = {}
        self.rate_limit_active: bool = False
        self.rate_limit_retry_after: int = 3

    def publish_post(
        self,
        platform: str,
        access_token: str,
        idempotency_key: str,
        caption: str,
        image_url: str
    ) -> tuple[int, Dict[str, Any], Dict[str, str]]:
        # 1. OAuth Bearer Token Verification
        if not access_token or "sk_fake" not in access_token:
            return 401, {"error": "Unauthorized: Invalid or missing OAuth Bearer token"}, {}

        # 2. Rate Limit Simulation (HTTP 429 + Retry-After)
        if self.rate_limit_active:
            logger.warning(f"⚠️ [Fake Platform] Rate limit 429 triggered on {platform}! Retry-After: {self.rate_limit_retry_after}s.")
            return 429, {
                "error": "Too Many Requests",
                "message": f"Rate limit exceeded on {platform}. Retry after {self.rate_limit_retry_after} seconds."
            }, {"Retry-After": str(self.rate_limit_retry_after)}

        # 3. Idempotency Key Deduplication Check (Probe 1)
        if idempotency_key in self.idempotency_store:
            stored_response = self.idempotency_store[idempotency_key]
            logger.info(f"🔄 [Fake Platform] Duplicate Idempotency-Key '{idempotency_key}' detected. Returning cached post ID without re-creating.")
            return 200, {**stored_response, "is_duplicate": True}, {}

        # 4. Create Post Record
        post_id = f"{platform}_post_{len(self.published_posts) + 101}"
        response_data = {
            "status": "queued",
            "platform": platform,
            "post_id": post_id,
            "idempotency_key": idempotency_key,
            "message": f"Post accepted by {platform} and queued for delivery."
        }

        self.idempotency_store[idempotency_key] = response_data
        self.published_posts[post_id] = response_data

        return 200, response_data, {}

    def generate_delivery_webhook(
        self,
        platform: str,
        post_id: str,
        idempotency_key: str,
        status: str = "published"
    ) -> tuple[bytes, str]:
        """Generates a signed delivery webhook payload and HMAC signature."""
        payload_dict = {
            "event_id": f"evt_{post_id}",
            "event_type": "post.delivered" if status == "published" else "post.failed",
            "platform": platform,
            "post_id": post_id,
            "idempotency_key": idempotency_key,
            "status": status,
            "timestamp": "2026-08-07T21:40:00Z"
        }
        
        payload_bytes = json.dumps(payload_dict).encode("utf-8")
        signature = compute_webhook_signature(payload_bytes, WEBHOOK_SECRET)
        return payload_bytes, signature

fake_platform = FakeSocialPlatformServer()
