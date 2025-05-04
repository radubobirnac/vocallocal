import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# OpenAI API configuration
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    print("Warning: OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
    exit(1)
else:
    print("OpenAI API key found")

# Test translation with OpenAI
def translate_with_openai(text, target_language):
    """Helper function to translate text using OpenAI"""
    # Create translation prompt
    prompt = f"You are a professional translator. Translate the text into {target_language}. Only respond with the translation, nothing else."
    
    print(f"Translating to {target_language}")
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
sample_text = "Hello, this is a test of the translation system."

# Test Spanish translation
print("Testing Spanish translation:")
translate_with_openai(sample_text, "Spanish")

# Test French translation
print("\nTesting French translation:")
translate_with_openai(sample_text, "French")
