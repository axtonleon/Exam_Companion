#!/usr/bin/env python3
"""
Simple startup script for the Automate Copywriter API.
Run this script to start the FastAPI application.
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Server will be available at: http://{settings.host}:{settings.port}")
    print(f"API Documentation: http://{settings.host}:{settings.port}/docs")
    print(f"Debug mode: {settings.debug}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
