from supabase import create_client, Client
from app.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Optional[Client] = None

def init_db():
    """Initialize Supabase connection"""
    global supabase
    if settings.supabase_url and settings.supabase_key:
        try:
            supabase = create_client(settings.supabase_url, settings.supabase_key)
            # Test connection - create users table if not exists
            try:
                supabase.table("users").select("*").limit(1).execute()
            except Exception as e:
                logger.info(f"Creating users table: {e}")
                # Table doesn't exist, create it
                supabase.table("users").create({
                    "id": "text primary key",
                    "email": "text unique not null",
                    "password_hash": "text not null",
                    "api_key": "text unique not null",
                    "plan": "text default 'free'",
                    "requests_this_month": "int default 0",
                    "words_this_month": "int default 0",
                    "created_at": "timestamp with time zone default now()",
                    "last_reset": "timestamp with time zone default now()"
                }).execute()
            logger.info("Supabase connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            supabase = None
    else:
        logger.warning("Supabase credentials not configured")
    return supabase

def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email"""
    if not supabase:
        return None
    result = supabase.table("users").select("*").eq("email", email).execute()
    return result.data[0] if result.data else None

def get_user_by_api_key(api_key: str) -> Optional[dict]:
    """Get user by API key"""
    if not supabase:
        return None
    result = supabase.table("users").select("*").eq("api_key", api_key).execute()
    return result.data[0] if result.data else None

def create_user(email: str, password_hash: str, api_key: str) -> dict:
    """Create new user"""
    if not supabase:
        return None
    data = {
        "id": api_key,
        "email": email,
        "password_hash": password_hash,
        "api_key": api_key,
        "plan": "free",
        "requests_this_month": 0,
        "words_this_month": 0
    }
    result = supabase.table("users").insert(data).execute()
    return result.data[0]

def update_user(api_key: str, updates: dict) -> dict:
    """Update user"""
    if not supabase:
        return None
    result = supabase.table("users").update(updates).eq("api_key", api_key).execute()
    return result.data[0] if result.data else None