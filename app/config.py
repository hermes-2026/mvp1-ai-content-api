from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """App configuration - loads from .env file"""
    
    # OpenAI
    openai_api_key: str = ""
    
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    
    # PayPal
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    paypal_mode: str = "sandbox"  # sandbox or live
    
    # App
    app_url: str = "http://localhost:8000"
    environment: str = "development"
    
    # Auth (Clerk)
    clerk_publishable_key: str = ""
    clerk_secret_key: str = ""
    
    class Config:
        env_file = "/home/openclaw/.openclaw/workspace/.env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()