"""Google API service for VocalLocal."""
import os
import logging
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)

# Try to import Google API libraries
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("Google Generative AI not available. Using mock implementation.")
    GEMINI_AVAILABLE = False

try:
    from google.oauth2 import service_account
    from google.cloud import speech, translate
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    logger.warning("Google Cloud libraries not available. Using mock implementation.")
    GOOGLE_CLOUD_AVAILABLE = False

class GoogleAPIService:
    """Service for Google API interactions (Speech-to-Text, Translation, Gemini)."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern to ensure one service instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize Google API clients with appropriate credentials."""
        self.initialized = False
        self.gemini_available = False
        self.speech_available = False
        self.translate_available = False
        
        # Set up Gemini if available
        if GEMINI_AVAILABLE:
            try:
                # Get API key from environment
                self.api_key = os.environ.get('GEMINI_API_KEY')
                
                if self.api_key:
                    # Configure Gemini
                    genai.configure(api_key=self.api_key)
                    self.gemini_available = True
                    logger.info("Gemini API configured successfully")
                else:
                    logger.warning("Gemini API key not found")
            except Exception as e:
                logger.error(f"Failed to configure Gemini API: {str(e)}")
        
        # Set up Google Cloud services if available
        if GOOGLE_CLOUD_AVAILABLE:
            try:
                # Set up service account credentials if available
                cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
                if cred_path and os.path.exists(cred_path):
                    self.credentials = service_account.Credentials.from_service_account_file(
                        cred_path,
                        scopes=["https://www.googleapis.com/auth/cloud-platform"]
                    )
                    
                    # Initialize Speech-to-Text client
                    self.speech_client = speech.SpeechClient(credentials=self.credentials)
                    self.speech_available = True
                    
                    # Initialize Translation client
                    self.translate_client = translate.TranslationServiceClient(credentials=self.credentials)
                    self.translate_available = True
                    
                    logger.info("Google API clients initialized successfully")
                else:
                    logger.warning("Google service account credentials not found")
                    self._setup_mock_services()
            except Exception as e:
                logger.error(f"Failed to initialize Google API services: {str(e)}")
                self._setup_mock_services()
        else:
            self._setup_mock_services()
            
        self.initialized = True
    
    def _setup_mock_services(self):
        """Set up mock services for local development."""
        self.speech_client = MagicMock()
        self.translate_client = MagicMock()
        logger.warning("Using mock Google API services")
    
    def transcribe_audio(self, audio_file_path, language_code="en-US"):
        """Transcribe audio using Google Speech-to-Text."""
        if not self.initialized or not self.speech_available:
            logger.error("Speech-to-Text client not available")
            return None
            
        try:
            with open(audio_file_path, "rb") as audio_file:
                content = audio_file.read()
                
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.MP3,
                sample_rate_hertz=16000,
                language_code=language_code,
            )
            
            response = self.speech_client.recognize(config=config, audio=audio)
            
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript
                
            return transcript
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return None
    
    def transcribe_with_gemini(self, audio_file_path, language="en"):
        """Transcribe audio using Gemini API."""
        if not self.initialized or not self.gemini_available:
            logger.error("Gemini API not available")
            return None
            
        try:
            import base64
            
            # Read audio file as bytes
            with open(audio_file_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
            
            # Convert to base64
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Determine MIME type based on file extension
            mime_type = "audio/mp3"  # Default
            if audio_file_path.endswith(".wav"):
                mime_type = "audio/wav"
            elif audio_file_path.endswith(".webm"):
                mime_type = "audio/webm"
            
            # Initialize Gemini model
            model = genai.GenerativeModel('gemini-2.0-flash-lite')
            
            # Create content parts
            parts = [
                {"text": f"Please transcribe the following audio. The language is {language}."},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": audio_b64
                    }
                }
            ]
            
            # Generate content with the audio
            response = model.generate_content(parts)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini transcription error: {str(e)}")
            return None
    
    def translate_text(self, text, target_language, source_language=None):
        """Translate text using Google Translation API."""
        if not self.initialized or not self.translate_available:
            logger.error("Translation client not available")
            return None
            
        try:
            parent = f"projects/{self.project_id}"
            
            response = self.translate_client.translate_text(
                request={
                    "parent": parent,
                    "contents": [text],
                    "mime_type": "text/plain",
                    "source_language_code": source_language,
                    "target_language_code": target_language,
                }
            )
            
            return response.translations[0].translated_text
            
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return None
