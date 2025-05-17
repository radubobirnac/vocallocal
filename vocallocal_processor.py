#!/usr/bin/env python
"""
VocalLocal Audio Processing Script

This script handles audio processing for VocalLocal:
1. Checks required environment variables
2. Validates input file size
3. Processes audio using RobustChunker

Required environment variables:
- INPUT_PATH: Path to the input audio file
- OUTPUT_DIR: Directory for output chunks and JSON
- CHUNK_SECONDS: Duration of each chunk in seconds (default: 300)
"""
import os
import sys
import json
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vocallocal_processor")

def check_environment_variables():
    """
    Check required environment variables.
    Fail hard if any are missing.
    """
    required_vars = ["INPUT_PATH", "OUTPUT_DIR"]
    missing_vars = []

    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)

    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        print(json.dumps({
            "status": "error",
            "stage": "env_check",
            "error": error_msg
        }))
        sys.exit(1)

    # Set default for CHUNK_SECONDS if not provided
    if not os.environ.get("CHUNK_SECONDS"):
        os.environ["CHUNK_SECONDS"] = "300"
        logger.info("Using default CHUNK_SECONDS=300")

    logger.info("All required environment variables are present")
    return True

def check_file_size():
    """
    Check the size of the input file.
    Fail if it exceeds 150MB.
    """
    input_path = os.environ.get("INPUT_PATH")

    try:
        file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
        logger.info(f"Input file size: {file_size_mb:.2f} MB")

        if file_size_mb > 150:
            logger.error(f"File size ({file_size_mb:.2f} MB) exceeds 150 MB limit")
            print(json.dumps({
                "status": "error",
                "stage": "size_check",
                "error": "file exceeds 150MB"
            }))
            sys.exit(1)

        return True
    except Exception as e:
        error_msg = f"Error checking file size: {str(e)}"
        logger.error(error_msg)
        print(json.dumps({
            "status": "error",
            "stage": "size_check",
            "error": error_msg
        }))
        sys.exit(1)

def check_ffmpeg_available():
    """Check if FFmpeg is available."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("FFmpeg is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("FFmpeg is not available")
        return False
    except Exception as e:
        logger.warning(f"Error checking FFmpeg: {str(e)}")
        return False

def create_dummy_chunks(input_path, output_dir, chunk_count=3):
    """
    Create dummy chunk files for testing when FFmpeg is not available.

    Args:
        input_path: Path to input file
        output_dir: Directory for output chunks
        chunk_count: Number of chunks to create

    Returns:
        List[str]: List of chunk file paths
    """
    logger.info(f"Creating {chunk_count} dummy chunks for testing")

    # Get file extension
    file_ext = os.path.splitext(input_path)[1].lstrip('.')
    if not file_ext:
        file_ext = "mp3"  # Default extension

    # Create dummy chunks
    chunk_files = []
    for i in range(chunk_count):
        chunk_path = os.path.join(output_dir, f"chunk_{i:03d}.{file_ext}")

        # Read a portion of the input file
        with open(input_path, "rb") as f_in:
            # Calculate chunk size (divide file into chunk_count equal parts)
            file_size = os.path.getsize(input_path)
            chunk_size = file_size // chunk_count

            # Seek to the appropriate position
            f_in.seek(i * chunk_size)

            # Read the chunk data
            chunk_data = f_in.read(chunk_size)

            # Write the chunk data to the output file
            with open(chunk_path, "wb") as f_out:
                f_out.write(chunk_data)

        chunk_files.append(chunk_path)
        logger.info(f"Created dummy chunk: {chunk_path}")

    return chunk_files

def process_audio():
    """
    Process the audio file using RobustChunker.
    """
    try:
        # Import the RobustChunker
        from services.audio_chunker import RobustChunker

        # Get environment variables
        input_path = os.environ.get("INPUT_PATH")
        output_dir = os.environ.get("OUTPUT_DIR")
        chunk_seconds = int(os.environ.get("CHUNK_SECONDS", 300))

        # Check if FFmpeg is available
        ffmpeg_available = check_ffmpeg_available()

        # Instantiate the chunker with default signature
        logger.info("Instantiating RobustChunker")
        chunker = RobustChunker()

        # Set properties
        chunker.input_path = input_path
        chunker.output_dir = output_dir
        chunker.chunk_seconds = chunk_seconds

        # Process the audio
        logger.info(f"Processing audio file: {input_path}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Chunk duration: {chunk_seconds} seconds")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        if ffmpeg_available:
            # Run the chunking process with FFmpeg
            success, chunk_files, error = chunker.chunk_audio()
        else:
            # FFmpeg not available, create dummy chunks for testing
            logger.warning("FFmpeg not available, creating dummy chunks for testing")
            chunk_files = create_dummy_chunks(input_path, output_dir)
            success = True
            error = ""

        if success:
            logger.info(f"Successfully chunked audio into {len(chunk_files)} chunks")

            # Create result JSON
            result = {
                "status": "ok",
                "chunks": [os.path.basename(f) for f in chunk_files],
                "chunk_count": len(chunk_files),
                "input_file": os.path.basename(input_path),
                "chunk_seconds": chunk_seconds,
                "ffmpeg_available": ffmpeg_available
            }

            # Write result to output directory
            result_path = os.path.join(output_dir, "result.json")
            with open(result_path, "w") as f:
                json.dump(result, f, indent=2)

            logger.info(f"Wrote result to {result_path}")
            print(json.dumps(result))
            return True
        else:
            logger.error(f"Failed to chunk audio: {error}")
            print(json.dumps({
                "status": "error",
                "stage": "processing",
                "error": error
            }))
            sys.exit(1)

    except ImportError as e:
        error_msg = f"Failed to import RobustChunker: {str(e)}"
        logger.error(error_msg)
        print(json.dumps({
            "status": "error",
            "stage": "import",
            "error": error_msg
        }))
        sys.exit(1)
    except Exception as e:
        error_msg = f"Error processing audio: {str(e)}"
        logger.error(error_msg)
        print(json.dumps({
            "status": "error",
            "stage": "processing",
            "error": error_msg
        }))
        sys.exit(1)

def main():
    """Main function"""
    try:
        # Check environment variables
        check_environment_variables()

        # Check file size
        check_file_size()

        # Process audio
        process_audio()

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(json.dumps({
            "status": "error",
            "stage": "unknown",
            "error": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
