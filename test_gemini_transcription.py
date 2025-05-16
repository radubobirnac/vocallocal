"""
Test script for the Gemini transcription functionality.

This script tests:
1. Creating a simple audio file
2. Transcribing it with Gemini
3. Verifying that the transcription works correctly
"""

import os
import sys
import wave
import struct
import math
import logging
import tempfile
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("gemini_transcription_test")

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create a simple test audio file
def create_test_audio():
    """Create a simple WAV file for testing"""
    logger.info("Creating test audio file...")
    
    # Create a simple sine wave
    duration = 3  # seconds
    sample_rate = 44100  # Hz
    frequency = 440  # Hz (A4)
    
    # Create WAV file
    wav_file_path = "test_audio.wav"
    with wave.open(wav_file_path, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes (16 bits)
        wav_file.setframerate(sample_rate)
        
        # Generate sine wave
        for i in range(int(duration * sample_rate)):
            value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            data = struct.pack("<h", value)
            wav_file.writeframes(data)
    
    logger.info(f"Test audio file created: {wav_file_path}")
    
    # Convert WAV to WebM using FFmpeg if available
    try:
        import subprocess
        webm_file_path = "test_audio.webm"
        logger.info(f"Converting WAV to WebM: {wav_file_path} -> {webm_file_path}")
        
        result = subprocess.run(
            ['ffmpeg', '-i', wav_file_path, '-c:a', 'libopus', webm_file_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"Conversion successful: {os.path.getsize(webm_file_path)} bytes")
        
        # Read the WebM file as bytes
        with open(webm_file_path, "rb") as f:
            audio_data = f.read()
        
        return audio_data, webm_file_path
    except Exception as e:
        logger.error(f"Error converting WAV to WebM: {str(e)}")
        
        # If conversion fails, just read the WAV file
        with open(wav_file_path, "rb") as f:
            audio_data = f.read()
        
        return audio_data, wav_file_path

def test_gemini_transcription():
    """Test the Gemini transcription functionality"""
    logger.info("=== Gemini Transcription Test ===")
    
    try:
        # Import the transcription service
        from services.transcription import transcription_service
        
        # Create test audio data
        audio_data, audio_file_path = create_test_audio()
        
        # Test transcription with Gemini
        logger.info("\n=== Testing Gemini transcription ===")
        try:
            result = transcription_service.transcribe_with_gemini(audio_data, "en", "gemini")
            logger.info(f"Transcription result: {result}")
            logger.info("Gemini transcription test successful!")
            success = True
        except Exception as e:
            logger.error(f"Gemini transcription test failed: {str(e)}")
            success = False
        
        # Clean up
        if os.path.exists("test_audio.wav"):
            os.remove("test_audio.wav")
            logger.info("Cleaned up test_audio.wav")
        
        if os.path.exists("test_audio.webm"):
            os.remove("test_audio.webm")
            logger.info("Cleaned up test_audio.webm")
        
        return success
    except Exception as e:
        logger.error(f"Test setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gemini_transcription()
    if success:
        logger.info("\n✅ Gemini transcription test passed!")
        sys.exit(0)
    else:
        logger.error("\n❌ Gemini transcription test failed!")
        sys.exit(1)
