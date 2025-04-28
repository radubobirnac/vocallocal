"""
Core configuration module for VocalLocal.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_KEY = os.getenv('OPENAI_API_KEY')
if not API_KEY:
    raise ValueError("OpenAI API key not found. Please set it in your .env file.")

# Audio Configuration
SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK_SIZE = 1024
MAX_RECORD_TIME = 120  # seconds

# File Configuration
TRANSCRIPTS_DIR = "transcripts"

# Recording Configuration
TRIGGER_KEY = "insert"  # Use Insert key for start/stop

# Supported Languages
SUPPORTED_LANGUAGES = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Dutch": "nl",
    "Japanese": "ja",
    "Chinese": "zh",
    "Korean": "ko",
    "Russian": "ru",
    "Arabic": "ar",
    "Hindi": "hi",
    "Turkish": "tr",
    "Swedish": "sv",
    "Polish": "pl",
    "Norwegian": "no",
    "Finnish": "fi",
    "Danish": "da",
    "Ukrainian": "uk",
    "Czech": "cs",
    "Romanian": "ro",
    "Hungarian": "hu",
    "Greek": "el",
    "Hebrew": "he",
    "Thai": "th",
    "Vietnamese": "vi",
    "Indonesian": "id",
    "Malay": "ms",
    "Bulgarian": "bg"
} 