"""
Main FastAPI application entry point.
Configures the application with middleware, error handling, and routes.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import time
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.routes.content import router as content_router
from app.schemas.content import ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize services here if needed
    try:
        # Test AI agent initialization
        from app.tools.agents import get_content_agents
        agents = get_content_agents()
        logger.info("AI agents initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI agents: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    **Automate Copywriter API** - AI-powered content generation using advanced agents.
    
    This API provides intelligent content generation capabilities using:
    - **AI Agents**: Multi-agent system for research, writing, and editing
    - **Web Scraping**: Jina AI integration for real-time information gathering
    - **SEO Optimization**: Built-in SEO analysis and optimization
    - **Multiple Content Types**: Blog posts, articles, social media, and more
    
    ## Features
    
    * **Intelligent Research**: AI agents research topics using web scraping and search
    * **Content Generation**: Generate various types of content with different tones
    * **SEO Optimization**: Automatic SEO analysis and keyword optimization
    * **Quality Control**: Multi-stage content review and editing process
    * **Flexible Configuration**: Customizable tone, audience, and content requirements
    
    ## Getting Started
    
    1. Set up your environment variables (see .env.example)
    2. Make a POST request to `/api/v1/content/generate`
    3. Specify your content requirements in the request body
    4. Receive high-quality, SEO-optimized content
    """,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    )


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=f"HTTP_{exc.status_code}",
            message=exc.detail,
            details={"path": str(request.url)}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with consistent error format."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details={"path": str(request.url)}
        ).dict()
    )


# Include routers
app.include_router(content_router)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        Dictionary with API information and available endpoints
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs" if settings.debug else "Documentation disabled in production",
        "endpoints": {
            "content_generation": "/api/v1/content/generate",
            "blog_post": "/api/v1/content/generate/blog-post",
            "seo_optimization": "/api/v1/content/optimize-seo",
            "health_check": "/api/v1/content/health",
            "generation_history": "/api/v1/content/history",
            "statistics": "/api/v1/content/stats"
        }
    }

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Simple health check endpoint.
    
    Returns:
        Dictionary with basic health status
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": time.time()
    }


# Custom OpenAPI schema
def custom_openapi():
    """Custom OpenAPI schema with additional information."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom information
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
