"""
Text-to-Speech Service

This module provides a service for converting text to speech using various providers
(OpenAI, Google) with automatic fallback and retry logic.
"""

import os
import time
import tempfile
from typing import Any, Dict, List, Optional, Union, BinaryIO

import openai
from dotenv import load_dotenv

from .base_service import (
    BaseService, ServiceError, ProviderError, ValidationError,
    ConfigurationError, AuthenticationError, RateLimitError, ResourceError
)

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Load environment variables
load_dotenv()

class TTSError(ServiceError):
    """Exception raised when text-to-speech conversion fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details['error_type'] = 'tts_error'
        super().__init__(message, details)

class TTSService(BaseService):
    """Service for converting text to speech"""

    def __init__(self):
        """Initialize the TTS service"""
        super().__init__("tts_service")

        # Initialize API keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        # Configure OpenAI
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.providers = ["openai", "gpt4o-mini"]
        else:
            self.logger.warning("OpenAI API key not found. OpenAI TTS will not be available.")
            self.providers = []

        # Configure Gemini if available
        if GEMINI_AVAILABLE and self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            if "google" not in self.providers:
                self.providers.append("google")
            # Add Gemini 2.5 Flash Preview TTS provider
            if "gemini-2.5-flash-tts" not in self.providers:
                self.providers.append("gemini-2.5-flash-tts")
        elif GEMINI_AVAILABLE:
            self.logger.warning("Gemini API key not found. Google TTS will not be available.")

    def synthesize(self, text: str,
                  language: str = "en",
                  provider: str = "auto",
                  model: Optional[str] = None,
                  voice: Optional[str] = None) -> bytes:
        """
        Convert text to speech.

        Args:
            text: Text to convert to speech
            language: Language code (e.g., "en", "es", "fr")
            provider: Provider to use ("openai", "gpt4o-mini", "google", or "auto" for automatic selection)
            model: Specific model to use (provider-dependent)
            voice: Voice to use (provider-dependent)

        Returns:
            Audio data as bytes

        Raises:
            ValidationError: If input validation fails
            ConfigurationError: If no providers are available
            ProviderError: If provider-specific errors occur
            TTSError: If text-to-speech conversion fails
        """
        # Validate inputs
        if not text or not text.strip():
            raise ValidationError("Text cannot be empty", {
                "text_length": len(text) if text else 0,
                "language": language
            })

        # Ensure we have at least one provider
        if not self.providers:
            raise ConfigurationError("No TTS providers available. Please configure API keys.", {
                "available_providers": self.providers,
                "requested_provider": provider
            })

        # Determine provider order based on preference
        provider_order = self._get_provider_order(provider)

        # Try each provider in order
        last_error = None
        for current_provider in provider_order:
            try:
                self.logger.info(f"Attempting TTS with {current_provider}")

                if current_provider == "openai":
                    return self._synthesize_with_openai(text, language, voice, model)
                elif current_provider == "gpt4o-mini":
                    return self._synthesize_with_gpt4o_mini(text, language)
                elif current_provider == "gemini-2.5-flash-tts":
                    return self._synthesize_with_gemini_2_5_flash_tts(text, language)
                elif current_provider == "google":
                    return self._synthesize_with_google(text, language)
                else:
                    raise ValidationError(f"Unknown provider: {current_provider}", {
                        "provider": current_provider,
                        "available_providers": self.providers
                    })

            except Exception as e:
                self.logger.warning(f"TTS with {current_provider} failed: {str(e)}")

                # Store the error for potential re-raising
                if isinstance(e, ServiceError):
                    last_error = e
                else:
                    # Convert generic exceptions to provider errors
                    last_error = ProviderError(
                        current_provider,
                        str(e),
                        {
                            "text_length": len(text),
                            "language": language,
                            "model": model,
                            "voice": voice
                        }
                    )

                # Record fallback metric
                self._record_metric("synthesize", "fallback", 1)

        # If we get here, all providers failed
        if last_error:
            raise last_error
        else:
            raise TTSError("All TTS providers failed", {
                "attempted_providers": provider_order
            })

    def _get_provider_order(self, provider: str) -> List[str]:
        """
        Determine the order of providers to try based on preference.

        Args:
            provider: Requested provider or "auto" for automatic selection

        Returns:
            List of providers to try in order
        """
        if provider == "auto":
            # Default order: gemini-2.5-flash-tts, gpt4o-mini, openai, google
            return [p for p in ["gemini-2.5-flash-tts", "gpt4o-mini", "openai", "google"] if p in self.providers]
        elif provider in self.providers:
            # If the requested provider is available, use it first, then try others
            others = [p for p in self.providers if p != provider]
            return [provider] + others
        else:
            # If the requested provider is not available, use the default order
            self.logger.warning(f"Requested provider {provider} is not available. Using default order.")
            return [p for p in ["gemini-2.5-flash-tts", "gpt4o-mini", "openai", "google"] if p in self.providers]

    def _synthesize_with_openai(self, text: str, language: str, voice: Optional[str] = None, model: Optional[str] = None) -> bytes:
        """
        Convert text to speech using OpenAI.

        Args:
            text: Text to convert to speech
            language: Language code (e.g., "en", "es", "fr")
            voice: Voice to use (default: "onyx")
            model: Model to use (default: "tts-1")

        Returns:
            Audio data as bytes

        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            ProviderError: If other OpenAI TTS errors occur
        """
        # Use default model and voice if not specified
        model = model or "tts-1"
        voice = voice or "onyx"

        try:
            # Track timing
            start_time = time.time()

            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file_path = temp_file.name

            # Generate speech with OpenAI
            response = self.with_retry(
                lambda: openai.audio.speech.create(
                    model=model,
                    voice=voice,
                    input=text
                ),
                operation="openai_tts"
            )

            # Save to the temporary file
            audio_data = b''
            with open(temp_file_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
                    audio_data += chunk

            # Clean up the temporary file
            os.remove(temp_file_path)

            # Record metrics
            elapsed = time.time() - start_time
            char_count = len(text)
            self._record_metric("openai_tts", "time", elapsed)
            self._record_metric("openai_tts", "chars", char_count)
            self._record_metric("openai_tts", "success", 1)

            return audio_data

        except Exception as e:
            # Record error metrics
            self._record_metric("openai_tts", "error", 1)

            # Get the error message
            error_msg = str(e).lower()

            # Check for specific error types
            if "authentication" in error_msg or "api key" in error_msg or "invalid api key" in error_msg:
                raise AuthenticationError("openai",
                    "Invalid API key. Please check your OpenAI API key in settings.",
                    {
                        "model": model,
                        "voice": voice,
                        "language": language,
                        "help_url": "https://platform.openai.com/account/api-keys"
                    }
                )
            elif "rate limit" in error_msg or "too many requests" in error_msg:
                raise RateLimitError("openai",
                    "Rate limit exceeded. Please try again in a few minutes.",
                    {
                        "model": model,
                        "voice": voice,
                        "language": language
                    }
                )
            elif "file" in error_msg and ("not found" in error_msg or "cannot access" in error_msg):
                raise ResourceError(
                    f"Could not access temporary file for OpenAI TTS",
                    {
                        "model": model,
                        "voice": voice,
                        "language": language
                    }
                )
            else:
                # Generic provider error for other cases
                raise ProviderError("openai", str(e), {
                    "model": model,
                    "voice": voice,
                    "language": language,
                    "error_type": type(e).__name__
                })

    def _synthesize_with_gpt4o_mini(self, text: str, language: str) -> bytes:
        """
        Convert text to speech using OpenAI's GPT-4o Mini TTS.

        Args:
            text: Text to convert to speech
            language: Language code (e.g., "en", "es", "fr")

        Returns:
            Audio data as bytes

        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            ProviderError: If other GPT-4o Mini TTS errors occur
        """
        try:
            # Track timing
            start_time = time.time()

            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file_path = temp_file.name

            # Generate speech with OpenAI's GPT-4o Mini TTS
            response = self.with_retry(
                lambda: openai.audio.speech.create(
                    model="gpt-4o-mini-tts",
                    voice="alloy",  # Use alloy voice for all languages
                    input=text
                ),
                operation="gpt4o_mini_tts"
            )

            # Save to the temporary file
            audio_data = b''
            with open(temp_file_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
                    audio_data += chunk

            # Clean up the temporary file
            os.remove(temp_file_path)

            # Record metrics
            elapsed = time.time() - start_time
            char_count = len(text)
            self._record_metric("gpt4o_mini_tts", "time", elapsed)
            self._record_metric("gpt4o_mini_tts", "chars", char_count)
            self._record_metric("gpt4o_mini_tts", "success", 1)

            return audio_data

        except Exception as e:
            # Record error metrics
            self._record_metric("gpt4o_mini_tts", "error", 1)

            # Get the error message
            error_msg = str(e).lower()

            # Check for specific error types
            if "authentication" in error_msg or "api key" in error_msg or "invalid api key" in error_msg:
                raise AuthenticationError("gpt4o-mini",
                    "Invalid API key. Please check your OpenAI API key in settings.",
                    {
                        "model": "gpt-4o-mini-tts",
                        "voice": "alloy",
                        "language": language,
                        "help_url": "https://platform.openai.com/account/api-keys"
                    }
                )
            elif "rate limit" in error_msg or "too many requests" in error_msg:
                raise RateLimitError("gpt4o-mini",
                    "Rate limit exceeded. Please try again in a few minutes.",
                    {
                        "model": "gpt-4o-mini-tts",
                        "voice": "alloy",
                        "language": language
                    }
                )
            elif "model" in error_msg and "not found" in error_msg:
                raise ProviderError("gpt4o-mini",
                    "The GPT-4o Mini TTS model is not available. This may be a temporary issue.",
                    {
                        "model": "gpt-4o-mini-tts",
                        "voice": "alloy",
                        "language": language
                    }
                )
            elif "file" in error_msg and ("not found" in error_msg or "cannot access" in error_msg):
                raise ResourceError(
                    f"Could not access temporary file for GPT-4o Mini TTS",
                    {
                        "model": "gpt-4o-mini-tts",
                        "voice": "alloy",
                        "language": language
                    }
                )
            else:
                # Generic provider error for other cases
                raise ProviderError("gpt4o-mini", str(e), {
                    "model": "gpt-4o-mini-tts",
                    "voice": "alloy",
                    "language": language,
                    "error_type": type(e).__name__
                })

    def _synthesize_with_gemini_2_5_flash_tts(self, text: str, language: str) -> bytes:
        """
        Convert text to speech using Gemini 2.5 Flash Preview TTS.

        Args:
            text: Text to convert to speech
            language: Language code (e.g., "en", "es", "fr")

        Returns:
            Audio data as bytes

        Raises:
            ConfigurationError: If Google Generative AI module is not available
            AuthenticationError: If API key is invalid
            ProviderError: If other Gemini TTS errors occur
        """
        # Check if Gemini is available
        if not GEMINI_AVAILABLE:
            raise ConfigurationError(
                "Google Generative AI module is not available. Please install it with 'pip install google-generativeai'.",
                {"provider": "gemini-2.5-flash-tts", "language": language}
            )

        # Check if API key is configured
        if not self.gemini_api_key:
            raise AuthenticationError(
                "gemini-2.5-flash-tts",
                "Gemini API key is not configured. Please add your Gemini API key to the .env file.",
                {"language": language, "help_url": "https://ai.google.dev/tutorials/setup"}
            )

        try:
            # Track timing
            start_time = time.time()

            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file_path = temp_file.name

            # Configure the Gemini 2.5 Flash TTS model
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash-preview-tts",
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 0,
                }
            )

            # Generate speech with Gemini 2.5 Flash TTS
            # Add instructions for voice characteristics directly in the prompt
            prompt = f"Please speak this in a male, enthusiastic voice, slightly faster than normal: {text}"

            # Configure the response to be audio-only
            generation_config = {
                "temperature": 0.2,
                "top_p": 0.95,
                "top_k": 0,
                "response_mime_type": "audio/mp3"  # Request audio-only response
            }

            response = self.with_retry(
                lambda: model.generate_content(
                    prompt,
                    stream=False,
                    generation_config=generation_config
                ),
                operation="gemini_2_5_flash_tts"
            )

            # Get the audio data from the response
            audio_data = response.audio.data

            # Save to the temporary file for debugging if needed
            with open(temp_file_path, 'wb') as f:
                f.write(audio_data)

            # Clean up the temporary file
            os.remove(temp_file_path)

            # Record metrics
            elapsed = time.time() - start_time
            char_count = len(text)
            self._record_metric("gemini_2_5_flash_tts", "time", elapsed)
            self._record_metric("gemini_2_5_flash_tts", "chars", char_count)
            self._record_metric("gemini_2_5_flash_tts", "success", 1)

            return audio_data

        except Exception as e:
            # Record error metrics
            self._record_metric("gemini_2_5_flash_tts", "error", 1)

            # Get the error message
            error_msg = str(e).lower()

            # Check for specific error types
            if "authentication" in error_msg or "api key" in error_msg or "invalid api key" in error_msg:
                raise AuthenticationError(
                    "gemini-2.5-flash-tts",
                    "Invalid API key. Please check your Gemini API key in settings.",
                    {"language": language, "help_url": "https://ai.google.dev/tutorials/setup"}
                )
            elif "rate limit" in error_msg or "quota" in error_msg or "exceeded your current quota" in error_msg:
                raise RateLimitError(
                    "gemini-2.5-flash-tts",
                    "Rate limit or quota exceeded. Please try again later.",
                    {"language": language}
                )
            elif "model" in error_msg and "not found" in error_msg:
                raise ProviderError(
                    "gemini-2.5-flash-tts",
                    "The Gemini 2.5 Flash TTS model is not available. This may be a temporary issue.",
                    {"language": language}
                )
            elif "not supported" in error_msg or "unsupported" in error_msg or "response modalities" in error_msg:
                # This could be a model limitation or API version issue
                raise ProviderError(
                    "gemini-2.5-flash-tts",
                    f"The Gemini 2.5 Flash TTS model may not support the requested operation. This could be due to API limitations or language support issues.",
                    {"language": language}
                )
            else:
                # Generic provider error for other cases
                raise ProviderError(
                    "gemini-2.5-flash-tts",
                    str(e),
                    {
                        "language": language,
                        "error_type": type(e).__name__
                    }
                )

    def _synthesize_with_google(self, text: str, language: str) -> bytes:
        """
        Convert text to speech using Google.

        Args:
            text: Text to convert to speech
            language: Language code (e.g., "en", "es", "fr")

        Returns:
            Audio data as bytes

        Raises:
            ConfigurationError: If Google Generative AI module is not available
            AuthenticationError: If API key is invalid
            ProviderError: If other Google TTS errors occur
        """
        # Check if Gemini is available
        if not GEMINI_AVAILABLE:
            raise ConfigurationError(
                "Google Generative AI module is not available. Please install it with 'pip install google-generativeai'.",
                {"provider": "google", "language": language}
            )

        # Check if API key is configured
        if not self.gemini_api_key:
            raise AuthenticationError(
                "google",
                "Google API key is not configured. Please add your Gemini API key to the .env file.",
                {"language": language, "help_url": "https://ai.google.dev/tutorials/setup"}
            )

        try:
            # For now, this is a placeholder for the actual Google TTS implementation
            # In a real implementation, we would use Google Cloud Text-to-Speech API
            self.logger.info(f"Google TTS request: language={language}, text_length={len(text)}")
            self.logger.info("Falling back to GPT-4o Mini TTS as Google TTS is not fully implemented yet")

            # Record metrics for the attempt
            self._record_metric("google_tts", "attempt", 1)

            # Use GPT-4o Mini TTS instead (as preferred fallback)
            return self._synthesize_with_gpt4o_mini(text, language)

        except Exception as e:
            # Record error metrics
            self._record_metric("google_tts", "error", 1)

            # Get the error message
            error_msg = str(e).lower()

            # Check for specific error types
            if "authentication" in error_msg or "api key" in error_msg or "invalid api key" in error_msg:
                raise AuthenticationError(
                    "google",
                    "Invalid API key. Please check your Google API key in settings.",
                    {"language": language, "help_url": "https://ai.google.dev/tutorials/setup"}
                )
            elif "rate limit" in error_msg or "quota" in error_msg:
                raise RateLimitError(
                    "google",
                    "Rate limit or quota exceeded. Please try again later.",
                    {"language": language}
                )
            elif "not supported" in error_msg or "unsupported" in error_msg:
                raise ProviderError(
                    "google",
                    f"The language '{language}' may not be supported by Google TTS.",
                    {"language": language}
                )
            else:
                # Generic provider error for other cases
                raise ProviderError(
                    "google",
                    str(e),
                    {
                        "language": language,
                        "error_type": type(e).__name__
                    }
                )
