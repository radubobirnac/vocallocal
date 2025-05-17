#!/usr/bin/env python
"""
Run the build and runtime engineer for VocalLocal.
This script sets up the environment and runs the build engineer.
"""
import os
import sys
import json
import tempfile
import argparse
from build_runtime_engineer import BuildRuntimeEngineer

def main():
    """Run the build and runtime engineer."""
    parser = argparse.ArgumentParser(description="Run the VocalLocal build and runtime engineer")
    parser.add_argument("--input-path", help="Path to input audio file")
    parser.add_argument("--output-dir", help="Directory for output chunks")
    parser.add_argument("--chunk-seconds", type=int, default=300, help="Duration of each chunk in seconds")
    parser.add_argument("--gunicorn-args", help="Additional Gunicorn arguments")
    args = parser.parse_args()
    
    # Set environment variables from arguments
    if args.input_path:
        os.environ["INPUT_PATH"] = args.input_path
    elif "INPUT_PATH" not in os.environ:
        # Create a temporary file as a placeholder
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file.write(b"test")
        temp_file.close()
        os.environ["INPUT_PATH"] = temp_file.name
        print(f"Created temporary input file: {temp_file.name}")
    
    if args.output_dir:
        os.environ["OUTPUT_DIR"] = args.output_dir
    elif "OUTPUT_DIR" not in os.environ:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        os.environ["OUTPUT_DIR"] = temp_dir
        print(f"Created temporary output directory: {temp_dir}")
    
    if args.chunk_seconds:
        os.environ["CHUNK_SECONDS"] = str(args.chunk_seconds)
    
    if args.gunicorn_args:
        os.environ["GUNICORN_CMD_ARGS"] = args.gunicorn_args
    
    # Run the build engineer
    engineer = BuildRuntimeEngineer()
    results = engineer.run()
    
    # Print the results
    print(json.dumps(results, indent=2))
    
    # Return the status code
    return 0 if results["status"] == "ok" else 1

if __name__ == "__main__":
    sys.exit(main())
