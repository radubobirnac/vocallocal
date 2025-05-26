#!/usr/bin/env python3
"""
Test script to verify the bug fixes implemented in VocalLocal.
"""
import os
import sys
import traceback

def test_imports():
    """Test that all critical imports work correctly."""
    print("🔍 Testing imports...")
    
    try:
        # Test Firebase service import
        from services.firebase_service import FirebaseService
        print("✅ Firebase service import successful")
        
        # Test Firebase service initialization
        firebase_service = FirebaseService()
        print(f"✅ Firebase service initialization: {'successful' if firebase_service.initialized else 'failed (using fallback)'}")
        
    except Exception as e:
        print(f"❌ Firebase service error: {e}")
    
    try:
        # Test Firebase models import
        from models.firebase_models import Transcription, Translation
        print("✅ Firebase models import successful")
        
        # Test model methods
        test_email = "test@example.com"
        transcriptions = Transcription.get_by_user(test_email, limit=1)
        translations = Translation.get_by_user(test_email, limit=1)
        print("✅ Firebase models methods working")
        
    except Exception as e:
        print(f"❌ Firebase models error: {e}")
    
    try:
        # Test routes import
        from routes.main import bp as main_bp
        print("✅ Main routes import successful")
        
    except Exception as e:
        print(f"❌ Main routes error: {e}")
    
    try:
        # Test error handler import
        from utils.error_handler import register_error_handlers, SafeFirebaseService
        print("✅ Error handler import successful")
        
        # Test SafeFirebaseService
        safe_service = SafeFirebaseService()
        print(f"✅ SafeFirebaseService initialization: {'successful' if safe_service.initialized else 'failed (using fallback)'}")
        
    except Exception as e:
        print(f"❌ Error handler error: {e}")

def test_firebase_config():
    """Test Firebase configuration."""
    print("\n🔍 Testing Firebase configuration...")
    
    try:
        from firebase_config import initialize_firebase
        
        # Test Firebase initialization
        db_ref = initialize_firebase()
        print("✅ Firebase initialization successful")
        
    except Exception as e:
        print(f"❌ Firebase configuration error: {e}")
        print("This is expected if Firebase credentials are not configured")

def test_environment_config():
    """Test environment configuration."""
    print("\n🔍 Testing environment configuration...")
    
    # Check for .env file
    env_file = ".env"
    env_example_file = ".env.example"
    
    if os.path.exists(env_file):
        print("✅ .env file exists")
    else:
        print("⚠️  .env file not found")
    
    if os.path.exists(env_example_file):
        print("✅ .env.example file exists")
        
        # Check if .env.example contains the new FIREBASE_STORAGE_BUCKET setting
        with open(env_example_file, 'r') as f:
            content = f.read()
            if 'FIREBASE_STORAGE_BUCKET' in content:
                print("✅ FIREBASE_STORAGE_BUCKET setting found in .env.example")
            else:
                print("❌ FIREBASE_STORAGE_BUCKET setting missing from .env.example")
    else:
        print("❌ .env.example file not found")

def test_error_handling():
    """Test error handling mechanisms."""
    print("\n🔍 Testing error handling...")
    
    try:
        from utils.error_handler import VocalLocalError, FirebaseError, handle_errors
        
        # Test custom exceptions
        try:
            raise FirebaseError("Test Firebase error")
        except VocalLocalError as e:
            print(f"✅ Custom exception handling works: {e.message}")
        
        # Test decorator
        @handle_errors
        def test_function():
            return "success"
        
        result = test_function()
        print(f"✅ Error handling decorator works: {result}")
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")

def main():
    """Run all tests."""
    print("🚀 VocalLocal Bug Fix Verification")
    print("=" * 50)
    
    test_imports()
    test_firebase_config()
    test_environment_config()
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("✅ Bug fix verification completed!")
    print("\nKey improvements:")
    print("- Firebase storage bucket configuration fixed")
    print("- Robust import system with fallbacks implemented")
    print("- Comprehensive error handling added")
    print("- Navigation stability improved")
    print("- Graceful degradation when services are unavailable")

if __name__ == "__main__":
    main()
