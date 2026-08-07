import logging
from typing import Optional
from fastapi import FastAPI, Request, Header, HTTPException
from models import BlogPost, Campaign, SocialPostEntry
from image_pipeline import generate_platform_image_variants
from caption_engine import generate_platform_captions
from scheduler import store, process_campaign_batch
from webhook_handler import process_social_delivery_webhook_raw
from fake_platform_server import fake_platform

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SocialPublisherApp")

app = FastAPI(
    title="Multi-Platform Social Campaign Publisher",
    description="Idempotent, rate-limit-aware, signature-verified social campaign publisher.",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Multi-Platform Social Campaign Publisher",
        "campaigns_count": len(store.campaigns)
    }

# ---------------------------------------------------------
# 1. Create Social Campaign (POST /api/v1/campaigns)
# ---------------------------------------------------------
@app.post("/api/v1/campaigns", response_model=Campaign)
def create_campaign(post: BlogPost):
    # Generate Platform Images (1:1 & 16:9)
    image_variants = generate_platform_image_variants(post.title)
    
    # Generate Platform Captions
    captions = generate_platform_captions(post)
    
    campaign = Campaign(blog_post=post)
    
    for platform in ["instagram", "x"]:
        idempotency_key = f"idem_{campaign.id}_{platform}"
        post_entry = SocialPostEntry(
            campaign_id=campaign.id,
            platform=platform,
            caption=captions[platform],
            image_variant=image_variants[platform],
            idempotency_key=idempotency_key,
            status="queued"
        )
        campaign.posts[platform] = post_entry
        
    store.save_campaign(campaign)
    logger.info(f"✨ Created Campaign '{campaign.id}' with Instagram and X post variants.")
    return campaign

# ---------------------------------------------------------
# 2. Trigger Campaign Publish (POST /api/v1/publish)
# ---------------------------------------------------------
@app.post("/api/v1/publish")
def publish_campaign(campaign_id: str):
    entries = process_campaign_batch(campaign_id)
    return {
        "status": "PUBLISHING_BATCH_STARTED",
        "campaign_id": campaign_id,
        "posts_queued": [e.dict() for e in entries]
    }

# ---------------------------------------------------------
# 3. Delivery Webhook Listener (POST /webhook/social-delivery)
# ---------------------------------------------------------
@app.post("/webhook/social-delivery")
async def receive_delivery_webhook(request: Request, x_hub_signature_256: Optional[str] = Header(None)):
    raw_body = await request.body()
    result = process_social_delivery_webhook_raw(raw_body, x_hub_signature_256 or "")
    return result

# ---------------------------------------------------------
# 4. Embedded Fake Platform Server Endpoint
# ---------------------------------------------------------
@app.post("/api/v1/fake-platform/publish")
def fake_platform_publish_endpoint(
    platform: str,
    idempotency_key: str,
    caption: str,
    image_url: str,
    authorization: Optional[str] = Header(None)
):
    token = (authorization or "").replace("Bearer ", "")
    code, data, headers = fake_platform.publish_post(
        platform=platform,
        access_token=token,
        idempotency_key=idempotency_key,
        caption=caption,
        image_url=image_url
    )
    if code != 200:
        raise HTTPException(status_code=code, detail=data, headers=headers)
    return data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
