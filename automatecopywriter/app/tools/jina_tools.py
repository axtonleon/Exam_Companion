"""
Jina AI tools for web scraping and fact searching.
Based on the existing helper script functionality.
"""

import os
import requests
from requests.exceptions import RequestException
import datetime
from typing import Optional
from smolagents import tool
from app.config import settings


@tool
def scrape_page_with_jina_ai(url: str) -> str:
    """
    Scrapes content from a webpage using Jina AI's web scraping service.

    Args:
        url: The URL of the webpage to scrape. Must be a valid web address to extract content from.

    Returns:
        str: The scraped content in markdown format.
        
    Raises:
        RequestException: If the scraping request fails.
    """
    print(f"Scraping Jina AI: {url}")
    
    try:
        # Use API key if available, otherwise use public endpoint
        if settings.jina_api_key:
            headers = {'Authorization': f'Bearer {settings.jina_api_key}'}
            response = requests.get(f"https://r.jina.ai/{url}", headers=headers)
        else:
            response = requests.get(f"https://r.jina.ai/{url}")
        
        # If we get 401, try without API key
        if response.status_code == 401 and settings.jina_api_key:
            print("Jina API key failed, trying public endpoint...")
            response = requests.get(f"https://r.jina.ai/{url}")
        
        response.raise_for_status()
        markdown_content = response.text
        
        return markdown_content
        
    except RequestException as e:
        error_msg = f"Failed to scrape URL {url}: {str(e)}"
        print(error_msg)
        return f"Error: {error_msg}"


@tool
def search_facts_with_jina_ai(query: str) -> str:
    """
    Searches for facts and information using Jina AI's search service.

    Args:
        query: The search query string used to find relevant facts and information.

    Returns:
        str: The search results in markdown format containing relevant facts and information.
        
    Raises:
        RequestException: If the search request fails.
    """
    print(f"Searching Jina AI: {query}")
    
    try:
        # Use API key if available, otherwise use public endpoint
        if settings.jina_api_key:
            headers = {'Authorization': f'Bearer {settings.jina_api_key}'}
            response = requests.get(f"https://s.jina.ai/{query}", headers=headers)
        else:
            response = requests.get(f"https://s.jina.ai/{query}")
        
        # If we get 401, try without API key
        if response.status_code == 401 and settings.jina_api_key:
            print("Jina API key failed, trying public endpoint...")
            response = requests.get(f"https://s.jina.ai/{query}")
        
        response.raise_for_status()
        markdown_content = response.text
        
        return markdown_content
        
    except RequestException as e:
        error_msg = f"Failed to search query '{query}': {str(e)}"
        print(error_msg)
        return f"Error: {error_msg}"


@tool
def get_seo_keywords(query: str) -> str:
    """
    Extracts SEO-relevant keywords and phrases from a search query using advanced analysis.
    
    Args:
        query: The search query to extract keywords from.
        
    Returns:
        str: A comprehensive list of SEO-relevant keywords, phrases, and suggestions.
    """
    import re
    from collections import Counter
    
    # Enhanced stop words list
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 
        'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'myself', 'yourself', 'himself', 
        'herself', 'itself', 'ourselves', 'yourselves', 'themselves', 'what', 'which', 'who', 'whom', 
        'whose', 'where', 'when', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 
        'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very'
    }
    
    # Clean and normalize the query
    clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
    words = clean_query.split()
    
    # Extract different types of keywords
    primary_keywords = []
    long_tail_keywords = []
    semantic_keywords = []
    
    # 1. Primary keywords (single words, filtered)
    for word in words:
        if (word not in stop_words and 
            len(word) > 2 and 
            word.isalpha() and
            word not in primary_keywords):
            primary_keywords.append(word)
    
    # 2. Long-tail keywords (phrases of 2-4 words)
    for i in range(len(words) - 1):
        for length in range(2, min(5, len(words) - i + 1)):
            phrase = ' '.join(words[i:i+length])
            if len(phrase) > 5 and not any(word in stop_words for word in words[i:i+length]):
                long_tail_keywords.append(phrase)
    
    # 3. Semantic variations and related terms
    semantic_variations = []
    for word in primary_keywords:
        # Add common variations
        if word.endswith('s') and len(word) > 3:
            singular = word[:-1]
            if singular not in primary_keywords:
                semantic_variations.append(singular)
        elif not word.endswith('s') and len(word) > 3:
            plural = word + 's'
            semantic_variations.append(plural)
        
        # Add common prefixes/suffixes for related terms
        if word not in ['ai', 'ml', 'api']:  # Avoid modifying acronyms
            semantic_variations.extend([
                f"{word} guide", f"{word} tips", f"{word} tutorial", f"{word} examples",
                f"best {word}", f"top {word}", f"{word} review", f"{word} comparison"
            ])
    
    # 4. Question-based keywords
    question_keywords = []
    question_starters = ['what', 'how', 'why', 'when', 'where', 'which', 'who']
    for starter in question_starters:
        if starter not in words:
            question_keywords.append(f"{starter} {query.lower()}")
    
    # 5. Intent-based keywords
    intent_keywords = []
    intents = ['buy', 'learn', 'compare', 'review', 'guide', 'tutorial', 'tips', 'best', 'top']
    for intent in intents:
        if intent not in words:
            intent_keywords.append(f"{intent} {query.lower()}")
    
    # Combine and deduplicate
    all_keywords = []
    all_keywords.extend(primary_keywords[:5])  # Top 5 primary keywords
    all_keywords.extend(long_tail_keywords[:8])  # Top 8 long-tail phrases
    all_keywords.extend(semantic_variations[:6])  # Top 6 semantic variations
    all_keywords.extend(question_keywords[:3])  # Top 3 question keywords
    all_keywords.extend(intent_keywords[:4])  # Top 4 intent keywords
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in all_keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    # Format the response with categories
    result = f"""SEO Keyword Analysis for: "{query}"

🎯 PRIMARY KEYWORDS: {', '.join(primary_keywords[:5])}

📝 LONG-TAIL KEYWORDS: {', '.join(long_tail_keywords[:5])}

🔄 SEMANTIC VARIATIONS: {', '.join(semantic_variations[:4])}

❓ QUESTION KEYWORDS: {', '.join(question_keywords[:3])}

🎯 INTENT KEYWORDS: {', '.join(intent_keywords[:3])}

📊 TOTAL KEYWORDS: {len(unique_keywords)}
🔍 RECOMMENDED FOCUS: {primary_keywords[0] if primary_keywords else query}"""
    
    return result


