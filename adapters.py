import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
from crypto_utils import decrypt_token
from fake_platform_server import fake_platform

logger = logging.getLogger("SocialPublisherAdapters")

class SocialPublisher(ABC):
    """Abstract Interface for Social Media Platform Publishing Adapters."""
    @abstractmethod
    def publish(
        self,
        encrypted_token: str,
        idempotency_key: str,
        caption: str,
        image_path: str
    ) -> Dict[str, Any]:
        pass

class FakeInstagramPublisher(SocialPublisher):
    """Adapter for Instagram Publishing via Fake Platform Server."""
    def publish(
        self,
        encrypted_token: str,
        idempotency_key: str,
        caption: str,
        image_path: str
    ) -> Dict[str, Any]:
        plain_token = decrypt_token(encrypted_token)
        
        # Execute publish against fake platform server with retry logic for 429
        max_retries = 3
        attempt = 0
        
        while attempt < max_retries:
            attempt += 1
            status_code, data, headers = fake_platform.publish_post(
                platform="instagram",
                access_token=plain_token,
                idempotency_key=idempotency_key,
                caption=caption,
                image_url=image_path
            )
            
            if status_code == 200:
                return data
            
            elif status_code == 429:
                retry_after = int(headers.get("Retry-After", "3"))
                logger.warning(f"⏳ [FakeInstagramPublisher] Received HTTP 429. Respecting Retry-After: {retry_after}s...")
                time.sleep(retry_after)
                continue
            
            else:
                raise RuntimeError(f"Instagram Publish Failed ({status_code}): {data}")
                
        raise RuntimeError("Instagram Publish failed after max retries due to rate limits.")

class FakeXPublisher(SocialPublisher):
    """Adapter for X (Twitter) Publishing via Fake Platform Server."""
    def publish(
        self,
        encrypted_token: str,
        idempotency_key: str,
        caption: str,
        image_path: str
    ) -> Dict[str, Any]:
        plain_token = decrypt_token(encrypted_token)
        
        max_retries = 3
        attempt = 0
        
        while attempt < max_retries:
            attempt += 1
            status_code, data, headers = fake_platform.publish_post(
                platform="x",
                access_token=plain_token,
                idempotency_key=idempotency_key,
                caption=caption,
                image_url=image_path
            )
            
            if status_code == 200:
                return data
            
            elif status_code == 429:
                retry_after = int(headers.get("Retry-After", "3"))
                logger.warning(f"⏳ [FakeXPublisher] Received HTTP 429. Respecting Retry-After: {retry_after}s...")
                time.sleep(retry_after)
                continue
            
            else:
                raise RuntimeError(f"X Publish Failed ({status_code}): {data}")
                
        raise RuntimeError("X Publish failed after max retries due to rate limits.")

# Registry mapping platform names to adapter instances
ADAPTERS: Dict[str, SocialPublisher] = {
    "instagram": FakeInstagramPublisher(),
    "x": FakeXPublisher()
}
