"""
Test script for the TTS service fallback mechanism.

This script tests:
1. Fallback from GPT-4o Mini to OpenAI when GPT-4o Mini fails
2. Proper error handling and logging
"""

import os
import sys
import logging
import tempfile
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tts_fallback_test")

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the TTSService
from services.tts import TTSService

def test_tts_fallback():
    """Test the TTS service fallback mechanism"""
    logger.info("=== TTS Fallback Test ===")
    
    # Create a TTSService instance
    tts_service = TTSService()
    
    # Test text
    test_text = "This is a test of the text-to-speech service fallback mechanism."
    
    # Create a mock for the GPT-4o Mini TTS method that raises an exception
    original_gpt4o_mini = tts_service.tts_with_gpt4o_mini
    
    def mock_gpt4o_mini(*args, **kwargs):
        """Mock GPT-4o Mini TTS method that raises an exception"""
        logger.info("Mock GPT-4o Mini TTS method called - simulating failure")
        raise RuntimeError("Simulated GPT-4o Mini TTS failure")
    
    # Test fallback from GPT-4o Mini to OpenAI
    logger.info("\n=== Testing fallback from GPT-4o Mini to OpenAI ===")
    
    # Patch the GPT-4o Mini TTS method
    tts_service.tts_with_gpt4o_mini = mock_gpt4o_mini
    
    try:
        # Call the synthesize method with GPT-4o Mini model
        output_file = tts_service.synthesize(test_text, "en", "gpt4o-mini")
        logger.info(f"Fallback successful! Output saved to {output_file}")
        
        # Clean up the output file
        if os.path.exists(output_file):
            os.remove(output_file)
            logger.info(f"Removed output file: {output_file}")
        
        logger.info("Fallback test passed!")
        return True
    except Exception as e:
        logger.error(f"Fallback test failed: {str(e)}")
        return False
    finally:
        # Restore the original GPT-4o Mini TTS method
        tts_service.tts_with_gpt4o_mini = original_gpt4o_mini

if __name__ == "__main__":
    success = test_tts_fallback()
    if success:
        logger.info("\n✅ TTS fallback test passed!")
        sys.exit(0)
    else:
        logger.error("\n❌ TTS fallback test failed!")
        sys.exit(1)
