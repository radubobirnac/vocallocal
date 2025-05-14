"""
Transcription service for VocalLocal
"""
import os
import time
import tempfile
import openai
from services.base_service import BaseService
from config import Config

class TranscriptionService(BaseService):
    """Service for handling audio transcription"""
    
    def __init__(self):
        """Initialize the transcription service"""
        super().__init__()
        self.gemini_available = False
        
        # Try to import Google Generative AI
        try:
            import google.generativeai as genai
            self.genai = genai
            self.gemini_available = True
            print("Google Generative AI module loaded successfully for transcription service")
        except ImportError as e:
            print(f"Google Generative AI module not available for transcription service: {str(e)}")
            self.genai = None
    
    def transcribe(self, audio_data, language, model="gemini-2.0-flash-lite"):
        """
        Transcribe audio data using the specified model
        
        Args:
            audio_data: Binary audio data
            language: Language code
            model: Model to use (gemini-2.0-flash-lite, gpt-4o-mini-transcribe, etc.)
            
        Returns:
            Transcription text
        """
        # Start timing for metrics
        start_time = time.time()
        
        try:
            # Check if we should use Gemini
            if (model.startswith('gemini') or model == 'gemini') and self.gemini_available:
                try:
                    # Use Gemini for transcription
                    transcription = self.transcribe_with_gemini(audio_data, language, model)
                    
                    # Calculate response time for metrics
                    response_time = time.time() - start_time
                    
                    # Track metrics
                    self.track_metrics("transcription", model, 0, len(transcription), response_time, True)
                    
                    return transcription
                except Exception as gemini_error:
                    # Log the error
                    print(f"Gemini transcription failed: {str(gemini_error)}")
                    print(f"Falling back to OpenAI GPT-4o Mini for transcription")
                    
                    # Track the error in metrics
                    response_time = time.time() - start_time
                    self.track_metrics("transcription", model, 0, 0, response_time, False)
                    
                    # Fallback to OpenAI
                    return self.transcribe_with_openai(audio_data, language)
            else:
                # Use OpenAI for transcription
                return self.transcribe_with_openai(audio_data, language, model)
        except Exception as e:
            # Track the error in metrics
            response_time = time.time() - start_time
            self.track_metrics("transcription", model, 0, 0, response_time, False)
            
            # Re-raise the exception
            raise e
    
    def transcribe_with_gemini(self, audio_data, language, model_type="gemini-2.0-flash-lite"):
        """Helper function to transcribe audio using Google Gemini"""
        # Start timing for metrics
        start_time = time.time()
        
        # Check if Gemini is available
        if not self.gemini_available:
            print("Google Generative AI module is not available. Cannot use Gemini for transcription.")
            print("Falling back to OpenAI for transcription.")
            return self.transcribe_with_openai(audio_data, language)
        
        try:
            # Configure the model
            generation_config = {
                "temperature": 0.2,
                "top_p": 0.95,
                "top_k": 0,
                "max_output_tokens": 8192,
            }
            
            # Handle model selection
            model_name = model_type
            # For metrics tracking, use a simplified model name
            display_model = model_type
            
            if model_type == 'gemini':
                # Use Gemini 2.0 Flash Lite for transcription
                model_name = "models/gemini-2.0-flash-lite"
                display_model = 'gemini-2.0-flash-lite'
                print(f"Using Gemini 2.0 Flash Lite model for transcription")
            elif 'gemini-2.5-flash-preview' in model_type:
                display_model = 'gemini-2.5-flash-preview'
            elif 'gemini-2.5-pro-preview' in model_type:
                # This model has been removed from the UI, but handle it in case it's still in localStorage
                print(f"Gemini 2.5 Pro Preview model is no longer supported for transcription")
                print(f"Falling back to Gemini 2.0 Flash Lite")
                model_name = "models/gemini-2.0-flash-lite"
                display_model = 'gemini-2.0-flash-lite'
            
            # Initialize the Gemini model
            model = self.genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config
            )
            
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Prepare the prompt
            prompt = f"Please transcribe the following audio file. The language is {language}."
            
            # For Gemini, we need to encode the audio file as base64
            import base64
            with open(temp_file_path, 'rb') as audio_file:
                audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
            
            # Clean up the temporary file
            os.remove(temp_file_path)
            
            # Create a multimodal content message with the audio
            response = model.generate_content([
                prompt,
                {"mime_type": "audio/mp3", "data": audio_base64}
            ])
            
            # Extract the transcription from the response
            transcription = response.text
            
            print(f"Gemini transcription completed: {len(transcription)} characters")
            print(f"Successfully transcribed with {model_type}")
            
            return transcription
            
        except Exception as e:
            print(f"Error in Gemini transcription: {str(e)}")
            
            # Check if this is a model not found error
            if "not found" in str(e) or "not supported" in str(e):
                print("The Gemini 2.5 Flash Preview model does not support audio transcription yet.")
                print("This feature may be available in a future update.")
            
            # Fall back to OpenAI for transcription
            print("Falling back to OpenAI for transcription.")
            return self.transcribe_with_openai(audio_data, language)
    
    def transcribe_with_openai(self, audio_data, language, model_type="gpt-4o-mini-transcribe"):
        """Helper function to transcribe audio using OpenAI"""
        # Start timing for metrics
        start_time = time.time()
        
        try:
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Open the file in binary mode
            with open(temp_file_path, 'rb') as audio_file:
                # Call the OpenAI API to transcribe the audio
                response = openai.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",  # Use GPT-4o Mini instead of Whisper
                    file=audio_file,
                    language=language if language != "auto" else None
                )
            
            # Clean up the temporary file
            os.remove(temp_file_path)
            
            # Extract the transcription from the response
            transcription = response.text
            
            print(f"OpenAI transcription completed: {len(transcription)} characters")
            
            # Calculate response time for metrics
            response_time = time.time() - start_time
            
            # Track metrics
            self.track_metrics("transcription", 'openai', 0, len(transcription), response_time, True)
            
            return transcription
            
        except Exception as e:
            print(f"Error in OpenAI transcription: {str(e)}")
            
            # Calculate response time for metrics
            response_time = time.time() - start_time
            
            # Track metrics
            self.track_metrics("transcription", 'openai', 0, 0, response_time, False)
            
            raise e
