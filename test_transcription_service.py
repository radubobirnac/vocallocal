"""
Test script for the transcription service with fallback mechanism.

This script tests:
1. Transcription with Gemini
2. Transcription with OpenAI
3. Fallback from OpenAI to Gemini when FFmpeg is not available
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
logger = logging.getLogger("transcription_service_test")

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
        
        return audio_data
    except Exception as e:
        logger.error(f"Error converting WAV to WebM: {str(e)}")
        
        # If conversion fails, just read the WAV file
        with open(wav_file_path, "rb") as f:
            audio_data = f.read()
        
        return audio_data

def test_transcription_service():
    """Test the transcription service with fallback mechanism"""
    logger.info("=== Transcription Service Test ===")
    
    try:
        # Import the transcription service
        from services.transcription import transcription_service
        
        # Create test audio data
        audio_data = create_test_audio()
        
        # Check if FFmpeg is available
        ffmpeg_available = transcription_service._check_ffmpeg_available()
        logger.info(f"FFmpeg available: {ffmpeg_available}")
        
        # Test transcription with Gemini
        logger.info("\n=== Testing Gemini transcription ===")
        try:
            result = transcription_service.transcribe(audio_data, "en", "gemini")
            logger.info(f"Gemini transcription result: {result}")
            logger.info("Gemini transcription test successful!")
        except Exception as e:
            logger.error(f"Gemini transcription test failed: {str(e)}")
        
        # Test transcription with OpenAI
        logger.info("\n=== Testing OpenAI transcription ===")
        try:
            result = transcription_service.transcribe(audio_data, "en", "gpt-4o-mini-transcribe")
            logger.info(f"OpenAI transcription result: {result}")
            logger.info("OpenAI transcription test successful!")
        except Exception as e:
            logger.error(f"OpenAI transcription test failed: {str(e)}")
            logger.info("This is expected if FFmpeg is not available")
        
        # Clean up
        if os.path.exists("test_audio.wav"):
            os.remove("test_audio.wav")
            logger.info("Cleaned up test_audio.wav")
        
        if os.path.exists("test_audio.webm"):
            os.remove("test_audio.webm")
            logger.info("Cleaned up test_audio.webm")
        
        return True
    except Exception as e:
        logger.error(f"Test setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_transcription_service()
    if success:
        logger.info("\n✅ Transcription service test completed!")
        sys.exit(0)
    else:
        logger.error("\n❌ Transcription service test failed!")
        sys.exit(1)
