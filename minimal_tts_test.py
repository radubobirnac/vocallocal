"""
Minimal test script for Gemini 2.5 Flash Preview TTS functionality
"""

import os
import wave
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Gemini API key
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    print("Gemini API key not found. Please set it in your .env file.")
    exit(1)

print("Importing Google Generative AI...")
from google import genai
from google.genai import types

print("Setting up Gemini client...")
genai.configure(api_key=gemini_api_key)

def save_wave_file(filename, pcm_data, channels=1, rate=24000, sample_width=2):
    """Save PCM data to a WAV file"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)
    print(f"Saved audio to {filename}")

def test_gemini_tts():
    """Test Gemini 2.5 Flash TTS using the correct response_modalities approach"""
    print("=== Testing Gemini 2.5 Flash TTS with response_modalities ===")
    
    try:
        # Test text
        text = "Hello, this is a test of the Gemini 2.5 Flash Preview TTS service."
        
        # Configure the model with response_modalities and speech_config
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-tts",
            generation_config={
                "response_modalities": ["AUDIO"],
            }
        )
        
        # Create speech config
        speech_config = types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Kore",  # Use one of the available voices
                )
            )
        )
        
        # Generate content
        print("Generating TTS content...")
        response = model.generate_content(
            text,
            generation_config={"response_modalities": ["AUDIO"]},
            speech_config=speech_config
        )
        
        print(f"Response type: {type(response)}")
        print(f"Response attributes: {dir(response)}")
        
        # Check if we got audio data
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            print(f"Candidate type: {type(candidate)}")
            print(f"Candidate attributes: {dir(candidate)}")
            
            if hasattr(candidate, 'content') and candidate.content:
                content = candidate.content
                print(f"Content type: {type(content)}")
                print(f"Content attributes: {dir(content)}")
                
                if hasattr(content, 'parts') and content.parts:
                    part = content.parts[0]
                    print(f"Part type: {type(part)}")
                    print(f"Part attributes: {dir(part)}")
                    
                    if hasattr(part, 'inline_data') and part.inline_data:
                        inline_data = part.inline_data
                        print(f"Inline data type: {type(inline_data)}")
                        print(f"Inline data attributes: {dir(inline_data)}")
                        
                        if hasattr(inline_data, 'data') and inline_data.data:
                            # Get the audio data
                            audio_data = inline_data.data
                            print(f"Audio data type: {type(audio_data)}")
                            print(f"Audio data size: {len(audio_data)} bytes")
                            
                            # Save to a file
                            output_file = "minimal_tts_test.wav"
                            save_wave_file(output_file, audio_data)
                            print(f"Success! Audio saved to {output_file}")
                            return True
        
        print("No audio data found in the response")
        return False
    
    except Exception as e:
        print(f"Error testing Gemini TTS: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("Starting minimal Gemini TTS test script")
    test_gemini_tts()
    print("Test script completed")
