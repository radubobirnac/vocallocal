"""
Transcription Service

This module provides a service for transcribing audio files using various providers
(OpenAI, Gemini) with automatic fallback and retry logic.
"""

import os
import io
import re
import time
import tempfile
from typing import Any, Dict, List, Optional, BinaryIO, Union, Tuple

import openai
from dotenv import load_dotenv

from .base_service import BaseService, ServiceError, ProviderError

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Load environment variables
load_dotenv()

class TranscriptionError(ServiceError):
    """Exception raised for errors in the transcription process"""
    pass

class TranscriptionService(BaseService):
    """Service for transcribing audio files"""

    def __init__(self):
        """Initialize the transcription service"""
        super().__init__("transcription_service")

        # Initialize API keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        # Configure OpenAI
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        else:
            self.logger.warning("OpenAI API key not found. OpenAI transcription will not be available.")

        # Configure Gemini if available
        if GEMINI_AVAILABLE and self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
        elif GEMINI_AVAILABLE:
            self.logger.warning("Gemini API key not found. Gemini transcription will not be available.")

        # Set default models
        self.default_openai_model = "gpt-4o-mini-transcribe"
        self.default_gemini_model = "gemini-2.0-flash-lite"

        # Track available providers
        self.providers = []
        if self.openai_api_key:
            self.providers.append("openai")
        if GEMINI_AVAILABLE and self.gemini_api_key:
            self.providers.append("gemini")

        if not self.providers:
            self.logger.error("No transcription providers available. Please configure API keys.")

    def _clean_gemini_transcription(self, text):
        """
        Clean up Gemini transcription by removing timestamps and bracketed artifacts.

        This method removes:
        - Timestamps in various formats (e.g., [00:00:00], (0:00), 00:00:00, etc.)
        - Bracketed artifacts at the end
        - Common timestamp patterns that Gemini models might add

        Args:
            text (str): The transcription text from Gemini

        Returns:
            str: Cleaned transcription text
        """
        original_text = text

        # Remove timestamps in various formats
        # Pattern 1: [HH:MM:SS] or [MM:SS] or [H:MM:SS]
        text = re.sub(r'\[\d{1,2}:\d{2}(?::\d{2})?\]', '', text)

        # Pattern 2: (HH:MM:SS) or (MM:SS) or (H:MM:SS)
        text = re.sub(r'\(\d{1,2}:\d{2}(?::\d{2})?\)', '', text)

        # Pattern 3: HH:MM:SS or MM:SS at the beginning of lines or standalone
        text = re.sub(r'(?:^|\s)\d{1,2}:\d{2}(?::\d{2})?\s*[-–—]?\s*', ' ', text, flags=re.MULTILINE)

        # Pattern 4: Timestamps with milliseconds [HH:MM:SS.mmm]
        text = re.sub(r'\[\d{1,2}:\d{2}:\d{2}\.\d{1,3}\]', '', text)

        # Pattern 5: Speaker labels with timestamps like "Speaker 1 [00:00:00]:"
        text = re.sub(r'Speaker\s+\d+\s*\[\d{1,2}:\d{2}(?::\d{2})?\]\s*:?\s*', '', text, flags=re.IGNORECASE)

        # Pattern 6: Time ranges like [00:00 - 00:30] or [0:00-0:30]
        text = re.sub(r'\[\d{1,2}:\d{2}(?::\d{2})?\s*[-–—]\s*\d{1,2}:\d{2}(?::\d{2})?\]', '', text)

        # Pattern 7: Standalone timestamps at the beginning of lines
        text = re.sub(r'^[\s]*\d{1,2}:\d{2}(?::\d{2})?\s*', '', text, flags=re.MULTILINE)

        # Pattern 8: Remove any remaining bracketed content that looks like metadata
        text = re.sub(r'\[(?:MUSIC|SOUND|NOISE|SILENCE|APPLAUSE|LAUGHTER|INAUDIBLE|CROSSTALK)\]', '', text, flags=re.IGNORECASE)

        # Pattern 9: Remove bracketed artifacts at the end (original functionality)
        text = re.sub(r'\s*\[[^\]]+\]\s*$', '', text)

        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        text = re.sub(r'\n\s*\n', '\n', text)  # Remove empty lines
        text = text.strip()  # Remove leading/trailing whitespace

        # Log if we removed something
        if text != original_text:
            removed_content = len(original_text) - len(text)
            self.logger.info(f"Cleaned Gemini transcription: removed {removed_content} characters (timestamps/artifacts)")

            # Log a sample of what was removed for debugging (first 200 chars)
            if len(original_text) > 200:
                self.logger.debug(f"Original text sample: {original_text[:200]}...")
                self.logger.debug(f"Cleaned text sample: {text[:200]}...")

        return text

    def transcribe(self, audio_data: Union[bytes, BinaryIO],
                  language: str = "en",
                  provider: str = "auto",
                  model: Optional[str] = None) -> str:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Audio data as bytes or file-like object
            language: Language code (e.g., "en", "es", "fr")
            provider: Provider to use ("openai", "gemini", or "auto" for automatic selection)
            model: Specific model to use (provider-dependent)

        Returns:
            Transcribed text

        Raises:
            TranscriptionError: If transcription fails
        """
        # Ensure we have at least one provider
        if not self.providers:
            raise TranscriptionError("No transcription providers available. Please configure API keys.")

        # Convert file-like object to bytes if needed
        if hasattr(audio_data, 'read'):
            audio_data = audio_data.read()

        # Determine provider order based on preference
        provider_order = self._get_provider_order(provider)

        # Try each provider in order
        last_error = None
        for current_provider in provider_order:
            try:
                self.logger.info(f"Attempting transcription with {current_provider}")

                if current_provider == "openai":
                    return self._transcribe_with_openai(audio_data, language, model)
                elif current_provider == "gemini":
                    return self._transcribe_with_gemini(audio_data, language, model)
                else:
                    raise TranscriptionError(f"Unknown provider: {current_provider}")

            except Exception as e:
                self.logger.warning(f"Transcription with {current_provider} failed: {str(e)}")
                last_error = e
                self._record_metric("transcribe", "fallback", 1)

        # If we get here, all providers failed
        error_msg = f"All transcription providers failed. Last error: {str(last_error)}"
        self.logger.error(error_msg)
        raise TranscriptionError(error_msg)

    def _get_provider_order(self, preferred_provider: str) -> List[str]:
        """
        Determine the order in which to try providers.

        Args:
            preferred_provider: Preferred provider ("openai", "gemini", or "auto")

        Returns:
            List of providers in order of preference
        """
        if preferred_provider == "auto":
            # Default order: try Gemini first, then OpenAI
            return [p for p in ["gemini", "openai"] if p in self.providers]

        # If specific provider requested, try that first, then others
        if preferred_provider in self.providers:
            provider_order = [preferred_provider]
            provider_order.extend([p for p in self.providers if p != preferred_provider])
            return provider_order

        # If requested provider not available, use all available providers
        self.logger.warning(f"Requested provider '{preferred_provider}' not available. Using available providers.")
        return self.providers

    def _transcribe_with_openai(self, audio_data: bytes, language: str, model: Optional[str] = None) -> str:
        """
        Transcribe audio using OpenAI.

        Args:
            audio_data: Audio data as bytes
            language: Language code
            model: OpenAI model to use

        Returns:
            Transcribed text

        Raises:
            ProviderError: If OpenAI transcription fails
        """
        if not self.openai_api_key:
            raise ProviderError("openai", "OpenAI API key not configured")

        # Use specified model or default
        model = model or self.default_openai_model

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        try:
            # Track timing
            start_time = time.time()

            # Open the file and send to OpenAI
            with open(temp_file_path, 'rb') as audio_file:
                response = self.with_retry(
                    lambda: openai.audio.transcriptions.create(
                        model=model,
                        file=audio_file,
                        language=language if language != "auto" else None
                    ),
                    operation="openai_transcribe"
                )

            # Record metrics
            elapsed = time.time() - start_time
            self._record_metric("openai_transcribe", "time", elapsed)
            self._record_metric("openai_transcribe", "success", 1)

            return response.text

        except Exception as e:
            # Record error metrics
            self._record_metric("openai_transcribe", "error", 1)

            # Convert to our error type
            raise ProviderError("openai", str(e), {"model": model, "language": language})

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def _transcribe_with_gemini(self, audio_data: bytes, language: str, model: Optional[str] = None) -> str:
        """
        Transcribe audio using Google Gemini.

        Args:
            audio_data: Audio data as bytes
            language: Language code
            model: Gemini model to use

        Returns:
            Transcribed text

        Raises:
            ProviderError: If Gemini transcription fails
        """
        if not GEMINI_AVAILABLE:
            raise ProviderError("gemini", "Gemini API not available")

        if not self.gemini_api_key:
            raise ProviderError("gemini", "Gemini API key not configured")

        # Use specified model or default
        model_name = model or self.default_gemini_model

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        try:
            # Track timing
            start_time = time.time()

            # Configure the model
            generation_config = {
                "temperature": 0.2,
                "top_p": 0.95,
                "top_k": 0,
                "max_output_tokens": 8192,
            }

            # Handle model name formatting
            if not model_name.startswith("models/"):
                model_name = f"models/{model_name}"

            # Initialize the Gemini model
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config
            )

            # Prepare the prompt
            if language and language != "auto":
                prompt = f"Please transcribe the following audio file to text only. The language is {language}. Do not include timestamps, speaker labels, or any metadata - just provide the spoken text."
            else:
                prompt = "Please transcribe the following audio file to text only. Do not include timestamps, speaker labels, or any metadata - just provide the spoken text."

            # For Gemini, we need to encode the audio file as base64
            import base64
            with open(temp_file_path, 'rb') as audio_file:
                audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')

            # Create a multimodal content message with the audio
            response = self.with_retry(
                lambda: model.generate_content([
                    prompt,
                    {"mime_type": "audio/mp3", "data": audio_base64}
                ]),
                operation="gemini_transcribe"
            )

            # Get the transcription text
            transcription = response.text

            # Clean up any bracketed artifacts at the end
            cleaned_transcription = self._clean_gemini_transcription(transcription)

            # Record metrics
            elapsed = time.time() - start_time
            self._record_metric("gemini_transcribe", "time", elapsed)
            self._record_metric("gemini_transcribe", "success", 1)

            return cleaned_transcription

        except Exception as e:
            # Record error metrics
            self._record_metric("gemini_transcribe", "error", 1)

            # Convert to our error type
            raise ProviderError("gemini", str(e), {"model": model_name, "language": language})

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
