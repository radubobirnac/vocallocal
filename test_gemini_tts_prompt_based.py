"""
Test script for Gemini 2.5 Flash TTS using a prompt-based approach

This script tests using Gemini 2.5 Flash Preview TTS by embedding voice instructions
in the prompt rather than using the speech_config parameter.
"""

import os
import sys
import json
import logging
import requests
import tempfile
import base64
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_gemini_tts_prompt_based.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_gemini_tts_prompt_based")

# Load environment variables
load_dotenv()

# Get Gemini API key
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    logger.error("Gemini API key not found. Please set it in your .env file.")
    sys.exit(1)

def test_gemini_tts_prompt_based():
    """Test Gemini 2.5 Flash TTS using a prompt-based approach"""
    logger.info("=== Testing Gemini 2.5 Flash TTS with Prompt-Based Approach ===")

    try:
        # Base text
        base_text = "This is a test of the Gemini 2.5 Flash Preview TTS service."

        # Add voice instructions to the prompt
        text = f"Please speak this in a male, enthusiastic voice, slightly faster than normal: {base_text}"

        # Gemini API endpoint for generating content
        api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent"

        # Request headers
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": gemini_api_key
        }

        # Request payload
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": text
                        }
                    ]
                }
            ],
            "generation_config": {
                "temperature": 0.2,
                "top_p": 0.95,
                "top_k": 0,
                "response_modalities": ["AUDIO"]
            }
        }

        # Make the API request
        logger.info("Sending request to Gemini API...")
        response = requests.post(api_url, headers=headers, json=payload)

        # Check if the request was successful
        if response.status_code == 200:
            logger.info("Request successful!")
            response_json = response.json()
            logger.info(f"Response structure: {json.dumps(list(response_json.keys()), indent=2)}")

            # Extract the audio data from the response
            if "candidates" in response_json and len(response_json["candidates"]) > 0:
                candidate = response_json["candidates"][0]
                logger.info(f"Candidate keys: {json.dumps(list(candidate.keys()), indent=2)}")

                if "content" in candidate:
                    content = candidate["content"]
                    logger.info(f"Content keys: {json.dumps(list(content.keys()), indent=2)}")

                    if "parts" in content:
                        parts = content["parts"]
                        logger.info(f"Found {len(parts)} parts")

                        for i, part in enumerate(parts):
                            logger.info(f"Part {i} keys: {json.dumps(list(part.keys()), indent=2)}")

                            if "inline_data" in part:
                                inline_data = part["inline_data"]
                                logger.info(f"Inline data keys: {json.dumps(list(inline_data.keys()), indent=2)}")

                                if "mime_type" in inline_data and "data" in inline_data:
                                    mime_type = inline_data["mime_type"]
                                    data_base64 = inline_data["data"]

                                    logger.info(f"Found audio data with MIME type: {mime_type}")

                                    # Decode the base64 data
                                    audio_data = base64.b64decode(data_base64)

                                    # Save to a file
                                    output_file = "test_gemini_tts_prompt_based.wav"
                                    if mime_type == "audio/mp3":
                                        output_file = "test_gemini_tts_prompt_based.mp3"

                                    with open(output_file, "wb") as f:
                                        f.write(audio_data)

                                    logger.info(f"Saved audio to {output_file}")
                                    return True

            logger.warning("No audio data found in the response")
            logger.info(f"Full response: {json.dumps(response_json, indent=2)}")

            # Check if there's text in the response
            if "candidates" in response_json and len(response_json["candidates"]) > 0:
                candidate = response_json["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    for part in parts:
                        if "text" in part:
                            logger.info(f"Found text response: {part['text']}")

                            # Save the text to a file for reference
                            with open("test_gemini_tts_text_response.txt", "w") as f:
                                f.write(part["text"])
                            logger.info("Saved text response to test_gemini_tts_text_response.txt")

            return False
        else:
            logger.error(f"Request failed with status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error testing Gemini TTS with prompt-based approach: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_with_different_models():
    """Test different Gemini models for TTS capability"""
    logger.info("=== Testing Different Gemini Models for TTS ===")

    # List of models to test
    models = [
        "gemini-2.5-flash-preview-tts",
        "gemini-2.5-flash-preview",
        "gemini-2.5-pro-preview",
        "gemini-2.5-pro-preview-tts",
        "gemini-2.5-flash",
        "gemini-2.5-pro"
    ]

    results = {}

    for model in models:
        try:
            logger.info(f"Testing with model: {model}")

            # Base text
            base_text = f"This is a test of the {model} model for TTS."

            # Add voice instructions to the prompt
            text = f"Please speak this in a male, enthusiastic voice, slightly faster than normal: {base_text}"

            # Gemini API endpoint for generating content
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

            # Request headers
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": gemini_api_key
            }

            # Request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": text
                            }
                        ]
                    }
                ],
                "generation_config": {
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 0,
                    "response_modalities": ["AUDIO"]
                }
            }

            # Make the API request
            response = requests.post(api_url, headers=headers, json=payload)

            # Check if the request was successful
            if response.status_code == 200:
                response_json = response.json()

                # Check if the response contains audio data
                has_audio = False

                if "candidates" in response_json and len(response_json["candidates"]) > 0:
                    candidate = response_json["candidates"][0]

                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]

                        for part in parts:
                            if "inline_data" in part:
                                inline_data = part["inline_data"]

                                if "mime_type" in inline_data and "data" in inline_data:
                                    mime_type = inline_data["mime_type"]
                                    data_base64 = inline_data["data"]

                                    # Decode the base64 data
                                    audio_data = base64.b64decode(data_base64)

                                    # Save to a file
                                    output_file = f"test_gemini_tts_{model.replace('-', '_')}.wav"
                                    if mime_type == "audio/mp3":
                                        output_file = f"test_gemini_tts_{model.replace('-', '_')}.mp3"

                                    with open(output_file, "wb") as f:
                                        f.write(audio_data)

                                    logger.info(f"Success! Audio saved to {output_file}")
                                    has_audio = True
                                    break

                if has_audio:
                    results[model] = True
                else:
                    logger.warning(f"No audio data found in the response for model {model}")

                    # Check if there's text in the response
                    has_text = False
                    if "candidates" in response_json and len(response_json["candidates"]) > 0:
                        candidate = response_json["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            for part in parts:
                                if "text" in part:
                                    logger.info(f"Found text response from {model}: {part['text'][:100]}...")

                                    # Save the text to a file for reference
                                    with open(f"test_gemini_tts_{model.replace('-', '_')}_text_response.txt", "w") as f:
                                        f.write(part["text"])
                                    logger.info(f"Saved text response to test_gemini_tts_{model.replace('-', '_')}_text_response.txt")
                                    has_text = True

                    results[model] = "Text Only" if has_text else False
            else:
                logger.error(f"Request failed with status code {response.status_code} for model {model}")
                logger.error(f"Response: {response.text}")
                results[model] = False

        except Exception as e:
            logger.error(f"Error with model {model}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            results[model] = False

    # Log summary of results
    logger.info("=== Model Test Results ===")
    for model, result in results.items():
        if result is True:
            status = "Success - Audio Generated"
        elif result == "Text Only":
            status = "Text Only - No Audio"
        else:
            status = "Failed"
        logger.info(f"{model}: {status}")

    return results

if __name__ == "__main__":
    logger.info("Starting Gemini TTS test script with prompt-based approach")

    # Test with prompt-based approach
    test_gemini_tts_prompt_based()

    # Test with different models
    test_with_different_models()

    logger.info("Test script completed")
