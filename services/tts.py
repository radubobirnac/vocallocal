"""
Text-to-Speech service for VocalLocal
"""
import os
import time
import tempfile
import openai
from services.base_service import BaseService
from config import Config

class TTSService(BaseService):
    """Service for handling text-to-speech conversion"""
    
    def __init__(self):
        """Initialize the TTS service"""
        super().__init__()
        self.gemini_available = False
        
        # Try to import Google Generative AI
        try:
            import google.generativeai as genai
            self.genai = genai
            self.gemini_available = True
            print("Google Generative AI module loaded successfully for TTS service")
        except ImportError as e:
            print(f"Google Generative AI module not available for TTS service: {str(e)}")
            self.genai = None
    
    def synthesize(self, text, language, model="gpt4o-mini"):
        """
        Convert text to speech using the specified model
        
        Args:
            text: Text to convert to speech
            language: Language code
            model: Model to use (gpt4o-mini, openai, etc.)
            
        Returns:
            Path to the generated audio file
        """
        # Start timing for metrics
        start_time = time.time()
        
        try:
            # Create a temporary file to store the audio
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.close()
            
            # First attempt with the selected model
            model_used = model
            fallback_used = False
            success = False
            
            if model == 'gpt4o-mini':
                try:
                    # Use the GPT-4o Mini TTS model
                    self.tts_with_gpt4o_mini(text, language, temp_file.name)
                    model_used = 'gpt4o-mini'
                    success = True
                except Exception as e:
                    # Log the error
                    print(f"GPT-4o Mini TTS error: {str(e)}")
                    print("Falling back to standard OpenAI TTS")
                    
                    try:
                        # Fallback to standard OpenAI TTS
                        self.tts_with_openai(text, language, temp_file.name)
                        model_used = 'openai'
                        fallback_used = True
                        success = True
                    except Exception as fallback_e:
                        # Log the error
                        print(f"Fallback OpenAI TTS error: {str(fallback_e)}")
                        
                        # Clean up the temporary file
                        if os.path.exists(temp_file.name):
                            os.remove(temp_file.name)
                        
                        # Re-raise the exception
                        raise e
            else:  # OpenAI
                try:
                    self.tts_with_openai(text, language, temp_file.name)
                    success = True
                except Exception as e:
                    # Log the error
                    print(f"OpenAI TTS error: {str(e)}")
                    
                    # Clean up the temporary file
                    if os.path.exists(temp_file.name):
                        os.remove(temp_file.name)
                    
                    # Re-raise the exception
                    raise e
            
            # Calculate performance metrics
            end_time = time.time()
            tts_time = end_time - start_time
            char_count = len(text)
            
            # Track metrics
            self.track_metrics("tts", model_used, char_count // 4, char_count, tts_time, success)
            
            return temp_file.name
        except Exception as e:
            # Track the error in metrics
            response_time = time.time() - start_time
            self.track_metrics("tts", model, 0, 0, response_time, False)
            
            # Re-raise the exception
            raise e
    
    def tts_with_openai(self, text, language, output_file_path):
        """Helper function to generate speech using OpenAI's TTS service"""
        # Use onyx voice for all languages
        voice = 'onyx'
        
        # Log request for debugging
        print(f"OpenAI TTS request: language={language}, voice={voice}, text_length={len(text)}")
        
        # Generate speech with OpenAI
        response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        # Save to the output file
        with open(output_file_path, 'wb') as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
        
        return True
    
    def tts_with_gpt4o_mini(self, text, language, output_file_path):
        """Helper function to generate speech using OpenAI's GPT-4o Mini TTS service"""
        # For GPT-4o Mini TTS, we'll use a simple approach without voice mapping
        # Just use 'alloy' voice for all languages
        
        # Log request for debugging
        print(f"GPT-4o Mini TTS request: language={language}, text_length={len(text)}")
        
        # Generate speech with OpenAI's GPT-4o Mini TTS
        response = openai.audio.speech.create(
            model="gpt-4o-mini-tts",  # Use the GPT-4o Mini TTS model
            voice="alloy",  # Use alloy voice for all languages
            input=text
        )
        
        # Save to the output file
        with open(output_file_path, 'wb') as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
        
        return True
    
    def tts_with_google(self, text, language, output_file_path):
        """Helper function to generate speech using Google's TTS service"""
        # Check if Gemini is available
        if not self.gemini_available:
            print("Google Generative AI module is not available. Cannot use Google for TTS.")
            return False
        
        try:
            # For now, we'll use a fallback to OpenAI TTS
            # This is a placeholder for the actual Google TTS implementation
            print(f"Google TTS request: language={language}, text_length={len(text)}")
            
            # In a real implementation, we would use Google Cloud Text-to-Speech API
            # For now, we'll fallback to OpenAI TTS
            print(f"Falling back to OpenAI TTS as Google TTS is not fully implemented yet")
            
            # Use OpenAI TTS instead
            return self.tts_with_openai(text, language, output_file_path)
            
        except Exception as e:
            print(f"Error in Google TTS: {str(e)}")
            return False
