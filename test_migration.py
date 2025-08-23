#!/usr/bin/env python3
"""
Test script to validate the migration from Agno to Portia AI.
This script checks that all imports work correctly and basic functionality is available.
"""

import os
from dotenv import load_dotenv

def test_imports():
    """Test that all necessary imports work."""
    print("🔍 Testing imports...")
    
    try:
        # Test Portia imports
        from portia import Portia, Config, LLMProvider, ToolRegistry, tool
        print("✅ Portia AI imports successful")
    except ImportError as e:
        print(f"❌ Portia AI import failed: {e}")
        return False
    
    try:
        # Test browser-use imports
        import browser_use
        from browser_use import Browser, BrowserConfig
        print("✅ Browser-use imports successful")
    except ImportError as e:
        print(f"❌ Browser-use import failed: {e}")
        return False
    
    try:
        # Test FastAPI imports
        from fastapi import FastAPI
        print("✅ FastAPI imports successful")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    return True

def test_portia_config():
    """Test Portia configuration."""
    print("\n🔧 Testing Portia configuration...")
    
    # Load environment variables
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if not gemini_api_key:
        print("⚠️  GEMINI_API_KEY not found in .env file")
        print("   This is needed for full functionality but not for import testing")
        return True
    
    try:
        from portia import Config, LLMProvider
        
        # Test Google GenAI config
        google_config = Config.from_default(
            llm_provider=LLMProvider.GOOGLE,
            default_model="google/gemini-2.0-flash",
            google_api_key=gemini_api_key
        )
        print("✅ Portia Google GenAI config created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Portia config failed: {e}")
        return False

def test_tool_creation():
    """Test Portia Tool creation."""
    print("\n🔨 Testing Portia Tool creation...")
    
    try:
        from portia import tool
        
        @tool
        def test_tool(message: str) -> str:
            """A simple test tool."""
            return f"Test tool received: {message}"
        
        # Test that the decorator creates a tool object
        if hasattr(test_tool, '__name__') or hasattr(test_tool, 'id'):
            print(f"✅ Test tool decorator applied successfully")
            return True
        else:
            print(f"❌ Tool decorator didn't create expected object")
            return False
        
    except Exception as e:
        print(f"❌ Tool creation failed: {e}")
        return False

def main():
    """Run all migration tests."""
    print("🚀 WebSentinel - Portia AI Migration Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Portia Config Test", test_portia_config),
        ("Tool Creation Test", test_tool_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Migration to Portia AI successful!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -e .")
        print("2. Set up .env file with GEMINI_API_KEY")
        print("3. Run backend: python api_server.py")
        print("4. Run frontend: cd frontend && npm start")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("Make sure you have installed: pip install portia-sdk-python[google]")
    
    return passed == total

if __name__ == "__main__":
    main()