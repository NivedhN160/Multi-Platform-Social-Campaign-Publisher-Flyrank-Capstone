from models import BlogPost

# Reusable Prompt Fragments (Mirrors config/social-prompts.config.ts)
BRAND_VOICE_FRAGMENT = (
  "You are a tech thought leader writing engaging, authoritative, and insightful content."
)

PLATFORM_RULES = {
  "instagram": (
    "Platform Rules (Instagram):\n"
    "- Visual, engaging tone with bullet points and line breaks.\n"
    "- Max 2200 characters.\n"
    "- Include 5 high-performing hashtags at the bottom.\n"
    "- Call to Action: 'Link in bio to read the full breakdown! 🚀'\n"
  ),
  "x": (
    "Platform Rules (X/Twitter):\n"
    "- Short, punchy, direct hook under 280 characters.\n"
    "- Max 2 hashtags.\n"
    "- Call to Action: Direct link provided.\n"
  )
}

def generate_platform_captions(post: BlogPost) -> dict[str, str]:
  """Generates platform-tailored captions from composable prompt fragments."""
  captions = {}

  # Instagram Caption
  captions["instagram"] = (
      f"✨ {post.title.upper()} ✨\n\n"
      f"{post.body[:150]}...\n\n"
      f"💡 Key Takeaways:\n"
      f"• Scalable architecture patterns\n"
      f"• Reliability & idempotency best practices\n"
      f"• Production engineering in action\n\n"
      f"🔗 Read full post: {post.url}\n\n"
      f"#Engineering #Backend #SoftwareArchitecture #FlyRank #TechTrends"
  )

  # X (Twitter) Caption
  captions["x"] = (
      f"🚨 New Tech Breakdown: {post.title}\n\n"
      f"{post.body[:120]}...\n\n"
      f"Read more: {post.url} ⚡ #BackendDev #SystemDesign"
  )

  return captions
