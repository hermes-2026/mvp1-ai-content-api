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
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --primary-light: #818cf8;
            --purple-glow: rgba(99, 102, 241, 0.15);
            --text: #1e293b;
            --text-muted: #64748b;
            --bg: #ffffff;
            --bg-alt: #f8fafc;
            --border: #e2e8f0;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: var(--text); background: var(--bg); }
        .container { max-width: 1100px; margin: 0 auto; padding: 0 24px; }
        
        /* Header */
        header { padding: 20px 0; border-bottom: 1px solid var(--border); position: sticky; top: 0; background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); z-index: 100; }
        header .container { display: flex; justify-content: space-between; align-items: center; }
        .logo { display: flex; align-items: center; gap: 10px; font-size: 22px; font-weight: 700; color: var(--text); }
        .logo-icon { width: 36px; height: 36px; background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center; }
        .logo-icon svg { width: 20px; height: 20px; color: white; }
        nav { display: flex; align-items: center; gap: 24px; }
        .nav-link { color: var(--text-muted); text-decoration: none; font-weight: 500; transition: color 0.2s; }
        .nav-link:hover { color: var(--primary); }
        .btn { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 14px; transition: all 0.2s; cursor: pointer; border: none; }
        .btn-primary { background: var(--primary-dark); color: white; box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35); }
        .btn-primary:hover { background: #4338ca; transform: translateY(-1px); box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4); }
        .btn-outline { background: transparent; color: var(--text-muted); border: 1.5px solid var(--border); }
        .btn-outline:hover { border-color: var(--primary); color: var(--primary); }
        
        /* Hero */
        .hero { padding: 120px 0 100px; text-align: center; position: relative; overflow: hidden; }
        .hero::before { content: ''; position: absolute; top: -50%; left: 50%; transform: translateX(-50%); width: 800px; height: 800px; background: radial-gradient(circle, var(--purple-glow) 0%, transparent 70%); pointer-events: none; }
        .hero h1 { font-size: 56px; font-weight: 800; margin-bottom: 24px; line-height: 1.1; letter-spacing: -0.02em; position: relative; }
        .hero h1 span { background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary-light) 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .hero p { font-size: 20px; color: var(--text-muted); max-width: 600px; margin: 0 auto 40px; }
        .hero-btns { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }
        
        /* Features */
        .features { padding: 120px 0; background: var(--bg-alt); }
        .section-title { text-align: center; font-size: 40px; font-weight: 700; margin-bottom: 60px; letter-spacing: -0.02em; }
        .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px; }
        .feature { background: white; padding: 32px; border-radius: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid var(--border); transition: all 0.3s; }
        .feature:hover { transform: translateY(-4px); box-shadow: 0 12px 40px rgba(99, 102, 241, 0.12); border-color: var(--primary-light); }
        .feature-icon { width: 48px; height: 48px; background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 20px; }
        .feature-icon svg { width: 24px; height: 24px; color: white; }
        .feature h3 { font-size: 18px; font-weight: 600; margin-bottom: 10px; text-align: left; }
        .feature p { color: var(--text-muted); font-size: 15px; text-align: left; line-height: 1.7; }
        
        /* Pricing */
        .pricing { padding: 120px 0; }
        .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; max-width: 900px; margin: 0 auto; }
        .plan { border: 1.5px solid var(--border); padding: 32px; border-radius: 16px; text-align: center; background: white; transition: all 0.3s; }
        .plan:hover { border-color: var(--primary-light); }
        .plan.popular { border-color: var(--primary); position: relative; box-shadow: 0 8px 30px rgba(99, 102, 241, 0.15); }
        .plan.popular::before { content: 'Most Popular'; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--primary); color: white; padding: 6px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .plan-name { font-size: 18px; font-weight: 600; margin-bottom: 8px; color: var(--text-muted); }
        .plan-price { font-size: 48px; font-weight: 800; margin-bottom: 8px; }
        .plan-price span { font-size: 16px; font-weight: 400; color: var(--text-muted); }
        .plan-features { list-style: none; margin: 24px 0; text-align: left; }
        .plan-features li { padding: 10px 0; color: var(--text); display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--border); }
        .plan-features li:last-child { border-bottom: none; }
        .plan-features .check { color: var(--primary); flex-shrink: 0; }
        .plan .btn { width: 100%; justify-content: center; }
        .plan.popular .btn { background: var(--primary-dark); color: white; }
        .plan:not(.popular) .btn { background: var(--bg-alt); color: var(--text); border: 1.5px solid var(--border); }
        .plan:not(.popular) .btn:hover { border-color: var(--primary); color: var(--primary); }
        
        /* How It Works */
        .how-it-works { padding: 120px 0; background: var(--bg-alt); }
        .steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; max-width: 900px; margin: 0 auto; position: relative; }
        .steps::before { content: ''; position: absolute; top: 32px; left: 15%; right: 15%; height: 2px; border-top: 2px dashed var(--border); z-index: 0; }
        .step { text-align: center; position: relative; z-index: 1; }
        .step-number { width: 64px; height: 64px; background: white; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 700; margin: 0 auto 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 2px solid var(--border); }
        .step:nth-child(1) .step-number { background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%); border-color: #a5b4fc; }
        .step:nth-child(2) .step-number { background: linear-gradient(135deg, #c7d2fe 0%, #a5b4fc 100%); border-color: #818cf8; }
        .step:nth-child(3) .step-number { background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%); border-color: #6366f1; color: white; }
        .step h3 { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
        .step p { color: var(--text-muted); font-size: 15px; }
        
        /* Code Section */
        .code-section { padding: 120px 0; }
        .code-section h2 { text-align: center; font-size: 36px; font-weight: 700; margin-bottom: 40px; }
        .code-block { background: #0f172a; color: #e2e8f0; padding: 32px; border-radius: 16px; overflow-x: auto; font-size: 14px; text-align: left; }
        .code-block code { font-family: 'JetBrains Mono', 'Fira Code', monospace; }
        .code-comment { color: #64748b; }
        .code-keyword { color: #818cf8; }
        .code-string { color: #34d399; }
        .code-url { color: #38bdf8; }
        
        /* Footer */
        footer { padding: 60px 0; text-align: center; color: var(--text-muted); border-top: 1px solid var(--border); }
        footer p { font-size: 15px; }
        
        @media (max-width: 768px) {
            .hero h1 { font-size: 36px; }
            .hero p { font-size: 17px; }
            .section-title { font-size: 28px; }
            .steps { grid-template-columns: 1fr; gap: 30px; }
            .steps::before { display: none; }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="logo">
                <div class="logo-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
                </div>
                ContentGen API
            </div>
            <nav>
                <a href="/docs" class="nav-link">API Docs →</a>
                <a href="/docs" class="btn btn-primary">Get Started</a>
            </nav>
        </div>
    </header>

    <section class="hero">
        <div class="container">
            <h1>Generate <span>High-Converting Content</span><br>with AI</h1>
            <p>Blog posts, social media, emails, and product descriptions — powered by GPT-4. Perfect for agencies and content teams.</p>
            <div class="hero-btns">
                <a href="/docs" class="btn btn-primary">Try the API</a>
                <a href="#pricing" class="btn btn-outline">View Pricing</a>
            </div>
        </div>
    </section>

    <section class="features">
        <div class="container">
            <h2 class="section-title">What You Can Create</h2>
            <div class="features-grid">
                <div class="feature">
                    <div class="feature-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>
                    </div>
                    <h3>Blog Posts</h3>
                    <p>SEO-optimized articles that rank and convert. Get 500-2000 words in seconds.</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
                    </div>
                    <h3>Social Media</h3>
                    <p>Engaging posts for Twitter, LinkedIn, Instagram. Capture attention instantly.</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                    </div>
                    <h3>Emails</h3>
                    <p>Cold emails, newsletters, and follow-ups that actually get responses.</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
                    </div>
                    <h3>Product Descriptions</h3>
                    <p>Compelling descriptions that drive sales for e-commerce and marketplaces.</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                    </div>
                    <h3>Landing Pages</h3>
                    <p>High-converting landing page copy. Headlines, subheads, CTAs included.</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
                    </div>
                    <h3>Multiple Tones</h3>
                    <p>Professional, casual, friendly, authoritative, or humorous — you choose.</p>
                </div>
            </div>
        </div>
    </section>

    <section class="pricing" id="pricing">
        <div class="container">
            <h2 class="section-title">Simple, Transparent Pricing</h2>
            <div class="pricing-grid">
                <div class="plan">
                    <div class="plan-name">Free</div>
                    <div class="plan-price">$0 <span>/month</span></div>
                    <ul class="plan-features">
                        <li><span class="check">✓</span> 5 requests/month</li>
                        <li><span class="check">✓</span> 1,000 words/month</li>
                        <li><span class="check">✓</span> All content types</li>
                        <li><span class="check">✓</span> Community support</li>
                    </ul>
                    <a href="/docs" class="btn">Get Started</a>
                </div>
                <div class="plan popular">
                    <div class="plan-name">Agency</div>
                    <div class="plan-price">$199 <span>/month</span></div>
                    <ul class="plan-features">
                        <li><span class="check">✓</span> 200 requests/month</li>
                        <li><span class="check">✓</span> 50,000 words/month</li>
                        <li><span class="check">✓</span> All content types</li>
                        <li><span class="check">✓</span> Priority support</li>
                        <li><span class="check">✓</span> White-label option</li>
                    </ul>
                    <a href="/docs" class="btn">Get Started</a>
                </div>
                <div class="plan">
                    <div class="plan-name">Enterprise</div>
                    <div class="plan-price">$499 <span>/month</span></div>
                    <ul class="plan-features">
                        <li><span class="check">✓</span> Unlimited requests</li>
                        <li><span class="check">✓</span> Unlimited words</li>
                        <li><span class="check">✓</span> All content types</li>
                        <li><span class="check">✓</span> Dedicated support</li>
                        <li><span class="check">✓</span> Custom integrations</li>
                    </ul>
                    <a href="/docs" class="btn">Contact Us</a>
                </div>
            </div>
        </div>
    </section>

    <section class="how-it-works">
        <div class="container">
            <h2 class="section-title">How It Works</h2>
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
curl -X POST <span class="code-url">https://your-app.onrender.com/v1/generate</span> \
  -H <span class="code-string">"Content-Type: application/json"</span> \
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
    "free": {"requests": 5, "words": 1000},
    "starter": {"requests": 50, "words": 10000},
    "agency": {"requests": 200, "words": 50000},
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