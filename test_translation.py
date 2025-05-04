import os
import sys
from dotenv import load_dotenv
import openai
import google.generativeai as genai

# Load environment variables
load_dotenv()

# OpenAI API configuration
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    print("Warning: OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
    sys.exit(1)

# Google Gemini API configuration
gemini_api_key = os.getenv('Gemini_Api_Key') or os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    print("Warning: Gemini API key not found. Set Gemini_Api_Key or GEMINI_API_KEY environment variable.")
    sys.exit(1)
else:
    genai.configure(api_key=gemini_api_key)
    print("Gemini API configured successfully")

# Helper function to get language name from language code
def get_language_name_from_code(language_code):
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

def translate_with_openai(text, target_language):
    """Helper function to translate text using OpenAI"""
    # Get language name for better prompting
    language_name = get_language_name_from_code(target_language)

    # Create translation prompt
    prompt = f"You are a professional translator. Translate the text into {language_name} (language code: {target_language}). Only respond with the translation, nothing else."

    # Log translation request details
    print(f"OpenAI translation request:")
    print(f"  - Target language: {language_name} (code: {target_language})")
    print(f"  - Text length: {len(text)} characters")
    print(f"  - Prompt: {prompt}")

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

    return translated_text

def translate_with_gemini(text, target_language):
    """Helper function to translate text using Google Gemini"""
    # Get language name for better prompting
    language_name = get_language_name_from_code(target_language)

    # Create translation prompt
    prompt = f"You are a professional translator. Translate the text into {language_name} (language code: {target_language}). Only respond with the translation, nothing else."

    # Log translation request details
    print(f"Gemini translation request:")
    print(f"  - Target language: {language_name} (code: {target_language})")
    print(f"  - Text length: {len(text)} characters")
    print(f"  - Prompt: {prompt}")

    # Configure the model
    generation_config = {
        "temperature": 0.2,
        "top_p": 0.95,
        "top_k": 0,
        "max_output_tokens": 8192,
    }

    # Select the appropriate model
    model_name = "gemini-2.0-flash-lite"  # Default model
    print(f"Using Gemini 2.0 Flash Lite model for translation")

    # Prepare input prompt
    input_prompt = f"{prompt}\n\nText to translate: {text}"

    # Initialize the Gemini model
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config
    )

    # Create the prompt with system and user messages
    chat = model.start_chat(history=[])
    response = chat.send_message(input_prompt)

    translated_text = response.text

    # Log translation result
    print(f"Gemini translation completed:")
    print(f"  - Model used: {model_name}")
    print(f"  - Result length: {len(translated_text)} characters")
    print(f"  - First 100 chars: {translated_text[:100]}...")

    return translated_text

def main():
    # Sample text to translate (English)
    sample_text = "Hello, this is a test of the translation system. We are checking if all languages work correctly."

    # Test languages
    test_languages = ["it", "es", "fr", "de", "zh", "ja", "ru"]

    print("=== Testing OpenAI Translation ===")
    for lang_code in test_languages:
        print(f"\nTesting translation to {get_language_name_from_code(lang_code)} ({lang_code}):")
        try:
            translated = translate_with_openai(sample_text, lang_code)
            print(f"Full translation: {translated}")
        except Exception as e:
            print(f"Error: {str(e)}")

    print("\n\n=== Testing Gemini Translation ===")
    for lang_code in test_languages:
        print(f"\nTesting translation to {get_language_name_from_code(lang_code)} ({lang_code}):")
        try:
            translated = translate_with_gemini(sample_text, lang_code)
            print(f"Full translation: {translated}")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
