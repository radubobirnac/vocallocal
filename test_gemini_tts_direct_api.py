"""
Test script for the updated Gemini 2.5 Flash TTS implementation using direct API calls
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
logger = logging.getLogger("test_gemini_tts_direct_api")

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
    """Test the TTS service implementation with direct API calls"""
    logger.info("=== Testing TTS Service Implementation with Direct API Calls ===")
    
    # Create a TTSService instance
    tts_service = TTSService()
    
    # Test text
    test_text = "Hello, this is a test of the Gemini 2.5 Flash Preview TTS service using direct API calls."
    
    # Test with Gemini 2.5 Flash TTS
    logger.info("Testing with Gemini 2.5 Flash TTS...")
    try:
        audio_data = tts_service.synthesize(
            text=test_text,
            language="en",
            provider="gemini-2.5-flash-tts"
        )
        
        # Save the audio to a file for testing
        output_file = "test_gemini_tts_direct_api.mp3"
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

def test_with_different_languages():
    """Test the TTS service with different languages"""
    logger.info("=== Testing TTS Service with Different Languages ===")
    
    # Create a TTSService instance
    tts_service = TTSService()
    
    # Test text in different languages
    test_texts = {
        "en": "Hello, this is a test of the Gemini 2.5 Flash Preview TTS service.",
        "es": "Hola, esta es una prueba del servicio Gemini 2.5 Flash Preview TTS.",
        "fr": "Bonjour, ceci est un test du service Gemini 2.5 Flash Preview TTS.",
        "de": "Hallo, dies ist ein Test des Gemini 2.5 Flash Preview TTS-Dienstes.",
        "it": "Ciao, questo è un test del servizio Gemini 2.5 Flash Preview TTS.",
        "pt": "Olá, este é um teste do serviço Gemini 2.5 Flash Preview TTS.",
        "ru": "Привет, это тест сервиса Gemini 2.5 Flash Preview TTS.",
        "ja": "こんにちは、これはGemini 2.5 Flash Preview TTSサービスのテストです。",
        "zh": "你好，这是Gemini 2.5 Flash Preview TTS服务的测试。"
    }
    
    results = {}
    
    for lang_code, text in test_texts.items():
        logger.info(f"Testing with {lang_code} text...")
        try:
            audio_data = tts_service.synthesize(
                text=text,
                language=lang_code,
                provider="gemini-2.5-flash-tts"
            )
            
            # Save the audio to a file for testing
            output_file = f"test_gemini_tts_direct_api_{lang_code}.mp3"
            with open(output_file, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"Success! Audio saved to {output_file}")
            logger.info(f"Audio size: {len(audio_data)} bytes")
            
            results[lang_code] = True
        except Exception as e:
            logger.error(f"Error with {lang_code} text: {str(e)}")
            results[lang_code] = False
    
    # Log summary of results
    logger.info("=== Language Test Results ===")
    for lang_code, success in results.items():
        logger.info(f"{lang_code}: {'Success' if success else 'Failed'}")
    
    return results

def test_fallback_mechanism():
    """Test the fallback mechanism"""
    logger.info("=== Testing Fallback Mechanism ===")
    
    # Create a TTSService instance
    tts_service = TTSService()
    
    # Test text
    test_text = "This is a test of the fallback mechanism."
    
    # Temporarily modify the _synthesize_with_gemini_2_5_flash_tts method to always fail
    original_method = tts_service._synthesize_with_gemini_2_5_flash_tts
    
    def mock_method(*args, **kwargs):
        logger.info("Mocked method called - simulating failure")
        raise Exception("Simulated failure")
    
    try:
        # Replace the method with our mock
        tts_service._synthesize_with_gemini_2_5_flash_tts = mock_method
        
        # Try to synthesize with Gemini 2.5 Flash TTS (should fall back to another provider)
        logger.info("Testing fallback with simulated failure...")
        audio_data = tts_service.synthesize(
            text=test_text,
            language="en",
            provider="gemini-2.5-flash-tts"
        )
        
        # Save the audio to a file for testing
        output_file = "test_gemini_tts_direct_api_fallback.mp3"
        with open(output_file, 'wb') as f:
            f.write(audio_data)
        
        logger.info(f"Success! Fallback worked. Audio saved to {output_file}")
        logger.info(f"Audio size: {len(audio_data)} bytes")
        
        return True
    except Exception as e:
        logger.error(f"Error testing fallback: {str(e)}")
        return False
    finally:
        # Restore the original method
        tts_service._synthesize_with_gemini_2_5_flash_tts = original_method

if __name__ == "__main__":
    logger.info("Starting TTS service implementation test with direct API calls")
    
    # Test the basic functionality
    test_tts_service()
    
    # Test with different languages
    test_with_different_languages()
    
    # Test the fallback mechanism
    test_fallback_mechanism()
    
    logger.info("Test completed")
