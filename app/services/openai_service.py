from openai import OpenAI
from app.config import settings
from app.models import ContentType, Tone, GenerateRequest
import tiktoken


client = OpenAI(api_key=settings.openai_api_key)


# System prompts for each content type
SYSTEM_PROMPTS = {
    ContentType.BLOG_POST: """You are an expert SEO content writer. Write compelling, 
    well-structured blog posts that rank well in search engines. Use clear headings, 
    short paragraphs, and include the keywords naturally throughout.""",
    
    ContentType.SOCIAL_POST: """You are a social media copywriter. Write engaging, 
    scroll-stopping posts for Twitter/X, LinkedIn, or Instagram. Keep it punchy, 
    use emojis sparingly, and include a clear call to action.""",
    
    ContentType.EMAIL: """You are an email marketing expert. Write emails that get 
    opened and clicked. Use a strong subject line, compelling hook, and clear CTA.
    Keep paragraphs short for mobile readers.""",
    
    ContentType.LANDING_PAGE: """You are a conversion copywriter. Write landing page 
    copy that persuades visitors to take action. Use benefit-driven headlines, 
    social proof, and clear CTAs.""",
    
    ContentType.PRODUCT_DESCRIPTION: """You are an e-commerce copywriter. Write 
    product descriptions that sell. Focus on benefits, use sensory language, 
    and include key features naturally.""",
}


def build_user_prompt(request: GenerateRequest) -> str:
    """Build the user prompt from request data"""
    prompt = f"Write a {request.content_type.value.replace('_', ' ')} about: {request.topic}\n"
    
    if request.word_count:
        prompt += f"Target length: approximately {request.word_count} words.\n"
    
    if request.keywords:
        prompt += f"Include these keywords naturally: {', '.join(request.keywords)}\n"
    
    if request.extra_instructions:
        prompt += f"Additional instructions: {request.extra_instructions}\n"
    
    prompt += f"\nTone: {request.tone.value}"
    
    return prompt


async def generate_content(request: GenerateRequest) -> tuple[str, int]:
    """
    Generate content using OpenAI
    
    Returns:
        tuple: (generated_content, tokens_used)
    """
    system_prompt = SYSTEM_PROMPTS.get(request.content_type, SYSTEM_PROMPTS[ContentType.BLOG_POST])
    user_prompt = build_user_prompt(request)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cheap and fast
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
    except Exception as e:
        raise Exception(f"OpenAI error: {str(e)}")
    
    content = response.choices[0].message.content
    tokens_used = response.usage.total_tokens
    
    return content, tokens_used


def count_tokens(text: str) -> int:
    """Count tokens in text (approximate)"""
    try:
        enc = tiktoken.encoding_for_model("gpt-4o-mini")
        return len(enc.encode(text))
    except:
        # Fallback: ~4 chars per token
        return len(text) // 4