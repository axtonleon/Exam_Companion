"""
Content generation service layer.
Handles business logic for AI agent orchestration and content generation.
"""

import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.tools.agents import get_content_agents
from app.schemas.content import (
    ContentGenerationRequest, 
    ContentGenerationResponse, 
    ContentType,
    Tone,
    TargetAudience
)
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentGenerationService:
    """Service for handling content generation using AI agents."""
    
    def __init__(self):
        """Initialize the content generation service."""
        self.agents = get_content_agents()
        self.generation_history: Dict[str, Dict[str, Any]] = {}
    
    async def generate_content(
        self, 
        request: ContentGenerationRequest
    ) -> ContentGenerationResponse:
        """
        Generate content based on the provided request.
        
        Args:
            request: The content generation request
            
        Returns:
            ContentGenerationResponse: The generated content and metadata
        """
        start_time = time.time()
        request_id = f"req_{int(time.time())}"
        
        try:
            logger.info(f"Starting content generation for topic: {request.topic}")
            
            # Validate request
            self._validate_request(request)
            
            # Generate content using appropriate method based on content type
            content = await self._generate_content_by_type(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Store generation history
            self.generation_history[request_id] = {
                "request": request.dict(),
                "generated_at": datetime.utcnow().isoformat(),
                "processing_time": processing_time,
                "success": True
            }
            
            # Create response
            response = ContentGenerationResponse(
                success=True,
                content=content,
                content_type=request.content_type,
                topic=request.topic,
                metadata={
                    "request_id": request_id,
                    "tone": request.tone,
                    "target_audience": request.target_audience,
                    "include_seo": request.include_seo,
                    "keywords": request.keywords,
                    "content_length": len(content) if content else 0
                },
                processing_time=processing_time
            )
            
            logger.info(f"Content generation completed successfully in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"Content generation failed: {error_msg}")
            
            # Store failed generation in history
            self.generation_history[request_id] = {
                "request": request.dict(),
                "generated_at": datetime.utcnow().isoformat(),
                "processing_time": processing_time,
                "success": False,
                "error": error_msg
            }
            
            return ContentGenerationResponse(
                success=False,
                content_type=request.content_type,
                topic=request.topic,
                error_message=error_msg,
                processing_time=processing_time,
                metadata={"request_id": request_id}
            )
    
    def _validate_request(self, request: ContentGenerationRequest) -> None:
        """
        Validate the content generation request.
        
        Args:
            request: The request to validate
            
        Raises:
            ValueError: If the request is invalid
        """
        if not request.topic.strip():
            raise ValueError("Topic cannot be empty")
        
        if request.max_length and request.max_length < 100:
            raise ValueError("Maximum length must be at least 100 characters")
        
        if request.keywords and len(request.keywords) > 20:
            raise ValueError("Too many keywords provided (maximum 20)")
    
    async def _generate_content_by_type(
        self, 
        request: ContentGenerationRequest
    ) -> str:
        """
        Generate content based on the specified type.
        
        Args:
            request: The content generation request
            
        Returns:
            str: The generated content
        """
        # Prepare generation parameters
        generation_params = {
            "tone": request.tone,
            "target_audience": request.target_audience,
            "include_seo": request.include_seo
        }
        
        # Add keywords if provided
        if request.keywords:
            generation_params["keywords"] = request.keywords
        
        # Add additional requirements if provided
        if request.additional_requirements:
            generation_params["additional_requirements"] = request.additional_requirements
        
        # Generate content based on type
        if request.content_type == ContentType.BLOG_POST:
            content = self.agents.generate_blog_post(
                request.topic, 
                **generation_params
            )
        elif request.content_type == ContentType.ARTICLE:
            content = self.agents.generate_article(
                request.topic, 
                **generation_params
            )
        elif request.content_type == ContentType.SOCIAL_MEDIA_POST:
            content = self.agents.generate_social_media_post(
                request.topic, 
                **generation_params
            )
        else:
            # Use generic content generation for other types
            content = self.agents.generate_content(
                request.topic,
                content_type=request.content_type.value,
                **generation_params
            )
        
        # Apply length constraints if specified
        if request.max_length and len(content) > request.max_length:
            content = content[:request.max_length] + "..."
        
        return content
    
    def get_generation_history(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get the recent content generation history.
        
        Args:
            limit: Maximum number of history entries to return
            
        Returns:
            Dict containing generation history
        """
        # Sort by timestamp and limit results
        sorted_history = sorted(
            self.generation_history.items(),
            key=lambda x: x[1]["generated_at"],
            reverse=True
        )[:limit]
        
        return {
            "total_generations": len(self.generation_history),
            "recent_generations": dict(sorted_history)
        }
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about content generation.
        
        Returns:
            Dict containing generation statistics
        """
        if not self.generation_history:
            return {
                "total_generations": 0,
                "successful_generations": 0,
                "failed_generations": 0,
                "average_processing_time": 0
            }
        
        total = len(self.generation_history)
        successful = sum(1 for entry in self.generation_history.values() if entry["success"])
        failed = total - successful
        
        # Calculate average processing time
        processing_times = [
            entry["processing_time"] 
            for entry in self.generation_history.values()
        ]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            "total_generations": total,
            "successful_generations": successful,
            "failed_generations": failed,
            "success_rate": (successful / total) * 100 if total > 0 else 0,
            "average_processing_time": round(avg_processing_time, 2)
        }


# Global service instance
content_service = ContentGenerationService()


def get_content_service() -> ContentGenerationService:
    """Get the content generation service instance."""
    return content_service
