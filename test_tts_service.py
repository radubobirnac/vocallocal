"""
Test script for the TTSService class

This script tests the functionality of the TTSService class, including:
- Basic text-to-speech conversion
- Provider selection
- Fallback behavior
- Error handling
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our services
try:
    from src.services.tts_service import TTSService
    print("TTSService imported successfully")
except ImportError as e:
    print(f"Error importing TTSService: {str(e)}")
    sys.exit(1)

def test_tts_with_provider(service, text, language, provider, voice=None):
    """Test TTS with a specific provider"""
    print(f"\n=== Testing TTS with provider: {provider} ===")
    print(f"Text: '{text}'")
    print(f"Language: {language}")
    print(f"Voice: {voice}")
    
    try:
        start_time = time.time()
        
        # Synthesize speech
        audio_data = service.synthesize(
            text=text,
            language=language,
            provider=provider,
            voice=voice
        )
        
        elapsed = time.time() - start_time
        
        # Save the audio to a file for testing
        output_file = f"test_output_{provider}_{language}.mp3"
        with open(output_file, 'wb') as f:
            f.write(audio_data)
        
        print(f"Success! Audio saved to {output_file}")
        print(f"Audio size: {len(audio_data)} bytes")
        print(f"Time taken: {elapsed:.2f} seconds")
        
        # Print metrics
        metrics = service.get_metrics()
        print(f"Metrics: {metrics}")
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("=== TTSService Test ===")
    
    # Initialize the service
    service = TTSService()
    
    # Test text in different languages
    test_texts = {
        "en": "Hello, this is a test of the text-to-speech service.",
        "es": "Hola, esta es una prueba del servicio de texto a voz.",
        "fr": "Bonjour, ceci est un test du service de synthèse vocale.",
        "de": "Hallo, dies ist ein Test des Text-zu-Sprache-Dienstes."
    }
    
    # Test with different providers
    providers = ["gpt4o-mini", "openai", "auto"]
    
    # Test with different voices (for OpenAI)
    voices = {
        "openai": ["onyx", "alloy", "echo", "fable", "nova", "shimmer"]
    }
    
    # Run tests
    results = {}
    
    # Test auto provider with English
    results["auto_en"] = test_tts_with_provider(
        service, 
        test_texts["en"], 
        "en", 
        "auto"
    )
    
    # Test each provider with English
    for provider in providers:
        if provider == "auto":
            continue  # Already tested
            
        results[f"{provider}_en"] = test_tts_with_provider(
            service, 
            test_texts["en"], 
            "en", 
            provider
        )
    
    # Test OpenAI with different voices
    if "openai" in providers:
        for voice in voices.get("openai", []):
            results[f"openai_en_{voice}"] = test_tts_with_provider(
                service, 
                test_texts["en"], 
                "en", 
                "openai", 
                voice
            )
    
    # Test different languages with the default provider
    for lang_code, text in test_texts.items():
        if lang_code == "en":
            continue  # Already tested
            
        results[f"auto_{lang_code}"] = test_tts_with_provider(
            service, 
            text, 
            lang_code, 
            "auto"
        )
    
    # Print summary
    print("\n=== Test Summary ===")
    for test_name, success in results.items():
        print(f"{test_name}: {'✅ Success' if success else '❌ Failed'}")
    
    # Print overall result
    if all(results.values()):
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed.")
        failed_tests = [name for name, success in results.items() if not success]
        print(f"Failed tests: {', '.join(failed_tests)}")

if __name__ == "__main__":
    main()
