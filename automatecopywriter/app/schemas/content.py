"""
Pydantic schemas for content generation API.
Defines request and response models for the FastAPI endpoints.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
import datetime


class ContentType(str, Enum):
    """Enumeration of supported content types."""
    BLOG_POST = "blog_post"
    ARTICLE = "article"
    SOCIAL_MEDIA_POST = "social_media_post"
    PRODUCT_DESCRIPTION = "product_description"
    EMAIL_CAMPAIGN = "email_campaign"
    LANDING_PAGE = "landing_page"


class Tone(str, Enum):
    """Enumeration of supported content tones."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"
    CREATIVE = "creative"


class TargetAudience(str, Enum):
    """Enumeration of target audience types."""
    GENERAL = "general"
    TECHNICAL = "technical"
    BUSINESS = "business"
    CONSUMER = "consumer"
    DEVELOPER = "developer"
    MARKETING = "marketing"
    SALES = "sales"


class ContentGenerationRequest(BaseModel):
    """Request model for content generation."""
    
    topic: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="The topic or title for the content to be generated"
    )
    
    content_type: ContentType = Field(
        default=ContentType.BLOG_POST,
        description="Type of content to generate"
    )
    
    tone: Tone = Field(
        default=Tone.PROFESSIONAL,
        description="The desired tone for the content"
    )
    
    target_audience: TargetAudience = Field(
        default=TargetAudience.GENERAL,
        description="The target audience for the content"
    )
    
    include_seo: bool = Field(
        default=True,
        description="Whether to include SEO optimization in the content"
    )
    
    max_length: Optional[int] = Field(
        default=None,
        ge=100,
        le=10000,
        description="Maximum length of the generated content in characters"
    )
    
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Specific keywords to include in the content"
    )
    
    additional_requirements: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Additional requirements or instructions for content generation"
    )
    
    @validator('topic')
    def validate_topic(cls, v):
        """Validate that the topic is meaningful."""
        if not v.strip():
            raise ValueError('Topic cannot be empty or just whitespace')
        return v.strip()
    
    @validator('keywords')
    def validate_keywords(cls, v):
        """Validate keywords list."""
        if v is not None:
            if len(v) > 20:
                raise ValueError('Too many keywords provided (max 20)')
            # Remove empty keywords
            v = [kw.strip() for kw in v if kw.strip()]
        return v


class ContentGenerationResponse(BaseModel):
    """Response model for content generation."""
    
    success: bool = Field(
        description="Whether the content generation was successful"
    )
    
    content: Optional[str] = Field(
        default=None,
        description="The generated content in markdown format"
    )
    
    content_type: ContentType = Field(
        description="The type of content that was generated"
    )
    
    topic: str = Field(
        description="The topic that was used for generation"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the generation process"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if generation failed"
    )
    
    generated_at: str = Field(
        default_factory=lambda: datetime.datetime.utcnow().isoformat(),
        description="Timestamp when the content was generated"
    )
    
    processing_time: Optional[float] = Field(
        default=None,
        description="Time taken to generate the content in seconds"
    )


class ContentGenerationStatus(BaseModel):
    """Status model for content generation progress."""
    
    status: str = Field(
        description="Current status of the generation process"
    )
    
    progress: int = Field(
        ge=0,
        le=100,
        description="Progress percentage (0-100)"
    )
    
    current_step: str = Field(
        description="Description of the current step being executed"
    )
    
    estimated_completion: Optional[datetime.datetime] = Field(
        default=None,
        description="Estimated time of completion"
    )


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(
        description="Health status of the service"
    )
    
    timestamp: str = Field(
        default_factory=lambda: datetime.datetime.utcnow().isoformat(),
        description="Timestamp of the health check"
    )
    
    version: str = Field(
        description="Application version"
    )
    
    dependencies: Dict[str, str] = Field(
        description="Status of external dependencies"
    )


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(
        description="Error type or code"
    )
    
    message: str = Field(
        description="Human-readable error message"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    
    timestamp: str = Field(
        default_factory=lambda: datetime.datetime.utcnow().isoformat(),
        description="Timestamp when the error occurred"
    )


# Landing page schemas

class SEOIntent(str, Enum):
    """Enumeration of supported SEO intents for landing pages."""
    TRANSACTIONAL = "transactional"
    INFORMATIONAL = "informational"
    COMMERCIAL = "commercial"
    NAVIGATIONAL = "navigational"


class HowItWorksStep(BaseModel):
    """A single step in the How It Works section."""
    step: int = Field(..., ge=1, description="Step number (1-based)")
    title: str = Field(..., min_length=3, max_length=120)
    description: str = Field(..., min_length=5, max_length=300)


class FAQItem(BaseModel):
    """A frequently asked question and its answer."""
    question: str = Field(..., min_length=5, max_length=200)
    answer: str = Field(..., min_length=5, max_length=600)


class LandingPageRequest(BaseModel):
    """Input parameters mapped from the provided columns to build a landing page JSON."""
    tool_name: str = Field(..., min_length=2, max_length=120, description="Tool Name column")
    feature_summary: str = Field(..., min_length=10, max_length=600, description="Feature Summary column")
    primary_keywords: List[str] = Field(..., min_items=1, max_items=20, description="Primary Keywords column")
    seo_intent: SEOIntent = Field(..., description="SEO Intent column")
    subjects: List[str] = Field(..., min_items=1, max_items=50, description="Subject/Exam Expansion column")

    # Optional overrides
    page_title_override: Optional[str] = Field(default=None, max_length=120)
    page_subtitle_override: Optional[str] = Field(default=None, max_length=300)
    strict_ai: bool = Field(default=False, description="If true, fail instead of using fallback template")
    require_seo: bool = Field(default=False, description="If true, response must include SEO analysis block")

    @validator("primary_keywords", each_item=True)
    def _validate_keywords_item(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("Keyword cannot be empty")
        return value

    @validator("subjects", each_item=True)
    def _validate_subjects_item(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("Subject cannot be empty")
        return value


class LandingPageResponse(BaseModel):
    """Landing page JSON structure to power the UI."""
    page_title: str
    page_subtitle: str
    how_it_works: List[HowItWorksStep]
    faq: List[FAQItem]


class LandingPageSEO(BaseModel):
    """SEO metadata generated by the agent."""
    meta_title: str = Field(..., min_length=3, max_length=120)
    meta_description: str = Field(..., min_length=20, max_length=180)
    extracted_keywords: List[str] = Field(default_factory=list, description="Keywords the agent recommends")


class LandingPageResponse(BaseModel):
    """Landing page JSON structure to power the UI, with SEO metadata."""
    page_title: str
    page_subtitle: str
    how_it_works: List[HowItWorksStep]
    faq: List[FAQItem]
    seo: LandingPageSEO