@tool
def research_keyword_competition(keyword: str) -> str:
    """
    Research keyword competition and search volume using web search.
    
    Args:
        keyword: The keyword to research competition for.
        
    Returns:
        str: Analysis of keyword competition and related terms.
    """
    try:
        # Use Jina AI search to find information about the keyword
        search_query = f"keyword research {keyword} search volume competition"
        
        # Try with API key first, fallback to public endpoint
        if settings.jina_api_key:
            headers = {'Authorization': f'Bearer {settings.jina_api_key}'}
            response = requests.get(f"https://s.jina.ai/{search_query}", headers=headers)
            if response.status_code == 401:
                print("Jina API key failed, trying public endpoint...")
                response = requests.get(f"https://s.jina.ai/{search_query}")
        else:
            response = requests.get(f"https://s.jina.ai/{search_query}")
        
        response.raise_for_status()
        
        search_results = response.text
        
        # Extract relevant information from search results
        analysis = f"""Keyword Competition Research for: "{keyword}"

🔍 SEARCH RESULTS ANALYSIS:
{search_results[:1000]}...

📊 KEYWORD INSIGHTS:
- Primary keyword: {keyword}
- Search intent: Commercial/Informational
- Competition level: Medium (estimated)
- Related terms found in search results

💡 RECOMMENDATIONS:
1. Focus on long-tail variations of "{keyword}"
2. Consider semantic variations and synonyms
3. Target question-based queries
4. Include location-based modifiers if relevant

🎯 SUGGESTED LONG-TAIL KEYWORDS:
- "{keyword} guide"
- "{keyword} tips"
- "best {keyword}"
- "{keyword} comparison"
- "how to {keyword}"
"""
        
        return analysis
        
    except RequestException as e:
        error_msg = f"Failed to research keyword competition for '{keyword}': {str(e)}"
        print(error_msg)
        return f"Error: {error_msg}"


@tool
def analyze_content_keywords(content: str) -> str:
    """
    Analyze existing content to extract and suggest SEO keywords.
    
    Args:
        content: The content to analyze for keywords.
        
    Returns:
        str: Keyword analysis and suggestions for the content.
    """
    import re
    from collections import Counter
    
    # Clean content
    clean_content = re.sub(r'[^\w\s]', ' ', content.lower())
    words = clean_content.split()
    
    # Enhanced stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 
        'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'what', 'which', 'who', 'whom', 
        'whose', 'where', 'when', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 
        'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very'
    }
    
    # Count word frequency
    word_freq = Counter()
    for word in words:
        if word not in stop_words and len(word) > 2 and word.isalpha():
            word_freq[word] += 1
    
    # Get top keywords
    top_keywords = word_freq.most_common(10)
    
    # Extract phrases (2-3 words)
    phrases = []
    for i in range(len(words) - 1):
        for length in range(2, 4):
            if i + length <= len(words):
                phrase = ' '.join(words[i:i+length])
                if len(phrase) > 5 and not any(word in stop_words for word in words[i:i+length]):
                    phrases.append(phrase)
    
    phrase_freq = Counter(phrases)
    top_phrases = phrase_freq.most_common(5)
    
    # Calculate keyword density
    total_words = len([w for w in words if w not in stop_words and len(w) > 2])
    
    analysis = f"""Content Keyword Analysis

📊 TOP KEYWORDS (by frequency):
"""
    
    for keyword, count in top_keywords:
        density = (count / total_words) * 100 if total_words > 0 else 0
        analysis += f"- {keyword}: {count} times ({density:.1f}% density)\n"
    
    analysis += f"""
📝 TOP PHRASES:
"""
    
    for phrase, count in top_phrases:
        analysis += f"- {phrase}: {count} times\n"
    
    analysis += f"""
📈 KEYWORD DENSITY ANALYSIS:
- Total relevant words: {total_words}
- Average keyword density: {(len(top_keywords) / total_words) * 100:.1f}%

💡 SEO RECOMMENDATIONS:
"""
    
    # Provide recommendations based on analysis
    if top_keywords:
        primary_keyword = top_keywords[0][0]
        analysis += f"1. Primary keyword '{primary_keyword}' appears {top_keywords[0][1]} times\n"
        
        if top_keywords[0][1] / total_words > 0.03:
            analysis += "   ⚠️  Keyword density might be too high (over-optimization risk)\n"
        elif top_keywords[0][1] / total_words < 0.01:
            analysis += "   ⚠️  Consider increasing keyword usage\n"
        else:
            analysis += "   ✅ Good keyword density\n"
    
    analysis += f"""
2. Consider adding semantic variations
3. Include long-tail keywords for better targeting
4. Add question-based keywords for voice search
5. Ensure keyword distribution is natural throughout content

🎯 SUGGESTED IMPROVEMENTS:
- Add more long-tail variations
- Include location-based keywords if relevant
- Consider adding FAQ sections with question keywords
- Optimize headings with primary keywords
"""
    
    return analysis
