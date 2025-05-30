"""
Translation Service

This module provides a service for translating text using various providers
(OpenAI, Gemini) with automatic fallback and retry logic.
"""

import os
import time
from typing import Any, Dict, List, Optional, Union

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

# Try to import token counter
try:
    from token_counter import count_openai_tokens, count_openai_chat_tokens, count_gemini_tokens
    TOKEN_COUNTER_AVAILABLE = True
except ImportError:
    TOKEN_COUNTER_AVAILABLE = False

class TranslationError(ServiceError):
    """Exception raised for errors in the translation process"""
    pass

class TranslationService(BaseService):
    """Service for translating text"""
    
    def __init__(self):
        """Initialize the translation service"""
        super().__init__("translation_service")
        
        # Initialize API keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Configure OpenAI
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        else:
            self.logger.warning("OpenAI API key not found. OpenAI translation will not be available.")
            
        # Configure Gemini if available
        if GEMINI_AVAILABLE and self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
        elif GEMINI_AVAILABLE:
            self.logger.warning("Gemini API key not found. Gemini translation will not be available.")
        
        # Set default models
        self.default_openai_model = "gpt-4.1-mini"
        self.default_gemini_model = "gemini-2.0-flash-lite"
        
        # Track available providers
        self.providers = []
        if self.openai_api_key:
            self.providers.append("openai")
        if GEMINI_AVAILABLE and self.gemini_api_key:
            self.providers.append("gemini")
            
        if not self.providers:
            self.logger.error("No translation providers available. Please configure API keys.")
    
    def translate(self, text: str, 
                 target_language: str,
                 source_language: str = "auto",
                 provider: str = "auto",
                 model: Optional[str] = None) -> str:
        """
        Translate text from one language to another.
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., "en", "es", "fr")
            source_language: Source language code or "auto" for auto-detection
            provider: Provider to use ("openai", "gemini", or "auto" for automatic selection)
            model: Specific model to use (provider-dependent)
            
        Returns:
            Translated text
            
        Raises:
            TranslationError: If translation fails
        """
        # Ensure we have at least one provider
        if not self.providers:
            raise TranslationError("No translation providers available. Please configure API keys.")
        
        # Determine provider order based on preference
        provider_order = self._get_provider_order(provider)
        
        # Create translation prompt
        language_name = self._get_language_name_from_code(target_language)
        prompt = f"You are a professional translator. Translate the text into {language_name} (language code: {target_language}). Only respond with the translation, nothing else."
        
        # Try each provider in order
        last_error = None
        for current_provider in provider_order:
            try:
                self.logger.info(f"Attempting translation with {current_provider}")
                
                if current_provider == "openai":
                    return self._translate_with_openai(text, target_language, prompt, model)
                elif current_provider == "gemini":
                    return self._translate_with_gemini(text, target_language, prompt, model)
                else:
                    raise TranslationError(f"Unknown provider: {current_provider}")
                    
            except Exception as e:
                self.logger.warning(f"Translation with {current_provider} failed: {str(e)}")
                last_error = e
                self._record_metric("translate", "fallback", 1)
                
        # If we get here, all providers failed
        error_msg = f"All translation providers failed. Last error: {str(last_error)}"
        self.logger.error(error_msg)
        raise TranslationError(error_msg)
    
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
    
    def _translate_with_openai(self, text: str, target_language: str, prompt: str, model: Optional[str] = None) -> str:
        """
        Translate text using OpenAI.
        
        Args:
            text: Text to translate
            target_language: Target language code
            prompt: Translation prompt
            model: OpenAI model to use
            
        Returns:
            Translated text
            
        Raises:
            ProviderError: If OpenAI translation fails
        """
        if not self.openai_api_key:
            raise ProviderError("openai", "OpenAI API key not configured")
        
        # Use specified model or default
        model_name = model or self.default_openai_model
        
        # Handle legacy model name
        if model_name == "openai":
            model_name = self.default_openai_model
            
        # Prepare messages
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ]
        
        # Count tokens for metrics
        if TOKEN_COUNTER_AVAILABLE:
            input_tokens = count_openai_chat_tokens(messages, model_name)
        else:
            input_tokens = len(text) // 4  # Rough estimate
        
        try:
            # Track timing
            start_time = time.time()
            
            # Make the API call
            response = self.with_retry(
                lambda: openai.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=5000
                ),
                operation="openai_translate"
            )
            
            # Get the translated text
            translated_text = response.choices[0].message.content
            
            # Count output tokens for metrics
            if TOKEN_COUNTER_AVAILABLE:
                output_tokens = count_openai_tokens(translated_text, model_name)
            else:
                output_tokens = len(translated_text) // 4  # Rough estimate
                
            # Record metrics
            elapsed = time.time() - start_time
            total_tokens = input_tokens + output_tokens
            self._record_metric("openai_translate", "time", elapsed)
            self._record_metric("openai_translate", "tokens", total_tokens)
            self._record_metric("openai_translate", "success", 1)
            
            return translated_text
            
        except Exception as e:
            # Record error metrics
            self._record_metric("openai_translate", "error", 1)
            
            # Convert to our error type
            raise ProviderError("openai", str(e), {"model": model_name, "target_language": target_language})
    
    def _translate_with_gemini(self, text: str, target_language: str, prompt: str, model: Optional[str] = None) -> str:
        """
        Translate text using Google Gemini.
        
        Args:
            text: Text to translate
            target_language: Target language code
            prompt: Translation prompt
            model: Gemini model to use
            
        Returns:
            Translated text
            
        Raises:
            ProviderError: If Gemini translation fails
        """
        if not GEMINI_AVAILABLE:
            raise ProviderError("gemini", "Gemini API not available")
            
        if not self.gemini_api_key:
            raise ProviderError("gemini", "Gemini API key not configured")
        
        # Use specified model or default
        model_name = model or self.default_gemini_model
        
        # Handle legacy model name
        if model_name == "gemini":
            model_name = self.default_gemini_model
            
        # Handle model name formatting
        if model_name == 'gemini-2.5-flash-preview-04-17':
            # This is the exact model ID used in the UI for "Gemini 2.5 Flash Preview"
            model_name = "models/gemini-2.5-flash-preview-04-17"
        elif 'gemini-2.5-flash' in model_name or model_name == 'gemini-2.5-flash':
            model_name = "models/gemini-2.5-flash-preview-04-17"
        elif 'gemini-2.5-pro' in model_name:
            model_name = "models/gemini-2.5-pro-preview-03-25"
        elif model_name == 'gemini-2.0-flash-lite' or model_name == 'gemini':
            model_name = "models/gemini-2.0-flash-lite"
        elif not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
            
        # Prepare input prompt
        input_prompt = f"{prompt}\n\nText to translate: {text}"
        
        # Count input tokens for metrics
        if TOKEN_COUNTER_AVAILABLE:
            input_tokens = count_gemini_tokens(input_prompt, model_name)
        else:
            input_tokens = len(input_prompt) // 3  # Rough estimate
        
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
            
            # Initialize the Gemini model
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config
            )
            
            # Create the prompt with system and user messages
            chat = model.start_chat(history=[])
            response = self.with_retry(
                lambda: chat.send_message(input_prompt),
                operation="gemini_translate"
            )
            
            # Get the translated text
            translated_text = response.text
            
            # Count output tokens for metrics
            if TOKEN_COUNTER_AVAILABLE:
                output_tokens = count_gemini_tokens(translated_text, model_name)
            else:
                output_tokens = len(translated_text) // 3  # Rough estimate
                
            # Record metrics
            elapsed = time.time() - start_time
            total_tokens = input_tokens + output_tokens
            self._record_metric("gemini_translate", "time", elapsed)
            self._record_metric("gemini_translate", "tokens", total_tokens)
            self._record_metric("gemini_translate", "success", 1)
            
            return translated_text
            
        except Exception as e:
            # Record error metrics
            self._record_metric("gemini_translate", "error", 1)
            
            # Convert to our error type
            raise ProviderError("gemini", str(e), {"model": model_name, "target_language": target_language})
    
    def _get_language_name_from_code(self, language_code: str) -> str:
        """
        Get the language name from a language code.
        
        Args:
            language_code: Language code (e.g., "en", "es", "fr")
            
        Returns:
            Language name
        """
        # Dictionary mapping language codes to language names
        language_map = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "nl": "Dutch",
            "ja": "Japanese",
            "zh": "Chinese",
            "ko": "Korean",
            "ru": "Russian",
            "ar": "Arabic",
            "hi": "Hindi",
            "tr": "Turkish",
            "sv": "Swedish",
            "pl": "Polish",
            "no": "Norwegian",
            "fi": "Finnish",
            "da": "Danish",
            "uk": "Ukrainian",
            "cs": "Czech",
            "ro": "Romanian",
            "hu": "Hungarian",
            "el": "Greek",
            "he": "Hebrew",
            "te": "Telugu",
            "th": "Thai",
            "vi": "Vietnamese",
            "id": "Indonesian",
            "ms": "Malay",
            "bg": "Bulgarian",
            "ur": "Urdu",
            "bn": "Bengali",
            "fa": "Persian",
            "sw": "Swahili",
            "ta": "Tamil",
            "pa": "Punjabi",
            "mr": "Marathi",
            "gu": "Gujarati",
            "kn": "Kannada",
            "ml": "Malayalam",
            "ne": "Nepali",
            "si": "Sinhala",
            "km": "Khmer",
            "lo": "Lao",
            "my": "Burmese",
            "ps": "Pashto",
            "am": "Amharic",
            "az": "Azerbaijani",
            "kk": "Kazakh",
            "sr": "Serbian",
            "tg": "Tajik",
            "uz": "Uzbek",
            "yo": "Yoruba",
            "zu": "Zulu",
            "wuu": "Wu Chinese",
            "ha": "Hausa",
            "yue": "Cantonese",
            "or": "Odia",
            "as": "Assamese",
            "nan": "Min Nan Chinese",
            "ku": "Kurdish",
            "ig": "Igbo"
        }
        
        # Return the language name if found, otherwise return the code
        return language_map.get(language_code, language_code)
