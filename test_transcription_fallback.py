"""
Test script for the improved transcription service with fallback mechanism.

This script tests:
1. FFmpeg detection
2. Automatic fallback from OpenAI to Gemini when FFmpeg is not available
3. Proper error handling and logging
"""

import os
import wave
import struct
import math
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("transcription_test")

# Load environment variables
load_dotenv()

# Create a simple test audio file
def create_test_audio():
    """Create a simple WAV file for testing"""
    logger.info("Creating test audio file...")
    
    # Create a simple sine wave
    duration = 3  # seconds
    sample_rate = 44100  # Hz
    frequency = 440  # Hz (A4)
    
    # Create WAV file
    with wave.open("test_audio.wav", "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes (16 bits)
        wav_file.setframerate(sample_rate)
        
        # Generate sine wave
        for i in range(int(duration * sample_rate)):
            value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            data = struct.pack("<h", value)
            wav_file.writeframes(data)
    
    logger.info("Test audio file created: test_audio.wav")
    
    # Read the file as bytes
    with open("test_audio.wav", "rb") as f:
        audio_data = f.read()
    
    return audio_data

def test_transcription_service():
    """Test the transcription service with fallback mechanism"""
    from services.transcription import transcription_service
    
    # Create test audio data
    audio_data = create_test_audio()
    
    # Test FFmpeg detection
    ffmpeg_available = transcription_service._check_ffmpeg_available()
    logger.info(f"FFmpeg available: {ffmpeg_available}")
    
    # Test transcription with OpenAI (should fall back to Gemini if FFmpeg is not available)
    logger.info("\n=== Testing OpenAI transcription (with potential fallback) ===")
    try:
        result = transcription_service.transcribe(audio_data, "en", "gpt-4o-mini-transcribe")
        logger.info(f"Transcription result: {result}")
        logger.info("OpenAI transcription test successful!")
    except Exception as e:
        logger.error(f"OpenAI transcription test failed: {str(e)}")
    
    # Test transcription with Gemini
    logger.info("\n=== Testing Gemini transcription ===")
    try:
        result = transcription_service.transcribe(audio_data, "en", "gemini")
        logger.info(f"Transcription result: {result}")
        logger.info("Gemini transcription test successful!")
    except Exception as e:
        logger.error(f"Gemini transcription test failed: {str(e)}")
    
    # Clean up
    if os.path.exists("test_audio.wav"):
        os.remove("test_audio.wav")
        logger.info("Cleaned up test audio file")

if __name__ == "__main__":
    test_transcription_service()
