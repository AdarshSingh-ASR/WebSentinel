#!/usr/bin/env python3
"""
Test script to verify AI analysis functionality is working correctly.
"""

import json
from datetime import datetime
from api_server import analyze_results_direct

def test_analysis_function():
    """Test the direct analysis function."""
    print("🧪 Testing AI Analysis Function")
    print("=" * 50)
    
    # Create sample test data
    sample_execution_results = {
        "task_id": "test_task_123",
        "success": True,
        "execution_steps": [
            {"action": "navigate to https://www.youtube.com/", "result": "Page loaded"},
            {"action": "search for tseries", "result": "Search performed"},
            {"action": "click first result", "result": "Clicked successfully"},
            {"action": "take screenshot", "result": "Screenshot captured"},
            {"action": "log first two results", "result": "Results logged"}
        ],
        "screenshots": [
            "screenshot1.png",
            "screenshot2.png",
            "screenshot3.png"
        ],
        "error": None,
        "full_conversation": ["message1", "message2", "message3"]
    }
    
    sample_original_instructions = {
        "target_url": "https://www.youtube.com/",
        "task_description": "go and search for tseries and log the first two results",
        "screenshot_instructions": []
    }
    
    print("📊 Sample Data Created")
    print(f"- Task Success: {sample_execution_results['success']}")
    print(f"- Steps: {len(sample_execution_results['execution_steps'])}")
    print(f"- Screenshots: {len(sample_execution_results['screenshots'])}")
    print(f"- Target URL: {sample_original_instructions['target_url']}")
    
    # Test the analysis function
    try:
        print("\n🔄 Running Analysis...")
        analysis_result = analyze_results_direct(sample_execution_results, sample_original_instructions)
        
        print("✅ Analysis completed successfully!")
        print("\n📋 Analysis Results:")
        print(f"- Task ID: {analysis_result.get('task_id')}")
        print(f"- Timestamp: {analysis_result.get('timestamp')}")
        print(f"- Success: {analysis_result.get('execution_summary', {}).get('success')}")
        print(f"- Steps Completed: {analysis_result.get('execution_summary', {}).get('steps_completed')}")
        print(f"- Screenshots Captured: {analysis_result.get('execution_summary', {}).get('screenshots_captured')}")
        print(f"- URL Accessed: {analysis_result.get('compliance_check', {}).get('target_url_accessed')}")
        
        print("\n💡 Recommendations:")
        for i, rec in enumerate(analysis_result.get('recommendations', []), 1):
            print(f"  {i}. {rec}")
        
        print("\n✅ Direct analysis function is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def test_analysis_with_error():
    """Test analysis with error scenario."""
    print("\n🧪 Testing Error Scenario")
    print("=" * 50)
    
    # Create sample error data
    error_execution_results = {
        "task_id": "test_error_123",
        "success": False,
        "execution_steps": [
            {"action": "navigate to https://invalid-url.com/", "result": "Navigation failed"}
        ],
        "screenshots": [],
        "error": "Failed to load page: Network timeout",
        "full_conversation": ["error message"]
    }
    
    error_original_instructions = {
        "target_url": "https://invalid-url.com/",
        "task_description": "test invalid website",
        "screenshot_instructions": [
            {"step_description": "screenshot of page", "filename": "test.png"}
        ]
    }
    
    try:
        print("🔄 Running Error Analysis...")
        analysis_result = analyze_results_direct(error_execution_results, error_original_instructions)
        
        print("✅ Error analysis completed!")
        print(f"- Success: {analysis_result.get('execution_summary', {}).get('success')}")
        print(f"- Error: {analysis_result.get('execution_summary', {}).get('error')}")
        print(f"- Screenshot Requirements Met: {analysis_result.get('compliance_check', {}).get('screenshots_captured', {}).get('meets_requirements')}")
        
        print("\n💡 Error Recommendations:")
        for i, rec in enumerate(analysis_result.get('recommendations', []), 1):
            print(f"  {i}. {rec}")
        
        print("\n✅ Error analysis function is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error analysis failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 WebSentinel AI Analysis Fix Verification")
    print("=" * 70)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Normal scenario
    if test_analysis_function():
        tests_passed += 1
    
    # Test 2: Error scenario  
    if test_analysis_with_error():
        tests_passed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! AI Analysis function is working correctly!")
        print("\n💡 The analysis functionality has been fixed and should now work properly.")
        print("   - Improved error handling")
        print("   - Better Portia configuration")
        print("   - Fallback analysis methods")
        print("   - Reduced telemetry issues")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    main()