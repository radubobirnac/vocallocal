#!/usr/bin/env python
"""
Load testing script for VocalLocal.
This script creates test files of different sizes and tests the chunking and transcription process.
"""
import os
import sys
import json
import time
import tempfile
import logging
import argparse
import importlib
import concurrent.futures
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("load_test")

def create_test_file(size_mb):
    """Create a test file of the specified size."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            # Generate random data of the specified size
            f.write(os.urandom(size_mb * 1024 * 1024))
            logger.info(f"Created test file of {size_mb}MB: {f.name}")
            return f.name
    except Exception as e:
        logger.error(f"Failed to create test file of {size_mb}MB: {str(e)}")
        return None

def test_file_processing(file_path, size_mb, chunk_seconds=300):
    """Test processing a file with the RobustChunker."""
    try:
        logger.info(f"Testing with {size_mb}MB file: {file_path}")
        
        # Set up environment for this test
        output_dir = tempfile.mkdtemp()
        
        # Import the RobustChunker
        try:
            chunker_module = importlib.import_module("services.robust_chunker")
            RobustChunker = chunker_module.RobustChunker
        except (ImportError, AttributeError):
            chunker_module = importlib.import_module("services.audio_chunker")
            RobustChunker = chunker_module.RobustChunker
        
        # Determine the correct parameter name
        import inspect
        params = inspect.signature(RobustChunker).parameters
        kwargs = {}
        
        if "chunk_duration" in params:
            kwargs["chunk_duration"] = chunk_seconds
        elif "chunk_duration_seconds" in params:
            kwargs["chunk_duration_seconds"] = chunk_seconds
        else:
            raise RuntimeError("RobustChunker accepts neither 'chunk_duration' nor 'chunk_duration_seconds'")
        
        # Add other parameters
        kwargs["input_path"] = file_path
        kwargs["output_dir"] = output_dir
        
        # Initialize the chunker
        chunker = RobustChunker(**kwargs)
        
        # Run the chunking process
        start_time = time.time()
        result = chunker.chunk_audio()
        elapsed_time = time.time() - start_time
        
        # Check the result
        if result[0]:  # Success
            logger.info(f"Successfully chunked {size_mb}MB file in {elapsed_time:.2f}s")
            return {
                "file_size_mb": size_mb,
                "success": True,
                "elapsed_time": elapsed_time,
                "chunks": len(result[1]),
                "message": f"Successfully chunked into {len(result[1])} chunks"
            }
        else:
            logger.error(f"Failed to chunk {size_mb}MB file: {result[2]}")
            return {
                "file_size_mb": size_mb,
                "success": False,
                "elapsed_time": elapsed_time,
                "message": result[2]
            }
    except Exception as e:
        logger.error(f"Error testing with {size_mb}MB file: {str(e)}")
        return {
            "file_size_mb": size_mb,
            "success": False,
            "elapsed_time": 0,
            "message": str(e)
        }
    finally:
        # Clean up
        try:
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
        except:
            pass

def run_concurrent_tests(file_paths, concurrency=3):
    """Run tests concurrently."""
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(test_file_processing, file_path, size_mb): (file_path, size_mb)
            for file_path, size_mb in file_paths
        }
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_file):
            file_path, size_mb = future_to_file[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {size_mb}MB file: {str(e)}")
                results.append({
                    "file_size_mb": size_mb,
                    "success": False,
                    "message": str(e)
                })
    
    return results

def main():
    """Run the load tests."""
    parser = argparse.ArgumentParser(description="Run load tests for VocalLocal")
    parser.add_argument("--sizes", type=int, nargs="+", default=[1, 10, 20],
                        help="File sizes to test in MB")
    parser.add_argument("--concurrency", type=int, default=3,
                        help="Number of concurrent tests to run")
    parser.add_argument("--chunk-seconds", type=int, default=300,
                        help="Duration of each chunk in seconds")
    args = parser.parse_args()
    
    # Create test files
    file_paths = []
    for size in args.sizes:
        file_path = create_test_file(size)
        if file_path:
            file_paths.append((file_path, size))
    
    if not file_paths:
        logger.error("Failed to create any test files")
        return 1
    
    try:
        # Run the tests
        logger.info(f"Running {len(file_paths)} tests with concurrency {args.concurrency}")
        results = run_concurrent_tests(file_paths, args.concurrency)
        
        # Print the results
        print(json.dumps({
            "status": "ok" if all(r["success"] for r in results) else "error",
            "tests": results
        }, indent=2))
        
        # Return the status code
        return 0 if all(r["success"] for r in results) else 1
    finally:
        # Clean up
        for file_path, _ in file_paths:
            try:
                os.remove(file_path)
            except:
                pass

if __name__ == "__main__":
    sys.exit(main())
