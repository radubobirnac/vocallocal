"""
Translation service for VocalLocal
"""
import time
import openai
from services.base_service import BaseService
from utils.language_utils import get_language_name_from_code
from config import Config

class TranslationService(BaseService):
    """Service for handling text translation"""

    def __init__(self):
        """Initialize the translation service"""
        super().__init__()
        self.gemini_available = False

        # Try to import Google Generative AI
        try:
            import google.generativeai as genai
            self.genai = genai
            self.gemini_available = True
            print("Google Generative AI module loaded successfully for translation service")
        except ImportError as e:
            print(f"Google Generative AI module not available for translation service: {str(e)}")
            self.genai = None

    def translate(self, text, target_language, model="gemini-2.0-flash-lite"):
        """
        Translate text to the target language using the specified model

        Args:
            text: Text to translate
            target_language: Target language code
            model: Model to use (gemini-2.0-flash-lite, gpt-4.1-mini, etc.)

        Returns:
            Translated text
        """
        # Start timing for metrics
        start_time = time.time()

        # Get language name for better prompting
        language_name = get_language_name_from_code(target_language)

        # Create translation prompt
        translation_prompt = f"You are a professional translator. Translate the text into {language_name} (language code: {target_language}). Only respond with the translation, nothing else."

        # Handle model name formatting - Updated November 2025 with current working models
        if model in ['gemini-2.5-flash-preview-04-17', 'gemini-2.5-flash-preview-05-20']:
            # Deprecated preview models - map to stable 2.5 Flash
            model = "models/gemini-2.5-flash"
        elif model == 'gemini-2.5-flash-preview' or model == 'gemini-2.5-flash':
            # Use stable Gemini 2.5 Flash
            model = "models/gemini-2.5-flash"
        elif 'gemini-2.5-pro' in model:
            # Use stable Gemini 2.5 Pro
            model = "models/gemini-2.5-pro"
        elif model == 'gemini-2.0-flash-lite':
            # Keep 2.0 Flash Lite as it's still available
            model = "models/gemini-2.0-flash-lite"

        try:
            # First attempt with the selected model
            if (model.startswith('gemini') or model == 'gemini-2.0-flash-lite') and self.gemini_available:
                try:
                    translated_text = self.translate_with_gemini(text, target_language, translation_prompt, model)

                    # Calculate response time for metrics
                    response_time = time.time() - start_time

                    # Track metrics
                    self.track_metrics("translation", model, 0, len(translated_text), response_time, True)

                    return translated_text
                except Exception as gemini_error:
                    # Log the error
                    print(f"Gemini translation failed: {str(gemini_error)}")
                    print(f"Falling back to OpenAI for translation")

                    # Track the error in metrics
                    response_time = time.time() - start_time
                    self.track_metrics("translation", model, 0, 0, response_time, False)

                    # Fallback to OpenAI
                    return self.translate_with_openai(text, target_language, translation_prompt)
            else:
                # Use OpenAI for translation
                return self.translate_with_openai(text, target_language, translation_prompt, model)
        except Exception as e:
            # Track the error in metrics
            response_time = time.time() - start_time
            self.track_metrics("translation", model, 0, 0, response_time, False)

            # Re-raise the exception
            raise e

    def translate_with_gemini(self, text, target_language, prompt, translation_model='gemini-2.0-flash-lite'):
        """Helper function to translate text using Google Gemini"""
        # Start timing for metrics
        start_time = time.time()

        # Get language name for better logging
        language_name = get_language_name_from_code(target_language)

        # Log translation request details
        print(f"Gemini translation request:")
        print(f"  - Target language: {language_name} (code: {target_language})")
        print(f"  - Text length: {len(text)} characters")
        print(f"  - Prompt: {prompt}")
        print(f"  - Requested model: {translation_model}")

        # Handle legacy model name
        if translation_model == 'gemini':
            translation_model = 'gemini-2.0-flash-lite'

        # Handle model name formatting
        model_name = translation_model
        if model_name in ['gemini-2.5-flash-preview-04-17', 'gemini-2.5-flash-preview-05-20']:
            # Deprecated preview models - map to stable 2.5 Flash
            model_name = "models/gemini-2.5-flash"
        elif model_name == 'gemini-2.5-flash-preview' or model_name == 'gemini-2.5-flash':
            # Use stable Gemini 2.5 Flash
            model_name = "models/gemini-2.5-flash"
        elif 'gemini-2.5-pro' in model_name:
            # Use stable Gemini 2.5 Pro
            model_name = "models/gemini-2.5-pro"
        elif model_name == 'gemini-2.0-flash-lite':
            # Keep 2.0 Flash Lite as it's still available
            model_name = "models/gemini-2.0-flash-lite"
        elif not model_name.startswith('models/'):
            model_name = f"models/{model_name}"

        print(f"  - Mapped model: {model_name}")

        # Create the model
        model = self.genai.GenerativeModel(model_name)

        # Create the full prompt
        full_prompt = f"{prompt}\n\nText to translate: {text}"

        # Generate the translation
        response = model.generate_content(full_prompt)

        # Get the translated text
        translated_text = response.text.strip()

        # Log translation result
        print(f"Gemini translation completed:")
        print(f"  - Result length: {len(translated_text)} characters")
        print(f"  - First 100 chars: {translated_text[:100]}...")

        return translated_text

    def translate_with_openai(self, text, target_language, prompt, display_model='gpt-4.1-mini'):
        """Helper function to translate text using OpenAI"""
        # Start timing for metrics
        start_time = time.time()

        # Get language name for better logging
        language_name = get_language_name_from_code(target_language)

        # Log translation request details
        print(f"OpenAI translation request:")
        print(f"  - Target language: {language_name} (code: {target_language})")
        print(f"  - Text length: {len(text)} characters")
        print(f"  - Prompt: {prompt}")
        print(f"  - Model: {display_model}")

        # Prepare messages
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ]

        # Make the API call
        response = openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=5000
        )

        # Get the response text
        translated_text = response.choices[0].message.content

        # Log translation result
        print(f"OpenAI translation completed:")
        print(f"  - Result length: {len(translated_text)} characters")
        print(f"  - First 100 chars: {translated_text[:100]}...")

        # Calculate response time for metrics
        response_time = time.time() - start_time

        # Track metrics
        self.track_metrics("translation", display_model, 0, len(translated_text), response_time, True)

        return translated_text

# Create a global instance for backward compatibility
translation_service = TranslationService()

def translate_text(text, target_language, model="gemini-2.0-flash-lite"):
    """Global function for backward compatibility"""
    return translation_service.translate(text, target_language, model)