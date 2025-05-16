"""Transcription service for VocalLocal."""
import os
import io
import time
import tempfile
import subprocess
import logging
import openai
import google.generativeai as genai
from services.base_service import BaseService
from metrics_tracker import track_transcription_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TranscriptionService(BaseService):
    """Service for transcribing audio files."""

    def __init__(self):
        """Initialize the transcription service."""
        super().__init__()
        self.logger = logging.getLogger("transcription")
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')

        # Configure OpenAI
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.openai_available = True
        else:
            self.openai_available = False
            self.logger.warning("OpenAI API key not found. OpenAI transcription will not be available.")

        # Configure Gemini
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_available = True
            self.logger.info("Google Generative AI module loaded successfully for transcription service")
        else:
            self.gemini_available = False
            self.logger.warning("Gemini API key not found. Gemini transcription will not be available.")

    @track_transcription_metrics
    def transcribe(self, audio_data, language, model="gemini"):
        """
        Transcribe audio data using the specified model.

        Args:
            audio_data (bytes): The audio data to transcribe
            language (str): The language code (e.g., 'en', 'es')
            model (str): The model to use ('gemini', 'gpt-4o-mini-transcribe', etc.)

        Returns:
            str: The transcribed text
        """
        self.logger.info(f"Transcribing audio with model: {model}, language: {language}, size: {len(audio_data)} bytes")

        # Check if FFmpeg is available if we're planning to use OpenAI
        ffmpeg_available = self._check_ffmpeg_available()
        if not ffmpeg_available and not (model.startswith('gemini-') or model == 'gemini'):
            self.logger.warning("FFmpeg not available and OpenAI model requested. Automatically switching to Gemini.")
            model = "gemini"  # Force using Gemini when FFmpeg is not available

        try:
            # Check if we should use Gemini
            if model.startswith('gemini-') or model == 'gemini':
                if not self.gemini_available:
                    self.logger.warning("Gemini not available. Falling back to OpenAI.")
                    if not ffmpeg_available:
                        self.logger.error("Cannot fall back to OpenAI because FFmpeg is not available.")
                        raise Exception("Transcription failed: Gemini not available and FFmpeg not installed for OpenAI fallback.")
                    return self.transcribe_with_openai(audio_data, language, "gpt-4o-mini-transcribe")

                return self.transcribe_with_gemini(audio_data, language, model)
            else:
                # Use OpenAI for transcription
                if not self.openai_available:
                    self.logger.warning("OpenAI not available. Falling back to Gemini.")
                    return self.transcribe_with_gemini(audio_data, language, "gemini")

                try:
                    return self.transcribe_with_openai(audio_data, language, model)
                except Exception as e:
                    # If OpenAI fails with FFmpeg error, try Gemini as fallback
                    error_str = str(e).lower()
                    if "ffmpeg" in error_str or "conversion" in error_str or "format" in error_str:
                        self.logger.warning(f"OpenAI transcription failed due to FFmpeg/format issue: {str(e)}")
                        self.logger.info("Falling back to Gemini for transcription")
                        return self.transcribe_with_gemini(audio_data, language, "gemini")
                    else:
                        # Re-raise other errors
                        raise
        except Exception as e:
            self.logger.error(f"Error in transcription: {str(e)}")
            raise e

    def _check_ffmpeg_available(self):
        """Check if FFmpeg is available on the system"""
        try:
            # Try to run FFmpeg version command
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            self.logger.info("FFmpeg is available")
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            self.logger.warning("FFmpeg is not available")
            return False

    def transcribe_with_gemini(self, audio_data, language, model_name="gemini"):
        """
        Transcribe audio using Google's Gemini model.

        Args:
            audio_data (bytes): The audio data to transcribe
            language (str): The language code
            model_name (str): The model name to use

        Returns:
            str: The transcribed text
        """
        temp_file_path = None

        try:
            self.logger.info(f"Using Gemini for transcription with model: {model_name}, language: {language}")

            # Map model name to actual Gemini model ID
            gemini_model_id = 'gemini-1.5-flash'  # Default model
            if model_name == 'gemini-2.0-flash-lite':
                gemini_model_id = 'gemini-1.5-flash'
            elif model_name == 'gemini-2.5-flash-preview':
                gemini_model_id = 'gemini-1.5-flash-preview'
            elif model_name == 'gemini-2.5-pro-preview':
                gemini_model_id = 'gemini-1.5-pro-preview'

            self.logger.info(f"Mapped model name '{model_name}' to Gemini model ID: {gemini_model_id}")

            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
                self.logger.info(f"Created temporary WebM file: {temp_file_path} ({len(audio_data)} bytes)")

            try:
                # Initialize the Gemini model
                self.logger.info(f"Initializing Gemini model: {gemini_model_id}")
                model = genai.GenerativeModel(gemini_model_id)

                # Read the audio file
                self.logger.info(f"Reading audio file: {temp_file_path}")
                with open(temp_file_path, 'rb') as f:
                    audio_bytes = f.read()
                    self.logger.info(f"Read {len(audio_bytes)} bytes from audio file")

                # Prepare generation config with language hint if provided
                generation_config = {
                    "temperature": 0,
                }

                # Add language hint if specified
                prompt_parts = []
                if language and language != "auto":
                    prompt = f"Please transcribe the following audio. The language is {language}."
                    prompt_parts.append(prompt)
                    self.logger.info(f"Added language hint to prompt: {language}")

                # Add the audio data
                prompt_parts.append(audio_bytes)

                # Generate content with the audio
                self.logger.info("Sending audio to Gemini for transcription")
                start_time = time.time()

                try:
                    if prompt_parts and len(prompt_parts) > 1:
                        # Use prompt with language hint
                        response = model.generate_content(
                            prompt_parts,
                            generation_config=generation_config,
                            stream=False
                        )
                    else:
                        # Use just the audio
                        response = model.generate_content(
                            audio_bytes,
                            generation_config=generation_config,
                            stream=False
                        )

                    elapsed_time = time.time() - start_time
                    self.logger.info(f"Gemini API call completed in {elapsed_time:.2f} seconds")

                    # Extract the transcription
                    transcription = response.text

                    # Log success with details
                    self.logger.info(f"Gemini transcription successful: {len(transcription)} characters")
                    if len(transcription) < 100:
                        # Log the full transcription if it's short
                        self.logger.info(f"Transcription content: {transcription}")
                    else:
                        # Log just the beginning if it's long
                        self.logger.info(f"Transcription begins with: {transcription[:100]}...")

                    return transcription

                except Exception as api_error:
                    self.logger.error(f"Gemini API error: {str(api_error)}")
                    # Check for specific error types
                    error_msg = str(api_error).lower()
                    if "permission" in error_msg or "access" in error_msg:
                        self.logger.error("Gemini API permission or access error")
                    elif "rate limit" in error_msg or "quota" in error_msg:
                        self.logger.error("Gemini API rate limit or quota exceeded")
                    elif "invalid" in error_msg and "api key" in error_msg:
                        self.logger.error("Invalid Gemini API key")
                    raise

            finally:
                # Clean up the temporary file
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                        self.logger.info(f"Removed temporary WebM file: {temp_file_path}")
                    except Exception as cleanup_error:
                        self.logger.warning(f"Failed to remove temporary WebM file: {str(cleanup_error)}")

        except Exception as e:
            self.logger.error(f"Error in Gemini transcription: {str(e)}")
            raise e

    def transcribe_with_openai(self, audio_data, language, model="gpt-4o-mini-transcribe"):
        """
        Transcribe audio using OpenAI's Whisper model.

        Args:
            audio_data (bytes): The audio data to transcribe
            language (str): The language code
            model (str): The model to use

        Returns:
            str: The transcribed text
        """
        temp_file_path = None
        mp3_file_path = None

        try:
            self.logger.info(f"Using OpenAI for transcription with model: {model}")

            # Check if FFmpeg is available before proceeding
            if not self._check_ffmpeg_available():
                self.logger.error("FFmpeg is required for OpenAI transcription but not available")
                raise Exception("FFmpeg not installed. Cannot convert audio format for OpenAI transcription.")

            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            # Convert WebM to MP3 using FFmpeg
            mp3_file_path = temp_file_path.replace('.webm', '.mp3')
            self.logger.info(f"Converting WebM to MP3: {temp_file_path} -> {mp3_file_path}")

            try:
                # Run FFmpeg to convert the file with detailed logging
                self.logger.info("Starting FFmpeg conversion process...")
                ffmpeg_cmd = ['ffmpeg', '-i', temp_file_path, '-vn', '-ar', '44100', '-ac', '2', '-b:a', '192k', mp3_file_path]
                self.logger.info(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")

                result = subprocess.run(
                    ffmpeg_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Log FFmpeg output for debugging
                if result.stdout:
                    self.logger.debug(f"FFmpeg stdout: {result.stdout}")
                if result.stderr:
                    self.logger.debug(f"FFmpeg stderr: {result.stderr}")

                if os.path.exists(mp3_file_path) and os.path.getsize(mp3_file_path) > 0:
                    self.logger.info(f"FFmpeg conversion successful: {os.path.getsize(mp3_file_path)} bytes")
                else:
                    self.logger.error("FFmpeg conversion failed: Output file is empty or does not exist")
                    raise Exception("Audio conversion failed: Output file is empty or does not exist")

            except subprocess.CalledProcessError as e:
                self.logger.error(f"FFmpeg conversion failed with return code {e.returncode}")
                self.logger.error(f"FFmpeg stderr: {e.stderr}")
                self.logger.error(f"FFmpeg stdout: {e.stdout}")
                raise Exception(f"Audio conversion failed: {e.stderr}")
            except FileNotFoundError:
                self.logger.error("FFmpeg executable not found in PATH")
                raise Exception("FFmpeg not installed or not in PATH. Cannot convert audio format.")

            # Open the MP3 file for OpenAI
            try:
                self.logger.info(f"Sending converted audio file to OpenAI ({os.path.getsize(mp3_file_path)} bytes)")
                with open(mp3_file_path, 'rb') as audio_file:
                    # Call OpenAI API
                    response = openai.audio.transcriptions.create(
                        model=model,
                        file=audio_file,
                        language=language
                    )

                transcription = response.text
                self.logger.info(f"OpenAI transcription successful: {len(transcription)} characters")
                return transcription
            except Exception as api_error:
                self.logger.error(f"OpenAI API error: {str(api_error)}")
                # Check for specific error types
                error_msg = str(api_error).lower()
                if "format" in error_msg:
                    self.logger.error("OpenAI rejected the audio format")
                elif "api key" in error_msg or "authentication" in error_msg:
                    self.logger.error("OpenAI API key authentication error")
                elif "too large" in error_msg or "file size" in error_msg:
                    self.logger.error("Audio file too large for OpenAI")
                raise

        except Exception as e:
            self.logger.error(f"Error in OpenAI transcription: {str(e)}")
            raise e

        finally:
            # Clean up the temporary files
            self.logger.info("Cleaning up temporary files")
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    self.logger.info(f"Removed temporary WebM file: {temp_file_path}")
                except Exception as cleanup_error:
                    self.logger.warning(f"Failed to remove temporary WebM file: {str(cleanup_error)}")

            if mp3_file_path and os.path.exists(mp3_file_path):
                try:
                    os.remove(mp3_file_path)
                    self.logger.info(f"Removed temporary MP3 file: {mp3_file_path}")
                except Exception as cleanup_error:
                    self.logger.warning(f"Failed to remove temporary MP3 file: {str(cleanup_error)}")

# Create a singleton instance
transcription_service = TranscriptionService()
