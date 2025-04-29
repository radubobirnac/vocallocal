"""
API module for handling transcription requests.
"""

import os
import io
import openai
from ..core.config import API_KEY

def initialize_api():
    """Initialize the OpenAI API with our key."""
    openai.api_key = API_KEY
    os.environ["OPENAI_API_KEY"] = API_KEY

def transcribe_audio(audio_data, model="gpt-4o-mini-transcribe", language="en"):
    """Transcribe audio using OpenAI API."""
    try:
        # Prepare audio file for API
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.wav"
        
        # Send to API with specified language
        response = openai.audio.transcriptions.create(
            model=model,
            file=audio_file,
            language=language
        )
        
        # Return transcription
        return response.text
        
    except Exception as e:
        print(f"Error transcribing with {model}: {e}")
        return None 