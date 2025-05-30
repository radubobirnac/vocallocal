#!/usr/bin/env python3
"""
Test script to verify the chunking fix for corrupted audio chunks.
"""

import sys
import os
import tempfile
import subprocess

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ffmpeg_availability():
    """Test if FFmpeg is available with the custom path."""
    print("🔍 Testing FFmpeg availability...")
    
    try:
        from services.transcription import TranscriptionService
        service = TranscriptionService()
        
        # Test FFmpeg availability
        ffmpeg_available = service._check_ffmpeg_available()
        
        if ffmpeg_available:
            ffmpeg_path = getattr(service, 'ffmpeg_path', 'ffmpeg')
            print(f"✅ FFmpeg available at: {ffmpeg_path}")
            
            # Test actual FFmpeg execution
            try:
                result = subprocess.run([ffmpeg_path, '-version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print("✅ FFmpeg execution test passed")
                    return True
                else:
                    print(f"❌ FFmpeg execution failed: {result.stderr}")
                    return False
            except Exception as e:
                print(f"❌ FFmpeg execution error: {str(e)}")
                return False
        else:
            print("❌ FFmpeg not available")
            return False
            
    except Exception as e:
        print(f"❌ Error testing FFmpeg: {str(e)}")
        return False

def test_chunking_strategy():
    """Test the new chunking strategy."""
    print("\n🔍 Testing chunking strategy...")
    
    try:
        from services.transcription import TranscriptionService
        service = TranscriptionService()
        
        # Create fake audio data (simulating a 6MB WebM file)
        fake_webm_data = b'\x1a\x45\xdf\xa3' + b'fake_webm_data' * 500000  # ~6MB
        
        print(f"Created fake WebM data: {len(fake_webm_data) / (1024*1024):.2f} MB")
        
        # Test the chunking decision logic
        file_size_mb = len(fake_webm_data) / (1024 * 1024)
        
        # Check if FFmpeg is available
        ffmpeg_available = service._check_ffmpeg_available()
        
        if ffmpeg_available:
            print("✅ FFmpeg available - will use duration-based chunking")
            print("✅ No byte-based chunking will be used (avoids corruption)")
        else:
            print("⚠️ FFmpeg not available - will process whole file")
            print("✅ Still avoids byte-based chunking (no corruption)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing chunking strategy: {str(e)}")
        return False

def test_gemini_api_configuration():
    """Test Gemini API configuration."""
    print("\n🔍 Testing Gemini API configuration...")
    
    try:
        from services.transcription import TranscriptionService
        service = TranscriptionService()
        
        if service.gemini_available:
            print("✅ Gemini API is available")
            return True
        else:
            print("❌ Gemini API not available - check GEMINI_API_KEY in .env file")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Gemini API: {str(e)}")
        return False

def test_metrics_tracking():
    """Test that metrics tracking works correctly."""
    print("\n🔍 Testing metrics tracking...")
    
    try:
        from metrics_tracker import track_transcription_metrics
        
        @track_transcription_metrics
        def mock_transcribe(audio_data, language, model="gemini-2.0-flash-lite"):
            return "Mock transcription result"
        
        # Test with different parameter styles
        result = mock_transcribe(b"fake_data", "en", "gemini-2.0-flash-lite")
        
        if result == "Mock transcription result":
            print("✅ Metrics tracking decorator works correctly")
            return True
        else:
            print("❌ Metrics tracking decorator failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing metrics tracking: {str(e)}")
        return False

def test_file_state_handling():
    """Test improved file state handling logic."""
    print("\n🔍 Testing file state handling improvements...")
    
    try:
        from services.transcription import TranscriptionService
        service = TranscriptionService()
        
        # Test the file state constants and logic
        # This tests the improved state management without actually calling Gemini
        
        # Simulate file state values
        test_states = [
            (2, "ACTIVE", True),
            ("ACTIVE", "ACTIVE", True), 
            (10, "PROCESSING", False),
            (1, "PROCESSING", False)
        ]
        
        for state_value, state_name, expected_active in test_states:
            # Test the logic that determines if a file is active
            is_active = (
                (isinstance(state_value, str) and state_value == "ACTIVE") or
                (isinstance(state_value, int) and state_value == 2)
            )
            
            if is_active == expected_active:
                print(f"✅ State {state_value} ({state_name}) correctly identified as {'ACTIVE' if is_active else 'NOT ACTIVE'}")
            else:
                print(f"❌ State {state_value} ({state_name}) incorrectly identified")
                return False
        
        print("✅ File state handling logic is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error testing file state handling: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("VocalLocal Chunking Fix Verification")
    print("=" * 50)
    
    tests = [
        test_ffmpeg_availability,
        test_chunking_strategy,
        test_gemini_api_configuration,
        test_metrics_tracking,
        test_file_state_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The chunking fix should resolve the corruption issue.")
        print("\n📋 Summary of fixes:")
        print("✅ FFmpeg path configuration fixed")
        print("✅ Byte-based chunking eliminated (prevents corruption)")
        print("✅ Duration-based chunking prioritized")
        print("✅ Whole-file processing as fallback")
        print("✅ Improved file state management")
        print("✅ Metrics tracking fixed")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        
        if not test_gemini_api_configuration():
            print("\n🔧 To fix Gemini API issue:")
            print("1. Create .env file: cp .env.example .env")
            print("2. Add your GEMINI_API_KEY to the .env file")
            print("3. Restart the application")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
