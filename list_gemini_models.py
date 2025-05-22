"""
Script to list available Gemini models and their capabilities
"""

import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("list_gemini_models.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("list_gemini_models")

# Load environment variables
load_dotenv()

# Get Gemini API key
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    logger.error("Gemini API key not found. Please set it in your .env file.")
    sys.exit(1)

def list_models():
    """List available Gemini models using the API"""
    logger.info("=== Listing Available Gemini Models ===")
    
    try:
        # Gemini API endpoint for listing models
        api_url = "https://generativelanguage.googleapis.com/v1beta/models"
        
        # Request headers
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": gemini_api_key
        }
        
        # Make the API request
        logger.info("Sending request to Gemini API...")
        response = requests.get(api_url, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            logger.info("Request successful!")
            response_json = response.json()
            
            # Save the full response to a file
            with open("gemini_models_full.json", "w") as f:
                json.dump(response_json, f, indent=2)
            logger.info("Saved full response to gemini_models_full.json")
            
            # Extract and display model information
            if "models" in response_json:
                models = response_json["models"]
                logger.info(f"Found {len(models)} models")
                
                # Create a summary of models
                model_summary = []
                for model in models:
                    model_info = {
                        "name": model.get("name", ""),
                        "display_name": model.get("displayName", ""),
                        "description": model.get("description", ""),
                        "generation_methods": model.get("supportedGenerationMethods", []),
                        "input_token_limit": model.get("inputTokenLimit", 0),
                        "output_token_limit": model.get("outputTokenLimit", 0)
                    }
                    model_summary.append(model_info)
                
                # Save the model summary to a file
                with open("gemini_models_summary.json", "w") as f:
                    json.dump(model_summary, f, indent=2)
                logger.info("Saved model summary to gemini_models_summary.json")
                
                # Display models with TTS-related capabilities
                tts_models = []
                for model in models:
                    name = model.get("name", "")
                    if "tts" in name.lower() or any("audio" in method.lower() for method in model.get("supportedGenerationMethods", [])):
                        tts_models.append(model)
                
                if tts_models:
                    logger.info(f"Found {len(tts_models)} models with potential TTS capabilities:")
                    for model in tts_models:
                        logger.info(f"  - Name: {model.get('name', '')}")
                        logger.info(f"    Display Name: {model.get('displayName', '')}")
                        logger.info(f"    Generation Methods: {model.get('supportedGenerationMethods', [])}")
                        logger.info(f"    Description: {model.get('description', '')}")
                        logger.info("")
                else:
                    logger.info("No models with TTS capabilities found")
                
                return True
            else:
                logger.warning("No models found in the response")
                return False
        else:
            logger.error(f"Request failed with status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error listing Gemini models: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_model_capabilities():
    """Test the capabilities of specific models"""
    logger.info("=== Testing Model Capabilities ===")
    
    try:
        # Load the model summary
        with open("gemini_models_summary.json", "r") as f:
            models = json.load(f)
        
        # Find models with generateContent capability
        generate_content_models = []
        for model in models:
            if "generateContent" in model.get("generation_methods", []):
                generate_content_models.append(model["name"])
        
        logger.info(f"Found {len(generate_content_models)} models with generateContent capability:")
        for model_name in generate_content_models:
            logger.info(f"  - {model_name}")
        
        # Test each model for response_modalities support
        for model_name in generate_content_models:
            logger.info(f"Testing {model_name} for response_modalities support...")
            
            # Gemini API endpoint for generating content
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            
            # Request headers
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": gemini_api_key
            }
            
            # Request payload with response_modalities
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": "Please convert this text to speech."
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
            
            # Check the response
            if response.status_code == 200:
                logger.info(f"  - {model_name}: Success (200 OK)")
                
                # Check if the response contains audio data
                response_json = response.json()
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
                                    logger.info(f"  - {model_name}: Found audio data with MIME type {mime_type}")
                                    has_audio = True
                
                if not has_audio:
                    logger.info(f"  - {model_name}: No audio data in response")
            else:
                logger.info(f"  - {model_name}: Failed ({response.status_code})")
                if "error" in response.json():
                    error_message = response.json()["error"].get("message", "Unknown error")
                    logger.info(f"    Error: {error_message}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing model capabilities: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("Starting Gemini models listing script")
    
    # List available models
    if list_models():
        # Test model capabilities
        test_model_capabilities()
    
    logger.info("Script completed")
