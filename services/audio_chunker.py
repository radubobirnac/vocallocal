"""Audio chunking service for VocalLocal using FFmpeg."""
import os
import time
import logging
import tempfile
import subprocess
import threading
from typing import List, Optional, Dict, Any

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
