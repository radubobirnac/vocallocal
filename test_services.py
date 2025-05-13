"""
Test script for VocalLocal services

This script tests the new service classes for transcription and translation.
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
    from src.services.transcription_service import TranscriptionService
    from src.services.translation_service import TranslationService
    print("Services imported successfully")
except ImportError as e:
    print(f"Error importing services: {str(e)}")
    sys.exit(1)

def test_translation_service():
    """Test the translation service"""
    print("\n=== Testing Translation Service ===")

    # Initialize the translation service
    translation_service = TranslationService()

    # Sample text to translate
    sample_text = "Hello, this is a test of the translation service. We are checking if it works correctly."

    # Test languages
    test_languages = ["es", "fr", "de", "it", "ja", "zh", "ru"]

    # Test with different providers
    for provider in ["gemini", "openai", "auto"]:
        print(f"\nTesting with provider: {provider}")

        for lang_code in test_languages:
            print(f"  Translating to {lang_code}...")
            try:
                # Translate the text
                start_time = time.time()
                translated_text = translation_service.translate(
                    text=sample_text,
                    target_language=lang_code,
                    source_language="en",
                    provider=provider
                )
                elapsed_time = time.time() - start_time

                # Print the result
                print(f"  ✓ Translation successful ({elapsed_time:.2f}s)")
                print(f"    Result: {translated_text[:100]}...")

            except Exception as e:
                print(f"  ✗ Translation failed: {str(e)}")

    # Print metrics
    print("\nTranslation Service Metrics:")
    metrics = translation_service.get_metrics()
    print(metrics)

def test_transcription_service():
    """Test the transcription service"""
    print("\n=== Testing Transcription Service ===")

    # Initialize the transcription service
    transcription_service = TranscriptionService()

    # Check if we have a test audio file
    test_audio_path = "test_audio.mp3"
    if not os.path.exists(test_audio_path):
        print(f"Test audio file not found: {test_audio_path}")
        print("Skipping transcription test")
        return

    # Load the test audio file
    with open(test_audio_path, "rb") as f:
        audio_data = f.read()

    # Test with different providers
    for provider in ["gemini", "openai", "auto"]:
        print(f"\nTesting with provider: {provider}")

        try:
            # Transcribe the audio
            start_time = time.time()
            transcribed_text = transcription_service.transcribe(
                audio_data=audio_data,
                language="en",
                provider=provider
            )
            elapsed_time = time.time() - start_time

            # Print the result
            print(f"✓ Transcription successful ({elapsed_time:.2f}s)")
            print(f"  Result: {transcribed_text[:100]}...")

        except Exception as e:
            print(f"✗ Transcription failed: {str(e)}")

    # Print metrics
    print("\nTranscription Service Metrics:")
    metrics = transcription_service.get_metrics()
    print(metrics)

def main():
    """Main function to run all tests"""
    print("Starting VocalLocal services test")

    # Test the translation service
    test_translation_service()

    # Skip the transcription test since we don't have a test audio file
    print("\n=== Skipping Transcription Service Test ===")
    print("No test audio file available in this environment.")
    print("To test the transcription service, create a test_audio.mp3 file and run this script again.")

    print("\nAll tests completed")

if __name__ == "__main__":
    main()
