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

# List available models
try:
    print("\nListing available models...")
    models = openai.models.list()
    
    # Filter for transcription and TTS models
    transcription_models = [model.id for model in models.data if "whisper" in model.id.lower() or "transcribe" in model.id.lower()]
    tts_models = [model.id for model in models.data if "tts" in model.id.lower()]
    
    print("\nAvailable transcription models:")
    for model in transcription_models:
        print(f"- {model}")
    
    print("\nAvailable TTS models:")
    for model in tts_models:
        print(f"- {model}")
    
except Exception as e:
    print(f"Error listing models: {str(e)}")

# Test TTS with different models
def test_tts(model_name, voice="alloy"):
    try:
        print(f"\nTesting TTS with model: {model_name}, voice: {voice}")
        response = openai.audio.speech.create(
            model=model_name,
            voice=voice,
            input="Hello, this is a test of the OpenAI TTS API."
        )
        
        # Save to a file to verify it works
        output_file = f"test_tts_{model_name}_{voice}.mp3"
        with open(output_file, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
        
        print(f"TTS test successful! Output saved to {output_file}")
        return True
    except Exception as e:
        print(f"TTS Error with {model_name}: {str(e)}")
        return False

# Test different TTS models and voices
tts_test_configs = [
    {"model": "tts-1", "voice": "alloy"},
    {"model": "tts-1", "voice": "echo"},
    {"model": "tts-1", "voice": "onyx"},
    {"model": "tts-1-hd", "voice": "alloy"},
]

# Add gpt-4o-mini-tts if it was found in the available models
if any("gpt-4o-mini-tts" in model for model in tts_models):
    tts_test_configs.append({"model": "gpt-4o-mini-tts", "voice": "alloy"})

# Run the TTS tests
for config in tts_test_configs:
    test_tts(config["model"], config["voice"])

print("\nTest complete.")
