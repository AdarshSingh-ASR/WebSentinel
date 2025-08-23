#!/usr/bin/env python3
"""
Test Portia Analysis Extraction
This script tests the Portia analysis functionality to debug extraction issues.
"""

import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Portia components
try:
    from portia import Portia, Config, LLMProvider
    PORTIA_AVAILABLE = True
except ImportError:
    print("❌ Portia is not available. Please install: pip install portia-sdk-python[google]")
    PORTIA_AVAILABLE = False

def test_portia_analysis():
    """Test Portia analysis extraction with debug logging."""
    if not PORTIA_AVAILABLE:
        return False
        
    # Check API key
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found in environment")
        return False
    
    print("🧪 Testing Portia Analysis Extraction")
    print("=" * 60)
    
    # Create test prompt similar to what we use in production
    prompt = """You are a website testing analysis expert. Analyze this browser automation test:

TEST OVERVIEW:
- Target URL: https://www.youtube.com/
- Task: Search for Charlie Puth and log first two results
- Success: True
- Steps Completed: 10
- Screenshots Captured: 10
- Error: None
- Target URL Accessed: True

KEY FINDINGS:
- Task completed successfully
- All steps executed without errors
- Screenshots captured properly
- Search results extracted correctly

Provide a comprehensive analysis with:
1. **Executive Summary** (2-3 sentences)
2. **Key Findings** (bullet points)
3. **Recommendations** (actionable items)
4. **Compliance Status** (Pass/Fail assessment)

Keep response clear and actionable."""
    
    try:
        print("🔧 Configuring Portia...")
        
        # Create Portia config
        google_config = Config.from_default(
            llm_provider=LLMProvider.GOOGLE,
            default_model="google/gemini-2.0-flash",
            google_api_key=GEMINI_API_KEY
        )
        
        # Disable telemetry if possible
        try:
            google_config.telemetry_enabled = False
        except:
            pass
        
        print("🚀 Creating Portia agent...")
        portia_agent = Portia(config=google_config)
        
        print("⚡ Running analysis...")
        plan_run = portia_agent.run(prompt)
        
        print("🔍 Examining Portia response...")
        print(f"📊 Plan run type: {type(plan_run)}")
        print(f"📋 Plan run attributes: {[attr for attr in dir(plan_run) if not attr.startswith('_')]}")
        
        # Test our extraction methods
        ai_analysis = None
        extraction_method = "unknown"
        
        # Method 1: Check outputs (most likely location)
        if hasattr(plan_run, 'outputs') and plan_run.outputs:
            print(f"🎯 outputs found: {type(plan_run.outputs)}")
            
            # Check if outputs has final_output with LocalDataValue
            if hasattr(plan_run.outputs, 'final_output') and plan_run.outputs.final_output:
                final_output = plan_run.outputs.final_output
                print(f"📋 final_output type: {type(final_output)}")
                
                if hasattr(final_output, 'value') and final_output.value:
                    content = str(final_output.value).strip()
                    print(f"📝 Found final_output.value: {len(content)} chars")
                    print(f"📝 Preview: {content[:200]}...")
                    if len(content) > 20:
                        ai_analysis = content
                        extraction_method = "outputs_final_output_value"
                        print("✅ Successfully extracted from outputs.final_output.value")
            
            # Check step_outputs if final_output didn't work
            if not ai_analysis and hasattr(plan_run.outputs, 'step_outputs'):
                step_outputs = plan_run.outputs.step_outputs
                print(f"📋 step_outputs: {type(step_outputs)}")
                
                if isinstance(step_outputs, dict):
                    for key in ['$analysis', 'analysis', 'result', 'output']:
                        if key in step_outputs:
                            step_output = step_outputs[key]
                            if hasattr(step_output, 'value') and step_output.value:
                                content = str(step_output.value).strip()
                                print(f"📝 Found step_outputs[{key}].value: {len(content)} chars")
                                if len(content) > 20:
                                    ai_analysis = content
                                    extraction_method = f"step_outputs_{key}_value"
                                    print(f"✅ Successfully extracted from step_outputs[{key}].value")
                                    break
        
        # Method 2: final_output
        if not ai_analysis and hasattr(plan_run, 'final_output') and plan_run.final_output:
            content = str(plan_run.final_output).strip()
            print(f"🎯 final_output found: {len(content)} characters")
            print(f"📝 final_output preview: {content[:200]}...")
            
            if (len(content) > 5 and 
                not content.startswith('Run(id=') and 
                not content.startswith('PlanRun(id=') and
                not content.startswith('<') and
                'object at 0x' not in content):
                ai_analysis = content
                extraction_method = "final_output"
                print("✅ Successfully extracted from final_output")
        
        # Method 2: output
        if not ai_analysis and hasattr(plan_run, 'output') and plan_run.output:
            content = str(plan_run.output).strip()
            print(f"🎯 output found: {len(content)} characters")
            print(f"📝 output preview: {content[:200]}...")
            
            if (len(content) > 5 and 
                not content.startswith('Run(id=') and 
                not content.startswith('PlanRun(id=') and
                not content.startswith('<') and
                'object at 0x' not in content):
                ai_analysis = content
                extraction_method = "output"
                print("✅ Successfully extracted from output")
        
        # Method 3: String conversion
        if not ai_analysis:
            content = str(plan_run).strip()
            print(f"🎯 String conversion: {len(content)} characters")
            print(f"📝 String preview: {content[:200]}...")
            
            if (len(content) > 20 and 
                not content.startswith('Run(id=') and
                not content.startswith('PlanRun(id=') and
                'object at 0x' not in content):
                ai_analysis = content
                extraction_method = "string_conversion"
                print("✅ Successfully extracted from string conversion")
        
        # Results
        if ai_analysis:
            print("\n" + "=" * 60)
            print("🎉 EXTRACTION SUCCESSFUL!")
            print(f"✅ Method: {extraction_method}")
            print(f"📏 Length: {len(ai_analysis)} characters")
            print("\n📄 FULL ANALYSIS:")
            print("-" * 40)
            print(ai_analysis)
            print("-" * 40)
            return True
        else:
            print("\n" + "=" * 60)
            print("❌ EXTRACTION FAILED!")
            print("No valid content found in any method")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_portia_analysis()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Portia analysis test {'passed' if success else 'failed'}")