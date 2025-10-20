"""
Configuration management for the FastAPI application.
Handles environment variables and application settings.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    app_name: str = Field(default="Automate Copywriter API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # AI Configuration
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    jina_api_key: Optional[str] = Field(default=None, env="JINA_API_KEY")
    model_id: str = Field(default="gemini/gemini-2.5-flash", env="MODEL_ID")
    
    # Content Generation Settings
    max_research_steps: int = Field(default=10, env="MAX_RESEARCH_STEPS")
    max_content_length: int = Field(default=5000, env="MAX_CONTENT_LENGTH")
    default_tone: str = Field(default="professional", env="DEFAULT_TONE")
    
    # CORS Configuration
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings
