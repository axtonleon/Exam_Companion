#!/usr/bin/env python3
"""
Test script to verify the FastAPI application setup.
Run this to check if all components are working correctly.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from app.config import settings
        print("✓ Configuration imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import configuration: {e}")
        return False
    
    try:
        from app.schemas.content import ContentGenerationRequest
        print("✓ Schemas imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import schemas: {e}")
        return False
    
    try:
        from app.services.content_service import get_content_service
        print("✓ Services imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import services: {e}")
        return False
    
    try:
        from app.routes.content import router
        print("✓ Routes imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import routes: {e}")
        return False
    
    try:
        from app.tools.agents import get_content_agents
        print("✓ AI agents imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import AI agents: {e}")
        return False
    
    try:
        from app.main import app
        print("✓ FastAPI app imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import FastAPI app: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration settings."""
    print("\nTesting configuration...")
    
    try:
        from app.config import settings
        
        print(f"✓ App name: {settings.app_name}")
        print(f"✓ App version: {settings.app_version}")
        print(f"✓ Debug mode: {settings.debug}")
        print(f"✓ Host: {settings.host}")
        print(f"✓ Port: {settings.port}")
        print(f"✓ Model ID: {settings.model_id}")
        
        # Check for API keys
        if settings.google_api_key:
            print("✓ Google API key is configured")
        else:
            print("⚠ Google API key is not configured (required for AI functionality)")
        
        if settings.jina_api_key:
            print("✓ Jina API key is configured")
        else:
            print("⚠ Jina API key is not configured (optional but recommended)")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_schema_validation():
    """Test Pydantic schema validation."""
    print("\nTesting schema validation...")
    
    try:
        from app.schemas.content import ContentGenerationRequest
        
        # Test valid request
        valid_request = ContentGenerationRequest(
            topic="Test topic for content generation",
            content_type="blog_post",
            tone="professional"
        )
        print("✓ Valid request schema validation passed")
        
        # Test invalid request
        try:
            invalid_request = ContentGenerationRequest(
                topic="",  # Empty topic should fail
                content_type="blog_post"
            )
            print("✗ Invalid request should have failed validation")
            return False
        except Exception:
            print("✓ Invalid request correctly rejected")
        
        return True
        
    except Exception as e:
        print(f"✗ Schema validation test failed: {e}")
        return False

def test_file_structure():
    """Test if all required files exist."""
    print("\nTesting file structure...")
    
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/config.py",
        "app/schemas/content.py",
        "app/services/content_service.py",
        "app/services/seo_service.py",
        "app/routes/content.py",
        "app/tools/jina_tools.py",
        "app/tools/agents.py",
        "app/utils/helpers.py",
        "requirements.txt",
        "README.md"
    ]
    
    all_files_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - Missing!")
            all_files_exist = False
    
    return all_files_exist

def main():
    """Run all tests."""
    print("=" * 50)
    print("Automate Copywriter API - Setup Test")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Schema Validation", test_schema_validation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        if test_func():
            passed += 1
            print(f"✓ {test_name} test passed")
        else:
            print(f"✗ {test_name} test failed")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Set up your .env file with API keys")
        print("2. Run: python run.py")
        print("3. Visit: http://localhost:8000/docs")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
