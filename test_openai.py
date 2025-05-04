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

# Test a simple completion
try:
    print("Testing OpenAI API...")
    response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello world"}
        ]
    )
    print(f"Response: {response.choices[0].message.content}")
    print("API test successful!")
except Exception as e:
    print(f"Error: {str(e)}")
