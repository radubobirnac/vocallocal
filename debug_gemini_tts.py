"""
Debug script for Gemini 2.5 Flash TTS functionality

This script tests the Gemini 2.5 Flash TTS functionality directly,
bypassing the service layer to identify any issues.
"""

import os
import sys
import logging
import tempfile
import traceback
from dotenv import load_dotenv

# Configure logging to both console and file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug_gemini_tts.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("debug_gemini_tts")

# Load environment variables
load_dotenv()

# Check if Gemini API key is available
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    logger.error("Gemini API key not found. Please set it in your .env file.")
    sys.exit(1)

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    logger.info("Google Generative AI module loaded successfully")
except ImportError:
    logger.error("Google Generative AI module not available. Please install it with 'pip install google-generativeai'.")
    GEMINI_AVAILABLE = False
    sys.exit(1)

def test_gemini_model_list():
    """Test listing available Gemini models"""
    logger.info("=== Testing Gemini Model List ===")

    try:
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)

        # List available models
        models = genai.list_models()
        logger.info(f"Found {len(models)} models")

        # Print model details
        for model in models:
            logger.info(f"Model: {model.name}")
            logger.info(f"  - Display name: {model.display_name}")
            logger.info(f"  - Description: {model.description}")
            logger.info(f"  - Supported generation methods: {model.supported_generation_methods}")
            logger.info(f"  - Input token limit: {model.input_token_limit}")
            logger.info(f"  - Output token limit: {model.output_token_limit}")
            logger.info(f"  - Temperature range: {model.temperature_range}")
            logger.info(f"  - Top-p range: {model.top_p_range}")
            logger.info(f"  - Top-k range: {model.top_k_range}")
            logger.info("---")

        # Check for TTS-specific models
        tts_models = [model for model in models if "tts" in model.name.lower()]
        if tts_models:
            logger.info(f"Found {len(tts_models)} TTS-specific models:")
            for model in tts_models:
                logger.info(f"  - {model.name}")
        else:
            logger.warning("No TTS-specific models found")

        # Check for Gemini 2.5 Flash Preview models
        flash_preview_models = [model for model in models if "2.5-flash-preview" in model.name.lower()]
        if flash_preview_models:
            logger.info(f"Found {len(flash_preview_models)} Gemini 2.5 Flash Preview models:")
            for model in flash_preview_models:
                logger.info(f"  - {model.name}")
        else:
            logger.warning("No Gemini 2.5 Flash Preview models found")

        return True
    except Exception as e:
        logger.error(f"Error listing Gemini models: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_gemini_tts_direct():
    """Test Gemini 2.5 Flash TTS directly"""
    logger.info("=== Testing Gemini 2.5 Flash TTS Directly ===")

    try:
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)

        # Test text
        text = "Hello, this is a test of the Gemini 2.5 Flash Preview TTS service."

        # Try both model names to see which one works
        model_names = [
            "gemini-2.5-flash-preview-tts",
            "gemini-2.5-flash-tts",
            "gemini-2.5-flash-preview"
        ]

        for model_name in model_names:
            logger.info(f"Testing with model name: {model_name}")

            try:
                # Configure the model
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config={
                        "temperature": 0.2,
                        "top_p": 0.95,
                        "top_k": 0,
                    }
                )

                # Add instructions for voice characteristics directly in the prompt
                prompt = f"Please speak this in a male, enthusiastic voice, slightly faster than normal: {text}"

                # Configure the response to be audio-only
                generation_config = {
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 0,
                    "response_mime_type": "audio/mp3"  # Request audio-only response
                }

                # Generate speech
                logger.info(f"Generating speech with model: {model_name}")
                response = model.generate_content(
                    prompt,
                    stream=False,
                    generation_config=generation_config
                )

                # Check response type
                logger.info(f"Response type: {type(response)}")
                logger.info(f"Response attributes: {dir(response)}")

                # Try to access audio data
                if hasattr(response, 'audio'):
                    logger.info("Response has 'audio' attribute")
                    logger.info(f"Audio attributes: {dir(response.audio)}")

                    if hasattr(response.audio, 'data'):
                        # Get the audio data
                        audio_data = response.audio.data
                        logger.info(f"Audio data type: {type(audio_data)}")
                        logger.info(f"Audio data size: {len(audio_data)} bytes")

                        # Save to a file
                        output_file = f"test_direct_{model_name.replace('-', '_')}.mp3"
                        with open(output_file, 'wb') as f:
                            f.write(audio_data)

                        logger.info(f"Audio saved to {output_file}")
                    else:
                        logger.warning("Response.audio does not have 'data' attribute")
                else:
                    logger.warning("Response does not have 'audio' attribute")

                    # Try alternative ways to get audio data
                    if hasattr(response, 'parts'):
                        logger.info("Response has 'parts' attribute")
                        for i, part in enumerate(response.parts):
                            logger.info(f"Part {i} type: {type(part)}")
                            logger.info(f"Part {i} attributes: {dir(part)}")

                            if hasattr(part, 'text'):
                                logger.info(f"Part {i} text: {part.text[:100]}...")

                            if hasattr(part, 'audio'):
                                logger.info(f"Part {i} has audio")
                                audio_data = part.audio.data
                                output_file = f"test_direct_{model_name.replace('-', '_')}_part_{i}.mp3"
                                with open(output_file, 'wb') as f:
                                    f.write(audio_data)
                                logger.info(f"Audio saved to {output_file}")

                logger.info(f"Test with {model_name} completed")
            except Exception as e:
                logger.error(f"Error with model {model_name}: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")

        return True
    except Exception as e:
        logger.error(f"Error testing Gemini TTS directly: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("Starting Gemini TTS debug script")

    # Test listing models
    test_gemini_model_list()

    # Test TTS directly
    test_gemini_tts_direct()

    logger.info("Debug script completed")
