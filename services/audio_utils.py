"""
Audio utility functions for VocalLocal application.
"""

import os
import subprocess
import tempfile
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def get_audio_duration_ffmpeg(file_path: str) -> Optional[float]:
    """
    Get audio duration using FFmpeg (most accurate method).
    
    Args:
        file_path (str): Path to the audio file
        
    Returns:
        Optional[float]: Duration in seconds, or None if failed
    """
    try:
        # Use ffprobe to get duration
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 
            'format=duration', '-of', 'csv=p=0', file_path
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            duration = float(result.stdout.strip())
            logger.info(f"FFmpeg detected audio duration: {duration:.2f} seconds")
            return duration
        else:
            logger.warning(f"FFmpeg failed to get duration: {result.stderr}")
            return None
            
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError, FileNotFoundError) as e:
        logger.warning(f"FFmpeg duration detection failed: {str(e)}")
        return None


def get_audio_duration_pydub(file_path: str) -> Optional[float]:
    """
    Get audio duration using pydub (fallback method).
    
    Args:
        file_path (str): Path to the audio file
        
    Returns:
        Optional[float]: Duration in seconds, or None if failed
    """
    try:
        from pydub import AudioSegment
        
        # Load audio file
        audio = AudioSegment.from_file(file_path)
        duration_seconds = len(audio) / 1000.0  # Convert milliseconds to seconds
        
        logger.info(f"Pydub detected audio duration: {duration_seconds:.2f} seconds")
        return duration_seconds
        
    except Exception as e:
        logger.warning(f"Pydub duration detection failed: {str(e)}")
        return None


def get_audio_duration(file_path: str) -> Tuple[Optional[float], str]:
    """
    Get audio duration with fallback methods.
    
    Args:
        file_path (str): Path to the audio file
        
    Returns:
        Tuple[Optional[float], str]: (duration_in_seconds, method_used)
    """
    if not os.path.exists(file_path):
        logger.error(f"Audio file not found: {file_path}")
        return None, "file_not_found"
    
    # Try FFmpeg first (most accurate)
    duration = get_audio_duration_ffmpeg(file_path)
    if duration is not None:
        return duration, "ffmpeg"
    
    # Fallback to pydub
    duration = get_audio_duration_pydub(file_path)
    if duration is not None:
        return duration, "pydub"
    
    # If all methods fail, return None
    logger.error(f"All audio duration detection methods failed for: {file_path}")
    return None, "failed"


def estimate_duration_from_text(text: str, words_per_minute: float = 150.0) -> float:
    """
    Estimate audio duration from text (fallback method).
    
    Args:
        text (str): Text to be converted to speech
        words_per_minute (float): Estimated speaking rate
        
    Returns:
        float: Estimated duration in minutes
    """
    word_count = len(text.split())
    estimated_minutes = max(0.1, word_count / words_per_minute)
    logger.info(f"Estimated duration from text: {estimated_minutes:.2f} minutes ({word_count} words)")
    return estimated_minutes


def calculate_tts_credits(user_plan: str, duration_minutes: float) -> float:
    """
    Calculate AI credits needed for TTS based on user plan and duration.
    
    Args:
        user_plan (str): User's subscription plan ('basic', 'professional', etc.)
        duration_minutes (float): Audio duration in minutes
        
    Returns:
        float: Credits needed
    """
    # Credit rates per minute based on plan
    credit_rates = {
        'basic': 0.833,        # 50 credits / 60 minutes
        'professional': 0.75,  # 150 credits / 200 minutes
        'free': 1.0,          # Default rate for free users
    }
    
    rate = credit_rates.get(user_plan.lower(), 1.0)
    credits = duration_minutes * rate
    
    logger.info(f"TTS credits calculation: {duration_minutes:.2f} min × {rate} = {credits:.2f} credits (plan: {user_plan})")
    return credits
