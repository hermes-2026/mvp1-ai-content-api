# ContentGen API - MVP 1

AI-powered content generation API for B2B content agencies.

## What It Does

Agencies send a topic → get SEO blog posts, social media copy, emails, landing pages, or product descriptions. No human writer needed.

## Target Customer

**Content agencies** that manage 20-100+ client blogs. They need cheap, fast content at scale.

## Pricing (B2B)

| Plan | Price/mo | Content/mo | Target |
|------|----------|------------|--------|
| Starter | $49 | 20 blogs | Small agencies |
| Agency | $199 | 100 blogs | Mid-size agencies |
| Enterprise | $499 | Unlimited | White-label, large agencies |

## Quick Start

```bash
# 1. Clone and install
cd mvp1-ai-content-api
pip install -r requirements.txt

# 2. Set up .env
cp .env.example .env
# Edit .env with your API keys

# 3. Run locally
python -m uvicorn app.main:app --reload

# 4. Test the API
curl -X POST http://localhost:8000/v1/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -d '{
    "topic": "best coffee shops in Austin",
    "content_type": "blog_post",
    "tone": "professional",
    "word_count": 500
  }'
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/v1/generate` | POST | Generate content |
| `/v1/usage` | GET | Check quota usage |
| `/v1/create-checkout-session` | POST | Create Stripe checkout |

## Tech Stack

- **API:** FastAPI (Python)
- **AI:** OpenAI GPT-4o-mini
- **Payments:** Stripe
- **Auth:** Clerk (or custom API keys)
- **Database:** Supabase (for production)

## Project Structure

```
mvp1-ai-content-api/
├── app/
│   ├── config.py       # Settings
│   ├── models.py       # Request/Response schemas
│   ├── main.py         # API endpoints
│   └── services/
│       └── openai_service.py  # OpenAI integration
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## To Launch

1. Deploy to Railway/Vercel
2. Set up Stripe products (Starter/Agency/Enterprise)
3. Set up Clerk for auth
4. Create landing page
5. Post in Indie Hackers, DM agencies

## Customer Acquisition Strategy

See `../Machine/20k-month-plan.md` for full strategy.

### Short version:
1. **Post in communities** - Indie Hackers, Twitter/X, LinkedIn
2. **DM content agencies directly** - Find agencies on Clutch, Upwork
3. **Offer white-label** - Agencies rebrand as their own
4. **Free trial** - 5 free generations to try
5. **Referral program** - Discount for bringing other agencies