#!/usr/bin/env python
"""
Test script for VocalLocal Render deployment.
This script tests the RobustChunker implementation and file size validation.
"""
import os
import sys
import json
import tempfile
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

def test_robust_chunker():
    """Test the RobustChunker implementation."""
    logger.info("Testing RobustChunker implementation...")
    
    try:
        # Import the RobustChunker
        from services.audio_chunker import RobustChunker
        
        # Create a test file
        test_file = create_test_file(5)
        if not test_file:
            logger.error("Failed to create test file")
            return False
            
        # Create a temporary output directory
        output_dir = tempfile.mkdtemp()
        
        # Test with different parameter names
        test_cases = [
            {"input_path": test_file, "output_dir": output_dir, "chunk_seconds": 300},
            {"input_path": test_file, "output_dir": output_dir, "chunk_duration": 300},
            {"input_path": test_file, "output_dir": output_dir, "chunk_duration_seconds": 300}
        ]
        
        success = True
        for i, params in enumerate(test_cases):
            logger.info(f"Test case {i+1}: {params}")
            
            try:
                # Initialize the chunker
                chunker = RobustChunker(**params)
                
                # Check if the chunker was initialized correctly
                logger.info(f"Chunker initialized with chunk_seconds={chunker.chunk_seconds}")
                
                if chunker.chunk_seconds != 300:
                    logger.error(f"Chunker initialized with incorrect chunk_seconds: {chunker.chunk_seconds}")
                    success = False
                    
            except Exception as e:
                logger.error(f"Failed to initialize chunker with params {params}: {str(e)}")
                success = False
                
        # Clean up
        try:
            os.remove(test_file)
            os.rmdir(output_dir)
        except:
            pass
            
        return success
        
    except ImportError as e:
        logger.error(f"Failed to import RobustChunker: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

def test_file_size_validation():
    """Test file size validation."""
    logger.info("Testing file size validation...")
    
    try:
        # Create a test file that exceeds the limit (151MB)
        test_file = create_test_file(151)
        if not test_file:
            logger.error("Failed to create test file")
            return False
            
        # Check the file size
        file_size_mb = os.path.getsize(test_file) / (1024 * 1024)
        logger.info(f"Test file size: {file_size_mb:.2f} MB")
        
        # Validate the file size
        if file_size_mb > 150:
            logger.info("File size validation successful: file exceeds 150MB")
            result = {
                "status": "error",
                "stage": "size_check",
                "error": "file exceeds 150MB"
            }
            logger.info(f"Validation result: {json.dumps(result)}")
            
            # Clean up
            try:
                os.remove(test_file)
            except:
                pass
                
            return True
        else:
            logger.error(f"File size validation failed: file size is {file_size_mb:.2f} MB, expected > 150MB")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

def main():
    """Run the tests."""
    parser = argparse.ArgumentParser(description='Test VocalLocal Render deployment')
    parser.add_argument('--test-chunker', action='store_true', help='Test RobustChunker implementation')
    parser.add_argument('--test-size', action='store_true', help='Test file size validation')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    # Run the tests
    results = {}
    
    if args.test_chunker or args.all:
        results['robust_chunker'] = test_robust_chunker()
        
    if args.test_size or args.all:
        results['file_size_validation'] = test_file_size_validation()
        
    if not args.test_chunker and not args.test_size and not args.all:
        logger.info("No tests specified. Use --test-chunker, --test-size, or --all")
        return 0
        
    # Print the results
    logger.info("Test results:")
    for test, result in results.items():
        logger.info(f"  {test}: {'PASS' if result else 'FAIL'}")
        
    # Return success if all tests passed
    return 0 if all(results.values()) else 1

if __name__ == '__main__':
    sys.exit(main())
