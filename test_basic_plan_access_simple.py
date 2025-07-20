#!/usr/bin/env python3
"""
Simple test to verify Basic Plan users have access to premium transcription models
"""

import sys
import os

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Test Basic Plan model access."""
    print("🚀 Basic Plan Model Access - Simple Test")
    print("=" * 60)
    
    try:
        from services.plan_access_control import PlanAccessControl
        
        # Models that should be accessible to Basic Plan users
        test_models = [
            'gpt-4o-transcribe',
            'gemini-2.5-flash-preview-05-20'
        ]
        
        print("🔍 Testing Basic Plan access to premium transcription models:")
        print("")
        
        all_passed = True
        
        for model in test_models:
            # Test if model is in accessible models list
            accessible_models = PlanAccessControl.get_accessible_models('transcription', 'basic')
            is_in_list = model in accessible_models
            
            # Test model validation
            is_allowed, result = PlanAccessControl.validate_model_access(model, 'transcription', 'basic')
            
            # Get model info
            model_info = PlanAccessControl.get_model_info(model)
            model_name = model_info.get('name', model)
            model_tier = model_info.get('tier', 'unknown')
            
            print(f"📋 {model_name} ({model}):")
            print(f"   ✅ In accessible models list: {is_in_list}")
            print(f"   ✅ Passes validation: {is_allowed}")
            print(f"   ✅ Model tier: {model_tier}")
            
            if is_in_list and is_allowed and model_tier == 'basic':
                print(f"   🎉 RESULT: ACCESSIBLE TO BASIC PLAN")
            else:
                print(f"   ❌ RESULT: NOT ACCESSIBLE TO BASIC PLAN")
                all_passed = False
            
            print("")
        
        print("=" * 60)
        if all_passed:
            print("🎉 SUCCESS: All premium transcription models are accessible to Basic Plan users!")
            print("")
            print("Expected behavior in the UI:")
            print("  🔓 Gemini 2.5 Flash Preview 05-20 - No lock icon")
            print("  🔓 OpenAI GPT-4o - No lock icon")
            print("  ✅ Both models selectable by Basic Plan users")
            return True
        else:
            print("❌ FAILURE: Some models are not accessible to Basic Plan users")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
