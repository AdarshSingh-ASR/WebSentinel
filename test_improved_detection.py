#!/usr/bin/env python3
"""
Test the improved URL detection with the actual data structure from execution logs.
"""

import json
from datetime import datetime
from api_server import analyze_results_direct

def test_with_real_structure():
    """Test with the actual data structure we found in the logs."""
    print("🧪 Testing Improved URL Detection with Real Data Structure")
    print("=" * 70)
    
    # Recreate the actual structure from the execution logs
    sample_execution_results = {
        "task_id": "test_real_structure",
        "success": True,
        "execution_steps": [
            {
                "step_number": 1,
                "action": "I am now typing in the search box",
                "result": "Results: 1 actions completed",
                "timestamp": "2025-08-23T02:54:32.729388",
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
                        "success": True,
                        "error": None
                    }
                ]
            },
            {
                "step_number": 2,
                "action": "I am now logging the first two results",
                "result": "Results: 4 actions completed",
                "timestamp": "2025-08-23T02:54:32.747108",
                "actions": [
                    {
                        "type": "log_action",
                        "details": {
                            "message": "I am now typing in the search box"
                        }
                    },
                    {
                        "type": "input",
                        "details": {
                            "text": "tseries",
                            "index": 3
                        }
                    }
                ],
                "results": [
                    {
                        "content": "Logged action: I am now typing in the search box",
                        "is_done": False,
                        "success": None,
                        "error": None
                    },
                    {
                        "content": "⌨️  Input tseries into index 3",
                        "is_done": False,
                        "success": None,
                        "error": None
                    }
                ]
            }
        ],
        "screenshots": ["screenshot1.png", "screenshot2.png", "screenshot3.png", "screenshot4.png", "screenshot5.png"],
        "error": None
    }
    
    sample_original_instructions = {
        "target_url": "https://www.youtube.com/",
        "task_description": "go and search for tseries and log the first two result on it",
        "screenshot_instructions": []
    }
    
    print("📊 Test Data Overview:")
    print(f"- Target URL: {sample_original_instructions['target_url']}")
    print(f"- Task Success: {sample_execution_results['success']}")
    print(f"- Steps: {len(sample_execution_results['execution_steps'])}")
    print(f"- Step 1 has navigation action: Yes")
    print(f"- Step 1 results show navigation: Yes")
    
    # Test the improved analysis function
    try:
        print("\\n🔄 Running Improved Analysis...")
        analysis_result = analyze_results_direct(sample_execution_results, sample_original_instructions)
        
        print("✅ Analysis completed successfully!")
        
        # Key results
        url_accessed = analysis_result.get('compliance_check', {}).get('target_url_accessed')
        success = analysis_result.get('execution_summary', {}).get('success')
        
        print(f"\\n📋 Analysis Results:")
        print(f"  - URL Accessed: {url_accessed}")
        print(f"  - Task Success: {success}")
        print(f"  - Compliance: {'PASS' if url_accessed and success else 'FAIL'}")
        
        print(f"\\n💡 Recommendations:")
        for i, rec in enumerate(analysis_result.get('recommendations', []), 1):
            icon = "✅" if "success" in rec.lower() else "💡"
            print(f"  {i}. {icon} {rec}")
        
        # Test outcome
        if url_accessed:
            print(f"\\n🎉 SUCCESS! Improved URL detection is working!")
            print(f"   The system correctly detected the YouTube navigation in step data.")
            return True
        else:
            print(f"\\n❌ FAILED! URL detection still not working.")
            print(f"   Need to debug further...")
            
            # Debug output
            print(f"\\n🔧 Debug Information:")
            print(f"  - Target URL: {sample_original_instructions['target_url']}")
            print(f"  - Step 1 action type: navigate")
            print(f"  - Step 1 URL: https://www.youtube.com/")
            print(f"  - Should match: Yes")
            
            return False
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def test_with_results_content():
    """Test URL detection via results content."""
    print("\\n🧪 Testing Results Content Detection")
    print("=" * 70)
    
    # Test with navigation info in results content
    sample_execution_results = {
        "task_id": "test_results_content",
        "success": True,
        "execution_steps": [
            {
                "step_number": 1,
                "action": "Navigating to website",
                "result": "Navigation completed",
                "timestamp": "2025-08-23T02:54:32.729388",
                "results": [
                    {
                        "content": "🔗  Navigated to https://www.youtube.com/",
                        "is_done": False,
                        "success": True,
                        "error": None
                    }
                ]
            }
        ],
        "screenshots": ["screenshot1.png"],
        "error": None
    }
    
    sample_original_instructions = {
        "target_url": "https://www.youtube.com/",
        "task_description": "test navigation",
        "screenshot_instructions": []
    }
    
    print("📊 Testing results content detection...")
    
    try:
        analysis_result = analyze_results_direct(sample_execution_results, sample_original_instructions)
        url_accessed = analysis_result.get('compliance_check', {}).get('target_url_accessed')
        
        if url_accessed:
            print("✅ Results content detection working!")
            return True
        else:
            print("❌ Results content detection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Improved URL Detection Validation Test")
    print("=" * 80)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Real data structure
    if test_with_real_structure():
        tests_passed += 1
    
    # Test 2: Results content
    if test_with_results_content():
        tests_passed += 1
    
    print("\\n" + "=" * 80)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The improved URL detection is working!")
        print("\\n🚀 The analysis should now correctly detect navigation in real scenarios.")
    else:
        print("⚠️  Some tests failed. URL detection needs more work.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    main()