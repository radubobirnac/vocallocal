"""Audio chunking service for VocalLocal using FFmpeg."""
import os
import time
import logging
import tempfile
import subprocess
import threading
from pathlib import Path
from typing import List, Optional, Tuple

class AudioChunker:
    """
    A robust audio chunking service that uses FFmpeg to split audio files into chunks.
    Designed for production use with retry logic, validation, and proper resource management.
    """

    def __init__(self, max_retries: int = 2, retry_delay: int = 2, chunk_duration: int = 300):
        """
        Initialize the AudioChunker.

        Args:
            max_retries: Maximum number of retries for chunking operations
            retry_delay: Delay between retries in seconds
            chunk_duration: Duration of each chunk in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.chunk_duration = chunk_duration
        self.logger = logging.getLogger("audio_chunker")

    def chunk_audio(self, input_data: bytes, format: str = "webm") -> List[bytes]:
        """
        Chunk audio data using FFmpeg's segment muxer with robust error handling.

        Args:
            input_data: Audio data to chunk
            format: Audio format (webm, mp3, etc.)

        Returns:
            List of audio chunks as bytes

        Raises:
            RuntimeError: If chunking fails after all retries
        """
        # Create temp directory and input file
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, f"input.{format}")

        try:
            # Write input data to file
            with open(input_path, "wb") as f:
                f.write(input_data)

            # Free memory
            del input_data

            # Run chunking with retries
            output_pattern = os.path.join(temp_dir, f"chunk_%03d.{format}")
            self._run_chunking_with_retries(input_path, output_pattern)

            # Validate and load chunks
            chunks = self._validate_and_load_chunks(temp_dir, format)

            return chunks

        finally:
            # Clean up
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                self.logger.warning(f"Failed to clean up temp directory: {e}")

    def _run_chunking_with_retries(self, input_path: str, output_pattern: str) -> None:
        """
        Run FFmpeg chunking with retries.

        Args:
            input_path: Path to input audio file
            output_pattern: Pattern for output chunk files

        Raises:
            RuntimeError: If chunking fails after all retries
        """
        for attempt in range(self.max_retries + 1):
            try:
                cmd = [
                    "ffmpeg", "-y",
                    "-i", input_path,
                    "-f", "segment",
                    "-segment_time", str(self.chunk_duration),
                    "-c", "copy",
                    "-reset_timestamps", "1",
                    "-map", "0",
                    output_pattern
                ]

                self.logger.info(f"Running FFmpeg chunking (attempt {attempt+1}/{self.max_retries+1})")
                result = subprocess.run(
                    cmd,
                    check=True,
                    timeout=self.chunk_duration + 30,
                    capture_output=True,
                    text=True
                )

                self.logger.info("FFmpeg chunking completed successfully")
                return

            except subprocess.TimeoutExpired:
                self.logger.warning(f"FFmpeg chunking timed out (attempt {attempt+1})")
            except subprocess.CalledProcessError as e:
                self.logger.warning(f"FFmpeg chunking failed (attempt {attempt+1}): {e.stderr}")
            except Exception as e:
                self.logger.warning(f"Unexpected error during chunking (attempt {attempt+1}): {str(e)}")

            if attempt < self.max_retries:
                self.logger.info(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
            else:
                raise RuntimeError(f"Audio chunking failed after {self.max_retries} retries")

    def _validate_and_load_chunks(self, temp_dir: str, format: str) -> List[bytes]:
        """
        Validate and load chunks into memory.

        Args:
            temp_dir: Directory containing chunk files
            format: Audio format

        Returns:
            List of audio chunks as bytes

        Raises:
            RuntimeError: If no valid chunks are found
        """
        chunk_files = sorted([
            os.path.join(temp_dir, f)
            for f in os.listdir(temp_dir)
            if f.startswith("chunk_")
        ])

        if not chunk_files:
            raise RuntimeError("No chunks were created during FFmpeg processing")

        self.logger.info(f"Found {len(chunk_files)} chunks to validate")

        chunks = []
        for i, chunk_file in enumerate(chunk_files):
            # Validate chunk
            try:
                self.logger.info(f"Validating chunk {i+1}/{len(chunk_files)}")
                subprocess.run(
                    ["ffmpeg", "-v", "error", "-i", chunk_file, "-f", "null", "-"],
                    check=True,
                    timeout=30,
                    capture_output=True
                )

                # Load chunk into memory
                with open(chunk_file, "rb") as f:
                    chunk_data = f.read()
                    chunk_size_mb = len(chunk_data) / (1024 * 1024)
                    self.logger.info(f"Loaded chunk {i+1}: {chunk_size_mb:.2f} MB")
                    chunks.append(chunk_data)

            except subprocess.CalledProcessError:
                self.logger.warning(f"Chunk {i+1} validation failed, skipping")
            except Exception as e:
                self.logger.warning(f"Error processing chunk {i+1}: {str(e)}")

        if not chunks:
            raise RuntimeError("All chunks failed validation")

        return chunks

    def chunk_audio_in_thread(self, input_data: bytes, format: str = "webm",
                              callback: Optional[callable] = None) -> threading.Thread:
        """
        Run chunking in a separate thread to avoid blocking.

        Args:
            input_data: Audio data to chunk
            format: Audio format
            callback: Function to call with chunks when complete

        Returns:
            Thread object running the chunking operation
        """
        def _run_chunking():
            try:
                chunks = self.chunk_audio(input_data, format)
                if callback:
                    callback(chunks, None)
            except Exception as e:
                self.logger.error(f"Error in chunking thread: {str(e)}")
                if callback:
                    callback(None, str(e))

        thread = threading.Thread(target=_run_chunking)
        thread.daemon = True
        thread.start()
        return thread


class RobustChunker:
    """
    Production-ready audio chunking service for VocalLocal.
    Processes audio files using FFmpeg's segment muxer.
    """

    def __init__(self, input_path=None, output_dir=None, chunk_seconds=300):
        """
        Initialize the RobustChunker.

        Args:
            input_path: Path to input audio file
            output_dir: Directory for output chunks
            chunk_seconds: Duration of each chunk in seconds
        """
        self.input_path = input_path
        self.output_dir = output_dir
        self.chunk_seconds = chunk_seconds
        self.logger = logging.getLogger("robust_chunker")

    def prepare_output_directory(self):
        """Ensure the output directory exists."""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.logger.info(f"Prepared output directory: {self.output_dir}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create output directory: {str(e)}")
            return False

    def chunk_audio(self) -> Tuple[bool, List[str], str]:
        """
        Chunk the audio file using FFmpeg.

        Returns:
            Tuple[bool, List[str], str]: (success, chunk_files, error_message)
        """
        if not self.input_path:
            return False, [], "No input path specified"

        if not os.path.exists(self.input_path):
            return False, [], f"Input file not found: {self.input_path}"

        if not self.output_dir:
            return False, [], "No output directory specified"

        # Ensure output directory exists
        if not self.prepare_output_directory():
            return False, [], f"Failed to prepare output directory: {self.output_dir}"

        # Get file extension
        file_ext = Path(self.input_path).suffix.lstrip('.')
        if not file_ext:
            file_ext = "mp3"  # Default extension

        # Build FFmpeg command
        output_pattern = os.path.join(self.output_dir, f"chunk_%03d.{file_ext}")
        cmd = [
            "ffmpeg", "-y",
            "-i", self.input_path,
            "-f", "segment",
            "-segment_time", str(self.chunk_seconds),
            "-c", "copy",
            output_pattern
        ]

        # Run FFmpeg
        try:
            self.logger.info(f"Running FFmpeg chunking for {self.input_path}")
            subprocess.run(
                cmd,
                check=True,
                timeout=self.chunk_seconds + 30,
                capture_output=True,
                text=True
            )

            # Get created chunk files
            chunk_files = sorted([
                os.path.join(self.output_dir, f)
                for f in os.listdir(self.output_dir)
                if f.startswith("chunk_") and f.endswith(f".{file_ext}")
            ])

            if not chunk_files:
                return False, [], "No chunks were created during FFmpeg processing"

            self.logger.info(f"Created {len(chunk_files)} chunks")
            return True, chunk_files, ""

        except subprocess.TimeoutExpired:
            return False, [], f"FFmpeg timed out after {self.chunk_seconds + 30} seconds"
        except subprocess.CalledProcessError as e:
            return False, [], f"FFmpeg error: {e.stderr}"
        except Exception as e:
            return False, [], f"Unexpected error: {str(e)}"
