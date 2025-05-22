"""
Test script for Gemini 2.5 Flash TTS using direct HTTP requests to the API

This script bypasses the Python SDK limitations by making direct HTTP requests
to the Gemini API endpoints for TTS functionality.
"""

import os
import sys
import json
import logging
import requests
import tempfile
import wave
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_gemini_tts_direct_http.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_gemini_tts_direct_http")

# Load environment variables
load_dotenv()

# Get Gemini API key
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    logger.error("Gemini API key not found. Please set it in your .env file.")
    sys.exit(1)

def save_wave_file(filename, pcm_data, channels=1, rate=24000, sample_width=2):
    """Save PCM data to a WAV file"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)
    logger.info(f"Saved audio to {filename}")

def test_gemini_tts_direct_http():
    """Test Gemini 2.5 Flash TTS using direct HTTP requests"""
    logger.info("=== Testing Gemini 2.5 Flash TTS with Direct HTTP Requests ===")
    
    try:
        # Test text
        text = "Hello, this is a test of the Gemini 2.5 Flash Preview TTS service using direct HTTP requests."
        
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
            },
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": "Kore"  # Use one of the available voices
                    }
                }
            }
        }
        
        # Make the API request
        logger.info("Sending request to Gemini API...")
        response = requests.post(api_url, headers=headers, json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            logger.info("Request successful!")
            response_json = response.json()
            logger.info(f"Response structure: {json.dumps(response_json.keys(), indent=2)}")
            
            # Extract the audio data from the response
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
                                
                                logger.info(f"Found audio data with MIME type: {mime_type}")
                                
                                # Decode the base64 data
                                import base64
                                audio_data = base64.b64decode(data_base64)
                                
                                # Save to a file
                                output_file = "test_gemini_tts_direct_http.wav"
                                if mime_type == "audio/wav":
                                    with open(output_file, "wb") as f:
                                        f.write(audio_data)
                                    logger.info(f"Saved WAV audio to {output_file}")
                                elif mime_type == "audio/x-wav":
                                    with open(output_file, "wb") as f:
                                        f.write(audio_data)
                                    logger.info(f"Saved WAV audio to {output_file}")
                                elif mime_type == "audio/mp3":
                                    output_file = "test_gemini_tts_direct_http.mp3"
                                    with open(output_file, "wb") as f:
                                        f.write(audio_data)
                                    logger.info(f"Saved MP3 audio to {output_file}")
                                else:
                                    logger.warning(f"Unknown MIME type: {mime_type}")
                                    output_file = f"test_gemini_tts_direct_http.{mime_type.split('/')[-1]}"
                                    with open(output_file, "wb") as f:
                                        f.write(audio_data)
                                    logger.info(f"Saved audio to {output_file}")
                                
                                return True
            
            logger.warning("No audio data found in the response")
            logger.info(f"Full response: {json.dumps(response_json, indent=2)}")
            return False
        else:
            logger.error(f"Request failed with status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error testing Gemini TTS with direct HTTP: {str(e)}")
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
            
            # Test text
            text = f"Hello, this is a test of the Gemini 2.5 Flash Preview TTS service using the {voice} voice."
            
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
                },
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": voice
                        }
                    }
                }
            }
            
            # Make the API request
            response = requests.post(api_url, headers=headers, json=payload)
            
            # Check if the request was successful
            if response.status_code == 200:
                response_json = response.json()
                
                # Extract the audio data from the response
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
                                    import base64
                                    audio_data = base64.b64decode(data_base64)
                                    
                                    # Save to a file
                                    output_file = f"test_gemini_tts_direct_http_{voice.lower()}.wav"
                                    if mime_type == "audio/mp3":
                                        output_file = f"test_gemini_tts_direct_http_{voice.lower()}.mp3"
                                    
                                    with open(output_file, "wb") as f:
                                        f.write(audio_data)
                                    
                                    logger.info(f"Success! Audio saved to {output_file}")
                                    results[voice] = True
                                    break
                        else:
                            logger.warning(f"No audio data found in the response for voice {voice}")
                            results[voice] = False
                    else:
                        logger.warning(f"No content or parts found in the response for voice {voice}")
                        results[voice] = False
                else:
                    logger.warning(f"No candidates found in the response for voice {voice}")
                    results[voice] = False
            else:
                logger.error(f"Request failed with status code {response.status_code} for voice {voice}")
                logger.error(f"Response: {response.text}")
                results[voice] = False
            
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
    logger.info("Starting Gemini TTS test script with direct HTTP requests")
    
    # Test with direct HTTP requests
    test_gemini_tts_direct_http()
    
    # Test with different voices
    test_with_voice_variations()
    
    logger.info("Test script completed")
