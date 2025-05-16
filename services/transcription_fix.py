"""Transcription service for VocalLocal."""
import os
import io
import tempfile
import subprocess
import openai
import google.generativeai as genai
from services.base_service import BaseService
from metrics_tracker import track_transcription_metrics

class TranscriptionService(BaseService):
    """Service for transcribing audio files."""

    def __init__(self):
        """Initialize the transcription service."""
        super().__init__("transcription")
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')

        # Configure OpenAI
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.openai_available = True
        else:
            self.openai_available = False
            self.logger.warning("OpenAI API key not found. OpenAI transcription will not be available.")

        # Configure Gemini
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_available = True
            self.logger.info("Google Generative AI module loaded successfully for transcription service")
        else:
            self.gemini_available = False
            self.logger.warning("Gemini API key not found. Gemini transcription will not be available.")

    @track_transcription_metrics
    def transcribe(self, audio_data, language, model="gemini"):
        """
        Transcribe audio data using the specified model.
        
        Args:
            audio_data (bytes): The audio data to transcribe
            language (str): The language code (e.g., 'en', 'es')
            model (str): The model to use ('gemini', 'gpt-4o-mini-transcribe', etc.)
            
        Returns:
            str: The transcribed text
        """
        self.logger.info(f"Transcribing audio with model: {model}, language: {language}, size: {len(audio_data)} bytes")
        
        try:
            # Check if we should use Gemini
            if model.startswith('gemini-') or model == 'gemini':
                if not self.gemini_available:
                    self.logger.warning("Gemini not available. Falling back to OpenAI.")
                    return self.transcribe_with_openai(audio_data, language, "gpt-4o-mini-transcribe")
                
                return self.transcribe_with_gemini(audio_data, language, model)
            else:
                # Use OpenAI for transcription
                if not self.openai_available:
                    self.logger.warning("OpenAI not available. Falling back to Gemini.")
                    return self.transcribe_with_gemini(audio_data, language, "gemini")
                
                return self.transcribe_with_openai(audio_data, language, model)
        except Exception as e:
            self.logger.error(f"Error in transcription: {str(e)}")
            raise e

    def transcribe_with_gemini(self, audio_data, language, model_name="gemini"):
        """
        Transcribe audio using Google's Gemini model.
        
        Args:
            audio_data (bytes): The audio data to transcribe
            language (str): The language code
            model_name (str): The model name to use
            
        Returns:
            str: The transcribed text
        """
        try:
            self.logger.info(f"Using Gemini for transcription with model: {model_name}")
            
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Use the generative model to transcribe
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Read the audio file
                with open(temp_file_path, 'rb') as f:
                    audio_bytes = f.read()
                
                # Generate content with the audio
                response = model.generate_content(
                    audio_bytes,
                    generation_config={
                        "temperature": 0,
                    },
                    stream=False
                )
                
                # Extract the transcription
                transcription = response.text
                
                self.logger.info(f"Gemini transcription successful: {len(transcription)} characters")
                return transcription
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    
        except Exception as e:
            self.logger.error(f"Error in Gemini transcription: {str(e)}")
            raise e

    def transcribe_with_openai(self, audio_data, language, model="gpt-4o-mini-transcribe"):
        """
        Transcribe audio using OpenAI's Whisper model.
        
        Args:
            audio_data (bytes): The audio data to transcribe
            language (str): The language code
            model (str): The model to use
            
        Returns:
            str: The transcribed text
        """
        try:
            self.logger.info(f"Using OpenAI for transcription with model: {model}")
            
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Convert WebM to MP3 using FFmpeg
                mp3_file_path = temp_file_path.replace('.webm', '.mp3')
                self.logger.info(f"Converting WebM to MP3: {temp_file_path} -> {mp3_file_path}")
                
                try:
                    # Run FFmpeg to convert the file
                    result = subprocess.run(
                        ['ffmpeg', '-i', temp_file_path, '-vn', '-ar', '44100', '-ac', '2', '-b:a', '192k', mp3_file_path],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    self.logger.info(f"FFmpeg conversion successful: {os.path.getsize(mp3_file_path)} bytes")
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"FFmpeg conversion failed: {e.stderr}")
                    raise Exception(f"Audio conversion failed: {e.stderr}")
                except FileNotFoundError:
                    self.logger.error("FFmpeg not found. Please install FFmpeg.")
                    raise Exception("FFmpeg not installed. Cannot convert audio format.")
                
                # Open the MP3 file for OpenAI
                with open(mp3_file_path, 'rb') as audio_file:
                    # Call OpenAI API
                    response = openai.audio.transcriptions.create(
                        model=model,
                        file=audio_file,
                        language=language
                    )
                
                transcription = response.text
                self.logger.info(f"OpenAI transcription successful: {len(transcription)} characters")
                return transcription
            finally:
                # Clean up the temporary files
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                mp3_path = temp_file_path.replace('.webm', '.mp3')
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)
                    
        except Exception as e:
            self.logger.error(f"Error in OpenAI transcription: {str(e)}")
            raise e

# Create a singleton instance
transcription_service = TranscriptionService()
