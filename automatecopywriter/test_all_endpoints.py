#!/usr/bin/env python3
"""
Comprehensive test script for all Automate Copywriter API endpoints.
Tests all functionality including content generation, SEO, and analysis.
"""

import requests
import json
import time
from typing import Dict, Any, List
import sys

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/content"

class APITester:
    """Test all API endpoints systematically."""
    
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AutomateCopywriter-TestSuite/1.0'
        })
    
    def log_result(self, endpoint: str, method: str, status: str, details: str = ""):
        """Log test result."""
        result = {
            'endpoint': endpoint,
            'method': method,
            'status': status,
            'details': details,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.results.append(result)
        
        # Print result
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {method} {endpoint} - {status}")
        if details:
            print(f"   {details}")
    
    def test_health_endpoints(self):
        """Test health check endpoints."""
        print("\n🏥 Testing Health Endpoints")
        print("=" * 50)
        
        # Test basic health
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_result("/health", "GET", "PASS", f"Status: {data.get('status')}")
            else:
                self.log_result("/health", "GET", "FAIL", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("/health", "GET", "FAIL", str(e))
        
        # Test API health
        try:
            response = self.session.get(f"{API_BASE}/health")
            if response.status_code == 200:
                data = response.json()
                deps = data.get('dependencies', {})
                self.log_result("/api/v1/content/health", "GET", "PASS", 
                              f"Dependencies: {', '.join(f'{k}={v}' for k, v in deps.items())}")
            else:
                self.log_result("/api/v1/content/health", "GET", "FAIL", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("/api/v1/content/health", "GET", "FAIL", str(e))
    
    def test_info_endpoints(self):
        """Test information endpoints."""
        print("\n📋 Testing Information Endpoints")
        print("=" * 50)
        
        # Test content types
        try:
            response = self.session.get(f"{API_BASE}/content-types")
            if response.status_code == 200:
                data = response.json()
                types = data.get('content_types', {})
                self.log_result("/api/v1/content/content-types", "GET", "PASS", 
                              f"Found {len(types)} content types")
            else:
                self.log_result("/api/v1/content/content-types", "GET", "FAIL", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("/api/v1/content/content-types", "GET", "FAIL", str(e))
        
        # Test tones
        try:
            response = self.session.get(f"{API_BASE}/tones")
            if response.status_code == 200:
                data = response.json()
                tones = data.get('tones', {})
                self.log_result("/api/v1/content/tones", "GET", "PASS", 
                              f"Found {len(tones)} tones")
            else:
                self.log_result("/api/v1/content/tones", "GET", "FAIL", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("/api/v1/content/tones", "GET", "FAIL", str(e))
    
    def test_content_generation(self):
        """Test content generation endpoints."""
        print("\n✍️ Testing Content Generation Endpoints")
        print("=" * 50)
        
        # Test main content generation
        test_payload = {
            "topic": "The Future of Artificial Intelligence",
            "content_type": "blog_post",
            "tone": "professional",
            "target_audience": "technical",
            "include_seo": True,
            "keywords": ["AI", "artificial intelligence", "machine learning"],
            "max_length": 1000
        }
        
        try:
            print("   Generating content (this may take 1-2 minutes)...")
            start_time = time.time()
            response = self.session.post(f"{API_BASE}/generate", json=test_payload)
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    content_length = len(data.get('content', ''))
                    processing_time = data.get('processing_time', 0)
                    self.log_result("/api/v1/content/generate", "POST", "PASS", 
                                  f"Generated {content_length} chars in {processing_time:.1f}s")
                else:
                    self.log_result("/api/v1/content/generate", "POST", "FAIL", 
                                  f"Generation failed: {data.get('error_message')}")
            else:
                self.log_result("/api/v1/content/generate", "POST", "FAIL", 
                              f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("/api/v1/content/generate", "POST", "FAIL", str(e))
        
        # Test blog post generation (query parameters)
        try:
            print("   Generating blog post...")
            params = {
                "topic": "Remote Work Productivity Tips",
                "tone": "casual",
                "target_audience": "general",
                "include_seo": True
            }
            response = self.session.post(f"{API_BASE}/generate/blog-post", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    content_length = len(data.get('content', ''))
                    self.log_result("/api/v1/content/generate/blog-post", "POST", "PASS", 
                                  f"Generated {content_length} chars")
                else:
                    self.log_result("/api/v1/content/generate/blog-post", "POST", "FAIL", 
                                  f"Generation failed: {data.get('error_message')}")
            else:
                self.log_result("/api/v1/content/generate/blog-post", "POST", "FAIL", 
                              f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("/api/v1/content/generate/blog-post", "POST", "FAIL", str(e))
    
    def test_seo_endpoints(self):
        """Test SEO and analysis endpoints."""
        print("\n🔍 Testing SEO and Analysis Endpoints")
        print("=" * 50)
        
        # Test keyword research
        try:
            params = {
                "query": "AI content creation tools",
                "include_competition": True
            }
            response = self.session.post(f"{API_BASE}/keyword-research", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result("/api/v1/content/keyword-research", "POST", "PASS", 
                                  "Keyword research completed")
                else:
                    self.log_result("/api/v1/content/keyword-research", "POST", "FAIL", 
                                  "Keyword research failed")
            else:
                self.log_result("/api/v1/content/keyword-research", "POST", "FAIL", 
                              f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("/api/v1/content/keyword-research", "POST", "FAIL", str(e))
        
        # Test SEO optimization
        try:
            params = {
                "content": "Artificial intelligence is revolutionizing healthcare. AI-powered tools help doctors diagnose diseases with remarkable accuracy. Machine learning algorithms can analyze medical images and predict patient outcomes.",
                "primary_keyword": "AI healthcare",
                "secondary_keywords": ["artificial intelligence medical", "AI diagnosis", "machine learning healthcare"]
            }
            response = self.session.post(f"{API_BASE}/optimize-seo", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result("/api/v1/content/optimize-seo", "POST", "PASS", 
                                  "SEO optimization completed")
                else:
                    self.log_result("/api/v1/content/optimize-seo", "POST", "FAIL", 
                                  "SEO optimization failed")
            else:
                self.log_result("/api/v1/content/optimize-seo", "POST", "FAIL", 
                              f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("/api/v1/content/optimize-seo", "POST", "FAIL", str(e))
        
        # Test content analysis
        try:
            params = {
                "content": "The future of artificial intelligence in healthcare looks promising. With advances in machine learning and deep learning, we can expect to see more accurate diagnoses, personalized treatments, and improved patient outcomes."
            }
            response = self.session.post(f"{API_BASE}/analyze-content", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    word_count = data.get('word_count', 0)
                    self.log_result("/api/v1/content/analyze-content", "POST", "PASS", 
                                  f"Analyzed {word_count} words")
                else:
                    self.log_result("/api/v1/content/analyze-content", "POST", "FAIL", 
                                  "Content analysis failed")
            else:
                self.log_result("/api/v1/content/analyze-content", "POST", "FAIL", 
                              f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("/api/v1/content/analyze-content", "POST", "FAIL", str(e))
    
    def test_statistics_endpoints(self):
        """Test statistics and history endpoints."""
        print("\n📊 Testing Statistics Endpoints")
        print("=" * 50)
        
        # Test generation history
        try:
            response = self.session.get(f"{API_BASE}/history?limit=5")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    history = data.get('history', {})
                    total = history.get('total_generations', 0)
                    self.log_result("/api/v1/content/history", "GET", "PASS", 
                                  f"Found {total} total generations")
                else:
                    self.log_result("/api/v1/content/history", "GET", "FAIL", 
                                  "Failed to retrieve history")
            else:
                self.log_result("/api/v1/content/history", "GET", "FAIL", 
                              f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("/api/v1/content/history", "GET", "FAIL", str(e))
        
        # Test statistics
        try:
            response = self.session.get(f"{API_BASE}/stats")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    stats = data.get('statistics', {})
                    total = stats.get('total_generations', 0)
                    success_rate = stats.get('success_rate', 0)
                    self.log_result("/api/v1/content/stats", "GET", "PASS", 
                                  f"{total} generations, {success_rate:.1f}% success rate")
                else:
                    self.log_result("/api/v1/content/stats", "GET", "FAIL", 
                                  "Failed to retrieve statistics")
            else:
                self.log_result("/api/v1/content/stats", "GET", "FAIL", 
                              f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("/api/v1/content/stats", "GET", "FAIL", str(e))
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        print("\n🏠 Testing Root Endpoint")
        print("=" * 50)
        
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                app_name = data.get('message', '')
                endpoints = data.get('endpoints', {})
                self.log_result("/", "GET", "PASS", 
                              f"{app_name} - {len(endpoints)} endpoints available")
            else:
                self.log_result("/", "GET", "FAIL", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("/", "GET", "FAIL", str(e))
    
    def run_all_tests(self):
        """Run all tests."""
        print("🚀 Automate Copywriter API - Comprehensive Test Suite")
        print("=" * 60)
        print(f"Testing against: {BASE_URL}")
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test suites
        self.test_root_endpoint()
        self.test_health_endpoints()
        self.test_info_endpoints()
        self.test_content_generation()
        self.test_seo_endpoints()
        self.test_statistics_endpoints()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary."""
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed = len([r for r in self.results if r['status'] == 'PASS'])
        failed = len([r for r in self.results if r['status'] == 'FAIL'])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total_tests)*100:.1f}%")
        
        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"   - {result['method']} {result['endpoint']}: {result['details']}")
        
        print(f"\n⏱️  Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save results to file
        with open('test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"📄 Detailed results saved to: test_results.json")

def main():
    """Main test function."""
    print("Starting API test suite...")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not responding at {BASE_URL}")
            print("Please make sure the FastAPI server is running with: python run.py")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("Please make sure the FastAPI server is running with: python run.py")
        sys.exit(1)
    
    # Run tests
    tester = APITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
