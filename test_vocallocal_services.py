import os
import tempfile
import time
import logging
from dotenv import load_dotenv
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vocallocal_test")

# Load environment variables
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.error("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
    exit(1)

logger.info(f"OpenAI API key loaded: {openai.api_key[:10]}...")

# Simple retry decorator
def with_retry(max_retries=3, initial_delay=1, backoff_factor=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            delay = initial_delay
            last_error = None
            
            while attempts <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    last_error = e
                    
                    if attempts <= max_retries:
                        logger.warning(f"Retry attempt {attempts}/{max_retries}: {str(e)}")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(f"All retry attempts failed: {str(e)}")
                        break
            
            raise last_error
        return wrapper
    return decorator

# TTS Service
class TTSService:
    def __init__(self):
        self.logger = logging.getLogger("tts_service")
    
    @with_retry(max_retries=2)
    def synthesize_with_openai(self, text, voice="onyx"):
        """Generate speech using OpenAI's TTS service"""
        self.logger.info(f"Generating speech with OpenAI TTS, voice={voice}, text_length={len(text)}")
        
        try:
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file_path = temp_file.name
            
            # Generate speech with OpenAI
            response = openai.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            # Save to the temporary file
            with open(temp_file_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
            
            self.logger.info(f"Speech generated successfully, saved to {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            self.logger.error(f"Error in OpenAI TTS: {str(e)}")
            raise e
    
    @with_retry(max_retries=2)
    def synthesize_with_gpt4o_mini(self, text):
        """Generate speech using OpenAI's GPT-4o Mini TTS service"""
        self.logger.info(f"Generating speech with GPT-4o Mini TTS, text_length={len(text)}")
        
        try:
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file_path = temp_file.name
            
            # Generate speech with OpenAI's GPT-4o Mini TTS
            response = openai.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",  # Use alloy voice for all languages
                input=text
            )
            
            # Save to the temporary file
            with open(temp_file_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
            
            self.logger.info(f"Speech generated successfully with GPT-4o Mini, saved to {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            self.logger.error(f"Error in GPT-4o Mini TTS: {str(e)}")
            raise e
    
    def synthesize(self, text, model="gpt4o-mini"):
        """Synthesize speech with fallback logic"""
        if model == "gpt4o-mini":
            try:
                return self.synthesize_with_gpt4o_mini(text)
            except Exception as e:
                self.logger.warning(f"GPT-4o Mini TTS failed: {str(e)}")
                self.logger.info("Falling back to standard OpenAI TTS")
                return self.synthesize_with_openai(text)
        else:
            return self.synthesize_with_openai(text)

# Transcription Service
class TranscriptionService:
    def __init__(self):
        self.logger = logging.getLogger("transcription_service")
    
    @with_retry(max_retries=2)
    def transcribe_with_openai(self, audio_file_path, language="en"):
        """Transcribe audio using OpenAI's Whisper model"""
        self.logger.info(f"Transcribing with OpenAI Whisper, language={language}, file={audio_file_path}")
        
        try:
            # Open the file and send to OpenAI
            with open(audio_file_path, 'rb') as audio_file:
                response = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language if language != "auto" else None
                )
            
            self.logger.info(f"Transcription successful: {len(response.text)} characters")
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error in OpenAI transcription: {str(e)}")
            raise e
    
    @with_retry(max_retries=2)
    def transcribe_with_gpt4o_mini(self, audio_file_path, language="en"):
        """Transcribe audio using OpenAI's GPT-4o Mini Transcribe model"""
        self.logger.info(f"Transcribing with GPT-4o Mini, language={language}, file={audio_file_path}")
        
        try:
            # Open the file and send to OpenAI
            with open(audio_file_path, 'rb') as audio_file:
                response = openai.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",
                    file=audio_file,
                    language=language if language != "auto" else None
                )
            
            self.logger.info(f"Transcription successful with GPT-4o Mini: {len(response.text)} characters")
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error in GPT-4o Mini transcription: {str(e)}")
            raise e
    
    def transcribe(self, audio_file_path, language="en", model="gpt4o-mini"):
        """Transcribe audio with fallback logic"""
        if model == "gpt4o-mini":
            try:
                return self.transcribe_with_gpt4o_mini(audio_file_path, language)
            except Exception as e:
                self.logger.warning(f"GPT-4o Mini transcription failed: {str(e)}")
                self.logger.info("Falling back to Whisper model")
                return self.transcribe_with_openai(audio_file_path, language)
        else:
            return self.transcribe_with_openai(audio_file_path, language)

# Test the services
def main():
    # Create test audio file
    import wave
    import struct
    import math
    
    logger.info("Creating test audio file...")
    duration = 3  # seconds
    sample_rate = 44100  # Hz
    frequency = 440  # Hz (A4)
    
    audio_file_path = "test_audio.wav"
    with wave.open(audio_file_path, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes (16 bits)
        wav_file.setframerate(sample_rate)
        
        # Generate sine wave
        for i in range(int(duration * sample_rate)):
            value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            data = struct.pack("<h", value)
            wav_file.writeframes(data)
    
    logger.info(f"Test audio file created: {audio_file_path}")
    
    # Test transcription service
    logger.info("Testing transcription service...")
    transcription_service = TranscriptionService()
    
    try:
        # Test with GPT-4o Mini model
        logger.info("Testing with GPT-4o Mini model...")
        transcription = transcription_service.transcribe(audio_file_path, model="gpt4o-mini")
        logger.info(f"GPT-4o Mini transcription result: {transcription}")
        
        # Test with Whisper model
        logger.info("Testing with Whisper model...")
        transcription = transcription_service.transcribe(audio_file_path, model="whisper")
        logger.info(f"Whisper transcription result: {transcription}")
    except Exception as e:
        logger.error(f"Transcription test failed: {str(e)}")
    
    # Test TTS service
    logger.info("Testing TTS service...")
    tts_service = TTSService()
    
    try:
        # Test with GPT-4o Mini model
        logger.info("Testing with GPT-4o Mini TTS model...")
        tts_file = tts_service.synthesize("This is a test of the GPT-4o Mini TTS service.", model="gpt4o-mini")
        logger.info(f"GPT-4o Mini TTS output: {tts_file}")
        
        # Test with standard OpenAI TTS
        logger.info("Testing with standard OpenAI TTS...")
        tts_file = tts_service.synthesize("This is a test of the standard OpenAI TTS service.", model="openai")
        logger.info(f"Standard OpenAI TTS output: {tts_file}")
    except Exception as e:
        logger.error(f"TTS test failed: {str(e)}")
    
    logger.info("Tests completed.")

if __name__ == "__main__":
    main()
