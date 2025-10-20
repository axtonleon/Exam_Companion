"""
FastAPI routes for content generation endpoints.
Handles HTTP requests for content generation and related functionality.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging

from app.services.content_service import get_content_service, ContentGenerationService
from app.services.seo_service import get_seo_service, SEOService
from app.schemas.content import (
    ContentGenerationRequest,
    ContentGenerationResponse,
    ContentGenerationStatus,
    HealthCheckResponse,
    ErrorResponse
)
from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/content",
    tags=["content"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


@router.post(
    "/generate",
    response_model=ContentGenerationResponse,
    summary="Generate content using AI agents",
    description="Generate various types of content using AI agents with SEO optimization and web scraping capabilities."
)
async def generate_content(
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    content_service: ContentGenerationService = Depends(get_content_service)
) -> ContentGenerationResponse:
    """
    Generate content based on the provided request.
    
    This endpoint uses AI agents to:
    1. Research the topic using web scraping and search
    2. Generate content based on the specified type and requirements
    3. Optimize the content for SEO if requested
    4. Edit and polish the final content
    
    Args:
        request: The content generation request
        background_tasks: FastAPI background tasks
        content_service: The content generation service
        
    Returns:
        ContentGenerationResponse: The generated content and metadata
        
    Raises:
        HTTPException: If content generation fails
    """
    try:
        logger.info(f"Received content generation request for topic: {request.topic}")
        
        # Generate content
        response = await content_service.generate_content(request)
        
        if not response.success:
            raise HTTPException(
                status_code=500,
                detail=f"Content generation failed: {response.error_message}"
            )
        
        # Log successful generation
        logger.info(f"Content generated successfully for topic: {request.topic}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in content generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during content generation"
        )


@router.post(
    "/generate/blog-post",
    response_model=ContentGenerationResponse,
    summary="Generate a blog post",
    description="Generate a blog post on the specified topic with SEO optimization."
)
async def generate_blog_post(
    topic: str,
    tone: str = "professional",
    target_audience: str = "general",
    include_seo: bool = True,
    max_length: Optional[int] = None,
    keywords: Optional[List[str]] = None,
    content_service: ContentGenerationService = Depends(get_content_service)
) -> ContentGenerationResponse:
    """
    Generate a blog post on the specified topic.
    
    Args:
        topic: The topic for the blog post
        tone: The desired tone (professional, casual, friendly, etc.)
        target_audience: The target audience (general, technical, business, etc.)
        include_seo: Whether to include SEO optimization
        max_length: Maximum length of the blog post
        keywords: Specific keywords to include
        content_service: The content generation service
        
    Returns:
        ContentGenerationResponse: The generated blog post
    """
    try:
        # Create request object
        request = ContentGenerationRequest(
            topic=topic,
            content_type="blog_post",
            tone=tone,
            target_audience=target_audience,
            include_seo=include_seo,
            max_length=max_length,
            keywords=keywords
        )
        
        # Generate content
        response = await content_service.generate_content(request)
        
        if not response.success:
            raise HTTPException(
                status_code=500,
                detail=f"Blog post generation failed: {response.error_message}"
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating blog post: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during blog post generation"
        )


@router.post(
    "/optimize-seo",
    summary="Optimize content for SEO",
    description="Optimize existing content for SEO with keyword analysis and suggestions."
)
async def optimize_content_seo(
    content: str,
    primary_keyword: str,
    secondary_keywords: Optional[List[str]] = None,
    seo_service: SEOService = Depends(get_seo_service)
) -> dict:
    """
    Optimize content for SEO.
    
    Args:
        content: The content to optimize
        primary_keyword: The primary keyword to focus on
        secondary_keywords: Optional secondary keywords
        seo_service: The SEO service
        
    Returns:
        Dictionary with optimization results and suggestions
    """
    try:
        optimization_result = seo_service.optimize_content_for_seo(
            content=content,
            primary_keyword=primary_keyword,
            secondary_keywords=secondary_keywords or []
        )
        
        return {
            "success": True,
            "optimization_result": optimization_result
        }
        
    except Exception as e:
        logger.error(f"Error optimizing content for SEO: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during SEO optimization"
        )


@router.get(
    "/history",
    summary="Get content generation history",
    description="Retrieve recent content generation history and statistics."
)
async def get_generation_history(
    limit: int = 10,
    content_service: ContentGenerationService = Depends(get_content_service)
) -> dict:
    """
    Get content generation history.
    
    Args:
        limit: Maximum number of history entries to return
        content_service: The content generation service
        
    Returns:
        Dictionary with generation history
    """
    try:
        history = content_service.get_generation_history(limit=limit)
        return {
            "success": True,
            "history": history
        }
        
    except Exception as e:
        logger.error(f"Error retrieving generation history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving history"
        )


@router.get(
    "/stats",
    summary="Get content generation statistics",
    description="Retrieve statistics about content generation performance."
)
async def get_generation_stats(
    content_service: ContentGenerationService = Depends(get_content_service)
) -> dict:
    """
    Get content generation statistics.
    
    Args:
        content_service: The content generation service
        
    Returns:
        Dictionary with generation statistics
    """
    try:
        stats = content_service.get_generation_stats()
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error retrieving generation statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving statistics"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check endpoint",
    description="Check the health status of the content generation service."
)
async def health_check() -> HealthCheckResponse:
    """
    Perform a health check on the service.
    
    Returns:
        HealthCheckResponse: Health status information
    """
    try:
        # Check dependencies
        dependencies = {
            "google_api": "healthy" if settings.google_api_key else "missing_key",
            "jina_api": "healthy" if settings.jina_api_key else "optional",
            "content_agents": "healthy"
        }
        
        return HealthCheckResponse(
            status="healthy",
            version=settings.app_version,
            dependencies=dependencies
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            version=settings.app_version,
            dependencies={"error": str(e)}
        )


@router.get(
    "/content-types",
    summary="Get available content types",
    description="Retrieve list of available content types for generation."
)
async def get_content_types() -> dict:
    """
    Get available content types.
    
    Returns:
        Dictionary with available content types and their descriptions
    """
    content_types = {
        "blog_post": "Long-form blog post with research and SEO optimization",
        "article": "Informational article with detailed analysis",
        "social_media_post": "Short-form social media content",
        "product_description": "Product-focused marketing content",
        "email_campaign": "Email marketing content",
        "landing_page": "Landing page copy and content"
    }
    
    return {
        "success": True,
        "content_types": content_types
    }


@router.get(
    "/tones",
    summary="Get available content tones",
    description="Retrieve list of available content tones."
)
async def get_content_tones() -> dict:
    """
    Get available content tones.
    
    Returns:
        Dictionary with available tones and their descriptions
    """
    tones = {
        "professional": "Formal, business-appropriate tone",
        "casual": "Relaxed, conversational tone",
        "friendly": "Warm, approachable tone",
        "authoritative": "Expert, confident tone",
        "conversational": "Natural, dialogue-like tone",
        "technical": "Precise, industry-specific tone",
        "creative": "Imaginative, engaging tone"
    }
    
    return {
        "success": True,
        "tones": tones
    }


@router.post(
    "/keyword-research",
    summary="Advanced keyword research and analysis",
    description="Perform comprehensive keyword research including competition analysis and SEO suggestions."
)
async def keyword_research(
    query: str,
    include_competition: bool = True,
    content_service: ContentGenerationService = Depends(get_content_service)
) -> dict:
    """
    Perform advanced keyword research for a given query.
    
    Args:
        query: The search query to research keywords for
        include_competition: Whether to include competition analysis
        content_service: The content generation service
        
    Returns:
        Dictionary with keyword research results
    """
    try:
        from app.tools.jina_tools import get_seo_keywords, research_keyword_competition
        
        # Get SEO keywords
        seo_analysis = get_seo_keywords(query)
        
        result = {
            "success": True,
            "query": query,
            "seo_analysis": seo_analysis
        }
        
        # Add competition research if requested
        if include_competition:
            competition_analysis = research_keyword_competition(query)
            result["competition_analysis"] = competition_analysis
        
        return result
        
    except Exception as e:
        logger.error(f"Error in keyword research: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during keyword research"
        )


@router.post(
    "/analyze-content",
    summary="Analyze existing content for SEO",
    description="Analyze existing content to extract keywords and provide SEO recommendations."
)
async def analyze_content(
    content: str,
    content_service: ContentGenerationService = Depends(get_content_service)
) -> dict:
    """
    Analyze existing content for SEO optimization.
    
    Args:
        content: The content to analyze
        content_service: The content generation service
        
    Returns:
        Dictionary with content analysis results
    """
    try:
        from app.tools.jina_tools import analyze_content_keywords
        
        # Analyze content keywords
        analysis = analyze_content_keywords(content)
        
        return {
            "success": True,
            "content_length": len(content),
            "word_count": len(content.split()),
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during content analysis"
        )
