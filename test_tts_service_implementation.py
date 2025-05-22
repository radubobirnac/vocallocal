"""
Test script for the updated TTS service implementation
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_tts_service")

# Load environment variables
load_dotenv()

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Import the TTS service
try:
    from src.services.tts_service import TTSService
    logger.info("TTSService imported successfully from src.services.tts_service")
except ImportError:
    try:
        from services.tts_service import TTSService
        logger.info("TTSService imported successfully from services.tts_service")
    except ImportError:
        logger.error("Error importing TTSService. Make sure the path is correct.")
        sys.exit(1)

def test_tts_service():
    """Test the TTS service implementation"""
    logger.info("=== Testing TTS Service Implementation ===")
    
    # Create a TTSService instance
    tts_service = TTSService()
    
    # Test text
    test_text = "Hello, this is a test of the Gemini 2.5 Flash Preview TTS service."
    
    # Test with Gemini 2.5 Flash TTS
    logger.info("Testing with Gemini 2.5 Flash TTS...")
    try:
        audio_data = tts_service.synthesize(
            text=test_text,
            language="en",
            provider="gemini-2.5-flash-tts"
        )
        
        # Save the audio to a file for testing
        output_file = "test_tts_service_gemini_2_5_flash_tts.mp3"
        with open(output_file, 'wb') as f:
            f.write(audio_data)
        
        logger.info(f"Success! Audio saved to {output_file}")
        logger.info(f"Audio size: {len(audio_data)} bytes")
        
        return True
    except Exception as e:
        logger.error(f"Error with Gemini 2.5 Flash TTS: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("Starting TTS service implementation test")
    test_tts_service()
    logger.info("Test completed")
