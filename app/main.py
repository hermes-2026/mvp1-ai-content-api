from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.config import settings
from app.models import (
    GenerateRequest, 
    GenerateResponse, 
    UsageResponse,
    ContentType
)
from app.services.openai_service import generate_content, count_tokens
from typing import Optional
import requests


LANDING_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ContentGen API - AI Content Generation for Agencies</title>
    <meta name="description" content="Generate blog posts, social media, emails, and more with AI. API-first content generation for agencies.">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1a1a2e; }
        .container { max-width: 1100px; margin: 0 auto; padding: 0 20px; }
        header { padding: 20px 0; border-bottom: 1px solid #eee; }
        header .container { display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 24px; font-weight: 700; color: #4f46e5; }
        .hero { padding: 80px 0; text-align: center; }
        .hero h1 { font-size: 48px; font-weight: 800; margin-bottom: 20px; line-height: 1.2; }
        .hero h1 span { color: #4f46e5; }
        .hero p { font-size: 20px; color: #666; max-width: 600px; margin: 0 auto 40px; }
        .cta { display: inline-block; background: #4f46e5; color: white; padding: 16px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 18px; transition: background 0.3s; }
        .cta:hover { background: #4338ca; }
        .cta-secondary { background: transparent; color: #4f46e5; border: 2px solid #4f46e5; margin-left: 10px; }
        .cta-secondary:hover { background: #4f46e5; color: white; }
        .features { padding: 80px 0; background: #f9fafb; }
        .features h2 { text-align: center; font-size: 36px; margin-bottom: 50px; }
        .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 30px; }
        .feature { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .feature h3 { font-size: 20px; margin-bottom: 10px; }
        .feature p { color: #666; }
        .pricing { padding: 80px 0; }
        .pricing h2 { text-align: center; font-size: 36px; margin-bottom: 50px; }
        .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px; }
        .plan { border: 2px solid #eee; padding: 30px; border-radius: 12px; text-align: center; }
        .plan.popular { border-color: #4f46e5; position: relative; }
        .plan.popular::before { content: 'Most Popular'; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #4f46e5; color: white; padding: 4px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .plan-name { font-size: 20px; font-weight: 600; margin-bottom: 10px; }
        .plan-price { font-size: 36px; font-weight: 800; margin-bottom: 20px; }
        .plan-price span { font-size: 16px; font-weight: 400; color: #666; }
        .plan-features { list-style: none; margin-bottom: 30px; }
        .plan-features li { padding: 8px 0; color: #666; }
        .how-it-works { padding: 80px 0; background: #f9fafb; }
        .how-it-works h2 { text-align: center; font-size: 36px; margin-bottom: 50px; }
        .steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px; }
        .step { text-align: center; }
        .step-number { width: 50px; height: 50px; background: #4f46e5; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 700; margin: 0 auto 20px; }
        .step h3 { margin-bottom: 10px; }
        .step p { color: #666; }
        .code-section { padding: 80px 0; }
        .code-section h2 { text-align: center; font-size: 36px; margin-bottom: 30px; }
        .code-block { background: #1a1a2e; color: #e0e0e0; padding: 30px; border-radius: 12px; overflow-x: auto; font-size: 14px; text-align: left; }
        .code-block code { font-family: 'Monaco', 'Consolas', monospace; }
        .code-comment { color: #6a9955; }
        .code-keyword { color: #569cd6; }
        .code-string { color: #ce9178; }
        footer { padding: 40px 0; text-align: center; color: #666; border-top: 1px solid #eee; }
        @media (max-width: 768px) {
            .hero h1 { font-size: 32px; }
            .hero p { font-size: 16px; }
            .cta { display: block; margin: 10px auto; }
            .cta-secondary { margin-left: 0; }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="logo">ContentGen API</div>
            <nav>
                <a href="/docs" style="color: #4f46e5; text-decoration: none; font-weight: 600;">API Docs →</a>
            </nav>
        </div>
    </header>

    <section class="hero">
        <div class="container">
            <h1>Generate <span>High-Converting Content</span><br>with AI</h1>
            <p>Blog posts, social media, emails, and product descriptions — powered by GPT-4. Perfect for agencies and content teams.</p>
            <a href="/docs" class="cta">Try the API</a>
            <a href="#pricing" class="cta cta-secondary">View Pricing</a>
        </div>
    </section>

    <section class="features">
        <div class="container">
            <h2>What You Can Create</h2>
            <div class="features-grid">
                <div class="feature">
                    <h3>📝 Blog Posts</h3>
                    <p>SEO-optimized articles that rank and convert. Get 500-2000 words in seconds.</p>
                </div>
                <div class="feature">
                    <h3>📱 Social Media</h3>
                    <p>Engaging posts for Twitter, LinkedIn, Instagram. Capture attention instantly.</p>
                </div>
                <div class="feature">
                    <h3>📧 Emails</h3>
                    <p>Cold emails, newsletters, and follow-ups that actually get responses.</p>
                </div>
                <div class="feature">
                    <h3>🛒 Product Descriptions</h3>
                    <p>Compelling descriptions that drive sales for e-commerce and marketplaces.</p>
                </div>
                <div class="feature">
                    <h3>🌐 Landing Pages</h3>
                    <p>High-converting landing page copy. Headlines, subheads, CTAs included.</p>
                </div>
                <div class="feature">
                    <h3>🎯 Multiple Tones</h3>
                    <p>Professional, casual, friendly, authoritative, or humorous — you choose.</p>
                </div>
            </div>
        </div>
    </section>

    <section class="pricing" id="pricing">
        <div class="container">
            <h2>Simple, Transparent Pricing</h2>
            <div class="pricing-grid">
                <div class="plan">
                    <div class="plan-name">Free</div>
                    <div class="plan-price">$0 <span>/month</span></div>
                    <ul class="plan-features">
                        <li>100 requests/month</li>
                        <li>50,000 words/month</li>
                        <li>All content types</li>
                        <li>Community support</li>
                    </ul>
                    <a href="/docs" class="cta" style="background: #666;">Get Started</a>
                </div>
                <div class="plan popular">
                    <div class="plan-name">Agency</div>
                    <div class="plan-price">$199 <span>/month</span></div>
                    <ul class="plan-features">
                        <li>2,000 requests/month</li>
                        <li>1,000,000 words/month</li>
                        <li>All content types</li>
                        <li>Priority support</li>
                        <li>White-label option</li>
                    </ul>
                    <a href="/docs" class="cta">Get Started</a>
                </div>
                <div class="plan">
                    <div class="plan-name">Enterprise</div>
                    <div class="plan-price">$499 <span>/month</span></div>
                    <ul class="plan-features">
                        <li>Unlimited requests</li>
                        <li>Unlimited words</li>
                        <li>All content types</li>
                        <li>Dedicated support</li>
                        <li>Custom integrations</li>
                    </ul>
                    <a href="/docs" class="cta" style="background: #666;">Contact Us</a>
                </div>
            </div>
        </div>
    </section>

    <section class="how-it-works">
        <div class="container">
            <h2>How It Works</h2>
            <div class="steps">
                <div class="step">
                    <div class="step-number">1</div>
                    <h3>Get Your API Key</h3>
                    <p>Sign up at /docs and get an API key instantly. No credit card required.</p>
                </div>
                <div class="step">
                    <div class="step-number">2</div>
                    <h3>Make a Request</h3>
                    <p>Send a POST request with your topic, content type, and preferred tone.</p>
                </div>
                <div class="step">
                    <div class="step-number">3</div>
                    <h3>Get Content</h3>
                    <p>Receive professionally written content in seconds. Edit or use as-is.</p>
                </div>
            </div>
        </div>
    </section>

    <section class="code-section">
        <div class="container">
            <h2>One Request, Endless Content</h2>
            <div class="code-block">
                <pre><code><span class="code-comment"># Generate a blog post</span>
curl -X POST https://ai-content-api-gvr1.onrender.com/v1/generate \\
  -H <span class="code-string">"Content-Type: application/json"</span> \\
  -d <span class="code-string">'{
    "content_type": "blog_post",
    "topic": "10 Tips for Remote Work",
    "tone": "professional",
    "keywords": ["remote work", "productivity"]
  }'</span>

<span class="code-comment"># Response</span>
{
  <span class="code-string">"content"</span>: <span class="code-string">"# 10 Tips for Remote Work Success\n\nWorking remotely..."</span>,
  <span class="code-string">"word_count"</span>: 850,
  <span class="code-string">"tokens_used"</span>: 1200,
  <span class="code-string">"remaining_quota"</span>: 99
}</code></pre>
            </div>
        </div>
    </section>

    <footer>
        <div class="container">
            <p>Built for content agencies. Powered by OpenAI.</p>
        </div>
    </footer>
</body>
</html>
"""


# PayPal API endpoints
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com" if settings.paypal_mode == "sandbox" else "https://api-m.paypal.com"


def get_paypal_token():
    """Get PayPal access token"""
    auth = (settings.paypal_client_id, settings.paypal_client_secret)
    response = requests.post(
        f"{PAYPAL_BASE_URL}/v1/oauth2/token",
        auth=auth,
        data={"grant_type": "client_credentials"}
    )
    return response.json().get("access_token")


app = FastAPI(
    title="ContentGen API",
    description="AI-powered content generation API for content agencies",
    version="1.0.0"
)

# CORS - allow all for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# MOCK DATABASE (Replace with Supabase/PostgreSQL in production)
# ============================================================================

# In-memory user storage for MVP
users_db = {}

# Plan quotas (requests per month)
PLAN_QUOTAS = {
    "free": {"requests": 100, "words": 50000},
    "starter": {"requests": 500, "words": 200000},
    "agency": {"requests": 2000, "words": 1000000},
    "enterprise": {"requests": 999999999, "words": 999999999},
}


# Plan prices in USD
PLAN_PRICES = {
    "starter": 49,
    "agency": 199,
    "enterprise": 499,
}


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Extract user from API key. 
    In production: verify Clerk JWT or your own API key system.
    MVP: accept any key and mock a user.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    # MVP: use the key as user ID
    user_id = authorization.replace("Bearer ", "")
    
    if user_id not in users_db:
        # Create user on first use
        users_db[user_id] = {
            "id": user_id,
            "plan": "free",
            "requests_this_month": 0,
            "words_this_month": 0,
        }
    
    return users_db[user_id]


@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page"""
    return LANDING_PAGE


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "ContentGen API", "version": "1.0.0"}


@app.post("/v1/generate", response_model=GenerateResponse)
async def generate(
    request: GenerateRequest,
    user: dict = Depends(get_current_user)
):
    """Generate content based on topic and type"""
    
    # Check quota
    plan = user["plan"]
    quota = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])
    
    if user["requests_this_month"] >= quota["requests"]:
        raise HTTPException(
            status_code=429, 
            detail="Quota exceeded. Upgrade your plan."
        )
    
    # Generate content
    try:
        content, tokens_used = await generate_content(request)
        word_count = len(content.split())
        
        # Check word quota
        if user["words_this_month"] + word_count > quota["words"]:
            raise HTTPException(
                status_code=429,
                detail="Word quota exceeded. Upgrade your plan."
            )
        
        # Update usage
        user["requests_this_month"] += 1
        user["words_this_month"] += word_count
        
        return GenerateResponse(
            content=content,
            word_count=word_count,
            content_type=request.content_type,
            tokens_used=tokens_used,
            remaining_quota=quota["requests"] - user["requests_this_month"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.get("/v1/usage", response_model=UsageResponse)
async def get_usage(user: dict = Depends(get_current_user)):
    """Get current user's usage statistics"""
    plan = user["plan"]
    quota = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])
    
    return UsageResponse(
        requests_this_month=user["requests_this_month"],
        words_generated_this_month=user["words_this_month"],
        current_plan=plan,
        quota_remaining=quota["requests"] - user["requests_this_month"],
        quota_total=quota["requests"]
    )


# ============================================================================
# PAYPAL CHECKOUT
# ============================================================================

@app.post("/v1/create-paypal-order")
async def create_paypal_order(plan: str, user: dict = Depends(get_current_user)):
    """Create a PayPal order for upgrading plan"""
    if plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    price = PLAN_PRICES[plan]
    
    try:
        # Get PayPal token
        token = get_paypal_token()
        
        # Create order
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": "USD",
                    "value": str(price)
                },
                "description": f"ContentGen API - {plan.title()} Plan"
            }],
            "application_context": {
                "return_url": f"{settings.app_url}/dashboard?success=true&plan={plan}",
                "cancel_url": f"{settings.app_url}/dashboard?canceled=true"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{PAYPAL_BASE_URL}/v2/checkout/orders",
            json=order_data,
            headers=headers
        )
        
        order = response.json()
        
        # Find approval URL
        approve_url = None
        for link in order.get("links", []):
            if link.get("rel") == "approve":
                approve_url = link.get("href")
                break
        
        return {
            "order_id": order.get("id"),
            "approve_url": approve_url,
            "plan": plan,
            "price": price
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PayPal error: {str(e)}")


@app.post("/v1/capture-paypal-order")
async def capture_paypal_order(order_id: str, user: dict = Depends(get_current_user)):
    """Capture (complete) a PayPal order after approval"""
    try:
        token = get_paypal_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture",
            headers=headers
        )
        
        result = response.json()
        
        if result.get("status") == "COMPLETED":
            # Update user plan - you would extract plan from metadata in production
            # For MVP, just upgrade to agency
            user["plan"] = "agency"
            return {"status": "success", "message": "Plan upgraded to agency"}
        
        return {"status": "pending", "details": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PayPal capture error: {str(e)}")


# ============================================================================
# PLANS INFO
# ============================================================================

@app.get("/v1/plans")
async def get_plans():
    """Get available plans and prices"""
    return {
        "plans": [
            {"name": "free", "price": 0, "requests": 100, "words": 50000},
            {"name": "starter", "price": 49, "requests": 500, "words": 200000},
            {"name": "agency", "price": 199, "requests": 2000, "words": 1000000},
            {"name": "enterprise", "price": 499, "requests": "unlimited", "words": "unlimited"},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)