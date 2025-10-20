"""
SEO optimization service.
Handles SEO-related functionality for content generation.
"""

import re
from typing import List, Dict, Any, Optional
from app.tools.jina_tools import get_seo_keywords
from app.config import settings


class SEOService:
    """Service for handling SEO optimization of generated content."""
    
    def __init__(self):
        """Initialize the SEO service."""
        self.common_stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 
            'her', 'us', 'them'
        }
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract SEO keywords from text.
        
        Args:
            text: The text to extract keywords from
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of extracted keywords
        """
        # Clean and normalize text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filter out stop words and short words
        keywords = [
            word for word in words 
            if word not in self.common_stop_words and len(word) > 2
        ]
        
        # Count word frequency
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_keywords[:max_keywords]]
    
    def generate_meta_description(self, content: str, max_length: int = 160) -> str:
        """
        Generate a meta description from content.
        
        Args:
            content: The content to generate description from
            max_length: Maximum length of the meta description
            
        Returns:
            Generated meta description
        """
        # Remove markdown formatting
        clean_content = re.sub(r'[#*`\[\]()]', '', content)
        
        # Get first sentence or paragraph
        sentences = re.split(r'[.!?]', clean_content)
        first_sentence = sentences[0].strip() if sentences else ""
        
        # Truncate if too long
        if len(first_sentence) > max_length:
            first_sentence = first_sentence[:max_length-3] + "..."
        
        return first_sentence
    
    def optimize_headings(self, content: str, primary_keyword: str) -> str:
        """
        Optimize headings in content for SEO.
        
        Args:
            content: The content with headings
            primary_keyword: The primary keyword to include in headings
            
        Returns:
            Content with optimized headings
        """
        # Find all headings (markdown format)
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        
        def optimize_heading(match):
            level = match.group(1)
            heading_text = match.group(2)
            
            # Add primary keyword if not already present
            if primary_keyword.lower() not in heading_text.lower():
                heading_text = f"{heading_text} - {primary_keyword}"
            
            return f"{level} {heading_text}"
        
        return re.sub(heading_pattern, optimize_heading, content, flags=re.MULTILINE)
    
    def add_alt_text_suggestions(self, content: str) -> str:
        """
        Add suggestions for alt text in content.
        
        Args:
            content: The content to analyze
            
        Returns:
            Content with alt text suggestions
        """
        # Find image references in markdown
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        def add_alt_suggestion(match):
            alt_text = match.group(1)
            image_url = match.group(2)
            
            if not alt_text:
                # Generate alt text based on context
                alt_text = "Relevant image for content"
            
            return f"![{alt_text}]({image_url})"
        
        return re.sub(image_pattern, add_alt_suggestion, content)
    
    def calculate_readability_score(self, content: str) -> Dict[str, Any]:
        """
        Calculate basic readability metrics for content.
        
        Args:
            content: The content to analyze
            
        Returns:
            Dictionary with readability metrics
        """
        # Remove markdown formatting
        clean_content = re.sub(r'[#*`\[\]()]', '', content)
        
        # Basic metrics
        sentences = re.split(r'[.!?]', clean_content)
        words = clean_content.split()
        
        total_sentences = len([s for s in sentences if s.strip()])
        total_words = len(words)
        total_syllables = sum(self._count_syllables(word) for word in words)
        
        if total_sentences == 0 or total_words == 0:
            return {
                "readability_score": 0,
                "grade_level": 0,
                "total_words": 0,
                "total_sentences": 0,
                "average_words_per_sentence": 0
            }
        
        # Simple Flesch Reading Ease approximation
        avg_sentence_length = total_words / total_sentences
        avg_syllables_per_word = total_syllables / total_words
        
        readability_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        
        # Grade level approximation
        grade_level = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
        
        return {
            "readability_score": round(readability_score, 2),
            "grade_level": round(grade_level, 1),
            "total_words": total_words,
            "total_sentences": total_sentences,
            "average_words_per_sentence": round(avg_sentence_length, 1)
        }
    
    def _count_syllables(self, word: str) -> int:
        """
        Count syllables in a word (approximation).
        
        Args:
            word: The word to count syllables for
            
        Returns:
            Number of syllables
        """
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def optimize_content_for_seo(
        self, 
        content: str, 
        primary_keyword: str,
        secondary_keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Optimize content for SEO.
        
        Args:
            content: The content to optimize
            primary_keyword: The primary keyword to focus on
            secondary_keywords: Optional secondary keywords
            
        Returns:
            Dictionary with optimization results and suggestions
        """
        # Extract keywords from content
        extracted_keywords = self.extract_keywords(content)
        
        # Generate meta description
        meta_description = self.generate_meta_description(content)
        
        # Optimize headings
        optimized_content = self.optimize_headings(content, primary_keyword)
        
        # Add alt text suggestions
        optimized_content = self.add_alt_text_suggestions(optimized_content)
        
        # Calculate readability
        readability = self.calculate_readability_score(content)
        
        # Check keyword density
        keyword_density = self._calculate_keyword_density(content, primary_keyword)
        
        # Generate suggestions
        suggestions = self._generate_seo_suggestions(
            content, primary_keyword, secondary_keywords or []
        )
        
        return {
            "optimized_content": optimized_content,
            "meta_description": meta_description,
            "extracted_keywords": extracted_keywords,
            "primary_keyword_density": keyword_density,
            "readability": readability,
            "suggestions": suggestions
        }
    
    def _calculate_keyword_density(self, content: str, keyword: str) -> float:
        """Calculate keyword density in content."""
        words = content.lower().split()
        keyword_count = sum(1 for word in words if keyword.lower() in word)
        return round((keyword_count / len(words)) * 100, 2) if words else 0
    
    def _generate_seo_suggestions(
        self, 
        content: str, 
        primary_keyword: str, 
        secondary_keywords: List[str]
    ) -> List[str]:
        """Generate SEO improvement suggestions."""
        suggestions = []
        
        # Check keyword density
        density = self._calculate_keyword_density(content, primary_keyword)
        if density < 1:
            suggestions.append(f"Increase usage of primary keyword '{primary_keyword}' (current density: {density}%)")
        elif density > 3:
            suggestions.append(f"Reduce usage of primary keyword '{primary_keyword}' (current density: {density}%)")
        
        # Check for headings
        if not re.search(r'^#{1,6}\s+', content, re.MULTILINE):
            suggestions.append("Add headings (H1, H2, H3) to improve content structure")
        
        # Check for images
        if not re.search(r'!\[.*\]\(.*\)', content):
            suggestions.append("Consider adding relevant images to improve engagement")
        
        # Check content length
        word_count = len(content.split())
        if word_count < 300:
            suggestions.append("Consider expanding content to at least 300 words for better SEO")
        
        return suggestions


# Global SEO service instance
seo_service = SEOService()


def get_seo_service() -> SEOService:
    """Get the SEO service instance."""
    return seo_service
