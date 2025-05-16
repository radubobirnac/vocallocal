"""
Test script for Gemini audio transcription.

This script tests the Gemini API's ability to transcribe audio files
using the correct API format.
"""

import os
import sys
import base64
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("gemini_audio_test")

# Load environment variables
load_dotenv()

# Get Gemini API key
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    logger.error("Gemini API key not found. Please set GEMINI_API_KEY in your .env file.")
    sys.exit(1)

# Configure Gemini
genai.configure(api_key=gemini_api_key)
logger.info("Gemini API configured successfully")

def test_gemini_audio_transcription():
    """Test Gemini audio transcription with a simple audio file"""
    logger.info("=== Gemini Audio Transcription Test ===")
    
    # Check if test audio file exists
    audio_file_path = "test_audio.wav"
    if not os.path.exists(audio_file_path):
        logger.info("Creating a simple test audio file...")
        create_test_audio_file(audio_file_path)
    
    # Read the audio file
    with open(audio_file_path, 'rb') as f:
        audio_bytes = f.read()
    
    logger.info(f"Read {len(audio_bytes)} bytes from audio file")
    
    # Convert audio bytes to base64
    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    # Initialize the Gemini model
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Method 1: Using inline_data
    try:
        logger.info("Testing Method 1: Using inline_data")
        
        # Create content parts
        parts = [
            {"text": "Please transcribe the following audio. The language is English."},
            {
                "inline_data": {
                    "mime_type": "audio/wav",
                    "data": audio_b64
                }
            }
        ]
        
        # Generate content with the audio
        response = model.generate_content(parts)
        
        logger.info(f"Method 1 Response: {response.text}")
        logger.info("Method 1 successful!")
    except Exception as e:
        logger.error(f"Method 1 failed: {str(e)}")
    
    # Method 2: Using the Files API
    try:
        logger.info("Testing Method 2: Using the Files API")
        
        # Upload the file
        file_obj = genai.upload_file(path=audio_file_path)
        
        # Create content with the file
        response = model.generate_content([
            "Please transcribe the following audio. The language is English.",
            file_obj
        ])
        
        logger.info(f"Method 2 Response: {response.text}")
        logger.info("Method 2 successful!")
    except Exception as e:
        logger.error(f"Method 2 failed: {str(e)}")
    
    # Method 3: Using direct file path
    try:
        logger.info("Testing Method 3: Using direct file path")
        
        # Generate content with the audio file path
        response = model.generate_content([
            "Please transcribe the following audio. The language is English.",
            {"file_path": audio_file_path}
        ])
        
        logger.info(f"Method 3 Response: {response.text}")
        logger.info("Method 3 successful!")
    except Exception as e:
        logger.error(f"Method 3 failed: {str(e)}")
    
    # Clean up
    if os.path.exists(audio_file_path):
        os.remove(audio_file_path)
        logger.info(f"Removed test audio file: {audio_file_path}")

def create_test_audio_file(file_path):
    """Create a simple WAV file for testing"""
    try:
        import wave
        import struct
        import math
        
        # Create a simple sine wave
        duration = 3  # seconds
        sample_rate = 44100  # Hz
        frequency = 440  # Hz (A4)
        
        # Create WAV file
        with wave.open(file_path, "w") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes (16 bits)
            wav_file.setframerate(sample_rate)
            
            # Generate sine wave
            for i in range(int(duration * sample_rate)):
                value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
                data = struct.pack("<h", value)
                wav_file.writeframes(data)
        
        logger.info(f"Created test audio file: {file_path}")
    except Exception as e:
        logger.error(f"Error creating test audio file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_gemini_audio_transcription()
