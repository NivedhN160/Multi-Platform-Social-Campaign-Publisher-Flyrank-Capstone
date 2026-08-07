from models import BlogPost
from scheduler import store
from image_pipeline import generate_platform_image_variants
from caption_engine import generate_platform_captions
from models import Campaign, SocialPostEntry

def seed():
    print("🌱 Seeding Demo Dataset for Multi-Platform Social Campaign Publisher...")

    post = BlogPost(
        id="post_demo_100",
        title="Building Distributed Systems That Never Double Post",
        body="Designing idempotent APIs, durable schedulers, and rate-limit aware publisher layers in backend AI engineering.",
        url="https://flyrank.ai/blog/distributed-systems-idempotency"
    )

    image_variants = generate_platform_image_variants(post.title)
    captions = generate_platform_captions(post)

    campaign = Campaign(id="camp_demo_100", blog_post=post)

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

    print(f"  ✓ Created Seed Campaign ID: '{campaign.id}'")
    print(f"  ✓ Instagram Image Variant: {image_variants['instagram'].width}x{image_variants['instagram'].height}")
    print(f"  ✓ X (Twitter) Image Variant: {image_variants['x'].width}x{image_variants['x'].height}")
    print("\n✅ SEED COMPLETE! Run pytest test_suite.py -v to verify all acceptance probes.")

if __name__ == "__main__":
    seed()
