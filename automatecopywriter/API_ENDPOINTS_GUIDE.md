# 📚 Automate Copywriter API - Complete Endpoints Guide

This comprehensive guide explains all available API endpoints, their purposes, parameters, and usage examples.

## 🚀 Base URL and Authentication

- **Base URL**: `http://localhost:8000` (development)
- **API Prefix**: `/api/v1/content`
- **Authentication**: No authentication required (API keys handled server-side)

## 📋 Table of Contents

1. [Root & Health Endpoints](#root--health-endpoints)
2. [Information Endpoints](#information-endpoints)
3. [Content Generation Endpoints](#content-generation-endpoints)
4. [SEO & Analysis Endpoints](#seo--analysis-endpoints)
5. [Statistics Endpoints](#statistics-endpoints)
6. [Content Types & Tones](#content-types--tones)
7. [Error Handling](#error-handling)
8. [Testing Examples](#testing-examples)

---

## 🏠 Root & Health Endpoints

### 1. Root Endpoint
**GET** `/`

**Purpose**: Get basic API information and available endpoints

**Response**:
```json
{
  "message": "Welcome to Automate Copywriter API",
  "version": "1.0.0",
  "status": "running",
  "docs_url": "/docs",
  "endpoints": {
    "content_generation": "/api/v1/content/generate",
    "blog_post": "/api/v1/content/generate/blog-post",
    "seo_optimization": "/api/v1/content/optimize-seo",
    "health_check": "/api/v1/content/health",
    "generation_history": "/api/v1/content/history",
    "statistics": "/api/v1/content/stats"
  }
}
```

### 2. Basic Health Check
**GET** `/health`

**Purpose**: Simple health status check

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 3. Detailed Health Check
**GET** `/api/v1/content/health`

**Purpose**: Detailed health check with dependency status

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:00:00Z",
  "dependencies": {
    "google_api": "healthy",
    "jina_api": "healthy",
    "content_agents": "healthy"
  }
}
```

---

## 📋 Information Endpoints

### 4. Get Content Types
**GET** `/api/v1/content/content-types`

**Purpose**: Retrieve all available content types for generation

**Response**:
```json
{
  "success": true,
  "content_types": {
    "blog_post": "Long-form blog post with research and SEO optimization",
    "article": "Informational article with detailed analysis",
    "social_media_post": "Short-form social media content",
    "product_description": "Product-focused marketing content",
    "email_campaign": "Email marketing content",
    "landing_page": "Landing page copy and content"
  }
}
```

### 5. Get Available Tones
**GET** `/api/v1/content/tones`

**Purpose**: Retrieve all available content tones

**Response**:
```json
{
  "success": true,
  "tones": {
    "professional": "Formal, business-appropriate tone",
    "casual": "Relaxed, conversational tone",
    "friendly": "Warm, approachable tone",
    "authoritative": "Expert, confident tone",
    "conversational": "Natural, dialogue-like tone",
    "technical": "Precise, industry-specific tone",
    "creative": "Imaginative, engaging tone"
  }
}
```

---

## ✍️ Content Generation Endpoints

### 6. Main Content Generation
**POST** `/api/v1/content/generate`

**Purpose**: Generate any type of content using AI agents with web research and SEO optimization

**Request Body** (JSON):
```json
{
  "topic": "The Future of Artificial Intelligence in Healthcare",
  "content_type": "blog_post",
  "tone": "professional",
  "target_audience": "technical",
  "include_seo": true,
  "max_length": 2000,
  "keywords": ["AI", "healthcare", "machine learning"],
  "additional_requirements": "Include recent statistics and case studies"
}
```

**Parameters**:
- `topic` (required): The topic or title for content generation (5-500 characters)
- `content_type` (optional): Type of content (default: "blog_post")
- `tone` (optional): Content tone (default: "professional")
- `target_audience` (optional): Target audience (default: "general")
- `include_seo` (optional): Include SEO optimization (default: true)
- `max_length` (optional): Maximum content length (100-10000 characters)
- `keywords` (optional): List of keywords to include (max 20)
- `additional_requirements` (optional): Additional instructions (max 1000 characters)

**Response**:
```json
{
  "success": true,
  "content": "# The Future of Artificial Intelligence in Healthcare...",
  "content_type": "blog_post",
  "topic": "The Future of Artificial Intelligence in Healthcare",
  "metadata": {
    "research_sources": 5,
    "seo_score": 85,
    "word_count": 1500
  },
  "error_message": null,
  "generated_at": "2024-01-01T12:00:00Z",
  "processing_time": 45.2
}
```

### 7. Blog Post Generation (Simplified)
**POST** `/api/v1/content/generate/blog-post`

**Purpose**: Simplified blog post generation using query parameters

**Query Parameters**:
- `topic` (required): The topic for the blog post
- `tone` (optional): Desired tone (default: "professional")
- `target_audience` (optional): Target audience (default: "general")
- `include_seo` (optional): Include SEO optimization (default: true)
- `max_length` (optional): Maximum length
- `keywords` (optional): Comma-separated keywords

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/content/generate/blog-post?topic=AI%20Content%20Creation&tone=casual&target_audience=general&include_seo=true"
```

**Response**: Same format as main content generation endpoint

---

## 🔍 SEO & Analysis Endpoints

### 8. Keyword Research
**POST** `/api/v1/content/keyword-research`

**Purpose**: Perform comprehensive keyword research and competition analysis

**Query Parameters**:
- `query` (required): The search query to research
- `include_competition` (optional): Include competition analysis (default: true)

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/content/keyword-research?query=AI%20content%20creation&include_competition=true"
```

**Response**:
```json
{
  "success": true,
  "query": "AI content creation",
  "seo_analysis": "SEO Keyword Analysis for: \"AI content creation\"\n\n🎯 PRIMARY KEYWORDS: ai, content, creation\n\n📝 LONG-TAIL KEYWORDS: ai content, content creation, ai content creation\n\n🔄 SEMANTIC VARIATIONS: ai guide, content tips, creation tutorial\n\n❓ QUESTION KEYWORDS: what ai content creation, how ai content creation\n\n🎯 INTENT KEYWORDS: buy ai content creation, learn ai content creation\n\n📊 TOTAL KEYWORDS: 15\n🔍 RECOMMENDED FOCUS: ai",
  "competition_analysis": "Keyword Competition Research for: \"AI content creation\"\n\n🔍 SEARCH RESULTS ANALYSIS: [Detailed analysis...]\n\n📊 KEYWORD INSIGHTS:\n- Primary keyword: AI content creation\n- Search intent: Commercial/Informational\n- Competition level: Medium (estimated)\n\n💡 RECOMMENDATIONS:\n1. Focus on long-tail variations\n2. Consider semantic variations and synonyms\n3. Target question-based queries"
}
```

### 9. SEO Optimization
**POST** `/api/v1/content/optimize-seo`

**Purpose**: Optimize existing content for SEO with keyword analysis

**Query Parameters**:
- `content` (required): The content to optimize
- `primary_keyword` (required): The primary keyword to focus on
- `secondary_keywords` (optional): Comma-separated secondary keywords

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/content/optimize-seo?content=Your%20content%20here&primary_keyword=AI%20content&secondary_keywords=automation,content%20marketing"
```

**Response**:
```json
{
  "success": true,
  "optimization_result": {
    "original_score": 65,
    "optimized_score": 85,
    "improvements": [
      "Added primary keyword in title",
      "Improved keyword density",
      "Added semantic variations"
    ],
    "optimized_content": "Optimized version of your content..."
  }
}
```

### 10. Content Analysis
**POST** `/api/v1/content/analyze-content`

**Purpose**: Analyze existing content to extract keywords and provide SEO recommendations

**Query Parameters**:
- `content` (required): The content to analyze

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/content/analyze-content?content=Your%20content%20to%20analyze"
```

**Response**:
```json
{
  "success": true,
  "content_length": 1250,
  "word_count": 200,
  "analysis": {
    "keyword_density": {
      "ai": 2.5,
      "content": 3.2,
      "creation": 1.8
    },
    "seo_score": 72,
    "recommendations": [
      "Increase primary keyword density",
      "Add more semantic variations",
      "Improve content structure"
    ]
  }
}
```

---

## 📊 Statistics Endpoints

### 11. Generation History
**GET** `/api/v1/content/history`

**Purpose**: Retrieve recent content generation history and statistics

**Query Parameters**:
- `limit` (optional): Maximum number of history entries (default: 10)

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/content/history?limit=5"
```

**Response**:
```json
{
  "success": true,
  "history": {
    "total_generations": 25,
    "recent_generations": [
      {
        "topic": "AI in Healthcare",
        "content_type": "blog_post",
        "generated_at": "2024-01-01T12:00:00Z",
        "processing_time": 45.2,
        "success": true
      }
    ]
  }
}
```

### 12. Generation Statistics
**GET** `/api/v1/content/stats`

**Purpose**: Retrieve comprehensive statistics about content generation performance

**Response**:
```json
{
  "success": true,
  "statistics": {
    "total_generations": 150,
    "success_rate": 96.7,
    "average_processing_time": 42.5,
    "content_types": {
      "blog_post": 85,
      "article": 32,
      "social_media_post": 18,
      "product_description": 10,
      "email_campaign": 3,
      "landing_page": 2
    },
    "tones": {
      "professional": 65,
      "casual": 45,
      "friendly": 25,
      "authoritative": 15
    }
  }
}
```

---

## 📝 Content Types & Tones

### Available Content Types
- **`blog_post`**: Long-form blog posts with research and SEO optimization
- **`article`**: Informational articles with detailed analysis
- **`social_media_post`**: Short-form social media content
- **`product_description`**: Product-focused marketing content
- **`email_campaign`**: Email marketing content
- **`landing_page`**: Landing page copy and content

### Available Tones
- **`professional`**: Formal, business-appropriate tone
- **`casual`**: Relaxed, conversational tone
- **`friendly`**: Warm, approachable tone
- **`authoritative`**: Expert, confident tone
- **`conversational`**: Natural, dialogue-like tone
- **`technical`**: Precise, industry-specific tone
- **`creative`**: Imaginative, engaging tone

### Available Target Audiences
- **`general`**: General public audience
- **`technical`**: Technical professionals
- **`business`**: Business professionals
- **`consumer`**: Consumer market
- **`developer`**: Software developers
- **`marketing`**: Marketing professionals
- **`sales`**: Sales professionals

---

## ⚠️ Error Handling

### Error Response Format
```json
{
  "success": false,
  "error": "ValidationError",
  "message": "Topic cannot be empty or just whitespace",
  "details": {
    "field": "topic",
    "value": ""
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Common HTTP Status Codes
- **200**: Success
- **400**: Bad Request (validation errors)
- **404**: Not Found
- **422**: Unprocessable Entity (validation errors)
- **500**: Internal Server Error

### Error Types
1. **Validation Errors**: Invalid input parameters
2. **API Key Errors**: Missing or invalid API keys
3. **Network Errors**: External service failures
4. **Content Generation Errors**: AI generation failures

---

## 🧪 Testing Examples

### Using curl

#### Generate Content
```bash
curl -X POST "http://localhost:8000/api/v1/content/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "The Future of AI in Healthcare",
    "content_type": "blog_post",
    "tone": "professional",
    "target_audience": "technical",
    "include_seo": true,
    "max_length": 2000,
    "keywords": ["AI", "healthcare", "machine learning"]
  }'
```

#### Keyword Research
```bash
curl -X POST "http://localhost:8000/api/v1/content/keyword-research?query=AI%20tools&include_competition=true"
```

#### SEO Optimization
```bash
curl -X POST "http://localhost:8000/api/v1/content/optimize-seo?content=Your%20content&primary_keyword=AI%20content"
```

### Using Python requests

```python
import requests

# Generate content
response = requests.post(
    "http://localhost:8000/api/v1/content/generate",
    json={
        "topic": "AI Content Creation Tools",
        "content_type": "blog_post",
        "tone": "casual",
        "target_audience": "general",
        "include_seo": True,
        "max_length": 1500
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Generated content: {data['content'][:100]}...")
else:
    print(f"Error: {response.text}")
```

---

## 📚 Additional Resources

- **Interactive API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Documentation**: `http://localhost:8000/redoc`
- **OpenAPI Specification**: `http://localhost:8000/openapi.json`
- **Testing Scripts**: Use `quick_test.py` and `test_all_endpoints.py` for comprehensive testing

---

## 🔧 Configuration

### Environment Variables
- `GOOGLE_API_KEY`: Required for AI content generation
- `JINA_API_KEY`: Optional for enhanced web scraping
- `DEBUG`: Enable debug mode (default: false)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `MODEL_ID`: AI model to use (default: gemini-1.5-flash)
- `MAX_RESEARCH_STEPS`: Maximum research steps (default: 10)
- `MAX_CONTENT_LENGTH`: Maximum content length (default: 5000)

### Rate Limits
- No built-in rate limiting (can be implemented)
- Content generation may take 30-120 seconds depending on complexity
- Web scraping operations are throttled to respect external APIs

---

This comprehensive guide covers all available endpoints in the Automate Copywriter API. For the most up-to-date information, always refer to the interactive documentation at `/docs` when the server is running.
