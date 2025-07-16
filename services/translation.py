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
            print(f"  - Converting legacy model name 'gemini' to '{translation_model}'")
        
        # Check if Gemini is available
        if not self.gemini_available:
            print("Google Generative AI module is not available. Falling back to OpenAI for translation.")
            return self.translate_with_openai(text, target_language, prompt)
        
        try:
            # Configure the model
            generation_config = {
                "temperature": 0.2,
                "top_p": 0.95,
                "top_k": 0,
                "max_output_tokens": 8192,
            }
            
            # Select the appropriate model based on the translation_model parameter
            model_name = "models/gemini-2.0-flash-lite"  # Default model
            display_model = translation_model  # For metrics tracking
            
            if translation_model == 'gemini-2.5-flash-preview-04-17':
                # 04-17 model is deprecated - automatically use 05-20 instead
                model_name = "models/gemini-2.5-flash-preview-05-20"
                display_model = "gemini-2.5-flash-preview-05-20"
                print(f"Using Gemini 2.5 Flash Preview 05-20 model for translation (04-17 is deprecated)")
            elif translation_model == 'gemini-2.5-flash-preview-05-20':
                # Direct mapping for the working 05-20 model
                model_name = "models/gemini-2.5-flash-preview-05-20"
                display_model = "gemini-2.5-flash-preview-05-20"
                print(f"Using Gemini 2.5 Flash Preview 05-20 model for translation")
            elif 'gemini-2.5-flash' in translation_model or translation_model == 'gemini-2.5-flash':
                # Use the working 05-20 model instead of deprecated 04-17
                model_name = "models/gemini-2.5-flash-preview-05-20"
                display_model = "gemini-2.5-flash-preview-05-20"
                print(f"Using Gemini 2.5 Flash Preview 05-20 model for translation")
            elif 'gemini-2.5-pro' in translation_model:
                # Use the full model name from the available models list
                model_name = "models/gemini-2.5-pro-preview-03-25"
                display_model = "gemini-2.5-pro"
                print(f"Using Gemini 2.5 Pro Preview model for translation")
            elif translation_model == 'gemini-2.0-flash-lite' or translation_model == 'gemini':
                model_name = "models/gemini-2.0-flash-lite"
                display_model = "gemini-2.0-flash-lite"
                print(f"Using Gemini 2.0 Flash Lite model for translation")
            else:
                # For any other model name, default to Gemini 2.0 Flash Lite
                model_name = "models/gemini-2.0-flash-lite"
                display_model = "gemini-2.0-flash-lite"
                print(f"Unknown model '{translation_model}', defaulting to Gemini 2.0 Flash Lite for translation")
            
            # Initialize the Gemini model
            model = self.genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config
            )
            
            # Create the prompt with system and user messages
            input_prompt = f"{prompt}\n\nText to translate: {text}"
            chat = model.start_chat(history=[])
            response = chat.send_message(input_prompt)
            
            translated_text = response.text
            
            # Log translation result
            print(f"Gemini translation completed:")
            print(f"  - Model used: {model_name}")
            print(f"  - Result length: {len(translated_text)} characters")
            print(f"  - First 100 chars: {translated_text[:100]}...")
            
            # Calculate response time for metrics
            response_time = time.time() - start_time
            
            # Track metrics
            self.track_metrics("translation", display_model, 0, len(translated_text), response_time, True)
            
            return translated_text
        except Exception as e:
            print(f"Error using Gemini API: {str(e)}. Falling back to OpenAI for translation.")
            print(f"  - Target language: {language_name} (code: {target_language})")
            print(f"  - Requested model: {translation_model}")
            
            # Calculate response time for metrics
            response_time = time.time() - start_time
            
            # Track metrics
            self.track_metrics("translation", display_model, 0, 0, response_time, False)
            
            return self.translate_with_openai(text, target_language, prompt)
    
    def translate_with_openai(self, text, target_language, prompt, translation_model='gpt-4.1-mini'):
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
        
        # Handle legacy model name
        display_model = translation_model
        if translation_model == 'openai':
            display_model = 'gpt-4.1-mini'
            print(f"  - Converting legacy model name 'openai' to '{display_model}'")
        
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
