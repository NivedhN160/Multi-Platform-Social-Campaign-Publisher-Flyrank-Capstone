# 📢 Multi-Platform Social Campaign Publisher

> A production-grade multi-platform social media publishing system that transforms single blog posts into scheduled, platform-tailored social campaigns. Provides **exact-once idempotency guarantees**, **durable crash recovery**, **AES-256-GCM encrypted OAuth token storage**, rate-limit backoff handling (`HTTP 429 Retry-After`), and **HMAC-SHA256 signature-verified delivery webhooks**.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Framework](https://img.shields.io/badge/framework-FastAPI%20%7C%20Pillow-orange.svg)](https://fastapi.tiangolo.com/)
[![Security](https://img.shields.io/badge/Security-AES--256--GCM%20Encrypted-brightgreen.svg)](README.md)

---

## 🏗️ Architecture Diagram & System Flow

```text
Blog Post Input (title, body, URL)
    │
    ├─► Image Variant Pipeline ──► Instagram (1080x1080 1:1) & X (1600x900 16:9)
    └─► Caption Composer ───────► Shared Voice + Platform Prompt Fragments
            │
            ▼
   Campaign Created (Status: Queued)
            │
            ▼
    Durable Scheduler Worker
            │
            ├─► Inspects external_post_id (Crash-recovery check)
            ├─► SocialPublisher Adapter Interface
            │      ├── FakeInstagramAdapter
            │      └── FakeXAdapter
            │            │
            │            ├─ Decrypts OAuth token in memory (AES-256-GCM)
            │            ├─ Attaches Idempotency-Key header
            │            └─ Handles 429 Retry-After Backoff
            │
            ▼
   FAKE SOCIAL PLATFORM SERVER
            │
            ▼
   POST /webhook/social-delivery (Signed Delivery Webhook)
   ├─► Signature Invalid (HMAC-SHA256) ──► HTTP 400 Bad Request
   └─► Signature Verified ───────────────► Post Status: Queued ──► Published
```

---

## 🔒 Security & Encrypted Token Storage

OAuth access tokens are **encrypted at rest** using **AES-256-GCM** with a fresh, random 12-byte Initialization Vector (IV) per encryption. Tokens are decrypted transiently in memory inside platform adapters and are **never stored in plaintext or logged**.

---

## 🛠️ Required Submission Pack Files (§ 11)

| Required File | Purpose & Contents |
| :--- | :--- |
| **`README.md`** | System architecture, setup/seed/run/test commands, encrypted token rules, and limitations note. |
| **`capstone.yaml`** | Evaluator manifest specifying `run: python main.py`, `seed: python seed_demo_data.py`, `test: pytest test_suite.py -v`, `base_url: http://localhost:8000`, and probe endpoints. |
| **`EVIDENCE.md`** | Verification transcripts and Pytest probe evidence for every Definition-of-Done checkbox. |
| **`BUILDLOG.md`** | AI usage log detailing prompt assistance, refactoring decisions, and bug fixes. |
| **`.env.example`** | Safe environment variable template with non-sensitive defaults. |

---

## 💻 Reproducible Setup & Run Instructions

### Step 1: Clone & Navigate to Repository
```bash
git clone https://github.com/NivedhN160/Multi-Platform-Social-Campaign-Publisher-Flyrank-Capstone.git
cd Multi-Platform-Social-Campaign-Publisher-Flyrank-Capstone
```

### Step 2: Create & Activate Virtual Environment
```bash
# Windows PowerShell:
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS/Linux:
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Seed Demo Data
```bash
python seed_demo_data.py
```

### Step 5: Start the API Server
```bash
python main.py
```
*API Server boots on `http://localhost:8000`. Interactive Swagger UI available at `http://localhost:8000/docs`.*

---

## 🧪 Automated Acceptance Probe Test Suite

Run the automated acceptance suite verifying all 6 evaluator probes (§ 12):
```bash
pytest test_suite.py -v
```

*Verification Results:*
```text
test_suite.py::test_probe_1_idempotent_publishing_no_duplicates PASSED   [ 16%]
test_suite.py::test_probe_2_rate_limit_429_backoff_handling PASSED       [ 33%]
test_suite.py::test_probe_3_durable_scheduler_crash_recovery PASSED      [ 50%]
test_suite.py::test_probe_4_forged_and_valid_delivery_webhook PASSED     [ 66%]
test_suite.py::test_probe_5_image_dimensions_and_distinct_captions PASSED [ 83%]
test_suite.py::test_probe_6_encrypted_tokens_at_rest PASSED              [100%]

======================= 6 passed in 10.43s =======================
```

---

## ⚠️ Honest Limitations Note

1. **Standalone Fake Platform Server:** All publishing and webhook delivery operations execute against the embedded fake platform server (`fake_platform_server.py`) to prevent account bans and API key leaks per § 3.
2. **Local Worker Queue:** Worker queues use persistent in-memory/SQLite store. Production multi-region deployments should pair with Redis/BullMQ.

---

## 📄 License

Built by **Nivedh** for the **FlyRank AI Internship — Backend AI Engineering Track Capstone**.  
Licensed under the [MIT License](LICENSE).
