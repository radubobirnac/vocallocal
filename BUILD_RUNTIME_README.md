# VocalLocal Build and Runtime Engineer

This directory contains scripts for the VocalLocal build and runtime engineer, which handles environment setup, dependency checking, and runtime configuration for the VocalLocal application.

## Overview

The build and runtime engineer follows these steps:

1. **Patch Gunicorn settings** - Appends the string `--worker-class gthread --threads 4 --timeout 120 --graceful-timeout 120` to the existing `GUNICORN_CMD_ARGS` environment variable.
2. **Ensure runtime dependencies** - Checks for the `tiktoken` module and installs it if not present.
3. **Locate the RobustChunker signature** - Safely locates the `RobustChunker` class and determines the correct parameter names.
4. **Audio processing pipeline** - Sets up the audio processing pipeline with FFmpeg's segment muxer for chunking.
5. **Unit tests** - Runs unit tests if they exist.
6. **Load tests** - Runs load tests with different file sizes (1MB, 10MB, 20MB) if FFmpeg is available.

## Files

- `vocallocal_build_runtime.py` - Main script for the build and runtime engineer.
- `build_runtime_engineer.py` - Implementation of the build and runtime engineer.
- `run_build_engineer.py` - Helper script to run the build and runtime engineer with environment variables.
- `load_test.py` - Script to run load tests with different file sizes.

## Usage

### Basic Usage

```bash
python vocallocal_build_runtime.py
```

This will run the build and runtime engineer with default settings.

### Advanced Usage

```bash
python vocallocal_build_runtime.py --input-path /path/to/input.mp3 --output-dir /path/to/output --chunk-seconds 300
```

### Environment Variables

The following environment variables can be set:

- `INPUT_PATH` - Path to input audio file
- `OUTPUT_DIR` - Directory for output chunks
- `CHUNK_SECONDS` - Duration of each chunk in seconds (default: 300)
- `GUNICORN_CMD_ARGS` - Additional Gunicorn arguments

### Output

The script outputs a JSON object with the following fields:

```json
{
  "status": "ok",
  "gunicorn_cmd": "--worker-class gthread --threads 4 --timeout 120 --graceful-timeout 120",
  "robust_chunker_kwargs": {
    "chunk_seconds": 300
  },
  "tests_passed": true,
  "notes": "All chunks processed; no timeouts; build ready for Render."
}
```

## Integration with Render

To use this script with Render, add the following to your `render.yaml` file:

```yaml
services:
  - type: web
    name: vocallocal
    env: python
    buildCommand: |
      pip install -r requirements.txt
      python vocallocal_build_runtime.py
    startCommand: gunicorn app:app
    envVars:
      - key: INPUT_PATH
        value: /tmp/input
      - key: OUTPUT_DIR
        value: /tmp/output
      - key: CHUNK_SECONDS
        value: 300
```

## Troubleshooting

### FFmpeg Not Available

If FFmpeg is not available, the load tests will be skipped. To install FFmpeg:

```bash
# On Ubuntu/Debian
apt-get update && apt-get install -y ffmpeg

# On Windows
# Download from https://ffmpeg.org/download.html
```

### Missing Dependencies

If the script fails to install dependencies, make sure you have pip installed and your Python environment is set up correctly.

### RobustChunker Not Found

If the script fails to locate the RobustChunker class, make sure the `services` directory is in your Python path and contains the `robust_chunker.py` or `audio_chunker.py` file.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
