"""Transcription service for VocalLocal."""
import os
import io
import re
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

    def _clean_gemini_transcription(self, text):
        """
        Clean up Gemini transcription by removing bracketed artifacts at the end.

        Args:
            text (str): The transcription text from Gemini

        Returns:
            str: Cleaned transcription text
        """
        # Pattern to match bracketed text at the end of the string
        pattern = r'\s*\[[^\]]+\]\s*$'
        cleaned_text = re.sub(pattern, '', text)

        # Log if we removed something
        if cleaned_text != text:
            self.logger.info(f"Removed bracketed artifact from end of Gemini transcription")

        return cleaned_text

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
        # Calculate file size in MB for better logging
        file_size_mb = len(audio_data) / (1024 * 1024)
        self.logger.info(f"Transcribing audio with model: {model}, language: {language}, size: {len(audio_data)} bytes ({file_size_mb:.2f} MB)")

        # Check if file is very large (over 100MB) and log a warning
        if file_size_mb > 100:
            self.logger.warning(f"Very large file detected: {file_size_mb:.2f} MB. This may cause memory issues.")

        # For extremely large files (over 150MB), recommend chunking
        if file_size_mb > 150:
            self.logger.warning(f"Extremely large file detected: {file_size_mb:.2f} MB. Consider splitting into smaller segments for better reliability.")
            # We'll still try to process it, but with a warning

        # Check if FFmpeg is available if we're planning to use OpenAI
        ffmpeg_available = self._check_ffmpeg_available()
        if not ffmpeg_available and not (model.startswith('gemini-') or model == 'gemini'):
            self.logger.warning("FFmpeg not available and OpenAI model requested. Automatically switching to Gemini.")
            model = "gemini"  # Force using Gemini when FFmpeg is not available

        # For OpenAI models, check if file is too large and switch to Gemini if needed
        if (model.startswith('gpt-') or model.startswith('whisper-')) and file_size_mb > 25:
            self.logger.warning(f"File size ({file_size_mb:.2f} MB) exceeds OpenAI's recommended limit. Automatically switching to Gemini.")
            model = "gemini"  # Force using Gemini for large files

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

                # Prepare generation config with language hint if provided
                generation_config = {
                    "temperature": 0,
                }

                # Prepare for audio transcription
                self.logger.info(f"Preparing audio file for Gemini: {temp_file_path}")

                try:
                    # Prepare the prompt parts
                    prompt_parts = []

                    # Add language hint if specified
                    if language and language != "auto":
                        prompt = f"Please transcribe the following audio. The language is {language}."
                        prompt_parts.append(prompt)
                        self.logger.info(f"Added language hint to prompt: {language}")

                    # Read the audio file
                    with open(temp_file_path, 'rb') as f:
                        audio_bytes = f.read()
                        self.logger.info(f"Read {len(audio_bytes)} bytes from audio file")

                    # Use the audio bytes directly
                    self.logger.info("Sending audio to Gemini for transcription")
                    start_time = time.time()

                    # Determine which method to use based on file size
                    # For files larger than 5MB, use Files API directly
                    file_size_mb = len(audio_bytes) / (1024 * 1024)
                    self.logger.info(f"Audio file size: {file_size_mb:.2f} MB")

                    # Set threshold for using Files API directly (5MB)
                    FILES_API_THRESHOLD_MB = 5

                    # For larger files, use Files API directly
                    if file_size_mb > FILES_API_THRESHOLD_MB:
                        self.logger.info(f"File size ({file_size_mb:.2f} MB) exceeds {FILES_API_THRESHOLD_MB} MB threshold, using Files API method directly")

                        try:
                            # Create a temporary file with the audio data
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
                                temp_file.write(audio_bytes)
                                temp_file_path = temp_file.name

                            try:
                                # Upload the file using the Files API
                                self.logger.info(f"Uploading temporary file: {temp_file_path}")
                                file_obj = genai.upload_file(path=temp_file_path)

                                # Create content with the file
                                prompt = f"Please transcribe the following audio. The language is {language}." if language and language != "auto" else "Please transcribe this audio."

                                # Generate content with the file
                                self.logger.info("Using Files API method for Gemini transcription")
                                response = model.generate_content([
                                    prompt,
                                    file_obj
                                ], generation_config=generation_config)
                            finally:
                                # Clean up the temporary file
                                if os.path.exists(temp_file_path):
                                    os.remove(temp_file_path)
                                    self.logger.info(f"Removed temporary file: {temp_file_path}")
                        except Exception as files_error:
                            self.logger.error(f"Files API method failed: {str(files_error)}")

                            # Add more detailed error logging
                            error_msg = str(files_error).lower()
                            if "timeout" in error_msg:
                                self.logger.error("Files API request timed out - file may be too large or network issues")
                            elif "memory" in error_msg:
                                self.logger.error("Possible memory limitation reached during Files API processing")
                            elif "size" in error_msg:
                                self.logger.error("File size limitation reached in Files API")

                            raise Exception(f"Files API method failed for large file ({file_size_mb:.2f} MB). Error: {str(files_error)}")
                    else:
                        # For smaller files, try inline_data first, then fall back to Files API
                        try:
                            # Method 1: Using inline_data with base64 encoding
                            import base64

                            # Convert audio bytes to base64
                            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

                            # Create content parts
                            parts = []

                            # Add language hint if specified
                            if language and language != "auto":
                                parts.append({"text": f"Please transcribe the following audio. The language is {language}."})

                            # Add the audio data
                            parts.append({
                                "inline_data": {
                                    "mime_type": "audio/webm",
                                    "data": audio_b64
                                }
                            })

                            # Generate content with the audio
                            self.logger.info("Using inline_data method for Gemini transcription")
                            response = model.generate_content(
                                parts,
                                generation_config=generation_config
                            )
                        except Exception as inline_error:
                            self.logger.warning(f"Inline data method failed: {str(inline_error)}")
                            self.logger.info("Trying Files API method as fallback")

                            # Method 2: Using the Files API as fallback
                            try:
                                # Create a temporary file with the audio data
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
                                    temp_file.write(audio_bytes)
                                    temp_file_path = temp_file.name

                                try:
                                    # Upload the file using the Files API
                                    self.logger.info(f"Uploading temporary file: {temp_file_path}")
                                    file_obj = genai.upload_file(path=temp_file_path)

                                    # Create content with the file
                                    prompt = f"Please transcribe the following audio. The language is {language}." if language and language != "auto" else "Please transcribe this audio."

                                    # Generate content with the file
                                    self.logger.info("Using Files API method for Gemini transcription")
                                    response = model.generate_content([
                                        prompt,
                                        file_obj
                                    ], generation_config=generation_config)
                                finally:
                                    # Clean up the temporary file
                                    if os.path.exists(temp_file_path):
                                        os.remove(temp_file_path)
                                        self.logger.info(f"Removed temporary file: {temp_file_path}")
                            except Exception as files_error:
                                self.logger.error(f"Files API method failed: {str(files_error)}")
                                raise Exception(f"All Gemini transcription methods failed. Last error: {str(files_error)}")

                    elapsed_time = time.time() - start_time
                    self.logger.info(f"Gemini API call completed in {elapsed_time:.2f} seconds")

                    # Extract the transcription
                    transcription = response.text

                    # Clean up any bracketed artifacts at the end
                    cleaned_transcription = self._clean_gemini_transcription(transcription)

                    # Log success with details
                    self.logger.info(f"Gemini transcription successful: {len(cleaned_transcription)} characters")
                    if len(cleaned_transcription) < 100:
                        # Log the full transcription if it's short
                        self.logger.info(f"Transcription content: {cleaned_transcription}")
                    else:
                        # Log just the beginning if it's long
                        self.logger.info(f"Transcription begins with: {cleaned_transcription[:100]}...")

                    return cleaned_transcription

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
                    elif "file_data" in error_msg or "mime_type" in error_msg:
                        self.logger.error("Error with audio file format for Gemini")
                    elif "audio" in error_msg and "format" in error_msg:
                        self.logger.error("Unsupported audio format for Gemini")
                    elif "memory" in error_msg or "out of memory" in error_msg:
                        self.logger.error("Memory limitation reached during Gemini processing")
                        # Try to provide a helpful message about file size
                        try:
                            file_size_mb = len(audio_bytes) / (1024 * 1024)
                            self.logger.error(f"File size was {file_size_mb:.2f} MB which may be too large for current memory constraints")
                        except:
                            pass
                    elif "timeout" in error_msg or "deadline exceeded" in error_msg:
                        self.logger.error("Request timed out - file may be too large or processing took too long")
                    elif "size" in error_msg and "limit" in error_msg:
                        self.logger.error("File size limitation reached in Gemini API")

                    # No temporary files to clean up in this implementation

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
                    # Get file size for better error reporting
                    try:
                        file_size_mb = os.path.getsize(mp3_file_path) / (1024 * 1024)
                        self.logger.error(f"Audio file too large for OpenAI: {file_size_mb:.2f} MB (limit is 25MB)")
                        self.logger.info("Consider using Gemini for larger files (up to 200MB)")
                    except:
                        self.logger.error("Audio file too large for OpenAI (limit is 25MB)")
                elif "timeout" in error_msg or "deadline" in error_msg:
                    self.logger.error("Request timed out - file may be too large or processing took too long")
                elif "memory" in error_msg:
                    self.logger.error("Memory limitation reached during OpenAI processing")
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
