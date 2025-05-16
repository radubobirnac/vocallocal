import os
import openai
from dotenv import load_dotenv
import subprocess
import tempfile

# Load environment variables
load_dotenv()

# Set up OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY environment variable not set")
    exit(1)

openai.api_key = api_key
print(f"API key loaded: {api_key[:10]}...")

# Check if FFmpeg is installed
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

ffmpeg_available = check_ffmpeg()
print(f"FFmpeg available: {ffmpeg_available}")

# Create a simple MP3 file for testing
def create_test_audio():
    # Create a text file
    with open("test_text.txt", "w") as f:
        f.write("This is a test file for transcription.")

    # Use FFmpeg to generate a silent MP3 file if available
    if ffmpeg_available:
        try:
            subprocess.run(
                ["ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "3", "-q:a", "9", "-acodec", "libmp3lame", "test_audio.mp3"],
                capture_output=True,
                check=True
            )
            print("Created test audio file with FFmpeg")
            return "test_audio.mp3"
        except subprocess.SubprocessError as e:
            print(f"Error creating test audio with FFmpeg: {e}")

    # If FFmpeg is not available or failed, create a simple WAV file
    print("Creating a simple WAV file...")
    try:
        import wave
        import struct
        import math

        # Create a simple sine wave
        duration = 3  # seconds
        sample_rate = 44100  # Hz
        frequency = 440  # Hz (A4)

        with wave.open("test_audio.wav", "w") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes (16 bits)
            wav_file.setframerate(sample_rate)

            # Generate sine wave
            for i in range(int(duration * sample_rate)):
                value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
                data = struct.pack("<h", value)
                wav_file.writeframes(data)

        print("Created simple WAV test file")
        return "test_audio.wav"
    except Exception as e:
        print(f"Error creating WAV file: {e}")
        return None

# Test transcription with different models
def test_transcription(model_name, audio_file):
    try:
        print(f"\nTesting transcription with model: {model_name}")
        with open(audio_file, "rb") as f:
            response = openai.audio.transcriptions.create(
                model=model_name,
                file=f
            )

        print(f"Transcription result: {response.text}")
        print(f"Transcription test successful with {model_name}!")
        return True
    except Exception as e:
        print(f"Transcription Error with {model_name}: {str(e)}")
        return False

# Create test audio file
audio_file = create_test_audio()
if not audio_file:
    print("Failed to create test audio file. Exiting.")
    exit(1)

# Test different transcription models
transcription_models = ["whisper-1", "gpt-4o-mini-transcribe"]

# Run the transcription tests
for model in transcription_models:
    test_transcription(model, audio_file)

print("\nTest complete.")
