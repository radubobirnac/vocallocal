"""
Test script for transcribing real audio files.

This script tests the transcription service with real audio files
to ensure it works correctly in production.
"""

import os
import sys
import logging
import tempfile
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("real_audio_test")

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_sample_audio():
    """Create a sample audio file for testing"""
    logger.info("Creating sample audio file...")

    try:
        # Create a temporary file
        temp_file_path = os.path.join(tempfile.gettempdir(), "test_audio.wav")

        # Try to use FFmpeg to create a test audio file with speech
        try:
            import subprocess

            # Create a text file with the speech content
            text_file_path = os.path.join(tempfile.gettempdir(), "test_text.txt")
            with open(text_file_path, "w") as f:
                f.write("This is a test of the transcription service. Testing both Gemini and OpenAI models.")

            # Use FFmpeg to generate a silent audio file
            subprocess.run(
                ["ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "3", "-q:a", "9", "-acodec", "libmp3lame", temp_file_path],
                capture_output=True,
                check=True
            )

            # Clean up the text file
            if os.path.exists(text_file_path):
                os.remove(text_file_path)

            logger.info(f"Created sample audio file with FFmpeg: {temp_file_path}")
            return temp_file_path
        except Exception as ffmpeg_error:
            logger.warning(f"Error creating audio with FFmpeg: {str(ffmpeg_error)}")

            # If FFmpeg fails, create a simple WAV file
            import wave
            import struct
            import math

            # Create a simple sine wave
            duration = 3  # seconds
            sample_rate = 44100  # Hz
            frequency = 440  # Hz (A4)

            # Create WAV file
            with wave.open(temp_file_path, "w") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 2 bytes (16 bits)
                wav_file.setframerate(sample_rate)

                # Generate sine wave
                for i in range(int(duration * sample_rate)):
                    value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
                    data = struct.pack("<h", value)
                    wav_file.writeframes(data)

            logger.info(f"Created simple WAV file: {temp_file_path}")
            return temp_file_path
    except Exception as e:
        logger.error(f"Error creating sample audio file: {str(e)}")
        return None

def test_transcription_with_real_audio():
    """Test the transcription service with a real audio file"""
    logger.info("=== Real Audio Transcription Test ===")

    try:
        # Import the transcription service
        from services.transcription import transcription_service

        # Create a sample audio file
        audio_file_path = create_sample_audio()
        if not audio_file_path:
            logger.error("Failed to create sample audio file. Exiting.")
            return False

        # Read the audio file
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()

        # Test transcription with Gemini
        logger.info("\n=== Testing Gemini transcription with real audio ===")
        try:
            result = transcription_service.transcribe(audio_data, "en", "gemini")
            logger.info(f"Gemini transcription result: {result}")
            logger.info("Gemini transcription test successful!")
        except Exception as e:
            logger.error(f"Gemini transcription test failed: {str(e)}")

        # Test transcription with OpenAI if FFmpeg is available
        ffmpeg_available = transcription_service._check_ffmpeg_available()
        if ffmpeg_available:
            logger.info("\n=== Testing OpenAI transcription with real audio ===")
            try:
                result = transcription_service.transcribe(audio_data, "en", "gpt-4o-mini-transcribe")
                logger.info(f"OpenAI transcription result: {result}")
                logger.info("OpenAI transcription test successful!")
            except Exception as e:
                logger.error(f"OpenAI transcription test failed: {str(e)}")
        else:
            logger.info("\nSkipping OpenAI transcription test because FFmpeg is not available")

        # Clean up
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)
            logger.info(f"Cleaned up audio file: {audio_file_path}")

        return True
    except Exception as e:
        logger.error(f"Test setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_transcription_with_real_audio()
    if success:
        logger.info("\n✅ Real audio transcription test completed!")
        sys.exit(0)
    else:
        logger.error("\n❌ Real audio transcription test failed!")
        sys.exit(1)
