#!/usr/bin/env python3
"""
Quick test script for individual endpoint testing.
Use this for testing specific endpoints without running the full suite.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/content"

def test_endpoint(endpoint_name: str, method: str, url: str, **kwargs):
    """Test a single endpoint."""
    print(f"\n🧪 Testing {endpoint_name}")
    print("-" * 40)
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, **kwargs)
        elif method.upper() == "POST":
            response = requests.post(url, **kwargs)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Success: {data.get('message', 'OK')}")
                if 'content' in data and len(data['content']) > 100:
                    print(f"📝 Content length: {len(data['content'])} characters")
                return True
            except json.JSONDecodeError:
                print(f"✅ Success: {response.text[:100]}...")
                return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def main():
    """Run quick tests."""
    if len(sys.argv) < 2:
        print("Usage: python quick_test.py <endpoint_name>")
        print("\nAvailable endpoints:")
        print("  health - Test health endpoints")
        print("  generate - Test content generation")
        print("  blog - Test blog post generation")
        print("  seo - Test SEO endpoints")
        print("  all - Test all endpoints")
        return
    
    endpoint = sys.argv[1].lower()
    
    if endpoint == "health":
        test_endpoint("Health Check", "GET", f"{BASE_URL}/health")
        test_endpoint("API Health", "GET", f"{API_BASE}/health")
        
    elif endpoint == "generate":
        payload = {
            "topic": "Quick Test Topic",
            "content_type": "blog_post",
            "tone": "professional",
            "target_audience": "general",
            "include_seo": True,
            "max_length": 500
        }
        test_endpoint("Content Generation", "POST", f"{API_BASE}/generate", 
                     json=payload, timeout=120)
        
    elif endpoint == "blog":
        params = {
            "topic": "Quick Blog Test",
            "tone": "casual",
            "target_audience": "general",
            "include_seo": True
        }
        test_endpoint("Blog Post Generation", "POST", f"{API_BASE}/generate/blog-post", 
                     params=params, timeout=120)
        
    elif endpoint == "seo":
        params = {"query": "AI tools", "include_competition": True}
        test_endpoint("Keyword Research", "POST", f"{API_BASE}/keyword-research", 
                     params=params)
        
        params = {
            "content": "This is a test content for SEO optimization.",
            "primary_keyword": "test keyword"
        }
        test_endpoint("SEO Optimization", "POST", f"{API_BASE}/optimize-seo", 
                     params=params)
        
    elif endpoint == "all":
        test_endpoint("Health Check", "GET", f"{BASE_URL}/health")
        test_endpoint("Content Types", "GET", f"{API_BASE}/content-types")
        test_endpoint("Tones", "GET", f"{API_BASE}/tones")
        test_endpoint("History", "GET", f"{API_BASE}/history")
        test_endpoint("Stats", "GET", f"{API_BASE}/stats")
        
    else:
        print(f"❌ Unknown endpoint: {endpoint}")
        print("Use 'python quick_test.py' to see available options")

if __name__ == "__main__":
    main()
