# VocalLocal Audio Processor

This is a build-and-runtime script for VocalLocal that handles audio processing. It reads environment variables, checks file sizes, and processes audio files using the RobustChunker.

## Requirements

- Python 3.6+
- FFmpeg (optional, will create dummy chunks if not available)

## Environment Variables

The script requires the following environment variables:

- `INPUT_PATH`: Path to the input audio file
- `OUTPUT_DIR`: Directory for output chunks and JSON
- `CHUNK_SECONDS`: Duration of each chunk in seconds (default: 300)

## Usage

### Direct Usage

```bash
# Set environment variables
export INPUT_PATH=/path/to/input.mp3
export OUTPUT_DIR=/path/to/output
export CHUNK_SECONDS=300

# Run the processor
python vocallocal_processor.py
```

### Using the Helper Script

```bash
# Run with specific input and output paths
python run_processor.py --input-path /path/to/input.mp3 --output-dir /path/to/output

# Create a test file and process it
python run_processor.py --create-test-file --test-file-size 10
```

## Process Flow

1. **Environment Check**: Verifies that all required environment variables are set.
2. **File Size Check**: Ensures the input file is not larger than 150MB.
3. **Audio Processing**: Chunks the audio file using RobustChunker.
4. **Output**: Generates a JSON result file and outputs the result to stdout.

## Output Format

The script outputs a JSON object with the following structure:

### Success

```json
{
  "status": "ok",
  "chunks": ["chunk_000.mp3", "chunk_001.mp3", "chunk_002.mp3"],
  "chunk_count": 3,
  "input_file": "input.mp3",
  "chunk_seconds": 300,
  "ffmpeg_available": true
}
```

### Error (File Too Large)

```json
{
  "status": "error",
  "stage": "size_check",
  "error": "file exceeds 150MB"
}
```

### Error (Missing Environment Variables)

```json
{
  "status": "error",
  "stage": "env_check",
  "error": "Missing required environment variables: INPUT_PATH, OUTPUT_DIR"
}
```

### Error (Processing)

```json
{
  "status": "error",
  "stage": "processing",
  "error": "FFmpeg error: ..."
}
```

## FFmpeg Support

The script checks if FFmpeg is available on the system. If FFmpeg is not available, it will create dummy chunks by splitting the input file into equal parts. This allows for testing without FFmpeg installed.

## File Size Limit

The script enforces a 150MB file size limit. If the input file is larger than 150MB, the script will exit with an error.

## Chunk Duration

The default chunk duration is 300 seconds (5 minutes). This can be changed by setting the `CHUNK_SECONDS` environment variable.

## Output Directory

The script will create the output directory if it doesn't exist. The output directory will contain:

- Chunk files (e.g., `chunk_000.mp3`, `chunk_001.mp3`, etc.)
- A `result.json` file with information about the chunks
