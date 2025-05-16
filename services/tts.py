"""
Text-to-Speech service for VocalLocal
"""
import os
import time
import tempfile
import logging
import openai
from services.base_service import BaseService
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TTSService(BaseService):
    """Service for handling text-to-speech conversion"""

    def __init__(self):
        """Initialize the TTS service"""
        super().__init__()
        self.logger = logging.getLogger("tts_service")
        self.gemini_available = False
        self.openai_available = False
        self.gpt4o_mini_available = False

        # Check OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.openai_available = True
            self.gpt4o_mini_available = True
            self.logger.info("OpenAI API key found. OpenAI TTS services available.")
        else:
            self.logger.warning("OpenAI API key not found. OpenAI TTS services will not be available.")

        # Try to import Google Generative AI
        try:
            import google.generativeai as genai
            self.genai = genai

            # Check Gemini API key
            self.gemini_api_key = os.getenv('GEMINI_API_KEY')
            if self.gemini_api_key:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_available = True
                self.logger.info("Google Generative AI module loaded successfully for TTS service")
            else:
                self.logger.warning("Gemini API key not found. Google TTS will not be available.")
        except ImportError as e:
            self.logger.warning(f"Google Generative AI module not available for TTS service: {str(e)}")
            self.genai = None

    def synthesize(self, text, language, model="gpt4o-mini"):
        """
        Convert text to speech using the specified model

        Args:
            text: Text to convert to speech
            language: Language code
            model: Model to use (gpt4o-mini, openai, google, auto)

        Returns:
            Path to the generated audio file
        """
        # Start timing for metrics
        start_time = time.time()
        temp_file_path = None

        try:
            # Validate input
            if not text or not text.strip():
                raise ValueError("Empty text provided")

            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file_path = temp_file.name

            self.logger.info(f"TTS request: model={model}, language={language}, text_length={len(text)}")

            # Determine provider order based on model selection and availability
            provider_order = []

            if model == "auto":
                # Auto mode: try GPT-4o Mini first, then OpenAI, then Google
                if self.gpt4o_mini_available:
                    provider_order.append("gpt4o-mini")
                if self.openai_available:
                    provider_order.append("openai")
                if self.gemini_available:
                    provider_order.append("google")
            elif model == "gpt4o-mini":
                # GPT-4o Mini mode: try GPT-4o Mini first, then OpenAI as fallback
                if self.gpt4o_mini_available:
                    provider_order.append("gpt4o-mini")
                if self.openai_available:
                    provider_order.append("openai")
            elif model == "openai":
                # OpenAI mode: use only OpenAI
                if self.openai_available:
                    provider_order.append("openai")
            elif model == "google":
                # Google mode: use only Google
                if self.gemini_available:
                    provider_order.append("google")
            else:
                # Unknown model: use auto mode
                self.logger.warning(f"Unknown model: {model}. Using auto mode.")
                if self.gpt4o_mini_available:
                    provider_order.append("gpt4o-mini")
                if self.openai_available:
                    provider_order.append("openai")
                if self.gemini_available:
                    provider_order.append("google")

            # If no providers are available, raise an error
            if not provider_order:
                raise RuntimeError("No TTS providers are available. Please check your API keys.")

            # Try each provider in order
            success = False
            model_used = None
            last_error = None

            for provider in provider_order:
                try:
                    self.logger.info(f"Attempting TTS with {provider}")

                    if provider == "gpt4o-mini":
                        self.tts_with_gpt4o_mini(text, language, temp_file_path)
                    elif provider == "openai":
                        self.tts_with_openai(text, language, temp_file_path)
                    elif provider == "google":
                        self.tts_with_google(text, language, temp_file_path)

                    # If we get here, the TTS was successful
                    success = True
                    model_used = provider
                    break

                except Exception as e:
                    # Log the error
                    self.logger.error(f"{provider} TTS error: {str(e)}")
                    last_error = e

                    # Continue to the next provider
                    continue

            # If all providers failed, raise the last error
            if not success:
                # Clean up the temporary file
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    self.logger.info(f"Removed temporary file: {temp_file_path}")

                # Raise the last error
                if last_error:
                    raise last_error
                else:
                    raise RuntimeError("All TTS providers failed")

            # Calculate performance metrics
            end_time = time.time()
            tts_time = end_time - start_time
            char_count = len(text)

            # Track metrics
            self.track_metrics("tts", model_used, char_count // 4, char_count, tts_time, success)

            self.logger.info(f"TTS successful with {model_used}. Output saved to {temp_file_path}")
            return temp_file_path

        except Exception as e:
            # Track the error in metrics
            response_time = time.time() - start_time
            self.track_metrics("tts", model, 0, 0, response_time, False)

            # Clean up the temporary file if it exists
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    self.logger.info(f"Removed temporary file: {temp_file_path}")
                except Exception as cleanup_error:
                    self.logger.warning(f"Failed to remove temporary file: {str(cleanup_error)}")

            # Re-raise the exception with more context
            self.logger.error(f"TTS failed: {str(e)}")
            raise RuntimeError(f"Text-to-speech conversion failed: {str(e)}") from e

    def tts_with_openai(self, text, language, output_file_path):
        """
        Helper function to generate speech using OpenAI's TTS service

        Args:
            text: Text to convert to speech
            language: Language code
            output_file_path: Path to save the output audio file

        Returns:
            True if successful, raises an exception otherwise

        Raises:
            RuntimeError: If the TTS operation fails
        """
        # Use onyx voice for all languages
        voice = 'onyx'

        # Check if OpenAI is available
        if not self.openai_available:
            raise RuntimeError("OpenAI API key is not configured. Cannot use OpenAI for TTS.")

        try:
            # Log request for debugging
            self.logger.info(f"OpenAI TTS request: language={language}, voice={voice}, text_length={len(text)}")

            # Generate speech with OpenAI
            start_time = time.time()
            response = openai.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            elapsed_time = time.time() - start_time
            self.logger.info(f"OpenAI TTS API call completed in {elapsed_time:.2f} seconds")

            # Save to the output file
            total_bytes = 0
            with open(output_file_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
                    total_bytes += len(chunk)

            self.logger.info(f"OpenAI TTS successful: {total_bytes} bytes written to {output_file_path}")
            return True

        except Exception as e:
            self.logger.error(f"OpenAI TTS error: {str(e)}")
            raise RuntimeError(f"OpenAI TTS failed: {str(e)}") from e

    def tts_with_gpt4o_mini(self, text, language, output_file_path):
        """
        Helper function to generate speech using OpenAI's GPT-4o Mini TTS service

        Args:
            text: Text to convert to speech
            language: Language code
            output_file_path: Path to save the output audio file

        Returns:
            True if successful, raises an exception otherwise

        Raises:
            RuntimeError: If the TTS operation fails
        """
        # Check if GPT-4o Mini is available
        if not self.gpt4o_mini_available:
            raise RuntimeError("OpenAI API key is not configured. Cannot use GPT-4o Mini for TTS.")

        try:
            # Log request for debugging
            self.logger.info(f"GPT-4o Mini TTS request: language={language}, text_length={len(text)}")

            # Generate speech with OpenAI's GPT-4o Mini TTS
            start_time = time.time()
            response = openai.audio.speech.create(
                model="gpt-4o-mini-tts",  # Use the GPT-4o Mini TTS model
                voice="alloy",  # Use alloy voice for all languages
                input=text
            )
            elapsed_time = time.time() - start_time
            self.logger.info(f"GPT-4o Mini TTS API call completed in {elapsed_time:.2f} seconds")

            # Save to the output file
            total_bytes = 0
            with open(output_file_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
                    total_bytes += len(chunk)

            self.logger.info(f"GPT-4o Mini TTS successful: {total_bytes} bytes written to {output_file_path}")
            return True

        except Exception as e:
            self.logger.error(f"GPT-4o Mini TTS error: {str(e)}")
            raise RuntimeError(f"GPT-4o Mini TTS failed: {str(e)}") from e

    def tts_with_google(self, text, language, output_file_path):
        """
        Helper function to generate speech using Google's TTS service

        Args:
            text: Text to convert to speech
            language: Language code
            output_file_path: Path to save the output audio file

        Returns:
            True if successful, raises an exception otherwise

        Raises:
            RuntimeError: If the TTS operation fails
        """
        # Check if Gemini is available
        if not self.gemini_available:
            raise RuntimeError("Google Generative AI module is not available. Cannot use Google for TTS.")

        try:
            # Log request for debugging
            self.logger.info(f"Google TTS request: language={language}, text_length={len(text)}")

            # For now, we'll use a fallback to OpenAI TTS
            # This is a placeholder for the actual Google TTS implementation
            self.logger.info("Falling back to OpenAI TTS as Google TTS is not fully implemented yet")

            # In a real implementation, we would use Google Cloud Text-to-Speech API
            # For now, we'll use OpenAI TTS instead
            if self.openai_available:
                return self.tts_with_openai(text, language, output_file_path)
            else:
                raise RuntimeError("OpenAI API key is not configured. Cannot use fallback for Google TTS.")

        except Exception as e:
            self.logger.error(f"Google TTS error: {str(e)}")
            raise RuntimeError(f"Google TTS failed: {str(e)}") from e
