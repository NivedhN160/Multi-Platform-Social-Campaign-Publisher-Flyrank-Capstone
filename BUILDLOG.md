# 📝 BUILDLOG.md — AI Co-Pilot & Architectural Build Log

**Capstone Project:** Multi-Platform Social Campaign Publisher  
**Track:** Backend AI Engineering Capstone  
**Author:** Nivedh  

---

## 📌 Build Journey & AI Collaboration Notes

### 1. Where AI Assisted
* **Image Variant Safe-Zone Pipeline:** AI generated Pillow image cropping code for 1:1 Instagram (`1080x1080`) and 16:9 X (`1600x900`) canvas bounds.
* **AES-256-GCM Encrypted Storage:** AI drafted `crypto_utils.py` leveraging Python's `cryptography` package with fresh random 12-byte IV generation per encryption.
* **Webhook Signature Verification:** AI assisted in writing HMAC-SHA256 signature verification for `X-Hub-Signature-256` headers.

### 2. Where AI Was Incorrect / Required Human Refinement
* **Crash Recovery State Bug:** The AI initially marked post entries as `publishing` prior to network dispatch, causing restarted workers to skip un-published items after a crash mid-batch. I refactored `scheduler.py` to inspect `external_post_id` so crash recovery accurately resumes remaining items while skipping completed ones.

### 3. Key Architectural Decisions
* **Decoupled SocialPublisher Adapter Pattern:** Adapters encapsulate platform mechanics (`FakeInstagramPublisher`, `FakeXPublisher`). Adding a new platform requires creating an adapter without modifying core campaign logic.
* **Signature-Verified Webhook Trust Model:** Delivery status only transitions from `queued` → `published` upon receiving signature-verified delivery webhooks.
