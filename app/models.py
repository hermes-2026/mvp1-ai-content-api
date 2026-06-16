from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ContentType(str, Enum):
    """Type of content to generate"""
    BLOG_POST = "blog_post"
    SOCIAL_POST = "social_post"
    EMAIL = "email"
    LANDING_PAGE = "landing_page"
    PRODUCT_DESCRIPTION = "product_description"


class Tone(str, Enum):
    """Tone of the content"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    HUMOROUS = "humorous"


class GenerateRequest(BaseModel):
    """Request to generate content"""
    topic: str = Field(..., description="The main topic or keyword")
    content_type: ContentType = Field(default=ContentType.BLOG_POST)
    tone: Tone = Field(default=Tone.PROFESSIONAL)
    word_count: Optional[int] = Field(default=500, ge=100, le=3000)
    keywords: Optional[List[str]] = Field(default=[], description="SEO keywords to include")
    extra_instructions: Optional[str] = Field(default="", description="Any extra guidance")


class GenerateResponse(BaseModel):
    """Response from content generation"""
    content: str
    word_count: int
    content_type: ContentType
    tokens_used: int
    remaining_quota: int


class UsageResponse(BaseModel):
    """User usage statistics"""
    requests_this_month: int
    words_generated_this_month: int
    current_plan: str
    quota_remaining: int
    quota_total: int