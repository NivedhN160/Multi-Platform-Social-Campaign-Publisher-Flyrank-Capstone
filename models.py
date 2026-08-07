import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# Blog Post Input
# ---------------------------------------------------------
class BlogPost(BaseModel):
    id: str = Field(default_factory=lambda: f"post_{uuid.uuid4().hex[:8]}")
    title: str
    body: str
    url: str
    author: str = "FlyRank Team"
    published_at: datetime = Field(default_factory=datetime.utcnow)

# ---------------------------------------------------------
# Image Variant Metadata
# ---------------------------------------------------------
class ImageVariant(BaseModel):
    platform: str # "instagram" or "x"
    width: int
    height: int
    aspect_ratio: str # "1:1" or "16:9"
    file_path: str
    safe_zone_validated: bool = True

# ---------------------------------------------------------
# Social Post Entry (Model shape from Flynn SocialPostEntry)
# ---------------------------------------------------------
class SocialPostEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"sp_{uuid.uuid4().hex[:10]}")
    campaign_id: str
    platform: str # "instagram" or "x"
    caption: str
    image_variant: ImageVariant
    status: str = "queued" # "queued" | "publishing" | "published" | "failed"
    idempotency_key: str
    external_post_id: Optional[str] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

# ---------------------------------------------------------
# Campaign Overview
# ---------------------------------------------------------
class Campaign(BaseModel):
    id: str = Field(default_factory=lambda: f"camp_{uuid.uuid4().hex[:8]}")
    blog_post: BlogPost
    posts: Dict[str, SocialPostEntry] = {} # platform -> SocialPostEntry
    scheduled_for: Optional[datetime] = None
    status: str = "created" # "created" | "scheduled" | "publishing" | "published" | "failed"
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ---------------------------------------------------------
# Encrypted OAuth Token Storage Model
# ---------------------------------------------------------
class PlatformAccount(BaseModel):
    platform: str
    account_handle: str
    encrypted_access_token: str # AES-256-GCM base64 string (NEVER PLAINTEXT)
    expires_at: datetime

# ---------------------------------------------------------
# Delivery Webhook Payload Schema
# ---------------------------------------------------------
class DeliveryWebhookPayload(BaseModel):
    event_id: str
    event_type: str # "post.delivered" or "post.failed"
    platform: str
    post_id: str
    idempotency_key: str
    status: str # "published" or "failed"
    timestamp: str
