import time
import logging
from typing import Dict, List, Optional
from models import Campaign, SocialPostEntry
from adapters import ADAPTERS
from crypto_utils import encrypt_token

logger = logging.getLogger("DurableScheduler")

class CampaignStore:
    def __init__(self):
        self.campaigns: Dict[str, Campaign] = {}
        self.encrypted_tokens: Dict[str, str] = {
            "instagram": encrypt_token("sk_fake_instagram_access_token_999"),
            "x": encrypt_token("sk_fake_x_access_token_888")
        }

    def save_campaign(self, campaign: Campaign):
        self.campaigns[campaign.id] = campaign

    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        return self.campaigns.get(campaign_id)

    def get_post_by_idempotency_key(self, key: str) -> Optional[SocialPostEntry]:
        for camp in self.campaigns.values():
            for post in camp.posts.values():
                if post.idempotency_key == key:
                    return post
        return None

store = CampaignStore()

def process_campaign_batch(campaign_id: str, simulate_crash_mid_batch: bool = False) -> List[SocialPostEntry]:
    """
    Durable worker process publishing campaign posts across platforms.
    Guarantees that a crash mid-batch followed by a restart will resume safely
    without publishing duplicate posts.
    """
    campaign = store.get_campaign(campaign_id)
    if not campaign:
        raise ValueError(f"Campaign '{campaign_id}' not found.")

    campaign.status = "publishing"
    published_entries = []
    
    platforms = list(campaign.posts.keys())
    
    for idx, platform in enumerate(platforms):
        post_entry = campaign.posts[platform]
        
        # Check if already successfully published to external platform (Durable crash recovery check!)
        if post_entry.external_post_id:
            logger.info(f"⏭️ Post '{post_entry.id}' for platform '{platform}' already has external ID '{post_entry.external_post_id}'. Skipping duplicate publish.")
            published_entries.append(post_entry)
            continue

        # Simulate worker crash mid-batch before item 2 publishes if requested
        if simulate_crash_mid_batch and idx == 1:
            logger.warning(f"💥 SIMULATED WORKER CRASH MID-BATCH on platform '{platform}'!")
            raise RuntimeError("Simulated Worker Crash Mid-Batch!")

        adapter = ADAPTERS.get(platform)
        if not adapter:
            logger.error(f"Unknown platform adapter: {platform}")
            continue

        encrypted_token = store.encrypted_tokens.get(platform, "")
        post_entry.status = "publishing"

        # Execute idempotent publish through adapter
        result = adapter.publish(
            encrypted_token=encrypted_token,
            idempotency_key=post_entry.idempotency_key,
            caption=post_entry.caption,
            image_path=post_entry.image_variant.file_path
        )

        post_entry.external_post_id = result.get("post_id")
        published_entries.append(post_entry)

    return published_entries
