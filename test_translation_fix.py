import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY environment variable not set")
    exit(1)

openai.api_key = api_key
print(f"API key loaded: {api_key[:5]}...")

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
        "ru": "Russian"
    }
    
    # Return the language name if found, otherwise return the code
    return language_map.get(language_code, language_code)

# Test translation with language code only
def test_translation_with_code(text, target_language_code):
    print(f"\n=== Testing translation with code only: {target_language_code} ===")
    
    # Create translation prompt
    prompt = f"You are a professional translator. Translate the text into {target_language_code}. Only respond with the translation, nothing else."
    
    print(f"Prompt: {prompt}")

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
    print(f"Translation: {translated_text}")
    return translated_text

# Test translation with language name and code
def test_translation_with_name_and_code(text, target_language_code):
    print(f"\n=== Testing translation with name and code: {target_language_code} ===")
    
    # Get language name
    language_name = get_language_name_from_code(target_language_code)
    
    # Create translation prompt
    prompt = f"You are a professional translator. Translate the text into {language_name} (language code: {target_language_code}). Only respond with the translation, nothing else."
    
    print(f"Prompt: {prompt}")

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
    print(f"Translation: {translated_text}")
    return translated_text

# Sample text to translate (English)
sample_text = "Hello, this is a test of the translation system. We are checking if all languages work correctly."

# Test languages
test_languages = ["es", "fr", "de", "zh", "ja", "ru"]

# Run tests
for lang_code in test_languages:
    try:
        # Test with code only
        code_only_result = test_translation_with_code(sample_text, lang_code)
        
        # Test with name and code
        name_and_code_result = test_translation_with_name_and_code(sample_text, lang_code)
        
        # Compare results
        print(f"\nComparison for {lang_code}:")
        print(f"Code only: {code_only_result}")
        print(f"Name and code: {name_and_code_result}")
        
        if code_only_result == name_and_code_result:
            print("Results are identical")
        else:
            print("Results are different")
            
    except Exception as e:
        print(f"Error testing {lang_code}: {str(e)}")
