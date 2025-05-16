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
print(f"API key loaded: {api_key[:10]}...")

# Test a simple chat completion
try:
    print("\nTesting OpenAI Chat API...")
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello world"}
        ]
    )
    print(f"Chat Response: {response.choices[0].message.content}")
    print("Chat API test successful!")
except Exception as e:
    print(f"Chat API Error: {str(e)}")

# Test the transcription API
try:
    print("\nTesting OpenAI Transcription API...")
    # Create a simple audio file for testing
    with open("test_audio.txt", "w") as f:
        f.write("This is a test file to check if the API key works.")
    
    # Try to use the transcription API (this will fail with a format error, but will validate the API key)
    try:
        with open("test_audio.txt", "rb") as audio_file:
            openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
    except Exception as e:
        # Check if the error is about the file format (expected) or about the API key (problem)
        error_str = str(e).lower()
        if "api key" in error_str or "authentication" in error_str or "unauthorized" in error_str:
            print(f"Transcription API Error (API key issue): {str(e)}")
        else:
            print(f"Transcription API test partially successful - API key accepted but got expected format error: {str(e)}")
except Exception as e:
    print(f"Transcription API Error: {str(e)}")

# Test the TTS API
try:
    print("\nTesting OpenAI TTS API...")
    response = openai.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input="Hello, this is a test of the OpenAI TTS API."
    )
    
    # Save to a file to verify it works
    with open("test_tts_output.mp3", "wb") as f:
        for chunk in response.iter_bytes():
            f.write(chunk)
    
    print("TTS API test successful! Output saved to test_tts_output.mp3")
except Exception as e:
    print(f"TTS API Error: {str(e)}")

print("\nTest complete.")
