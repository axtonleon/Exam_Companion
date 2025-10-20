# Automate Copywriter API

A FastAPI-based content generation API that uses AI agents with web scraping and SEO optimization capabilities.

## Features

- **AI-Powered Content Generation**: Multi-agent system for research, writing, and editing
- **Web Scraping**: Real-time information gathering using Jina AI
- **SEO Optimization**: Built-in SEO analysis and keyword optimization
- **Multiple Content Types**: Blog posts, articles, social media, product descriptions, and more
- **Flexible Configuration**: Customizable tone, audience, and content requirements
- **RESTful API**: Clean, well-documented API endpoints

## Architecture

The application follows a clean, modular architecture:

```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── services/            # Business logic layer
│   ├── content_service.py
│   └── seo_service.py
├── routes/              # API endpoints
│   └── content.py
├── schemas/             # Pydantic models
│   └── content.py
├── tools/               # AI agent tools
│   ├── jina_tools.py
│   └── agents.py
└── utils/               # Utility functions
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd automatecopywriter
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Run the application**:
   ```bash
   python -m app.main
   # Or using uvicorn directly:
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Configuration

### Required Environment Variables

- `GOOGLE_API_KEY`: Your Google API key for Gemini model access
- `JINA_API_KEY`: Your Jina AI API key for web scraping (optional but recommended)

### Optional Environment Variables

- `DEBUG`: Enable debug mode (default: false)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `MODEL_ID`: AI model to use (default: gemini-1.5-flash)
- `MAX_RESEARCH_STEPS`: Maximum research steps (default: 10)
- `MAX_CONTENT_LENGTH`: Maximum content length (default: 5000)

## API Usage

### Generate Content

**POST** `/api/v1/content/generate`

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

### Generate Blog Post (Simplified)

**POST** `/api/v1/content/generate/blog-post`

```
topic: "Top 5 AI Tools for Content Creation"
tone: "casual"
target_audience: "general"
include_seo: true
```

### SEO Optimization

**POST** `/api/v1/content/optimize-seo`

```json
{
  "content": "Your content here...",
  "primary_keyword": "AI content creation",
  "secondary_keywords": ["automation", "content marketing"]
}
```

## Available Content Types

- `blog_post`: Long-form blog posts with research and SEO optimization
- `article`: Informational articles with detailed analysis
- `social_media_post`: Short-form social media content
- `product_description`: Product-focused marketing content
- `email_campaign`: Email marketing content
- `landing_page`: Landing page copy and content

## Available Tones

- `professional`: Formal, business-appropriate tone
- `casual`: Relaxed, conversational tone
- `friendly`: Warm, approachable tone
- `authoritative`: Expert, confident tone
- `conversational`: Natural, dialogue-like tone
- `technical`: Precise, industry-specific tone
- `creative`: Imaginative, engaging tone

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Development

### Code Quality

The project uses several tools for code quality:

- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Pytest**: Testing

Run code quality checks:

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/

# Run tests
pytest
```

### Adding New Content Types

1. Add the new content type to the `ContentType` enum in `app/schemas/content.py`
2. Update the content generation logic in `app/tools/agents.py`
3. Add any specific handling in `app/services/content_service.py`

### Adding New AI Tools

1. Create the tool function in `app/tools/jina_tools.py` or a new tools file
2. Add the tool to the appropriate agent in `app/tools/agents.py`
3. Update the service layer if needed

## Security Considerations

- API keys are stored in environment variables
- CORS is configurable for production use
- Input validation using Pydantic models
- Rate limiting can be implemented
- Trusted host middleware for production

## Performance

- Asynchronous request handling
- Background task support
- Configurable content length limits
- Efficient AI agent orchestration

## Monitoring and Logging

- Structured logging with timestamps
- Request/response timing
- Error tracking and reporting
- Generation history and statistics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run code quality checks
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the configuration options in `.env.example`

## Changelog

### v1.0.0
- Initial release
- AI agent-based content generation
- Web scraping integration
- SEO optimization
- Multiple content types and tones
- RESTful API with comprehensive documentation
