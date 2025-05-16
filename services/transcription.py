"""Transcription service for VocalLocal."""
import os
import io
import re
import time
import math
import tempfile
import subprocess
import logging
import openai
import google.generativeai as genai
from services.base_service import BaseService
from metrics_tracker import track_transcription_metrics

# Try to import pydub for audio chunking, but make it optional
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logging.getLogger("transcription").warning("pydub not available. Audio chunking will be disabled.")

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

    def _chunk_audio_file(self, audio_bytes, chunk_size_mb=5, format="webm"):
        """
        Split a large audio file into smaller chunks for more reliable processing.
        Memory-optimized version that processes chunks sequentially.

        Args:
            audio_bytes (bytes): The audio data to split
            chunk_size_mb (int): Target size for each chunk in MB
            format (str): Audio format (webm, mp3, etc.)

        Returns:
            list: List of byte arrays containing the audio chunks
        """
        self.logger.info(f"Chunking audio file of size {len(audio_bytes)/(1024*1024):.2f} MB into {chunk_size_mb}MB chunks")

        # Check if pydub is available
        if not PYDUB_AVAILABLE:
            self.logger.warning("Audio chunking requires pydub, which is not available. Using simple byte-based chunking.")
            return self._simple_chunk_audio_file(audio_bytes, chunk_size_mb)

        # Create a temporary file to store the audio
        temp_file_path = None
        chunks = []

        try:
            # Save the audio bytes to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format}') as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name

            # Free up memory by clearing the original audio bytes
            del audio_bytes

            try:
                # Get audio information without loading the entire file
                audio_info = AudioSegment.from_file(temp_file_path, format=format).info
                total_duration_ms = audio_info.length * 1000  # Convert to milliseconds

                # Calculate file size
                file_size_bytes = os.path.getsize(temp_file_path)
                file_size_mb = file_size_bytes / (1024 * 1024)

                # Calculate bytes per millisecond (approximate)
                bytes_per_ms = file_size_bytes / total_duration_ms if total_duration_ms > 0 else 0

                # Calculate chunk duration to achieve target chunk size
                chunk_size_bytes = chunk_size_mb * 1024 * 1024
                chunk_duration_ms = int(chunk_size_bytes / bytes_per_ms) if bytes_per_ms > 0 else 60000

                # Ensure chunk duration is reasonable (between 30 seconds and 3 minutes)
                chunk_duration_ms = max(30000, min(chunk_duration_ms, 180000))

                self.logger.info(f"Total duration: {total_duration_ms/1000:.1f} seconds, calculated chunk duration: {chunk_duration_ms/1000:.1f} seconds")

                # Calculate number of chunks
                num_chunks = math.ceil(total_duration_ms / chunk_duration_ms)
                self.logger.info(f"Splitting audio into {num_chunks} chunks")

                # Process chunks one at a time to minimize memory usage
                for i in range(num_chunks):
                    start_ms = i * chunk_duration_ms
                    end_ms = min((i + 1) * chunk_duration_ms, total_duration_ms)

                    self.logger.info(f"Processing chunk {i+1}/{num_chunks} ({start_ms/1000:.1f}s to {end_ms/1000:.1f}s)")

                    # Create a temporary file for this chunk
                    chunk_file_path = None

                    try:
                        # Use ffmpeg directly to extract the chunk (more memory efficient)
                        chunk_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format}')
                        chunk_file_path = chunk_file.name
                        chunk_file.close()

                        # Convert milliseconds to HH:MM:SS.mmm format for ffmpeg
                        start_time = self._ms_to_ffmpeg_time(start_ms)
                        duration = self._ms_to_ffmpeg_time(end_ms - start_ms)

                        # Use ffmpeg to extract the chunk
                        cmd = [
                            'ffmpeg',
                            '-i', temp_file_path,
                            '-ss', start_time,
                            '-t', duration,
                            '-c', 'copy',  # Copy without re-encoding to save CPU
                            '-y',  # Overwrite output file
                            chunk_file_path
                        ]

                        self.logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
                        result = subprocess.run(cmd, capture_output=True, text=True)

                        if result.returncode != 0:
                            self.logger.warning(f"FFmpeg extraction failed: {result.stderr}")
                            # Fall back to pydub if ffmpeg direct extraction fails
                            self.logger.info("Falling back to pydub for this chunk")

                            # Load just this segment using pydub
                            audio = AudioSegment.from_file(temp_file_path)
                            chunk = audio[start_ms:end_ms]
                            chunk.export(chunk_file_path, format=format)

                            # Free memory
                            del audio
                            del chunk

                        # Read the chunk file into memory
                        with open(chunk_file_path, 'rb') as f:
                            chunk_bytes = f.read()
                            chunk_size = len(chunk_bytes) / (1024 * 1024)
                            self.logger.info(f"Created chunk {i+1}/{num_chunks}: {chunk_size:.2f} MB")
                            chunks.append(chunk_bytes)

                    except Exception as chunk_error:
                        self.logger.error(f"Error processing chunk {i+1}: {str(chunk_error)}")
                        # Continue with other chunks
                    finally:
                        # Clean up the temporary chunk file
                        if chunk_file_path and os.path.exists(chunk_file_path):
                            try:
                                os.remove(chunk_file_path)
                            except Exception as e:
                                self.logger.warning(f"Failed to remove temporary chunk file: {str(e)}")

                if not chunks:
                    self.logger.error("No chunks were successfully created. Falling back to simple chunking.")
                    return self._simple_chunk_audio_file_stream(temp_file_path, chunk_size_mb)

                return chunks

            except Exception as pydub_error:
                self.logger.error(f"Error using pydub for audio chunking: {str(pydub_error)}")
                # If pydub processing fails, try a simpler byte-based chunking approach
                return self._simple_chunk_audio_file_stream(temp_file_path, chunk_size_mb)

        except Exception as e:
            self.logger.error(f"Error chunking audio file: {str(e)}")
            # If chunking fails, return the original file as a single chunk
            if 'audio_bytes' in locals() and audio_bytes:
                return [audio_bytes]
            else:
                # If we've already deleted audio_bytes, read it back from the temp file
                try:
                    with open(temp_file_path, 'rb') as f:
                        return [f.read()]
                except:
                    self.logger.error("Failed to recover original audio data")
                    raise

        finally:
            # Clean up the temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    self.logger.warning(f"Failed to remove temporary file: {str(e)}")

    def _ms_to_ffmpeg_time(self, ms):
        """Convert milliseconds to FFmpeg time format (HH:MM:SS.mmm)"""
        seconds = ms / 1000
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

    def _simple_chunk_audio_file_stream(self, file_path, chunk_size_mb=5):
        """
        A memory-efficient version of simple chunking that reads from a file in chunks.

        Args:
            file_path (str): Path to the audio file
            chunk_size_mb (int): Target size for each chunk in MB

        Returns:
            list: List of byte arrays containing the audio chunks
        """
        self.logger.info(f"Using streaming byte-based chunking for audio file")

        # Get file size
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        self.logger.info(f"File size: {file_size_mb:.2f} MB")

        # Convert chunk size to bytes
        chunk_size_bytes = chunk_size_mb * 1024 * 1024

        # If the file is smaller than the chunk size, return it as is
        if file_size <= chunk_size_bytes:
            with open(file_path, 'rb') as f:
                return [f.read()]

        # Calculate number of chunks
        num_chunks = math.ceil(file_size / chunk_size_bytes)
        self.logger.info(f"Splitting file into {num_chunks} chunks of {chunk_size_mb}MB each")

        # Create chunks by reading the file in parts
        chunks = []
        with open(file_path, 'rb') as f:
            for i in range(num_chunks):
                chunk = f.read(chunk_size_bytes)
                if chunk:  # Make sure we got some data
                    chunks.append(chunk)
                    self.logger.info(f"Created simple chunk {i+1}/{num_chunks}: {len(chunk)/(1024*1024):.2f} MB")

        self.logger.warning("Simple byte-based chunking may result in corrupted audio chunks. Results may be unreliable.")
        return chunks

    def _simple_chunk_audio_file(self, audio_bytes, chunk_size_mb=5):
        """
        A simpler fallback method to split audio data into chunks based on byte size.
        This is used when pydub is not available or fails.

        Args:
            audio_bytes (bytes): The audio data to split
            chunk_size_mb (int): Target size for each chunk in MB

        Returns:
            list: List of byte arrays containing the audio chunks
        """
        self.logger.info(f"Using simple byte-based chunking for audio file of size {len(audio_bytes)/(1024*1024):.2f} MB")

        # Convert chunk size to bytes
        chunk_size_bytes = chunk_size_mb * 1024 * 1024

        # If the file is smaller than the chunk size, return it as is
        if len(audio_bytes) <= chunk_size_bytes:
            return [audio_bytes]

        # Calculate number of chunks
        num_chunks = math.ceil(len(audio_bytes) / chunk_size_bytes)
        self.logger.info(f"Splitting audio into {num_chunks} chunks")

        # Create chunks
        chunks = []
        for i in range(num_chunks):
            start_byte = i * chunk_size_bytes
            end_byte = min((i + 1) * chunk_size_bytes, len(audio_bytes))

            # Get the chunk
            chunk = audio_bytes[start_byte:end_byte]
            chunks.append(chunk)

            self.logger.info(f"Created simple chunk {i+1}/{num_chunks}: {len(chunk)/(1024*1024):.2f} MB")

        self.logger.warning("Simple byte-based chunking may result in corrupted audio chunks. Results may be unreliable.")
        return chunks

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

    def _transcribe_chunked_audio(self, audio_data, language, model_name="gemini", chunk_size_mb=5):
        """
        Transcribe a large audio file by splitting it into smaller chunks and combining the results.
        Memory-optimized version that processes chunks sequentially and cleans up after each chunk.

        Args:
            audio_data (bytes): The audio data to transcribe
            language (str): The language code
            model_name (str): The model name to use
            chunk_size_mb (int): Size of each chunk in MB

        Returns:
            str: The combined transcribed text
        """
        file_size_mb = len(audio_data) / (1024 * 1024)
        self.logger.info(f"Using chunked transcription for large file ({file_size_mb:.2f} MB) with {chunk_size_mb}MB chunks")

        # Split the audio into chunks
        chunks = self._chunk_audio_file(audio_data, chunk_size_mb=chunk_size_mb)

        # Free up memory by clearing the original audio data
        del audio_data

        if len(chunks) == 1:
            self.logger.info("Chunking resulted in a single chunk, proceeding with normal transcription")
            result = self._transcribe_with_gemini_internal(chunks[0], language, model_name)
            # Free memory
            del chunks
            return result

        # Transcribe each chunk with memory cleanup after each
        transcriptions = []
        total_chunks = len(chunks)

        for i in range(total_chunks):
            # Get the current chunk and immediately free memory for other chunks
            chunk = chunks[i]

            # Log progress
            chunk_size_mb = len(chunk) / (1024 * 1024)
            self.logger.info(f"Transcribing chunk {i+1}/{total_chunks} ({chunk_size_mb:.2f} MB)")

            try:
                # Transcribe this chunk
                chunk_transcription = self._transcribe_with_gemini_internal(chunk, language, model_name)
                transcriptions.append(chunk_transcription)
                self.logger.info(f"Successfully transcribed chunk {i+1}: {len(chunk_transcription)} characters")

                # Free memory
                del chunk_transcription
            except Exception as e:
                self.logger.error(f"Error transcribing chunk {i+1}: {str(e)}")
                # Continue with other chunks even if one fails
                transcriptions.append(f"[Error transcribing part {i+1}]")
            finally:
                # Free memory for this chunk
                del chunk

                # Force garbage collection to free memory
                try:
                    import gc
                    gc.collect()
                except:
                    pass

        # Combine the transcriptions
        combined_transcription = " ".join(transcriptions)
        self.logger.info(f"Combined transcription from {total_chunks} chunks: {len(combined_transcription)} characters")

        # Free memory
        del chunks
        del transcriptions

        return combined_transcription

    def transcribe_with_gemini(self, audio_data, language, model_name="gemini"):
        """
        Transcribe audio using Google's Gemini model.
        For large files, this method will automatically use chunking to improve reliability.

        Args:
            audio_data (bytes): The audio data to transcribe
            language (str): The language code
            model_name (str): The model name to use

        Returns:
            str: The transcribed text
        """
        # Calculate file size in MB
        file_size_mb = len(audio_data) / (1024 * 1024)

        # For files over 15MB, use chunking to avoid memory issues and "not in an ACTIVE state" errors
        # Lower threshold to prevent memory issues on Render's free tier
        CHUNKING_THRESHOLD_MB = 15

        # Use smaller chunks for larger files to reduce memory usage
        chunk_size_mb = 5  # Default to 5MB chunks

        # Adjust chunk size based on file size
        if file_size_mb > 100:
            chunk_size_mb = 3  # Use smaller chunks for very large files
        elif file_size_mb > 50:
            chunk_size_mb = 4  # Use medium chunks for large files

        if file_size_mb > CHUNKING_THRESHOLD_MB:
            self.logger.info(f"Large file detected ({file_size_mb:.2f} MB). Using chunked transcription with {chunk_size_mb}MB chunks.")

            # Always try to use chunking for files over the threshold
            # For extremely large files (>50MB), force chunking even if pydub is not available
            if not PYDUB_AVAILABLE:
                self.logger.warning(f"Pydub not available. Using simple byte-based chunking for {file_size_mb:.2f} MB file.")
                return self._transcribe_chunked_audio(audio_data, language, model_name, chunk_size_mb=chunk_size_mb)

            # Use memory-optimized chunking
            return self._transcribe_chunked_audio(audio_data, language, model_name, chunk_size_mb=chunk_size_mb)

        # For smaller files or when chunking is not available, use the standard transcription method
        return self._transcribe_with_gemini_internal(audio_data, language, model_name)

    def _transcribe_with_gemini_internal(self, audio_data, language, model_name="gemini"):
        """
        Internal method to transcribe audio using Google's Gemini model.
        Used by both the main transcribe_with_gemini method and the chunked transcription method.

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
                    # For files larger than 15MB, use Files API directly
                    file_size_mb = len(audio_bytes) / (1024 * 1024)
                    self.logger.info(f"Audio file size: {file_size_mb:.2f} MB")

                    # Set threshold for using Files API directly (15MB)
                    # Increased from 5MB to 15MB to avoid worker timeouts with the Files API
                    FILES_API_THRESHOLD_MB = 15

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
                                self.logger.info(f"File uploaded successfully with name: {file_obj.name}")

                                # Wait for file to be processed (reach ACTIVE state)
                                # This is necessary for large files to avoid "not in an ACTIVE state" errors
                                max_wait_time = 20  # Maximum wait time in seconds (reduced to avoid worker timeout)
                                wait_interval = 1   # Check interval in seconds (reduced to check more frequently)
                                max_attempts = 5    # Maximum number of attempts to check file state
                                wait_start_time = time.time()
                                attempts = 0

                                # Check if file is already in ACTIVE state (could be numeric 2 or string "ACTIVE")
                                is_active = (
                                    (isinstance(file_obj.state, str) and file_obj.state == "ACTIVE") or
                                    (isinstance(file_obj.state, int) and file_obj.state == 2)  # 2 appears to be the numeric code for ACTIVE
                                )

                                self.logger.info(f"Checking file state: {file_obj.state} (type: {type(file_obj.state).__name__})")

                                # Only wait if file is not already active
                                if not is_active:
                                    while attempts < max_attempts:
                                        attempts += 1
                                        elapsed_wait = time.time() - wait_start_time

                                        if elapsed_wait > max_wait_time:
                                            self.logger.warning(f"Timed out waiting for file to become ACTIVE after {elapsed_wait:.1f} seconds")
                                            break

                                        # For files over 10MB, we'll try to use it anyway after a few attempts
                                        # since waiting longer risks worker timeout
                                        if file_size_mb > 10 and attempts >= 3:
                                            self.logger.warning(f"Large file ({file_size_mb:.2f} MB): proceeding after {attempts} attempts to avoid timeout")
                                            break

                                        self.logger.info(f"File is not yet ACTIVE (current state: {file_obj.state}). Attempt {attempts}/{max_attempts}, waiting {wait_interval}s...")
                                        time.sleep(wait_interval)

                                        # Get updated file state
                                        try:
                                            file_obj = genai.get_file(name=file_obj.name)
                                            self.logger.info(f"Updated file state: {file_obj.state} (type: {type(file_obj.state).__name__})")

                                            # Check if file is now active
                                            is_active = (
                                                (isinstance(file_obj.state, str) and file_obj.state == "ACTIVE") or
                                                (isinstance(file_obj.state, int) and file_obj.state == 2)
                                            )

                                            if is_active:
                                                self.logger.info("File is now ACTIVE and ready for processing")
                                                break

                                        except Exception as state_error:
                                            self.logger.error(f"Error checking file state: {str(state_error)}")
                                            # Continue with the file we have
                                            break

                                # Log final state
                                if is_active:
                                    self.logger.info(f"File is in ACTIVE state and ready for processing")
                                else:
                                    self.logger.warning(f"Proceeding with file in non-ACTIVE state: {file_obj.state}")

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
                            elif "not in an active state" in error_msg or "failedprecondition" in error_msg:
                                self.logger.error("File is not in an ACTIVE state - the file was uploaded but not fully processed")
                                self.logger.info("This usually happens with large files. The system will try to use the file anyway.")

                                # Try to use the file anyway as a last resort
                                try:
                                    self.logger.warning("Attempting to use file despite non-ACTIVE state...")
                                    prompt = f"Please transcribe the following audio. The language is {language}." if language and language != "auto" else "Please transcribe this audio."

                                    # Generate content with the file
                                    response = model.generate_content([
                                        prompt,
                                        file_obj
                                    ], generation_config=generation_config)

                                    # Extract the transcription
                                    transcription = response.text

                                    # Clean up any bracketed artifacts at the end
                                    cleaned_transcription = self._clean_gemini_transcription(transcription)

                                    self.logger.info(f"Successfully transcribed despite file state issue: {len(cleaned_transcription)} characters")
                                    return cleaned_transcription

                                except Exception as retry_error:
                                    self.logger.error(f"Failed retry attempt with non-ACTIVE file: {str(retry_error)}")
                                    # Continue to the original exception

                            # If we get here, all attempts have failed
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
                                    self.logger.info(f"File uploaded successfully with name: {file_obj.name}")

                                    # Wait for file to be processed (reach ACTIVE state)
                                    # This is necessary for large files to avoid "not in an ACTIVE state" errors
                                    max_wait_time = 20  # Maximum wait time in seconds (reduced to avoid worker timeout)
                                    wait_interval = 1   # Check interval in seconds (reduced to check more frequently)
                                    max_attempts = 5    # Maximum number of attempts to check file state
                                    wait_start_time = time.time()
                                    attempts = 0

                                    # Check if file is already in ACTIVE state (could be numeric 2 or string "ACTIVE")
                                    is_active = (
                                        (isinstance(file_obj.state, str) and file_obj.state == "ACTIVE") or
                                        (isinstance(file_obj.state, int) and file_obj.state == 2)  # 2 appears to be the numeric code for ACTIVE
                                    )

                                    self.logger.info(f"Checking file state: {file_obj.state} (type: {type(file_obj.state).__name__})")

                                    # Only wait if file is not already active
                                    if not is_active:
                                        while attempts < max_attempts:
                                            attempts += 1
                                            elapsed_wait = time.time() - wait_start_time

                                            if elapsed_wait > max_wait_time:
                                                self.logger.warning(f"Timed out waiting for file to become ACTIVE after {elapsed_wait:.1f} seconds")
                                                break

                                            # For files over 10MB, we'll try to use it anyway after a few attempts
                                            # since waiting longer risks worker timeout
                                            if file_size_mb > 10 and attempts >= 3:
                                                self.logger.warning(f"Large file ({file_size_mb:.2f} MB): proceeding after {attempts} attempts to avoid timeout")
                                                break

                                            self.logger.info(f"File is not yet ACTIVE (current state: {file_obj.state}). Attempt {attempts}/{max_attempts}, waiting {wait_interval}s...")
                                            time.sleep(wait_interval)

                                            # Get updated file state
                                            try:
                                                file_obj = genai.get_file(name=file_obj.name)
                                                self.logger.info(f"Updated file state: {file_obj.state} (type: {type(file_obj.state).__name__})")

                                                # Check if file is now active
                                                is_active = (
                                                    (isinstance(file_obj.state, str) and file_obj.state == "ACTIVE") or
                                                    (isinstance(file_obj.state, int) and file_obj.state == 2)
                                                )

                                                if is_active:
                                                    self.logger.info("File is now ACTIVE and ready for processing")
                                                    break

                                            except Exception as state_error:
                                                self.logger.error(f"Error checking file state: {str(state_error)}")
                                                # Continue with the file we have
                                                break

                                    # Log final state
                                    if is_active:
                                        self.logger.info(f"File is in ACTIVE state and ready for processing")
                                    else:
                                        self.logger.warning(f"Proceeding with file in non-ACTIVE state: {file_obj.state}")

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
                                elif "not in an active state" in error_msg or "failedprecondition" in error_msg:
                                    self.logger.error("File is not in an ACTIVE state - the file was uploaded but not fully processed")
                                    self.logger.info("This usually happens with large files. The system will try to use the file anyway.")

                                    # Try to use the file anyway as a last resort
                                    try:
                                        self.logger.warning("Attempting to use file despite non-ACTIVE state...")
                                        prompt = f"Please transcribe the following audio. The language is {language}." if language and language != "auto" else "Please transcribe this audio."

                                        # Generate content with the file
                                        response = model.generate_content([
                                            prompt,
                                            file_obj
                                        ], generation_config=generation_config)

                                        # Extract the transcription
                                        transcription = response.text

                                        # Clean up any bracketed artifacts at the end
                                        cleaned_transcription = self._clean_gemini_transcription(transcription)

                                        self.logger.info(f"Successfully transcribed despite file state issue: {len(cleaned_transcription)} characters")
                                        return cleaned_transcription

                                    except Exception as retry_error:
                                        self.logger.error(f"Failed retry attempt with non-ACTIVE file: {str(retry_error)}")
                                        # Continue to the original exception

                                # If we get here, all attempts have failed
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
                    elif "not in an active state" in error_msg:
                        self.logger.error("File is not in an ACTIVE state - the file was uploaded but not fully processed")
                        self.logger.info("This usually happens with large files. Try increasing the wait time or reducing file size.")

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
