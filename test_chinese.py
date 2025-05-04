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
def test_translation_with_name_and_code(text, target_language_code, language_name):
    print(f"\n=== Testing translation with name and code: {target_language_code} ===")
    
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

# Test Chinese translation
try:
    # Test with code only
    code_only_result = test_translation_with_code(sample_text, "zh")
    
    # Test with name and code
    name_and_code_result = test_translation_with_name_and_code(sample_text, "zh", "Chinese")
    
    # Compare results
    print(f"\nComparison for Chinese:")
    print(f"Code only: {code_only_result}")
    print(f"Name and code: {name_and_code_result}")
    
    if code_only_result == name_and_code_result:
        print("Results are identical")
    else:
        print("Results are different")
        
except Exception as e:
    print(f"Error testing Chinese: {str(e)}")
