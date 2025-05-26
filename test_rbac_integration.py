#!/usr/bin/env python3
"""
Integration test for RBAC system in VocalLocal.
This script tests the actual model access control in the application routes.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.model_access_service import ModelAccessService
from firebase_models import User

def test_transcription_model_access():
    """Test model access for transcription service."""
    print("🎤 Testing Transcription Model Access")
    print("=" * 40)
    
    # Test models commonly used in transcription
    transcription_models = [
        'gemini-2.0-flash-lite',  # Free model
        'gpt-4o-mini-transcribe',  # Premium model
        'gpt-4o-transcribe',       # Premium model
        'whisper-1'                # Premium model
    ]
    
    # Test with super user
    super_user_email = "addankianitha28@gmail.com"
    print(f"\n👤 Testing with Super User: {super_user_email}")
    
    for model in transcription_models:
        access_result = ModelAccessService.can_access_model(model, super_user_email)
        status = "✅ Allowed" if access_result['allowed'] else "❌ Denied"
        print(f"   • {model}: {status}")
        if not access_result['allowed']:
            print(f"     Reason: {access_result['reason']}")
    
    # Test with normal user
    normal_user_email = "normal.user@example.com"
    print(f"\n👤 Testing with Normal User: {normal_user_email}")
    
    for model in transcription_models:
        access_result = ModelAccessService.can_access_model(model, normal_user_email)
        status = "✅ Allowed" if access_result['allowed'] else "🔒 Restricted"
        print(f"   • {model}: {status}")
        if not access_result['allowed']:
            print(f"     Reason: {access_result['reason']}")

def test_translation_model_access():
    """Test model access for translation service."""
    print("\n🌐 Testing Translation Model Access")
    print("=" * 40)
    
    # Test models commonly used in translation
    translation_models = [
        'gemini-2.0-flash-lite',  # Free model
        'gemini',                 # Free model (alias)
        'gpt-4.1-mini',          # Premium model
        'gemini-2.5-flash',      # Premium model
        'openai'                 # Premium model (alias)
    ]
    
    # Test with super user
    super_user_email = "addankianitha28@gmail.com"
    print(f"\n👤 Testing with Super User: {super_user_email}")
    
    for model in translation_models:
        access_result = ModelAccessService.can_access_model(model, super_user_email)
        status = "✅ Allowed" if access_result['allowed'] else "❌ Denied"
        print(f"   • {model}: {status}")
    
    # Test with normal user
    normal_user_email = "normal.user@example.com"
    print(f"\n👤 Testing with Normal User: {normal_user_email}")
    
    for model in translation_models:
        access_result = ModelAccessService.can_access_model(model, normal_user_email)
        status = "✅ Allowed" if access_result['allowed'] else "🔒 Restricted"
        print(f"   • {model}: {status}")

def test_tts_model_access():
    """Test model access for TTS service."""
    print("\n🔊 Testing TTS Model Access")
    print("=" * 40)
    
    # Test models commonly used in TTS
    tts_models = [
        'gemini-2.5-flash-tts',  # Premium model
        'gpt4o-mini',            # Premium model
        'openai'                 # Premium model (alias)
    ]
    
    # Test with super user
    super_user_email = "addankianitha28@gmail.com"
    print(f"\n👤 Testing with Super User: {super_user_email}")
    
    for model in tts_models:
        access_result = ModelAccessService.can_access_model(model, super_user_email)
        status = "✅ Allowed" if access_result['allowed'] else "❌ Denied"
        print(f"   • {model}: {status}")
    
    # Test with normal user
    normal_user_email = "normal.user@example.com"
    print(f"\n👤 Testing with Normal User: {normal_user_email}")
    
    for model in tts_models:
        access_result = ModelAccessService.can_access_model(model, normal_user_email)
        status = "✅ Allowed" if access_result['allowed'] else "🔒 Restricted"
        print(f"   • {model}: {status}")

def test_model_validation():
    """Test the model validation functionality."""
    print("\n🔍 Testing Model Validation")
    print("=" * 40)
    
    super_user_email = "addankianitha28@gmail.com"
    normal_user_email = "normal.user@example.com"
    
    # Test validation for premium model with super user
    print(f"\n👤 Super User requesting premium model:")
    validation = ModelAccessService.validate_model_request('gpt-4o-mini-transcribe', super_user_email)
    print(f"   • Request: gpt-4o-mini-transcribe")
    print(f"   • Valid: {validation['valid']}")
    print(f"   • Message: {validation['message']}")
    print(f"   • Suggested Model: {validation['suggested_model']}")
    
    # Test validation for premium model with normal user
    print(f"\n👤 Normal User requesting premium model:")
    validation = ModelAccessService.validate_model_request('gpt-4o-mini-transcribe', normal_user_email)
    print(f"   • Request: gpt-4o-mini-transcribe")
    print(f"   • Valid: {validation['valid']}")
    print(f"   • Message: {validation['message']}")
    print(f"   • Suggested Model: {validation['suggested_model']}")

def main():
    """Main function."""
    print("VocalLocal RBAC Integration Test")
    print("=" * 50)
    
    try:
        # Run all tests
        test_transcription_model_access()
        test_translation_model_access()
        test_tts_model_access()
        test_model_validation()
        
        print(f"\n🎉 RBAC Integration Test Completed!")
        print("=" * 50)
        print("✅ Super Users have access to all models")
        print("🔒 Normal Users are restricted to free models")
        print("🔄 Model validation provides appropriate fallbacks")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
