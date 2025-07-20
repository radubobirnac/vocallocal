#!/usr/bin/env python3
"""
Test Basic Plan Model Access
Verify that Basic Plan users have access to premium transcription models
"""

import sys
import os

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_backend_model_access():
    """Test the backend model access configuration."""
    print("🔧 Testing Backend Model Access Configuration")
    print("=" * 60)
    
    try:
        from services.plan_access_control import PlanAccessControl
        
        # Test Basic Plan transcription model access
        print("📋 Basic Plan Transcription Models:")
        basic_transcription_models = PlanAccessControl.get_accessible_models('transcription', 'basic')
        for model in basic_transcription_models:
            print(f"  ✅ {model}")
        
        # Check specific models that should be accessible
        required_models = [
            'gpt-4o-transcribe',
            'gemini-2.5-flash-preview-05-20'
        ]
        
        print(f"\n🔍 Checking Required Models for Basic Plan:")
        all_accessible = True
        for model in required_models:
            if model in basic_transcription_models:
                print(f"  ✅ {model} - ACCESSIBLE")
            else:
                print(f"  ❌ {model} - NOT ACCESSIBLE")
                all_accessible = False
        
        # Test model validation
        print(f"\n🔍 Testing Model Validation:")
        for model in required_models:
            is_allowed, result = PlanAccessControl.validate_model_access(model, 'transcription', 'basic')
            status = "✅ ALLOWED" if is_allowed else "❌ DENIED"
            print(f"  {model}: {status}")
            if not is_allowed:
                print(f"    Reason: {result.get('error', {}).get('message', 'Unknown')}")
                all_accessible = False
        
        # Test model info
        print(f"\n📋 Model Information:")
        for model in required_models:
            model_info = PlanAccessControl.get_model_info(model)
            if model_info:
                print(f"  {model}:")
                print(f"    Name: {model_info['name']}")
                print(f"    Tier: {model_info['tier']}")
                print(f"    Description: {model_info['description']}")
            else:
                print(f"  {model}: No model info found")
                all_accessible = False
        
        return all_accessible
        
    except Exception as e:
        print(f"❌ Error testing backend: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_model_access():
    """Test the frontend model access configuration by reading the JS file."""
    print("\n🔧 Testing Frontend Model Access Configuration")
    print("=" * 60)
    
    try:
        # Read the frontend plan access control file
        js_file_path = 'static/js/plan-access-control.js'
        
        if not os.path.exists(js_file_path):
            print(f"❌ Frontend file not found: {js_file_path}")
            return False
        
        with open(js_file_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Check if required models are in the basic plan transcription list
        required_models = [
            'gpt-4o-transcribe',
            'gemini-2.5-flash-preview-05-20'
        ]
        
        print("🔍 Checking Frontend Basic Plan Configuration:")
        all_found = True
        
        for model in required_models:
            if model in js_content:
                print(f"  ✅ {model} - FOUND in frontend config")
            else:
                print(f"  ❌ {model} - NOT FOUND in frontend config")
                all_found = False
        
        # Check tier assignments in modelInfo
        print(f"\n🔍 Checking Model Tier Assignments:")
        for model in required_models:
            # Look for the model in modelInfo with tier: 'basic'
            model_pattern = f"'{model}'"
            tier_pattern = "tier: 'basic'"
            
            if model_pattern in js_content:
                # Find the line with the model
                lines = js_content.split('\n')
                model_line_idx = None
                for i, line in enumerate(lines):
                    if model_pattern in line and 'modelInfo' in js_content[:js_content.find(line)]:
                        model_line_idx = i
                        break
                
                if model_line_idx is not None:
                    # Check the next few lines for tier assignment
                    tier_found = False
                    for j in range(max(0, model_line_idx-2), min(len(lines), model_line_idx+3)):
                        if tier_pattern in lines[j]:
                            tier_found = True
                            break
                    
                    if tier_found:
                        print(f"  ✅ {model} - Tier: basic")
                    else:
                        print(f"  ❌ {model} - Tier: NOT basic")
                        all_found = False
                else:
                    print(f"  ❌ {model} - Model info not found")
                    all_found = False
            else:
                print(f"  ❌ {model} - Not found in frontend")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ Error testing frontend: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    print("🚀 Basic Plan Model Access Test")
    print("=" * 80)
    
    print("Testing model access for Basic Plan users to premium transcription models:")
    print("  - Gemini 2.5 Flash Preview 05-20")
    print("  - OpenAI GPT-4o")
    print("")
    
    # Test backend configuration
    backend_success = test_backend_model_access()
    
    # Test frontend configuration
    frontend_success = test_frontend_model_access()
    
    # Overall result
    print(f"\n" + "="*80)
    if backend_success and frontend_success:
        print(f"🎉 SUCCESS: Basic Plan Model Access Configuration")
        print(f"="*80)
        print(f"")
        print(f"✅ Backend: All required models accessible for Basic Plan")
        print(f"✅ Frontend: All required models configured for Basic Plan")
        print(f"")
        print(f"Basic Plan users should now have access to:")
        print(f"  🔓 Gemini 2.5 Flash Preview 05-20")
        print(f"  🔓 OpenAI GPT-4o")
        print(f"")
        print(f"The 🔒 lock icons should be removed from these models.")
        return True
    else:
        print(f"❌ FAILURE: Basic Plan Model Access Configuration")
        print(f"="*80)
        print(f"")
        if not backend_success:
            print(f"❌ Backend: Configuration issues found")
        if not frontend_success:
            print(f"❌ Frontend: Configuration issues found")
        print(f"")
        print(f"Please check the error details above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
