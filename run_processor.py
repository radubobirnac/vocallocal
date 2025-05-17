#!/usr/bin/env python
"""
Test script for VocalLocal processor.
This script sets up the environment and runs the processor.
"""
import os
import sys
import tempfile
import argparse

def main():
    """Run the VocalLocal processor with test data."""
    parser = argparse.ArgumentParser(description="Run the VocalLocal processor")
    parser.add_argument("--input-path", help="Path to input audio file")
    parser.add_argument("--output-dir", help="Directory for output chunks")
    parser.add_argument("--chunk-seconds", type=int, default=300, help="Duration of each chunk in seconds")
    parser.add_argument("--create-test-file", action="store_true", help="Create a test file of specified size")
    parser.add_argument("--test-file-size", type=int, default=10, help="Size of test file in MB")
    args = parser.parse_args()
    
    # Create a test file if requested
    if args.create_test_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            # Generate random data of the specified size
            f.write(os.urandom(args.test_file_size * 1024 * 1024))
            test_file_path = f.name
            print(f"Created test file of {args.test_file_size}MB: {test_file_path}")
            
            # Use the test file as input if no input path was provided
            if not args.input_path:
                args.input_path = test_file_path
    
    # Set environment variables from arguments
    if args.input_path:
        os.environ["INPUT_PATH"] = args.input_path
    
    if args.output_dir:
        os.environ["OUTPUT_DIR"] = args.output_dir
    else:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        os.environ["OUTPUT_DIR"] = temp_dir
        print(f"Created temporary output directory: {temp_dir}")
    
    if args.chunk_seconds:
        os.environ["CHUNK_SECONDS"] = str(args.chunk_seconds)
    
    # Run the processor
    print("Running VocalLocal processor...")
    os.system("python vocallocal_processor.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
