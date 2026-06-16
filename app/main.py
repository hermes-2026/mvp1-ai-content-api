from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
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


@app.get("/")
async def root():
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