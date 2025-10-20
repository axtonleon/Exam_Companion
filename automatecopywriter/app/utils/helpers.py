"""
Utility helper functions for the application.
Common functions used across different modules.
"""

import re
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    
    return sanitized


def generate_request_id() -> str:
    """
    Generate a unique request ID.
    
    Returns:
        Unique request ID string
    """
    timestamp = datetime.utcnow().isoformat()
    hash_object = hashlib.md5(timestamp.encode())
    return f"req_{hash_object.hexdigest()[:8]}"


def extract_domain_from_url(url: str) -> Optional[str]:
    """
    Extract domain from a URL.
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        Domain name or None if invalid
    """
    try:
        # Simple domain extraction
        if url.startswith(('http://', 'https://')):
            domain = url.split('/')[2]
        else:
            domain = url.split('/')[0]
        
        # Remove port if present
        domain = domain.split(':')[0]
        
        return domain
    except (IndexError, AttributeError):
        return None


def clean_text_for_analysis(text: str) -> str:
    """
    Clean text for analysis by removing extra whitespace and formatting.
    
    Args:
        text: The text to clean
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove markdown formatting
    text = re.sub(r'[#*`\[\]()]', '', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def validate_content_length(content: str, max_length: int) -> bool:
    """
    Validate that content doesn't exceed maximum length.
    
    Args:
        content: The content to validate
        max_length: Maximum allowed length
        
    Returns:
        True if content is within limits, False otherwise
    """
    return len(content) <= max_length


def format_timestamp(timestamp: datetime) -> str:
    """
    Format timestamp for display.
    
    Args:
        timestamp: The timestamp to format
        
    Returns:
        Formatted timestamp string
    """
    return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.
    
    Args:
        text: The text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text.
    
    Args:
        text: The text to extract hashtags from
        
    Returns:
        List of hashtags
    """
    hashtag_pattern = r'#\w+'
    hashtags = re.findall(hashtag_pattern, text)
    return [tag.lower() for tag in hashtags]


def extract_mentions(text: str) -> List[str]:
    """
    Extract mentions from text.
    
    Args:
        text: The text to extract mentions from
        
    Returns:
        List of mentions
    """
    mention_pattern = r'@\w+'
    mentions = re.findall(mention_pattern, text)
    return [mention.lower() for mention in mentions]


def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Calculate estimated reading time for text.
    
    Args:
        text: The text to calculate reading time for
        words_per_minute: Average reading speed
        
    Returns:
        Estimated reading time in minutes
    """
    word_count = len(text.split())
    reading_time = max(1, round(word_count / words_per_minute))
    return reading_time


def validate_email_format(email: str) -> bool:
    """
    Validate email format using regex.
    
    Args:
        email: The email to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def create_content_summary(content: str, max_sentences: int = 3) -> str:
    """
    Create a summary of content by extracting key sentences.
    
    Args:
        content: The content to summarize
        max_sentences: Maximum number of sentences in summary
        
    Returns:
        Content summary
    """
    sentences = re.split(r'[.!?]+', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= max_sentences:
        return '. '.join(sentences) + '.'
    
    # Take first and last sentences, plus middle ones
    summary_sentences = []
    summary_sentences.append(sentences[0])
    
    if max_sentences > 2:
        middle_sentences = sentences[1:-1]
        middle_count = max_sentences - 2
        if middle_sentences:
            step = len(middle_sentences) // middle_count
            for i in range(0, len(middle_sentences), step):
                if len(summary_sentences) < max_sentences - 1:
                    summary_sentences.append(middle_sentences[i])
    
    summary_sentences.append(sentences[-1])
    
    return '. '.join(summary_sentences[:max_sentences]) + '.'


def safe_get_nested_value(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    Safely get a nested value from a dictionary.
    
    Args:
        data: The dictionary to search
        keys: List of keys to traverse
        default: Default value if key not found
        
    Returns:
        The value at the nested key or default
    """
    try:
        current = data
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default
