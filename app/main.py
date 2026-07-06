from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.models import (
    GenerateRequest, 
    GenerateResponse, 
    UsageResponse,
    ContentType
)
from app.services.openai_service import generate_content, count_tokens
from app.db import init_db, get_user_by_email, get_user_by_api_key, create_user, update_user
from typing import Optional
from pydantic import BaseModel
import requests
import uuid
import hashlib
from datetime import datetime, timedelta

# Initialize database
init_db()


# ============================================================================
# AUTH HELPERS
# ============================================================================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_api_key() -> str:
    return f"cg_{uuid.uuid4().hex}"

def create_access_token(user_email: str) -> str:
    """Simple token generation - in production use JWT"""
    return f"token_{user_email}_{uuid.uuid4().hex}"

def verify_token(token: str, db: dict) -> Optional[dict]:
    """Verify token and return user - in production use JWT verification"""
    if not token.startswith("token_"):
        return None
    # Simple lookup
    for email, user in db.items():
        expected = f"token_{email}_"
        if token.startswith(expected):
            return user
    return None

def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    
    # Extract API key from token (format: token_email_uuid)
    if not token.startswith("token_"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Token format: token_{email}_{uuid}
    # Find the last underscore to extract email (email may contain @)
    after_token = token[6:]  # Remove "token_"
    last_underscore = after_token.rfind("_")
    if last_underscore <= 0:
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    email_part = after_token[:last_underscore]
    
    user = get_user_by_email(email_part)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Reset monthly usage on new month
    now = datetime.now()
    if user.get("last_reset"):
        last_reset = user["last_reset"]
        if isinstance(last_reset, str):
            last_reset = datetime.fromisoformat(last_reset.replace("Z", "+00:00"))
        if now.month != last_reset.month or now.year != last_reset.year:
            # Update in DB
            update_user(user["api_key"], {
                "requests_this_month": 0,
                "words_this_month": 0,
                "last_reset": now.isoformat()
            })
            user["requests_this_month"] = 0
            user["words_this_month"] = 0
            user["last_reset"] = now
    
    return user




LANDING_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ContentGen API - AI Content Generation for Agencies</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #6366f1; --primary-dark: #4f46e5; --primary-light: #818cf8; --text: #1e293b; --text-muted: #64748b; --bg: #ffffff; --bg-alt: #f8fafc; --border: #e2e8f0; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; color: var(--text); background: var(--bg); }
        .container { max-width: 1100px; margin: 0 auto; padding: 0 24px; }
        header { padding: 20px 0; border-bottom: 1px solid var(--border); position: sticky; top: 0; background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); z-index: 100; }
        header .container { display: flex; justify-content: space-between; align-items: center; }
        .logo { display: flex; align-items: center; gap: 10px; font-size: 22px; font-weight: 700; }
        .logo-icon { width: 36px; height: 36px; background: linear-gradient(135deg, var(--primary), var(--primary-light)); border-radius: 10px; display: flex; align-items: center; justify-content: center; }
        .logo-icon svg { width: 20px; height: 20px; color: white; }
        nav { display: flex; align-items: center; gap: 24px; }
        .nav-link { color: var(--text-muted); text-decoration: none; font-weight: 500; }
        .btn { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 14px; border: none; }
        .btn-primary { background: var(--primary-dark); color: white; box-shadow: 0 4px 14px rgba(79,70,229,0.35); }
        .btn-outline { background: transparent; color: var(--text-muted); border: 1.5px solid var(--border); }
        .hero { padding: 120px 0 100px; text-align: center; position: relative; overflow: hidden; }
        .hero::before { content:''; position: absolute; top:-50%; left:50%; transform:translateX(-50%); width:800px; height:800px; background:radial-gradient(circle,rgba(99,102,241,0.15),transparent 70%); }
        .hero h1 { font-size: 56px; font-weight: 800; margin-bottom: 24px; line-height: 1.1; }
        .hero h1 span { background: linear-gradient(135deg, var(--primary-dark), var(--primary-light)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .hero p { font-size: 20px; color: var(--text-muted); max-width: 600px; margin: 0 auto 40px; }
        .hero-btns { display: flex; gap: 16px; justify-content: center; }
        .features { padding: 120px 0; background: var(--bg-alt); }
        .section-title { text-align: center; font-size: 40px; font-weight: 700; margin-bottom: 60px; }
        .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px; }
        .feature { background: white; padding: 32px; border-radius: 16px; border: 1px solid var(--border); transition: all 0.3s; }
        .feature:hover { transform: translateY(-4px); border-color: var(--primary-light); }
        .feature-icon { width: 48px; height: 48px; background: linear-gradient(135deg, var(--primary), var(--primary-light)); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 20px; }
        .feature-icon svg { width: 24px; height: 24px; color: white; }
        .feature h3 { font-size: 18px; font-weight: 600; margin-bottom: 10px; text-align: left; }
        .feature p { color: var(--text-muted); font-size: 15px; text-align: left; }
        .pricing { padding: 120px 0; }
        .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; max-width: 900px; margin: 0 auto; }
        .plan { border: 1.5px solid var(--border); padding: 32px; border-radius: 16px; text-align: center; background: white; }
        .plan.popular { border-color: var(--primary); box-shadow: 0 8px 30px rgba(99,102,241,0.15); position: relative; }
        .plan.popular::before { content:'Most Popular'; position:absolute; top:-12px; left:50%; transform:translateX(-50%); background:var(--primary); color:white; padding:6px 16px; border-radius:20px; font-size:12px; font-weight:600; }
        .plan-name { font-size: 18px; font-weight: 600; margin-bottom: 8px; color: var(--text-muted); }
        .plan-price { font-size: 48px; font-weight: 800; margin-bottom: 8px; }
        .plan-price span { font-size: 16px; font-weight: 400; color: var(--text-muted); }
        .plan-features { list-style: none; margin: 24px 0; text-align: left; }
        .plan-features li { padding: 10px 0; color: var(--text); display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--border); }
        .plan-features .check { color: var(--primary); }
        .how-it-works { padding: 120px 0; background: var(--bg-alt); }
        .steps { display: grid; grid-template-columns: repeat(3,1fr); gap: 40px; max-width: 900px; margin: 0 auto; position: relative; }
        .steps::before { content:''; position: absolute; top: 32px; left: 15%; right: 15%; height: 2px; border-top: 2px dashed var(--border); z-index: 0; }
        .step { text-align: center; position: relative; z-index: 1; }
        .step-number { width: 64px; height: 64px; background: white; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 700; margin: 0 auto 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 2px solid var(--border); }
        .step:nth-child(1) .step-number { background: linear-gradient(135deg,#e0e7ff,#c7d2fe); border-color: #a5b4fc; }
        .step:nth-child(2) .step-number { background: linear-gradient(135deg,#c7d2fe,#a5b4fc); border-color: #818cf8; }
        .step:nth-child(3) .step-number { background: linear-gradient(135deg,#6366f1,#818cf8); border-color: #6366f1; color: white; }
        .step h3 { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
        .step p { color: var(--text-muted); font-size: 15px; }
        footer { padding: 60px 0; text-align: center; color: var(--text-muted); border-top: 1px solid var(--border); }
        @media (max-width: 768px) { .hero h1 { font-size: 36px; } .steps { grid-template-columns: 1fr; } .steps::before { display: none; } }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="logo"><div class="logo-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg></div>ContentGen API</div>
            <nav><a href="/docs" class="nav-link">API Docs</a><a href="/docs" class="btn btn-primary">Get Started</a></nav>
        </div>
    </header>
    <section class="hero">
        <div class="container">
            <h1>Generate <span>High-Converting Content</span><br>with AI</h1>
            <p>Blog posts, social media, emails, and product descriptions - powered by GPT-4. Perfect for agencies.</p>
            <div class="hero-btns"><a href="/docs" class="btn btn-primary">Try the API</a><a href="#pricing" class="btn btn-outline">View Pricing</a></div>
        </div>
    </section>
    <section class="features">
        <div class="container">
            <h2 class="section-title">What You Can Create</h2>
            <div class="features-grid">
                <div class="feature"><div class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/></svg></div><h3>Blog Posts</h3><p>SEO-optimized articles that rank.</p></div>
                <div class="feature"><div class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg></div><h3>Social Media</h3><p>Engaging posts for all platforms.</p></div>
                <div class="feature"><div class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg></div><h3>Emails</h3><p>Cold emails that get responses.</p></div>
                <div class="feature"><div class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg></div><h3>Products</h3><p>Compelling product descriptions.</p></div>
                <div class="feature"><div class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg></div><h3>Landing Pages</h3><p>High-converting copy.</p></div>
                <div class="feature"><div class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/></svg></div><h3>Multiple Tones</h3><p>Professional or friendly.</p></div>
            </div>
        </div>
    </section>
    <section class="pricing" id="pricing">
        <div class="container">
            <h2 class="section-title">Simple, Transparent Pricing</h2>
            <div class="pricing-grid">
                <div class="plan"><div class="plan-name">Free</div><div class="plan-price">$0<span>/month</span></div><ul class="plan-features"><li><span class="check">✓</span> 5 requests/month</li><li><span class="check">✓</span> 1,000 words/month</li><li><span class="check">✓</span> All content types</li></ul><a href="/docs" class="btn btn-outline">Get Started</a></div>
                <div class="plan popular"><div class="plan-name">Agency</div><div class="plan-price">$199<span>/month</span></div><ul class="plan-features"><li><span class="check">✓</span> 200 requests/month</li><li><span class="check">✓</span> 50,000 words/month</li><li><span class="check">✓</span> All content types</li><li><span class="check">✓</span> White-label</li></ul><a href="/docs" class="btn btn-primary">Get Started</a></div>
                <div class="plan"><div class="plan-name">Enterprise</div><div class="plan-price">$499<span>/month</span></div><ul class="plan-features"><li><span class="check">✓</span> Unlimited requests</li><li><span class="check">✓</span> Unlimited words</li><li><span class="check">✓</span> Dedicated support</li></ul><a href="/docs" class="btn btn-outline">Contact Us</a></div>
            </div>
        </div>
    </section>
    <section class="how-it-works">
        <div class="container">
            <h2 class="section-title">How It Works</h2>
            <div class="steps">
                <div class="step"><div class="step-number">1</div><h3>Get Your API Key</h3><p>Sign up at /docs and get a key instantly.</p></div>
                <div class="step"><div class="step-number">2</div><h3>Make a Request</h3><p>Send a POST request with your topic.</p></div>
                <div class="step"><div class="step-number">3</div><h3>Get Content</h3><p>Receive content in seconds.</p></div>
            </div>
        </div>
    </section>
    <footer><div class="container"><p>Built for content agencies. Powered by OpenAI.</p></div></footer>
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

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# ============================================================================
# MOCK DATABASE (Replace with Supabase/PostgreSQL in production)
# ============================================================================

# In-memory user storage for MVP
users_db = {}

# Plan quotas (requests per month)
PLAN_QUOTAS = {
    "free": {"requests": 5, "words": 1000},
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


@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page"""
    with open("static/index.html", "r") as f:
        return f.read()


@app.get("/signup", response_class=HTMLResponse)
async def signup_page():
    """Signup page"""
    with open("static/signup.html", "r") as f:
        return f.read()


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Login page"""
    with open("static/login.html", "r") as f:
        return f.read()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Dashboard page - requires auth"""
    with open("static/dashboard.html", "r") as f:
        return f.read()


# ============================================================================
# AUTH API ROUTES
# ============================================================================

class AuthSignupRequest(BaseModel):
    email: str
    password: str

class AuthLoginRequest(BaseModel):
    email: str
    password: str


@app.post("/v1/auth/signup")
async def signup(request: AuthSignupRequest):
    """Create a new account"""
    email = request.email.lower().strip()
    
    # Check if user exists
    existing = get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    api_key = generate_api_key()
    user = create_user(email, hash_password(request.password), api_key)
    
    # Create token
    token = create_access_token(email)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "email": email,
        "api_key": api_key
    }


@app.post("/v1/auth/login")
async def login(request: AuthLoginRequest):
    """Login to existing account"""
    email = request.email.lower().strip()
    
    # Check if user exists
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if user["password_hash"] != hash_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create token
    token = create_access_token(email)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "email": email,
        "api_key": user["api_key"]
    }


@app.get("/v1/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "email": user.get("email"),
        "api_key": user.get("api_key"),
        "plan": user.get("plan", "free"),
        "requests_this_month": user.get("requests_this_month", 0),
        "words_this_month": user.get("words_this_month", 0),
    }


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
        
        # Save to database
        update_user(user["api_key"], {
            "requests_this_month": user["requests_this_month"],
            "words_this_month": user["words_this_month"]
        })

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
            {"name": "free", "price": 0, "requests": 5, "words": 1000},
            {"name": "starter", "price": 49, "requests": 500, "words": 200000},
            {"name": "agency", "price": 199, "requests": 2000, "words": 1000000},
            {"name": "enterprise", "price": 499, "requests": "unlimited", "words": "unlimited"},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)