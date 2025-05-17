#!/usr/bin/env python
"""
Verify that the RobustChunker fix works.
This script imports the RobustChunker and TranscriptionService classes
and verifies that they can be instantiated without errors.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_robust_chunker():
    """Verify that RobustChunker can be instantiated."""
    try:
        from services.robust_chunker import RobustChunker
        
        # Test with chunk_seconds parameter
        chunker1 = RobustChunker(chunk_seconds=300)
        logger.info(f"Successfully created RobustChunker with chunk_seconds parameter: {chunker1.chunk_seconds}")
        
        # Test with positional parameter
        chunker2 = RobustChunker(None, None, 300)
        logger.info(f"Successfully created RobustChunker with positional parameter: {chunker2.chunk_seconds}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to instantiate RobustChunker: {str(e)}")
        return False

def verify_transcription_service():
    """Verify that TranscriptionService can be instantiated."""
    try:
        from services.transcription import TranscriptionService
        
        # Create a transcription service
        service = TranscriptionService()
        logger.info(f"Successfully created TranscriptionService")
        
        # Check if robust_chunker was initialized correctly
        if hasattr(service, 'robust_chunker'):
            logger.info(f"TranscriptionService has robust_chunker attribute with chunk_seconds={service.robust_chunker.chunk_seconds}")
            return True
        else:
            logger.error("TranscriptionService does not have robust_chunker attribute")
            return False
    except Exception as e:
        logger.error(f"Failed to instantiate TranscriptionService: {str(e)}")
        return False

def main():
    """Run the verification tests."""
    logger.info("Verifying RobustChunker fix...")
    
    # Verify RobustChunker
    robust_chunker_ok = verify_robust_chunker()
    
    # Verify TranscriptionService
    transcription_service_ok = verify_transcription_service()
    
    # Print results
    logger.info(f"RobustChunker verification: {'PASS' if robust_chunker_ok else 'FAIL'}")
    logger.info(f"TranscriptionService verification: {'PASS' if transcription_service_ok else 'FAIL'}")
    
    # Return success if both tests passed
    return 0 if robust_chunker_ok and transcription_service_ok else 1

if __name__ == '__main__':
    sys.exit(main())
