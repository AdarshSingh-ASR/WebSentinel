#!/usr/bin/env python3
"""
Debug script to test the current analysis with the real recent execution data.
"""

import json
from datetime import datetime
from pathlib import Path
from api_server import analyze_results_direct

def test_current_execution():
    """Test with the actual current execution data."""
    print("🔍 Debugging Current Execution Analysis")
    print("=" * 60)
    
    # Load the actual execution data
    execution_file = Path("./operation_logs/browser_execution_task_20250823_025339_773018_20250823_025432.json")
    
    if not execution_file.exists():
        print(f"❌ Execution file not found: {execution_file}")
        return False
    
    try:
        with open(execution_file, 'r') as f:
            execution_data = json.load(f)
        
        print("✅ Loaded execution data successfully")
        print(f"📊 Data Overview:")
        print(f"  - Task ID: {execution_data.get('task_id')}")
        print(f"  - Success: {execution_data.get('success')}")
        print(f"  - Steps: {len(execution_data.get('execution_steps', []))}")
        print(f"  - Enhanced Steps: {len(execution_data.get('enhanced_steps', []))}")
        
        # Check for navigation in enhanced steps
        enhanced_steps = execution_data.get('enhanced_steps', [])
        navigation_found = False
        
        print(f"\\n🔍 Checking Enhanced Steps for Navigation:")
        for i, step in enumerate(enhanced_steps):
            actions = step.get('actions', [])
            print(f"  Step {i+1}: {len(actions)} actions")
            for j, action in enumerate(actions):
                action_type = action.get('type')
                details = action.get('details', {})
                print(f"    Action {j+1}: type='{action_type}', details={details}")
                if action_type == 'navigate':
                    url = details.get('url', '')
                    if 'youtube.com' in url:
                        navigation_found = True
                        print(f"    ✅ NAVIGATION FOUND: {url}")
        
        if navigation_found:
            print(f"\\n✅ Navigation to YouTube detected in enhanced steps")
        else:
            print(f"\\n❌ No YouTube navigation found in enhanced steps")
        
        # Test with our original instructions
        original_instructions = {
            "target_url": "https://www.youtube.com/",
            "task_description": "go and search for tseries and log the first two result on it",
            "screenshot_instructions": []
        }
        
        print(f"\\n🔄 Running Analysis with Current Data...")
        analysis_result = analyze_results_direct(execution_data, original_instructions)
        
        print(f"\\n📋 Analysis Results:")
        print(f"  - URL Accessed: {analysis_result.get('compliance_check', {}).get('target_url_accessed')}")
        print(f"  - Success Status: {analysis_result.get('execution_summary', {}).get('success')}")
        
        print(f"\\n💡 Recommendations:")
        for i, rec in enumerate(analysis_result.get('recommendations', []), 1):
            print(f"  {i}. {rec}")
        
        url_accessed = analysis_result.get('compliance_check', {}).get('target_url_accessed', False)
        
        if url_accessed:
            print(f"\\n🎉 SUCCESS! URL detection is working correctly.")
            print(f"The analysis correctly detected the YouTube navigation.")
            return True
        else:
            print(f"\\n❌ PROBLEM! URL detection is still failing.")
            print(f"Even with enhanced steps containing navigation data, URL access shows as False.")
            
            # Debug the URL detection logic
            print(f"\\n🔧 Debugging URL Detection Logic:")
            target_url = original_instructions.get("target_url", "")
            print(f"  Target URL: {target_url}")
            
            # Method 1 check
            enhanced_steps = execution_data.get("enhanced_steps", [])
            method1_found = False
            for step in enhanced_steps:
                if isinstance(step, dict) and "actions" in step:
                    for action in step.get("actions", []):
                        if (action.get("type") == "navigate" and 
                            action.get("details", {}).get("url", "").startswith(target_url.rstrip("/"))):
                            method1_found = True
                            print(f"  ✅ Method 1 (Enhanced Steps): SHOULD WORK")
                            print(f"     Action type: {action.get('type')}")
                            print(f"     URL: {action.get('details', {}).get('url', '')}")
                            print(f"     Target: {target_url.rstrip('/')}")
                            break
            
            if not method1_found:
                print(f"  ❌ Method 1 (Enhanced Steps): Failed")
            
            return False
        
    except Exception as e:
        print(f"❌ Error loading/analyzing execution data: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def main():
    """Main test function."""
    print("🚀 Current Analysis Debug Test")
    print("=" * 80)
    
    success = test_current_execution()
    
    print("\\n" + "=" * 80)
    if success:
        print("✅ Analysis is working correctly!")
    else:
        print("❌ Analysis needs further debugging!")
        print("\\n🔧 Next steps:")
        print("  1. Check if the tool version matches the direct function")
        print("  2. Verify the data being passed to the analysis")
        print("  3. Test the URL detection logic manually")
    
    return success

if __name__ == "__main__":
    main()