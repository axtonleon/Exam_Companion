"""
AI Agents setup using smolagents for content generation.
Simplified version without ManagedAgent dependency.
"""

from smolagents import (
    CodeAgent,
    ToolCallingAgent,
    LiteLLMModel,
    DuckDuckGoSearchTool,
)
from app.tools.jina_tools import (
    scrape_page_with_jina_ai, 
    search_facts_with_jina_ai, 
    get_seo_keywords,
    research_keyword_competition,
    analyze_content_keywords
)
from app.config import settings
import os
from typing import Optional, List


class ContentGenerationAgents:
    """Manages all AI agents for content generation."""
    
    def __init__(self):
        """Initialize the AI agents with proper configuration."""
        # Initialize the model
        self.model = LiteLLMModel(
            model_id=settings.model_id,
            api_key=settings.google_api_key
        )
        
        # Initialize agents
        self._setup_research_agent()
        self._setup_writer_agent()
        # Blog manager will be set up after other agents are created
        self._setup_blog_manager()
    
    def _setup_research_agent(self):
        """Setup the research agent with web scraping and search tools."""
        self.research_agent = ToolCallingAgent(
            tools=[
                scrape_page_with_jina_ai, 
                search_facts_with_jina_ai, 
                DuckDuckGoSearchTool(),
                get_seo_keywords,
                research_keyword_competition,
                analyze_content_keywords
            ],
            model=self.model,
            max_steps=settings.max_research_steps,
        )
    
    def _setup_writer_agent(self):
        """Setup the writer agent."""
        self.writer_agent = ToolCallingAgent(
            tools=[],
            model=self.model,
        )
    
    def _setup_blog_manager(self):
        """Setup the main blog manager agent."""
        self.blog_manager = CodeAgent(
            tools=[
                scrape_page_with_jina_ai, 
                search_facts_with_jina_ai, 
                DuckDuckGoSearchTool(),
                get_seo_keywords,
                research_keyword_competition,
                analyze_content_keywords
            ],
            model=self.model,
            additional_authorized_imports=["re"],
        )
    
    def generate_content(
        self, 
        topic: str, 
        content_type: str = "blog_post",
        tone: str = "professional",
        target_audience: str = "general",
        include_seo: bool = True,
        keywords: Optional[List[str]] = None,
        additional_requirements: Optional[str] = None
    ) -> str:
        """
        Generate content using the AI agents.
        
        Args:
            topic: The topic or title for the content
            content_type: Type of content to generate (blog_post, article, etc.)
            tone: The desired tone for the content
            target_audience: The target audience for the content
            include_seo: Whether to include SEO optimization
            
        Returns:
            str: The generated content in markdown format
        """
        # Build the prompt based on parameters
        prompt = f"""Create a {content_type} about: {topic}
        
        Requirements:
        - Tone: {tone}
        - Target Audience: {target_audience}
        - Include SEO optimization: {include_seo}
        """
        
        # Add keywords if provided
        if keywords:
            prompt += f"\n- Keywords to include: {', '.join(keywords)}"
        
        # Add additional requirements if provided
        if additional_requirements:
            prompt += f"\n- Additional requirements: {additional_requirements}"
        
        prompt += """
        
        Process:
        1. First, research the topic thoroughly using web scraping and search tools
        2. Extract relevant keywords and analyze SEO opportunities
        3. Write an engaging content with proper structure
        4. Include relevant data, statistics, and examples
        5. Optimize for SEO with proper headings and keyword usage
        """
        
        try:
            # Use the blog manager to orchestrate the entire process
            result = self.blog_manager.run(prompt)
            return result
        except Exception as e:
            return f"Error generating content: {str(e)}"
    
    def generate_blog_post(self, topic: str, **kwargs) -> str:
        """Generate a blog post specifically."""
        return self.generate_content(topic, content_type="blog_post", **kwargs)
    
    def generate_article(self, topic: str, **kwargs) -> str:
        """Generate an article specifically."""
        return self.generate_content(topic, content_type="article", **kwargs)
    
    def generate_social_media_post(self, topic: str, **kwargs) -> str:
        """Generate social media content."""
        return self.generate_content(topic, content_type="social_media_post", **kwargs)
    
    def research_topic(self, topic: str) -> str:
        """Research a topic using the research agent."""
        try:
            return self.research_agent.run(f"Research the topic: {topic}")
        except Exception as e:
            return f"Error researching topic: {str(e)}"


# Global agents instance
content_agents = ContentGenerationAgents()


def get_content_agents() -> ContentGenerationAgents:
    """Get the content generation agents instance."""
    return content_agents