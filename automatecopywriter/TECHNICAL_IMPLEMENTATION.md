# 🔧 Technical Implementation Guide

Detailed technical documentation for developers working with the Automate Copywriter API.

## 📋 Table of Contents

1. [Development Setup](#development-setup)
2. [Code Architecture](#code-architecture)
3. [AI Agent Implementation](#ai-agent-implementation)
4. [API Implementation](#api-implementation)
5. [Database Schema](#database-schema)
6. [Configuration Management](#configuration-management)
7. [Error Handling Implementation](#error-handling-implementation)
8. [Testing Implementation](#testing-implementation)
9. [Deployment Guide](#deployment-guide)
10. [Performance Monitoring](#performance-monitoring)

## 🚀 Development Setup

### Prerequisites

```bash
# Python 3.8+
python --version

# Required system packages
pip install -r requirements.txt

# Environment setup
cp .env.example .env
# Edit .env with your API keys
```

### Project Structure

```
automatecopywriter/
├── app/                          # Main application package
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Configuration management
│   ├── routes/                  # API route definitions
│   │   ├── __init__.py
│   │   └── content.py           # Content-related endpoints
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── content_service.py   # Content generation service
│   │   └── seo_service.py       # SEO optimization service
│   ├── schemas/                 # Pydantic models
│   │   ├── __init__.py
│   │   └── content.py           # Request/response schemas
│   ├── tools/                   # External tool integrations
│   │   ├── __init__.py
│   │   ├── agents.py            # AI agent definitions
│   │   └── jina_tools.py        # Jina AI integration
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       └── helpers.py           # Common utilities
├── tests/                       # Test suite
├── docs/                        # Documentation
├── requirements.txt             # Python dependencies
├── .env.example                # Environment template
├── run.py                      # Application runner
└── README.md                   # Project documentation
```

## 🏗️ Code Architecture

### FastAPI Application Structure

```python
# app/main.py
from fastapi import FastAPI
from app.routes.content import router as content_router
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# Middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

# Router inclusion
app.include_router(content_router)
```

### Configuration Management

```python
# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Automate Copywriter API"
    app_version: str = "1.0.0"
    debug: bool = Field(default=True, env="DEBUG")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # API Keys
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")
    jina_api_key: Optional[str] = Field(default=None, env="JINA_API_KEY")
    
    # Model settings
    model_id: str = Field(default="gemini/gemini-2.5-flash", env="MODEL_ID")
    
    # Content settings
    max_research_steps: int = Field(default=5, env="MAX_RESEARCH_STEPS")
    max_content_length: int = Field(default=10000, env="MAX_CONTENT_LENGTH")
    default_tone: str = Field(default="professional", env="DEFAULT_TONE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

## 🤖 AI Agent Implementation

### Agent Base Classes

```python
# app/tools/agents.py
from smolagents import ToolCallingAgent, CodeAgent
from litellm import LiteLLMModel
from app.config import settings

class ContentGenerationAgents:
    def __init__(self):
        # Initialize LLM model
        self.model = LiteLLMModel(
            model=settings.model_id,
            api_key=settings.google_api_key
        )
        
        # Initialize agents
        self.research_agent = self._create_research_agent()
        self.writer_agent = self._create_writer_agent()
        self.blog_manager = self._create_blog_manager()
    
    def _create_research_agent(self) -> ToolCallingAgent:
        """Create research agent with web scraping tools."""
        return ToolCallingAgent(
            model=self.model,
            tools=[
                scrape_page_with_jina_ai,
                search_facts_with_jina_ai,
                get_seo_keywords,
                research_keyword_competition,
                analyze_content_keywords
            ],
            system_prompt="""You are a research specialist. Your job is to:
            1. Gather comprehensive information about the given topic
            2. Verify facts and check for accuracy
            3. Analyze competitor content and identify opportunities
            4. Extract relevant keywords and SEO data
            5. Provide structured research data for content creation"""
        )
    
    def _create_writer_agent(self) -> ToolCallingAgent:
        """Create writer agent for content generation."""
        return ToolCallingAgent(
            model=self.model,
            tools=[],
            system_prompt="""You are a professional content writer. Your job is to:
            1. Create engaging, well-structured content
            2. Maintain consistent tone and style
            3. Integrate SEO keywords naturally
            4. Ensure content meets length requirements
            5. Write for the specified target audience"""
        )
    
    def _create_blog_manager(self) -> CodeAgent:
        """Create blog manager for orchestration."""
        return CodeAgent(
            model=self.model,
            tools=[
                scrape_page_with_jina_ai,
                search_facts_with_jina_ai,
                get_seo_keywords,
                research_keyword_competition,
                analyze_content_keywords,
                DuckDuckGoSearchTool()
            ],
            system_prompt="""You are a content manager. Your job is to:
            1. Orchestrate the content creation process
            2. Coordinate between research and writing agents
            3. Ensure quality and consistency
            4. Handle error recovery and fallbacks
            5. Manage the complete workflow from research to final content"""
        )
```

### Agent Workflow Implementation

```python
async def generate_content(
    self,
    topic: str,
    content_type: str = "blog_post",
    tone: str = "professional",
    target_audience: str = "general",
    include_seo: bool = True,
    keywords: Optional[List[str]] = None,
    additional_requirements: Optional[str] = None
) -> Dict[str, Any]:
    """Generate content using AI agents."""
    
    # Create comprehensive prompt
    prompt = f"""
    Create a {content_type} about "{topic}" with the following requirements:
    
    Content Type: {content_type}
    Tone: {tone}
    Target Audience: {target_audience}
    Include SEO: {include_seo}
    Keywords: {keywords or 'Auto-generated'}
    Additional Requirements: {additional_requirements or 'None'}
    
    Process:
    1. Research the topic thoroughly using web scraping and fact-checking
    2. Analyze competitor content and identify opportunities
    3. Extract and research relevant keywords
    4. Generate high-quality, SEO-optimized content
    5. Ensure the content matches the specified tone and audience
    
    Return the final content with metadata including:
    - Word count
    - SEO score
    - Research sources used
    - Keywords integrated
    """
    
    # Execute content generation
    result = await self.blog_manager.run(prompt)
    
    return {
        "content": result.content,
        "metadata": result.metadata,
        "success": True
    }
```

## 🔌 API Implementation

### Route Definitions

```python
# app/routes/content.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.content import (
    ContentGenerationRequest,
    ContentGenerationResponse,
    SEOOptimizationRequest,
    SEOOptimizationResponse
)
from app.services.content_service import ContentGenerationService

router = APIRouter(prefix="/api/v1/content")

@router.post(
    "/generate",
    response_model=ContentGenerationResponse,
    summary="Generate content",
    description="Generate content on a specified topic with SEO optimization."
)
async def generate_content(
    request: ContentGenerationRequest,
    content_service: ContentGenerationService = Depends(get_content_service)
) -> ContentGenerationResponse:
    """Generate content based on the provided request."""
    try:
        result = await content_service.generate_content(
            topic=request.topic,
            content_type=request.content_type,
            tone=request.tone,
            target_audience=request.target_audience,
            include_seo=request.include_seo,
            keywords=request.keywords,
            max_length=request.max_length
        )
        
        return ContentGenerationResponse(
            success=True,
            content=result["content"],
            content_type=request.content_type,
            topic=request.topic,
            metadata=result["metadata"],
            generated_at=datetime.utcnow().isoformat(),
            processing_time=result["processing_time"]
        )
        
    except Exception as e:
        logger.error(f"Content generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Content generation failed: {str(e)}"
        )
```

### Service Layer Implementation

```python
# app/services/content_service.py
import time
from typing import Dict, Any, Optional, List
from app.tools.agents import ContentGenerationAgents
from app.config import settings

class ContentGenerationService:
    def __init__(self):
        self.agents = ContentGenerationAgents()
        self.generation_history = []
    
    async def generate_content(
        self,
        topic: str,
        content_type: str = "blog_post",
        tone: str = "professional",
        target_audience: str = "general",
        include_seo: bool = True,
        keywords: Optional[List[str]] = None,
        max_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate content using AI agents."""
        
        start_time = time.time()
        
        try:
            # Generate content using agents
            result = await self.agents.generate_content(
                topic=topic,
                content_type=content_type,
                tone=tone,
                target_audience=target_audience,
                include_seo=include_seo,
                keywords=keywords
            )
            
            processing_time = time.time() - start_time
            
            # Log generation
            generation_record = {
                "topic": topic,
                "content_type": content_type,
                "tone": tone,
                "target_audience": target_audience,
                "processing_time": processing_time,
                "timestamp": datetime.utcnow().isoformat(),
                "success": True
            }
            self.generation_history.append(generation_record)
            
            return {
                "content": result["content"],
                "metadata": result["metadata"],
                "processing_time": processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Log failed generation
            generation_record = {
                "topic": topic,
                "content_type": content_type,
                "tone": tone,
                "target_audience": target_audience,
                "processing_time": processing_time,
                "timestamp": datetime.utcnow().isoformat(),
                "success": False,
                "error": str(e)
            }
            self.generation_history.append(generation_record)
            
            raise e
```

## 🗄️ Database Schema

### In-Memory Storage (Current Implementation)

```python
# app/services/content_service.py
class ContentGenerationService:
    def __init__(self):
        self.generation_history = []  # List of generation records
        self.statistics = {
            "total_generations": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "average_processing_time": 0.0,
            "success_rate": 0.0
        }
    
    def get_generation_history(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent generation history."""
        recent_history = self.generation_history[-limit:]
        return {
            "history": {
                "recent_generations": recent_history,
                "total_generations": len(self.generation_history)
            },
            "success": True
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get generation statistics."""
        total = len(self.generation_history)
        successful = len([g for g in self.generation_history if g.get("success", False)])
        failed = total - successful
        
        avg_time = 0.0
        if total > 0:
            avg_time = sum(g.get("processing_time", 0) for g in self.generation_history) / total
        
        success_rate = (successful / total * 100) if total > 0 else 0.0
        
        return {
            "statistics": {
                "total_generations": total,
                "successful_generations": successful,
                "failed_generations": failed,
                "average_processing_time": avg_time,
                "success_rate": success_rate
            },
            "success": True
        }
```

### Future Database Schema (PostgreSQL)

```sql
-- Content generations table
CREATE TABLE content_generations (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    tone VARCHAR(50) NOT NULL,
    target_audience VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    processing_time DECIMAL(10,2),
    success BOOLEAN NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SEO data table
CREATE TABLE seo_data (
    id SERIAL PRIMARY KEY,
    generation_id INTEGER REFERENCES content_generations(id),
    keywords JSONB,
    seo_score INTEGER,
    competitor_analysis JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Usage statistics table
CREATE TABLE usage_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    total_generations INTEGER DEFAULT 0,
    successful_generations INTEGER DEFAULT 0,
    failed_generations INTEGER DEFAULT 0,
    average_processing_time DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## ⚙️ Configuration Management

### Environment Variables

```bash
# .env file
# Required
GOOGLE_API_KEY=your_google_api_key_here
MODEL_ID=gemini/gemini-2.5-flash

# Optional
JINA_API_KEY=your_jina_api_key_here
DEBUG=true
HOST=0.0.0.0
PORT=8000
MAX_RESEARCH_STEPS=5
MAX_CONTENT_LENGTH=10000
DEFAULT_TONE=professional

# Database (for future implementation)
DATABASE_URL=postgresql://user:password@localhost/automatecopywriter
REDIS_URL=redis://localhost:6379

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn_here
```

### Configuration Validation

```python
# app/config.py
from pydantic import validator
from typing import Optional

class Settings(BaseSettings):
    # ... existing fields ...
    
    @validator('google_api_key')
    def validate_google_api_key(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Google API key is required and must be valid')
        return v
    
    @validator('model_id')
    def validate_model_id(cls, v):
        valid_models = [
            'gemini/gemini-2.5-flash',
            'gemini/gemini-1.5-flash',
            'gemini/gemini-1.5-pro'
        ]
        if v not in valid_models:
            raise ValueError(f'Model ID must be one of: {valid_models}')
        return v
    
    @validator('max_content_length')
    def validate_max_content_length(cls, v):
        if v < 100 or v > 50000:
            raise ValueError('Max content length must be between 100 and 50000')
        return v
```

## 🛡️ Error Handling Implementation

### Custom Exception Classes

```python
# app/utils/exceptions.py
class ContentGenerationError(Exception):
    """Base exception for content generation errors."""
    pass

class ResearchError(ContentGenerationError):
    """Exception raised during research phase."""
    pass

class WritingError(ContentGenerationError):
    """Exception raised during writing phase."""
    pass

class SEOError(ContentGenerationError):
    """Exception raised during SEO optimization."""
    pass

class APIKeyError(ContentGenerationError):
    """Exception raised for API key issues."""
    pass
```

### Error Handling Middleware

```python
# app/main.py
from app.utils.exceptions import ContentGenerationError

@app.exception_handler(ContentGenerationError)
async def content_generation_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_message": str(exc),
            "error_type": type(exc).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(APIKeyError)
async def api_key_exception_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={
            "success": False,
            "error_message": "API key validation failed",
            "error_type": "APIKeyError",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### Retry Logic Implementation

```python
# app/utils/retry.py
import asyncio
from functools import wraps
from typing import Callable, Any

def retry(max_attempts: int = 3, delay: float = 1.0):
    """Decorator for retrying failed operations."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                    else:
                        raise last_exception
            
            return None
        return wrapper
    return decorator

# Usage in services
@retry(max_attempts=3, delay=1.0)
async def call_external_api(self, url: str) -> Dict[str, Any]:
    """Call external API with retry logic."""
    # Implementation here
    pass
```

## 🧪 Testing Implementation

### Unit Tests

```python
# tests/test_content_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.content_service import ContentGenerationService

class TestContentGenerationService:
    @pytest.fixture
    def content_service(self):
        return ContentGenerationService()
    
    @pytest.mark.asyncio
    async def test_generate_content_success(self, content_service):
        """Test successful content generation."""
        with patch.object(content_service.agents, 'generate_content') as mock_generate:
            mock_generate.return_value = {
                "content": "Test content",
                "metadata": {"word_count": 100}
            }
            
            result = await content_service.generate_content(
                topic="Test Topic",
                content_type="blog_post"
            )
            
            assert result["content"] == "Test content"
            assert "processing_time" in result
            assert len(content_service.generation_history) == 1
    
    @pytest.mark.asyncio
    async def test_generate_content_failure(self, content_service):
        """Test content generation failure."""
        with patch.object(content_service.agents, 'generate_content') as mock_generate:
            mock_generate.side_effect = Exception("Generation failed")
            
            with pytest.raises(Exception):
                await content_service.generate_content(
                    topic="Test Topic",
                    content_type="blog_post"
                )
            
            assert len(content_service.generation_history) == 1
            assert content_service.generation_history[0]["success"] == False
```

### Integration Tests

```python
# tests/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_content_generation_endpoint():
    """Test content generation endpoint."""
    payload = {
        "topic": "Test Topic",
        "content_type": "blog_post",
        "tone": "professional",
        "target_audience": "general",
        "include_seo": True
    }
    
    response = client.post("/api/v1/content/generate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] == True
    assert "content" in data
    assert data["topic"] == "Test Topic"
```

## 🚀 Deployment Guide

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "run.py"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - JINA_API_KEY=${JINA_API_KEY}
      - DEBUG=false
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app
    restart: unless-stopped
```

### Production Configuration

```python
# app/config.py - Production settings
class ProductionSettings(Settings):
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security settings
    cors_origins: List[str] = ["https://yourdomain.com"]
    
    # Performance settings
    max_workers: int = 4
    timeout: int = 300
    
    # Monitoring
    log_level: str = "INFO"
    sentry_dsn: Optional[str] = None
```

## 📊 Performance Monitoring

### Logging Configuration

```python
# app/utils/logging.py
import logging
import sys
from app.config import settings

def setup_logging():
    """Setup application logging."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log')
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()
```

### Performance Metrics

```python
# app/utils/metrics.py
import time
from functools import wraps
from typing import Callable, Any

def track_performance(func: Callable) -> Callable:
    """Decorator to track function performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log performance metrics
            logger.info(f"{func.__name__} executed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f}s: {str(e)}")
            raise
    
    return wrapper
```

This technical implementation guide provides detailed code examples and implementation patterns for developers working with the Automate Copywriter API. It covers all aspects from basic setup to advanced deployment and monitoring.
