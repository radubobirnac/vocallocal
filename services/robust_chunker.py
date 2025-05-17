"""
Robust audio chunking and transcription service for VocalLocal.
Designed for production use with proper error handling, parallel processing,
and graceful shutdown.
"""
import os
import sys
import json
import time
import signal
import logging
import tempfile
import threading
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("robust_chunker")

class RobustChunker:
    """
    Production-ready audio chunking and transcription service.
    Follows a strict protocol for error handling, resource management,
    and parallel processing.
    """

    def __init__(self,
                 input_path: Optional[str] = None,
                 output_dir: Optional[str] = None,
                 chunk_seconds: Optional[int] = None,
                 max_retries: Optional[int] = None,
                 retry_delay: Optional[int] = None,
                 transcription_service = None):
        """
        Initialize the RobustChunker with environment variables or provided values.

        Args:
            input_path: Path to input audio file (overrides INPUT_PATH env var)
            output_dir: Directory for output chunks (overrides OUTPUT_DIR env var)
            chunk_seconds: Duration of each chunk in seconds (overrides CHUNK_SECONDS env var)
            max_retries: Maximum retry attempts (overrides MAX_RETRIES env var)
            retry_delay: Delay between retries in seconds (overrides RETRY_DELAY env var)
            transcription_service: Service to use for transcription
        """
        # Read from environment variables with fallbacks to provided values or defaults
        self.input_path = input_path or os.environ.get('INPUT_PATH')
        self.output_dir = output_dir or os.environ.get('OUTPUT_DIR') or tempfile.mkdtemp()
        self.chunk_seconds = int(chunk_seconds or os.environ.get('CHUNK_SECONDS', 300))
        self.max_retries = int(max_retries or os.environ.get('MAX_RETRIES', 2))
        self.retry_delay = int(retry_delay or os.environ.get('RETRY_DELAY', 2))
        self.transcription_service = transcription_service

        # Determine input file extension
        if self.input_path:
            self.input_ext = Path(self.input_path).suffix.lstrip('.')
        else:
            self.input_ext = "mp3"  # Default extension

        # Set up heartbeat and shutdown flags
        self.shutdown_requested = False
        self.heartbeat_thread = None

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        logger.info(f"Initialized RobustChunker with: chunk_seconds={self.chunk_seconds}, "
                   f"max_retries={self.max_retries}, retry_delay={self.retry_delay}")

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        self.shutdown_requested = True

    def _start_heartbeat(self):
        """Start a heartbeat thread to keep the worker alive."""
        def _heartbeat():
            while not self.shutdown_requested:
                logger.debug("Heartbeat ping")
                sys.stdout.flush()  # Ensure output is flushed to keep worker alive
                time.sleep(5)

        self.heartbeat_thread = threading.Thread(target=_heartbeat, daemon=True)
        self.heartbeat_thread.start()
        logger.info("Started heartbeat thread")

    def _stop_heartbeat(self):
        """Stop the heartbeat thread."""
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.shutdown_requested = True
            self.heartbeat_thread.join(timeout=1)
            logger.info("Stopped heartbeat thread")

    def prepare_output_directory(self) -> bool:
        """
        Ensure the output directory exists.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            logger.info(f"Prepared output directory: {self.output_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to create output directory: {str(e)}")
            return False

    def chunk_audio(self) -> Tuple[bool, List[str], str]:
        """
        Chunk the audio file using FFmpeg with retries.

        Returns:
            Tuple[bool, List[str], str]: (success, chunk_files, error_message)
        """
        if not self.input_path:
            return False, [], "No input path specified"

        if not os.path.exists(self.input_path):
            return False, [], f"Input file not found: {self.input_path}"

        # Ensure output directory exists
        if not self.prepare_output_directory():
            return False, [], f"Failed to prepare output directory: {self.output_dir}"

        # Build FFmpeg command
        output_pattern = os.path.join(self.output_dir, f"chunk_%03d.{self.input_ext}")
        cmd = [
            "ffmpeg", "-y",
            "-i", self.input_path,
            "-f", "segment",
            "-segment_time", str(self.chunk_seconds),
            "-c", "copy",
            output_pattern
        ]

        # Try to run FFmpeg with retries
        success = False
        error_message = ""

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Running FFmpeg chunking (attempt {attempt+1}/{self.max_retries+1})")
                result = subprocess.run(
                    cmd,
                    check=True,
                    timeout=self.chunk_seconds + 10,
                    capture_output=True,
                    text=True
                )
                success = True
                logger.info("FFmpeg chunking completed successfully")
                break
            except subprocess.TimeoutExpired as e:
                error_message = f"FFmpeg timed out after {self.chunk_seconds + 10} seconds"
                logger.warning(f"{error_message} (attempt {attempt+1})")
            except subprocess.CalledProcessError as e:
                error_message = f"FFmpeg error: {e.stderr}"
                logger.warning(f"{error_message} (attempt {attempt+1})")
            except Exception as e:
                error_message = f"Unexpected error: {str(e)}"
                logger.warning(f"{error_message} (attempt {attempt+1})")

            if attempt < self.max_retries:
                logger.info(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)

        if not success:
            return False, [], f"Chunking failed after {self.max_retries + 1} attempts: {error_message}"

        # Get all created chunk files
        chunk_files = sorted([
            os.path.join(self.output_dir, f)
            for f in os.listdir(self.output_dir)
            if f.startswith("chunk_") and f.endswith(f".{self.input_ext}")
        ])

        if not chunk_files:
            return False, [], "No chunks were created during FFmpeg processing"

        logger.info(f"Created {len(chunk_files)} chunks")
        return True, chunk_files, ""

    def validate_chunks(self, chunk_files: List[str]) -> Tuple[bool, List[str], str]:
        """
        Validate each chunk to ensure it's decodable.

        Args:
            chunk_files: List of chunk file paths

        Returns:
            Tuple[bool, List[str], str]: (success, valid_chunks, error_message)
        """
        valid_chunks = []

        for i, chunk_file in enumerate(chunk_files):
            try:
                logger.info(f"Validating chunk {i+1}/{len(chunk_files)}: {os.path.basename(chunk_file)}")
                result = subprocess.run(
                    ["ffmpeg", "-v", "error", "-i", chunk_file, "-f", "null", "-"],
                    check=True,
                    timeout=30,
                    capture_output=True,
                    text=True
                )
                valid_chunks.append(chunk_file)
            except subprocess.TimeoutExpired:
                logger.error(f"Validation timed out for chunk: {chunk_file}")
                return False, valid_chunks, f"Validation timed out for chunk: {os.path.basename(chunk_file)}"
            except subprocess.CalledProcessError as e:
                logger.error(f"Validation failed for chunk: {chunk_file}, error: {e.stderr}")
                return False, valid_chunks, f"Validation failed for chunk: {os.path.basename(chunk_file)}: {e.stderr}"
            except Exception as e:
                logger.error(f"Unexpected error validating chunk: {chunk_file}, error: {str(e)}")
                return False, valid_chunks, f"Unexpected error validating chunk: {os.path.basename(chunk_file)}: {str(e)}"

        logger.info(f"All {len(valid_chunks)} chunks validated successfully")
        return True, valid_chunks, ""

    def transcribe_chunk(self, chunk_file: str, language: str, model: str) -> Tuple[bool, str, str]:
        """
        Transcribe a single chunk.

        Args:
            chunk_file: Path to the chunk file
            language: Language code
            model: Model name

        Returns:
            Tuple[bool, str, str]: (success, transcription, error_message)
        """
        try:
            # Read the chunk file
            with open(chunk_file, 'rb') as f:
                chunk_data = f.read()

            # Get chunk size for logging
            chunk_size_mb = len(chunk_data) / (1024 * 1024)
            logger.info(f"Transcribing chunk {os.path.basename(chunk_file)} ({chunk_size_mb:.2f} MB)")

            # Call the transcription service
            if self.transcription_service:
                transcription = self.transcription_service._transcribe_with_gemini_internal(
                    chunk_data, language, model
                )
                return True, transcription, ""
            else:
                return False, "", "No transcription service available"

        except Exception as e:
            logger.error(f"Error transcribing chunk {chunk_file}: {str(e)}")
            return False, "", f"Error transcribing chunk {os.path.basename(chunk_file)}: {str(e)}"

    def transcribe_chunks_parallel(self, chunk_files: List[str], language: str, model: str) -> Tuple[bool, List[Tuple[str, str]], str]:
        """
        Transcribe chunks in parallel using a thread pool.

        Args:
            chunk_files: List of chunk file paths
            language: Language code
            model: Model name

        Returns:
            Tuple[bool, List[Tuple[str, str]], str]: (success, [(chunk_file, transcription)], error_message)
        """
        # Start heartbeat to keep worker alive during long-running operation
        self._start_heartbeat()

        try:
            results = []
            failed_chunks = []

            # Use a thread pool to process chunks in parallel
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Submit all transcription tasks
                future_to_chunk = {
                    executor.submit(self.transcribe_chunk, chunk_file, language, model): chunk_file
                    for chunk_file in chunk_files
                }

                # Process results as they complete
                for future in as_completed(future_to_chunk):
                    chunk_file = future_to_chunk[future]
                    try:
                        success, transcription, error = future.result()
                        if success:
                            results.append((chunk_file, transcription))
                            logger.info(f"Successfully transcribed {os.path.basename(chunk_file)}")
                        else:
                            failed_chunks.append((chunk_file, error))
                            logger.error(f"Failed to transcribe {os.path.basename(chunk_file)}: {error}")
                    except Exception as e:
                        failed_chunks.append((chunk_file, str(e)))
                        logger.error(f"Exception while transcribing {os.path.basename(chunk_file)}: {str(e)}")

            # Check if any chunks failed
            if failed_chunks:
                error_message = f"Failed to transcribe {len(failed_chunks)} chunks: " + \
                               ", ".join([os.path.basename(c) for c, _ in failed_chunks])
                return False, results, error_message

            # Sort results by chunk file name to maintain original order
            results.sort(key=lambda x: os.path.basename(x[0]))

            return True, results, ""

        finally:
            # Stop heartbeat
            self._stop_heartbeat()

    def cleanup_chunks(self, chunk_files: List[str]) -> None:
        """
        Delete chunk files to free disk space.

        Args:
            chunk_files: List of chunk file paths
        """
        for chunk_file in chunk_files:
            try:
                os.remove(chunk_file)
                logger.debug(f"Removed chunk file: {os.path.basename(chunk_file)}")
            except Exception as e:
                logger.warning(f"Failed to remove chunk file {os.path.basename(chunk_file)}: {str(e)}")

        logger.info(f"Cleaned up {len(chunk_files)} chunk files")

    def process_audio_file(self, input_path: str, language: str, model: str) -> Dict[str, Any]:
        """
        Process an audio file: chunk, validate, transcribe, and cleanup.

        Args:
            input_path: Path to the input audio file
            language: Language code
            model: Model name

        Returns:
            Dict[str, Any]: Result with status, chunks, and transcript
        """
        # Set input path
        self.input_path = input_path
        self.input_ext = Path(input_path).suffix.lstrip('.')

        # Step 1: Chunk the audio file
        success, chunk_files, error = self.chunk_audio()
        if not success:
            return {
                "status": "error",
                "message": error
            }

        # Step 2: Validate the chunks
        success, valid_chunks, error = self.validate_chunks(chunk_files)
        if not success:
            # Clean up any created chunks
            self.cleanup_chunks(chunk_files)
            return {
                "status": "error",
                "message": error
            }

        # Step 3: Transcribe chunks in parallel
        success, transcription_results, error = self.transcribe_chunks_parallel(valid_chunks, language, model)

        # Step 4: Combine transcriptions and clean up
        chunk_names = [os.path.basename(chunk) for chunk in valid_chunks]

        if success:
            # Extract transcriptions in the correct order
            transcriptions = [t for _, t in transcription_results]
            combined_transcript = " ".join(transcriptions)

            # Clean up chunks
            self.cleanup_chunks(valid_chunks)

            return {
                "status": "ok",
                "chunks": chunk_names,
                "transcript": combined_transcript
            }
        else:
            # Clean up chunks even on failure
            self.cleanup_chunks(valid_chunks)

            return {
                "status": "error",
                "message": error,
                "chunks": chunk_names,
                "partial_results": [
                    {"chunk": os.path.basename(chunk), "text": text}
                    for chunk, text in transcription_results
                ]
            }

    @staticmethod
    def run_stress_test(
        transcription_service,
        test_files: List[Tuple[str, int]],  # [(file_path, size_mb)]
        concurrency_levels: List[int] = [1, 5, 10],
        language: str = "en",
        model: str = "gemini"
    ) -> Dict[str, Any]:
        """
        Run stress tests with various file sizes and concurrency levels.

        Args:
            transcription_service: Service to use for transcription
            test_files: List of (file_path, size_mb) tuples
            concurrency_levels: List of concurrency levels to test
            language: Language code
            model: Model name

        Returns:
            Dict[str, Any]: Test results
        """
        results = {
            "status": "ok",
            "tests": []
        }

        for file_path, size_mb in test_files:
            for concurrency in concurrency_levels:
                logger.info(f"Running stress test: file={file_path} ({size_mb}MB), concurrency={concurrency}")

                # Create temporary output directories
                output_dirs = [tempfile.mkdtemp() for _ in range(concurrency)]

                # Create chunkers
                chunkers = [
                    RobustChunker(
                        input_path=file_path,
                        output_dir=output_dir,
                        transcription_service=transcription_service
                    )
                    for output_dir in output_dirs
                ]

                # Start timing
                start_time = time.time()

                # Run in parallel
                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = [
                        executor.submit(chunker.process_audio_file, file_path, language, model)
                        for chunker in chunkers
                    ]

                    # Collect results
                    test_results = []
                    for future in as_completed(futures):
                        try:
                            result = future.result()
                            test_results.append(result)
                        except Exception as e:
                            test_results.append({
                                "status": "error",
                                "message": f"Exception in test: {str(e)}"
                            })

                # Calculate elapsed time
                elapsed_time = time.time() - start_time

                # Clean up
                for output_dir in output_dirs:
                    try:
                        import shutil
                        shutil.rmtree(output_dir, ignore_errors=True)
                    except:
                        pass

                # Record results
                success_count = sum(1 for r in test_results if r["status"] == "ok")

                results["tests"].append({
                    "file_size_mb": size_mb,
                    "concurrency": concurrency,
                    "elapsed_time": elapsed_time,
                    "success_count": success_count,
                    "total_count": concurrency,
                    "success_rate": success_count / concurrency
                })

                logger.info(f"Test completed: success_rate={success_count}/{concurrency}, time={elapsed_time:.2f}s")

        return results
