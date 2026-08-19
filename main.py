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

from fastapi.responses import JSONResponse, HTMLResponse

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Multi-Platform Social Campaign Publisher",
        "campaigns_count": len(store.campaigns)
    }

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def live_dashboard():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>FlyRank Social Campaign Publisher — Live Console</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Plus+Jakarta+Sans:wght@700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Inter', sans-serif; background: #0F172A; color: #F8FAFC; margin: 0; padding: 24px; }
    .container { max-width: 1100px; margin: 0 auto; }
    .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 16px; margin-bottom: 24px; }
    .title { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 24px; color: #38BDF8; margin: 0; }
    .badge { background: #0369A1; color: #E0F2FE; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: bold; }
    .stat-row { display: flex; gap: 16px; margin-bottom: 24px; }
    .stat-box { flex: 1; background: #1E293B; padding: 14px; border-radius: 8px; border: 1px solid #334155; text-align: center; }
    .stat-val { font-size: 26px; font-weight: 700; color: #38BDF8; }
    .stat-lbl { font-size: 12px; color: #94A3B8; text-transform: uppercase; margin-top: 4px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
    .card { background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 20px; }
    .card h3 { margin-top: 0; color: #F1F5F9; font-size: 18px; border-bottom: 1px solid #334155; padding-bottom: 10px; }
    input, textarea, button { width: 100%; box-sizing: border-box; background: #0F172A; border: 1px solid #475569; color: #FFF; padding: 10px; border-radius: 6px; margin-bottom: 10px; font-family: inherit; }
    button { background: #0284C7; border: none; font-weight: bold; cursor: pointer; }
    button:hover { background: #0369A1; }
    .log-box { background: #020617; border: 1px solid #1E293B; border-radius: 6px; padding: 12px; font-family: monospace; font-size: 12px; color: #34D399; height: 180px; overflow-y: auto; white-space: pre-wrap; }
    .platform-card { background: #0F172A; border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-bottom: 12px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1 class="title">🚀 Multi-Platform Social Campaign Publisher</h1>
        <p style="color: #94A3B8; margin: 4px 0 0 0; font-size: 14px;">AES-256 Encrypted Token Vaults, Aspect-Ratio Cropping & Signature Verification</p>
      </div>
      <span class="badge">PROD RUNTIME (PORT 8000)</span>
    </div>

    <div class="stat-row">
      <div class="stat-box"><div class="stat-val">AES-256-GCM</div><div class="stat-lbl">Token Encryption</div></div>
      <div class="stat-box"><div class="stat-val">1:1 & 16:9</div><div class="stat-lbl">Auto Image Crops</div></div>
      <div class="stat-box"><div class="stat-val" style="color:#34D399;">HMAC-SHA256</div><div class="stat-lbl">Webhook Signature</div></div>
      <div class="stat-box"><div class="stat-val" style="color:#38BDF8;">100% IDEMPOTENT</div><div class="stat-lbl">Duplicate Shield</div></div>
    </div>

    <div class="grid">
      <div class="card">
        <h3>📝 Create & Publish Multi-Platform Campaign</h3>
        <form id="campaign-form" onsubmit="createAndPublishCampaign(event)">
          <input type="text" id="post-title" placeholder="Blog Post Title" required value="Building Distributed Microservices with FastAPI & Redis">
          <textarea id="post-content" placeholder="Post Excerpt / Body" required style="height: 90px;">Deep dive into high-throughput asynchronous job workers, idempotency locks, and multi-tenant rate limits.</textarea>
          <input type="text" id="post-url" placeholder="Canonical Article URL" value="https://nivedh-portfolio.netlify.app/blog/fastapi-redis">
          <button type="submit">Create Campaign & Generate Variants ➔</button>
        </form>
        <div style="margin-top: 14px;">
          <div style="font-size: 12px; color: #94A3B8; margin-bottom: 6px;">Live Execution Logs:</div>
          <div class="log-box" id="campaign-logs">Ready to generate campaigns...</div>
        </div>
      </div>

      <div class="card">
        <h3>📱 Generated Platform Variants Preview</h3>
        <div id="variants-preview">
          <div class="platform-card">
            <div style="font-weight:bold; color:#E1306C; margin-bottom:4px;">📸 Instagram Post (1:1 Square Aspect Ratio)</div>
            <div style="font-size:12px; color:#94A3B8; margin-bottom:6px;">Image: <code>artifacts/campaign_demo_ig_1x1.png</code> (1080x1080)</div>
            <div style="font-size:13px; color:#E2E8F0; background:#1E293B; padding:8px; border-radius:4px;">
              🚀 Building Distributed Microservices with FastAPI & Redis! Deep dive into asynchronous architecture. 💡 #FastAPI #Redis #BackendEngineering #Python
            </div>
          </div>
          <div class="platform-card">
            <div style="font-weight:bold; color:#1DA1F2; margin-bottom:4px;">🐦 X / Twitter Post (16:9 Landscape Aspect Ratio)</div>
            <div style="font-size:12px; color:#94A3B8; margin-bottom:6px;">Image: <code>artifacts/campaign_demo_x_16x9.png</code> (1200x675)</div>
            <div style="font-size:13px; color:#E2E8F0; background:#1E293B; padding:8px; border-radius:4px;">
              Building Distributed Microservices with FastAPI & Redis: High-throughput job queues & idempotency. Read more: https://nivedh-portfolio.netlify.app 🧵👇
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    async function createAndPublishCampaign(e) {
      e.preventDefault();
      const logs = document.getElementById('campaign-logs');
      logs.innerText = "Creating campaign via POST /api/v1/campaigns...";
      const payload = {
        title: document.getElementById('post-title').value,
        content: document.getElementById('post-content').value,
        url: document.getElementById('post-url').value
      };
      try {
        const res = await fetch('/api/v1/campaigns', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const campaign = await res.json();
        logs.innerText = "✨ Campaign Created! Triggering live batch publisher...\n" + JSON.stringify(campaign, null, 2);
        
        const pubRes = await fetch(`/api/v1/publish?campaign_id=${campaign.id}`, { method: 'POST' });
        const pubData = await pubRes.json();
        logs.innerText += "\n\n🚀 Published Batch Status:\n" + JSON.stringify(pubData, null, 2);
      } catch(err) {
        logs.innerText = "Error: " + err.message;
      }
    }
  </script>
</body>
</html>
    """

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
