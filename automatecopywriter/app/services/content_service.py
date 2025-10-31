"""
Content generation service layer.
Handles business logic for AI agent orchestration and content generation.
"""

import time
import json
import re
import logging
from typing import Optional, Dict, Any, List
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
from app.schemas.content import (
    LandingPageRequest,
    LandingPageResponse,
    LandingPageSEO,
    HowItWorksStep,
    FAQItem,
)
from app.tools.agents import get_content_agents

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
        
        # Return full content without truncation
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


class LandingPageService:
    """Service to build structured landing page JSON from column-like inputs."""

    def __init__(self) -> None:
        self.agents = get_content_agents()

    def build_landing_page(self, request: LandingPageRequest) -> LandingPageResponse:
        """Build the landing page structure based on provided inputs."""
        page_title_default = request.page_title_override or request.tool_name.strip()
        page_subtitle_default = (request.page_subtitle_override or request.feature_summary.strip())[:300]

        prompt = (
            "You are an expert product marketer and SEO specialist. Create a landing page JSON strictly matching this schema: "
            '{"page_title": string, "page_subtitle": string, "how_it_works": [{"step": number, "title": string, "description": string}], '
            '"faq": [{"question": string, "answer": string}], "seo": {"meta_title": string, "meta_description": string, "extracted_keywords": [string]}}.'
        )
        prompt += "\nUse the inputs below. Keep copy concise, clear, and conversion-oriented. Incorporate the primary keywords naturally.\n"
        prompt += f"Tool Name: {request.tool_name}\n"
        prompt += f"Feature Summary: {request.feature_summary}\n"
        prompt += f"Primary Keywords: {', '.join(request.primary_keywords)}\n"
        prompt += f"SEO Intent: {request.seo_intent.value}\n"
        prompt += f"Subjects: {', '.join(request.subjects)}\n"
        prompt += (
            "Rules: First, if tools are available, analyze keywords and topic to inform copy. "
            "Return ONLY minified JSON with the exact keys. Steps should be 2-4 items starting at 1. "
            "FAQ should contain 2-4 items. The 'seo.meta_title' ≤ 60 chars; 'seo.meta_description' 150-180 chars; include 5-12 extracted_keywords."
        )

        ai_output = None
        try:
            # Use the agent to produce JSON output
            ai_raw = self.agents.blog_manager.run(prompt)
            # Extract JSON substring
            match = re.search(r"\{[\s\S]*\}", ai_raw)
            if match:
                ai_output = json.loads(match.group(0))
        except Exception:
            ai_output = None

        if ai_output:
            # Validate and coerce into Pydantic models, with safe fallbacks
            try:
                # Overrides
                if request.page_title_override:
                    ai_output["page_title"] = request.page_title_override
                if request.page_subtitle_override:
                    ai_output["page_subtitle"] = request.page_subtitle_override

                how_it_works_items = [
                    HowItWorksStep(
                        step=max(1, int(item.get("step", idx + 1))),
                        title=str(item.get("title", ""))[:120],
                        description=str(item.get("description", ""))[:300],
                    )
                    for idx, item in enumerate(ai_output.get("how_it_works", []))
                ]

                # Ensure step numbering sequential starting at 1
                for idx, step in enumerate(how_it_works_items):
                    step.step = idx + 1

                faq_items = [
                    FAQItem(
                        question=str(item.get("question", ""))[:200],
                        answer=str(item.get("answer", ""))[:600],
                    )
                    for item in ai_output.get("faq", [])
                ]

                # Build SEO block with safe coercion
                seo_obj = ai_output.get("seo", {}) if isinstance(ai_output.get("seo", {}), dict) else {}
                meta_title = str(seo_obj.get("meta_title", ai_output.get("page_title", page_title_default)))[:120]
                # Default description from subtitle, trimmed to typical snippet length if missing
                meta_desc_raw = str(seo_obj.get("meta_description", ai_output.get("page_subtitle", page_subtitle_default)))
                meta_description = meta_desc_raw[:180]
                extracted_keywords = [str(k).strip() for k in (seo_obj.get("extracted_keywords") or []) if str(k).strip()]

                # If require_seo, enforce presence of extracted keywords
                if request.require_seo and not extracted_keywords:
                    raise ValueError("SEO analysis required but missing extracted_keywords")

                return LandingPageResponse(
                    page_title=str(ai_output.get("page_title", page_title_default))[:120],
                    page_subtitle=str(ai_output.get("page_subtitle", page_subtitle_default))[:300],
                    how_it_works=how_it_works_items or [
                        HowItWorksStep(step=1, title="Create an account", description=f"Sign up to start using {request.tool_name}."),
                        HowItWorksStep(step=2, title="Add your inputs", description="Provide notes, files, or text to generate outputs."),
                    ],
                    faq=faq_items or [
                        FAQItem(question="Can I cancel anytime?", answer="Yes, you can cancel from your dashboard."),
                        FAQItem(question="Do you offer student discounts?", answer="Yes, verified students receive discounts."),
                    ],
                    seo=LandingPageSEO(
                        meta_title=meta_title,
                        meta_description=meta_description,
                        extracted_keywords=extracted_keywords[:12],
                    ),
                )
            except Exception:
                pass

        # Fallback static structure if AI generation fails
        if request.strict_ai:
            raise ValueError("AI generation failed and strict_ai is enabled")
        how_it_works: List[HowItWorksStep] = [
            HowItWorksStep(
                step=1,
                title="Create an account",
                description=f"Sign up in seconds to start using {request.tool_name}.",
            ),
            HowItWorksStep(
                step=2,
                title="Add your inputs",
                description="Provide notes, files, or text to generate tailored outputs.",
            ),
        ]
        faq: List[FAQItem] = [
            FAQItem(
                question="Can I cancel anytime?",
                answer="Yes, cancel your subscription anytime from your dashboard.",
            ),
            FAQItem(
                question="Do you offer student discounts?",
                answer="Yes, verified students receive discounted pricing.",
            ),
        ]

        # Fallback SEO metadata influenced by provided keywords
        fallback_meta_title = page_title_default[:60]
        # Build a concise meta description up to ~160 chars
        fallback_meta_description = (page_subtitle_default or request.feature_summary)[:170]
        fallback_keywords = [kw for kw in request.primary_keywords][:8]

        return LandingPageResponse(
            page_title=page_title_default,
            page_subtitle=page_subtitle_default,
            how_it_works=how_it_works,
            faq=faq,
            seo=LandingPageSEO(
                meta_title=fallback_meta_title,
                meta_description=fallback_meta_description,
                extracted_keywords=fallback_keywords,
            ),
        )


# Global landing page service instance
landing_page_service = LandingPageService()


def get_landing_page_service() -> LandingPageService:
    """Get the landing page service instance."""
    return landing_page_service
