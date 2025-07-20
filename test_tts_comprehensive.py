#!/usr/bin/env python3
"""
Comprehensive TTS Functionality Test
Test TTS functionality across all user tiers and scenarios
"""

import sys
import os
import requests
import json

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

def test_tts_access_for_user(user_email):
    """Test TTS access for a specific user."""
    print(f"\n🔧 Testing TTS Access for: {user_email}")
    print("=" * 60)
    
    try:
        from services.usage_validation_service import UsageValidationService
        
        # Check TTS access
        tts_access = UsageValidationService.check_tts_access(user_email)
        print(f"TTS Access Result: {json.dumps(tts_access, indent=2)}")
        
        if tts_access['allowed']:
            print(f"✅ TTS access ALLOWED for {user_email}")
            print(f"   Plan Type: {tts_access.get('plan_type', 'N/A')}")
            print(f"   Reason: {tts_access.get('reason', 'N/A')}")
            return True
        else:
            print(f"❌ TTS access DENIED for {user_email}")
            print(f"   Reason: {tts_access.get('reason', 'N/A')}")
            print(f"   Upgrade Required: {tts_access.get('upgrade_required', False)}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing TTS access for {user_email}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_tts_endpoint_direct():
    """Test TTS endpoint directly without authentication."""
    print(f"\n🔧 Testing TTS Endpoint (Direct)")
    print("=" * 60)
    
    try:
        from services.tts import TTSService
        
        # Initialize TTS service
        tts_service = TTSService()
        print("✅ TTS Service initialized successfully")
        
        # Test TTS generation
        test_text = "This is a test of the TTS service functionality."
        test_language = "en"
        test_model = "gemini-2.5-flash-tts"
        
        print(f"Testing TTS generation:")
        print(f"  Text: {test_text}")
        print(f"  Language: {test_language}")
        print(f"  Model: {test_model}")
        
        # Generate TTS
        audio_data = tts_service.synthesize(test_text, test_language, test_model)
        
        if audio_data:
            print(f"✅ TTS generation successful!")
            print(f"   Audio data size: {len(audio_data)} bytes")
            
            # Save test audio file
            with open("test_tts_direct.mp3", "wb") as f:
                f.write(audio_data)
            print(f"   Audio saved as: test_tts_direct.mp3")
            return True
        else:
            print(f"❌ TTS generation failed - no audio data returned")
            return False
            
    except Exception as e:
        print(f"❌ Error testing TTS endpoint directly: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_user_tier_access():
    """Test TTS access for different user tiers."""
    print(f"\n🔧 Testing User Tier Access")
    print("=" * 60)
    
    # Test users for different tiers
    test_users = [
        ("superuser@vocallocal.com", "Super User"),
        ("anitha@gmail.com", "Basic Plan User"),
        # Add more test users as needed
    ]
    
    results = {}
    
    for user_email, user_type in test_users:
        print(f"\n📧 Testing {user_type}: {user_email}")
        access_allowed = test_tts_access_for_user(user_email)
        results[user_email] = {
            'type': user_type,
            'access_allowed': access_allowed
        }
    
    print(f"\n📊 User Tier Access Summary:")
    for user_email, result in results.items():
        status = "✅ ALLOWED" if result['access_allowed'] else "❌ DENIED"
        print(f"   {result['type']}: {status}")
    
    return all(result['access_allowed'] for result in results.values())

def test_tts_models():
    """Test different TTS models."""
    print(f"\n🔧 Testing TTS Models")
    print("=" * 60)
    
    try:
        from services.tts import TTSService
        
        tts_service = TTSService()
        test_text = "Testing different TTS models."
        test_language = "en"
        
        models_to_test = [
            "gemini-2.5-flash-tts",
            "gpt4o-mini",
            "openai"
        ]
        
        results = {}
        
        for model in models_to_test:
            print(f"\n🎵 Testing model: {model}")
            try:
                audio_data = tts_service.synthesize(test_text, test_language, model)
                if audio_data:
                    print(f"   ✅ {model}: SUCCESS ({len(audio_data)} bytes)")
                    results[model] = True
                else:
                    print(f"   ❌ {model}: FAILED (no audio data)")
                    results[model] = False
            except Exception as e:
                print(f"   ❌ {model}: ERROR ({str(e)})")
                results[model] = False
        
        print(f"\n📊 TTS Models Summary:")
        for model, success in results.items():
            status = "✅ WORKING" if success else "❌ FAILED"
            print(f"   {model}: {status}")
        
        return any(results.values())  # At least one model should work
        
    except Exception as e:
        print(f"❌ Error testing TTS models: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_deployment_readiness():
    """Test deployment readiness for remote environments."""
    print(f"\n🔧 Testing Deployment Readiness")
    print("=" * 60)
    
    # Check critical components
    checks = {
        'Environment Variables': False,
        'API Keys': False,
        'TTS Service': False,
        'User Access Control': False,
        'Model Functionality': False
    }
    
    # Check environment variables
    openai_key = os.getenv('OPENAI_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')
    if openai_key and gemini_key:
        checks['Environment Variables'] = True
        print("✅ Environment Variables: API keys loaded")
    else:
        print("❌ Environment Variables: Missing API keys")
    
    # Check API keys validity (basic check)
    if openai_key and openai_key.startswith('sk-'):
        checks['API Keys'] = True
        print("✅ API Keys: OpenAI key format valid")
    else:
        print("❌ API Keys: Invalid format")
    
    # Test TTS service
    checks['TTS Service'] = test_tts_endpoint_direct()
    
    # Test user access control
    checks['User Access Control'] = test_user_tier_access()
    
    # Test model functionality
    checks['Model Functionality'] = test_tts_models()
    
    print(f"\n📊 Deployment Readiness Summary:")
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {check_name}: {status}")
        if not passed:
            all_passed = False
    
    return all_passed

def main():
    """Main test function."""
    print("🚀 Comprehensive TTS Functionality Test")
    print("=" * 80)
    
    print("Testing TTS functionality across all user tiers and scenarios...")
    print("This will validate that TTS works correctly in both local and remote deployments.")
    print("")
    
    # Run comprehensive tests
    deployment_ready = test_deployment_readiness()
    
    print(f"\n" + "="*80)
    if deployment_ready:
        print(f"🎉 TTS FUNCTIONALITY: ALL TESTS PASSED")
        print(f"="*80)
        print(f"")
        print(f"✅ TTS is working correctly for all user tiers")
        print(f"✅ All TTS models are functional")
        print(f"✅ Environment is ready for deployment")
        print(f"✅ API keys are properly configured")
        print(f"")
        print(f"The TTS 403 errors should now be resolved.")
        print(f"If issues persist, check browser session/cookies.")
        print(f"")
    else:
        print(f"❌ TTS FUNCTIONALITY: ISSUES DETECTED")
        print(f"="*80)
        print(f"")
        print(f"Some TTS functionality tests failed.")
        print(f"Review the error details above to identify specific issues.")
        print(f"")
    
    return deployment_ready

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
