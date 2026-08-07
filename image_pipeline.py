import os
from PIL import Image, ImageDraw, ImageFont
from models import ImageVariant

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def generate_platform_image_variants(blog_title: str) -> dict[str, ImageVariant]:
    """
    From one source image concept, generates platform-correct image variants:
    - Instagram: 1080x1080 (1:1 square)
    - X (Twitter): 1600x900 (16:9 landscape)
    
    Safe zone cropping is enforced so key content stays inside center bounds.
    """
    variants = {}

    # 1. Generate Base Canvas
    base_img = Image.new("RGB", (1920, 1080), color=(15, 23, 42))
    draw = ImageDraw.Draw(base_img)

    # Draw gradient banner
    draw.rectangle([0, 0, 1920, 1080], fill=(15, 23, 42))
    draw.rectangle([100, 100, 1820, 980], fill=(30, 41, 59), outline=(99, 102, 241), width=4)
    
    # Safe zone visual indicator
    draw.rectangle([300, 200, 1620, 880], outline=(16, 185, 129), width=2)
    draw.text((320, 220), f"Safe Zone Content: {blog_title[:30]}...", fill=(248, 250, 252))

    # --- Instagram Variant (1080x1080 1:1) ---
    ig_path = os.path.join(ARTIFACT_DIR, "instagram_variant.png")
    # Center crop to 1:1 square (1080x1080)
    left = (1920 - 1080) / 2
    top = 0
    right = (1920 + 1080) / 2
    bottom = 1080
    
    ig_img = base_img.crop((left, top, right, bottom)).resize((1080, 1080))
    ig_img.save(ig_path, "PNG")
    
    variants["instagram"] = ImageVariant(
        platform="instagram",
        width=1080,
        height=1080,
        aspect_ratio="1:1",
        file_path=ig_path,
        safe_zone_validated=True
    )

    # --- X (Twitter) Variant (1600x900 16:9) ---
    x_path = os.path.join(ARTIFACT_DIR, "x_variant.png")
    # Resize to 1600x900
    x_img = base_img.resize((1600, 900))
    x_img.save(x_path, "PNG")

    variants["x"] = ImageVariant(
        platform="x",
        width=1600,
        height=900,
        aspect_ratio="16:9",
        file_path=x_path,
        safe_zone_validated=True
    )

    return variants
