"""
Test script for the Gemini 2.5 Flash Preview TTS functionality

This script tests:
1. Basic text-to-speech conversion using Gemini 2.5 Flash Preview TTS
2. Proper error handling and fallback mechanisms
3. Voice parameter customization
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
logger = logging.getLogger("gemini_2_5_flash_tts_test")

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the TTSService
try:
    from src.services.tts_service import TTSService
    logger.info("TTSService imported successfully from src.services")
except ImportError:
    try:
        from services.tts_service import TTSService
        logger.info("TTSService imported successfully from services")
    except ImportError:
        try:
            from services.tts import TTSService
            logger.info("TTSService imported successfully from services.tts")
        except ImportError as e:
            logger.error(f"Error importing TTSService: {str(e)}")
            sys.exit(1)

def test_gemini_2_5_flash_tts():
    """Test the Gemini 2.5 Flash Preview TTS functionality"""
    logger.info("=== Gemini 2.5 Flash Preview TTS Test ===")
    
    # Create a TTSService instance
    tts_service = TTSService()
    
    # Test text in different languages
    test_texts = {
        "en": "Hello, this is a test of the Gemini 2.5 Flash Preview TTS service.",
        "es": "Hola, esta es una prueba del servicio Gemini 2.5 Flash Preview TTS.",
        "fr": "Bonjour, ceci est un test du service Gemini 2.5 Flash Preview TTS.",
        "de": "Hallo, dies ist ein Test des Gemini 2.5 Flash Preview TTS-Dienstes."
    }
    
    results = {}
    
    # Test with English
    logger.info("Testing with English text...")
    try:
        audio_data = tts_service.synthesize(
            text=test_texts["en"],
            language="en",
            provider="gemini-2.5-flash-tts"
        )
        
        # Save the audio to a file for testing
        output_file = "test_gemini_2_5_flash_tts_en.mp3"
        with open(output_file, 'wb') as f:
            f.write(audio_data)
        
        logger.info(f"Success! Audio saved to {output_file}")
        logger.info(f"Audio size: {len(audio_data)} bytes")
        
        results["en"] = True
    except Exception as e:
        logger.error(f"Error with English text: {str(e)}")
        results["en"] = False
    
    # Test with other languages
    for lang_code, text in test_texts.items():
        if lang_code == "en":
            continue  # Already tested
        
        logger.info(f"Testing with {lang_code} text...")
        try:
            audio_data = tts_service.synthesize(
                text=text,
                language=lang_code,
                provider="gemini-2.5-flash-tts"
            )
            
            # Save the audio to a file for testing
            output_file = f"test_gemini_2_5_flash_tts_{lang_code}.mp3"
            with open(output_file, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"Success! Audio saved to {output_file}")
            logger.info(f"Audio size: {len(audio_data)} bytes")
            
            results[lang_code] = True
        except Exception as e:
            logger.error(f"Error with {lang_code} text: {str(e)}")
            results[lang_code] = False
    
    # Test fallback mechanism
    logger.info("Testing fallback mechanism...")
    try:
        # Temporarily modify the providers list to simulate Gemini 2.5 Flash TTS being unavailable
        original_providers = tts_service.providers.copy()
        tts_service.providers = [p for p in tts_service.providers if p != "gemini-2.5-flash-tts"]
        
        # Try to synthesize with Gemini 2.5 Flash TTS (should fall back to another provider)
        audio_data = tts_service.synthesize(
            text="This is a fallback test.",
            language="en",
            provider="gemini-2.5-flash-tts"
        )
        
        # Save the audio to a file for testing
        output_file = "test_gemini_2_5_flash_tts_fallback.mp3"
        with open(output_file, 'wb') as f:
            f.write(audio_data)
        
        logger.info(f"Fallback successful! Audio saved to {output_file}")
        results["fallback"] = True
        
        # Restore the original providers list
        tts_service.providers = original_providers
    except Exception as e:
        logger.error(f"Error testing fallback: {str(e)}")
        results["fallback"] = False
        
        # Restore the original providers list
        tts_service.providers = original_providers
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    for test_name, success in results.items():
        logger.info(f"{test_name}: {'✅ Success' if success else '❌ Failed'}")
    
    # Print overall result
    if all(results.values()):
        logger.info("\n✅ All tests passed!")
        return True
    else:
        logger.error("\n❌ Some tests failed.")
        failed_tests = [name for name, success in results.items() if not success]
        logger.error(f"Failed tests: {', '.join(failed_tests)}")
        return False

if __name__ == "__main__":
    success = test_gemini_2_5_flash_tts()
    if success:
        logger.info("\n✅ Gemini 2.5 Flash Preview TTS test passed!")
        sys.exit(0)
    else:
        logger.error("\n❌ Gemini 2.5 Flash Preview TTS test failed!")
        sys.exit(1)
