#!/usr/bin/env python3
"""
Test script to verify the improved URL detection logic works correctly.
"""

import json
from datetime import datetime
from api_server import analyze_results_direct

def test_url_detection_with_enhanced_steps():
    """Test URL detection using enhanced steps data structure."""
    print("🧪 Testing Enhanced Steps URL Detection")
    print("=" * 50)
    
    # Sample data based on actual execution results structure
    sample_execution_results = {
        "task_id": "test_task_enhanced",
        "success": True,
        "execution_steps": [
            {
                "step_number": 1,
                "action": "I am now typing in the search box",
                "result": "Results: 1 actions completed",
                "timestamp": "2025-08-23T02:40:37.979088"
            },
            {
                "step_number": 2,
                "action": "I am now logging the first two results",
                "result": "Results: 4 actions completed",
                "timestamp": "2025-08-23T02:40:37.985974"
            }
        ],
        "enhanced_steps": [
            {
                "step_number": 1,
                "action_type": "navigate",
                "success": True,
                "actions": [
                    {
                        "type": "navigate",
                        "details": {
                            "url": "https://www.youtube.com/"
                        }
                    }
                ],
                "results": [
                    {
                        "content": "🔗  Navigated to https://www.youtube.com/",
                        "is_done": False,
                        "success": None,
                        "error": None
                    }
                ]
            },
            {
                "step_number": 2,
                "action_type": "input",
                "success": True,
                "actions": [
                    {
                        "type": "input_text",
                        "details": {
                            "text": "tseries"
                        }
                    }
                ]
            }
        ],
        "screenshots": ["screenshot1.png", "screenshot2.png", "screenshot3.png"],
        "error": None
    }
    
    sample_original_instructions = {
        "target_url": "https://www.youtube.com/",
        "task_description": "go and search for tseries and log the first two results",
        "screenshot_instructions": []
    }
    
    print("📊 Testing with enhanced steps data")
    print(f"- Target URL: {sample_original_instructions['target_url']}")
    print(f"- Enhanced steps available: {len(sample_execution_results['enhanced_steps'])}")
    print(f"- Navigation action in enhanced steps: Yes")
    
    # Test the analysis function
    try:
        print("\\n🔄 Running Enhanced Analysis...")
        analysis_result = analyze_results_direct(sample_execution_results, sample_original_instructions)
        
        print("✅ Analysis completed successfully!")
        print(f"\\n📋 Enhanced Analysis Results:")
        print(f"- Task ID: {analysis_result.get('task_id')}")
        print(f"- Success: {analysis_result.get('execution_summary', {}).get('success')}")
        print(f"- URL Accessed: {analysis_result.get('compliance_check', {}).get('target_url_accessed')}")
        
        print("\\n💡 Recommendations:")
        for i, rec in enumerate(analysis_result.get('recommendations', []), 1):
            print(f"  {i}. {rec}")
        
        # Check if URL was properly detected
        url_accessed = analysis_result.get('compliance_check', {}).get('target_url_accessed', False)
        if url_accessed:
            print("\\n✅ URL detection PASSED! Enhanced steps navigation detected correctly.")
            return True
        else:
            print("\\n❌ URL detection FAILED! Enhanced steps navigation not detected.")
            return False
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

def test_url_detection_fallback():
    """Test URL detection using fallback methods."""
    print("\\n🧪 Testing Fallback URL Detection")
    print("=" * 50)
    
    # Sample data without enhanced steps (fallback scenario)
    sample_execution_results = {
        "task_id": "test_task_fallback",
        "success": True,
        "execution_steps": [
            {
                "step_number": 1,
                "action": "Navigating to https://www.youtube.com/",
                "result": "Page loaded successfully",
                "timestamp": "2025-08-23T02:40:37.979088"
            },
            {
                "step_number": 2,
                "action": "Searching for tseries",
                "result": "Search completed",
                "timestamp": "2025-08-23T02:40:37.985974"
            }
        ],
        "screenshots": ["screenshot1.png"],
        "error": None
    }
    
    sample_original_instructions = {
        "target_url": "https://www.youtube.com/",
        "task_description": "go and search for tseries",
        "screenshot_instructions": []
    }
    
    print("📊 Testing with fallback methods")
    print(f"- Target URL: {sample_original_instructions['target_url']}")
    print(f"- Enhanced steps available: No")
    print(f"- Navigation in action text: Yes")
    
    # Test the analysis function
    try:
        print("\\n🔄 Running Fallback Analysis...")
        analysis_result = analyze_results_direct(sample_execution_results, sample_original_instructions)
        
        print("✅ Analysis completed successfully!")
        print(f"\\n📋 Fallback Analysis Results:")
        print(f"- URL Accessed: {analysis_result.get('compliance_check', {}).get('target_url_accessed')}")
        
        print("\\n💡 Recommendations:")
        for i, rec in enumerate(analysis_result.get('recommendations', []), 1):
            print(f"  {i}. {rec}")
        
        # Check if URL was properly detected
        url_accessed = analysis_result.get('compliance_check', {}).get('target_url_accessed', False)
        if url_accessed:
            print("\\n✅ Fallback URL detection PASSED!")
            return True
        else:
            print("\\n❌ Fallback URL detection FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

def main():
    """Run all URL detection tests."""
    print("🚀 WebSentinel AI Analysis URL Detection Fix Test")
    print("=" * 70)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Enhanced steps detection
    if test_url_detection_with_enhanced_steps():
        tests_passed += 1
    
    # Test 2: Fallback detection
    if test_url_detection_fallback():
        tests_passed += 1
    
    print("\\n" + "=" * 70)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! URL detection logic is working correctly!")
        print("\\n💡 The URL detection has been significantly improved:")
        print("   - ✅ Enhanced steps navigation detection (primary method)")
        print("   - ✅ Fallback to action/result text analysis")
        print("   - ✅ Domain-based detection as final fallback")
        print("   - ✅ More accurate analysis reports")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    main()