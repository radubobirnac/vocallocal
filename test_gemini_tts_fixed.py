"""
Test script for Gemini 2.5 Flash Preview TTS functionality using the correct API approach

This script tests the Gemini 2.5 Flash Preview TTS functionality using the proper
response_modalities and speech_config parameters instead of response_mime_type.
"""

import os
import sys
import logging
import tempfile
import wave
from dotenv import load_dotenv

# Configure logging to both console and file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_gemini_tts_fixed.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_gemini_tts_fixed")

# Load environment variables
load_dotenv()

# Check if Gemini API key is available
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    logger.error("Gemini API key not found. Please set it in your .env file.")
    sys.exit(1)

# Try to import Google Generative AI
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
    logger.info("Google Generative AI module loaded successfully")
except ImportError:
    logger.error("Google Generative AI module not available. Please install it with 'pip install google-generativeai'.")
    GEMINI_AVAILABLE = False
    sys.exit(1)

def save_wave_file(filename, pcm_data, channels=1, rate=24000, sample_width=2):
    """Save PCM data to a WAV file"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)
    logger.info(f"Saved audio to {filename}")

def test_gemini_tts_with_response_modalities():
    """Test Gemini 2.5 Flash TTS using the correct response_modalities approach"""
    logger.info("=== Testing Gemini 2.5 Flash TTS with response_modalities ===")
    
    try:
        # Initialize the Gemini client
        client = genai.Client(api_key=gemini_api_key)
        
        # Test text
        text = "Hello, this is a test of the Gemini 2.5 Flash Preview TTS service."
        
        # Configure the model with response_modalities and speech_config
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Kore",  # Use one of the available voices
                        )
                    )
                ),
            )
        )
        
        # Check if we got audio data
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                content = candidate.content
                if hasattr(content, 'parts') and content.parts:
                    part = content.parts[0]
                    if hasattr(part, 'inline_data') and part.inline_data:
                        inline_data = part.inline_data
                        if hasattr(inline_data, 'data') and inline_data.data:
                            # Get the audio data
                            audio_data = inline_data.data
                            logger.info(f"Audio data type: {type(audio_data)}")
                            logger.info(f"Audio data size: {len(audio_data)} bytes")
                            
                            # Save to a file
                            output_file = "test_gemini_tts_fixed.wav"
                            save_wave_file(output_file, audio_data)
                            logger.info(f"Success! Audio saved to {output_file}")
                            return True
        
        logger.warning("No audio data found in the response")
        logger.info(f"Response structure: {dir(response)}")
        return False
    
    except Exception as e:
        logger.error(f"Error testing Gemini TTS: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_with_voice_variations():
    """Test Gemini 2.5 Flash TTS with different voice options"""
    logger.info("=== Testing Gemini 2.5 Flash TTS with different voices ===")
    
    # List of available voices to test
    voices = ["Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede"]
    
    results = {}
    
    for voice in voices:
        try:
            logger.info(f"Testing with voice: {voice}")
            
            # Initialize the Gemini client
            client = genai.Client(api_key=gemini_api_key)
            
            # Test text
            text = f"Hello, this is a test of the Gemini 2.5 Flash Preview TTS service using the {voice} voice."
            
            # Configure the model with response_modalities and speech_config
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice,
                            )
                        )
                    ),
                )
            )
            
            # Get the audio data
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            
            # Save to a file
            output_file = f"test_gemini_tts_fixed_{voice.lower()}.wav"
            save_wave_file(output_file, audio_data)
            
            logger.info(f"Success! Audio saved to {output_file}")
            results[voice] = True
            
        except Exception as e:
            logger.error(f"Error with voice {voice}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            results[voice] = False
    
    # Log summary of results
    logger.info("=== Voice Test Results ===")
    for voice, success in results.items():
        logger.info(f"{voice}: {'Success' if success else 'Failed'}")
    
    return results

if __name__ == "__main__":
    logger.info("Starting Gemini TTS test script with fixed implementation")
    
    # Test with the correct response_modalities approach
    test_gemini_tts_with_response_modalities()
    
    # Test with different voices
    test_with_voice_variations()
    
    logger.info("Test script completed")
