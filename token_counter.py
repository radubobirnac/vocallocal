"""
Token Counter Module for VocalLocal

This module provides functions to count tokens for different AI models:
- OpenAI (GPT models)
- Google Gemini models
"""

import tiktoken
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default tokenizer for OpenAI models
DEFAULT_OPENAI_TOKENIZER = "cl100k_base"  # Used by GPT-4 and GPT-3.5-turbo

def count_openai_tokens(text, model="gpt-4"):
    """
    Count tokens for OpenAI models using tiktoken
    
    Args:
        text (str): The text to count tokens for
        model (str): The OpenAI model name
    
    Returns:
        int: Number of tokens
    """
    try:
        # Get the appropriate tokenizer for the model
        if model.startswith("gpt-4"):
            encoding = tiktoken.encoding_for_model("gpt-4")
        elif model.startswith("gpt-3.5"):
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        else:
            # Use default tokenizer for unknown models
            encoding = tiktoken.get_encoding(DEFAULT_OPENAI_TOKENIZER)
        
        # Count tokens
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception as e:
        logger.error(f"Error counting OpenAI tokens: {e}")
        # Fallback to a simple approximation (1 token ≈ 4 characters)
        return len(text) // 4

def count_openai_chat_tokens(messages, model="gpt-4"):
    """
    Count tokens for OpenAI chat models
    
    Args:
        messages (list): List of message dictionaries with 'role' and 'content'
        model (str): The OpenAI model name
    
    Returns:
        int: Number of tokens
    """
    try:
        # Get the appropriate tokenizer for the model
        if model.startswith("gpt-4"):
            encoding = tiktoken.encoding_for_model("gpt-4")
        elif model.startswith("gpt-3.5"):
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        else:
            # Use default tokenizer for unknown models
            encoding = tiktoken.get_encoding(DEFAULT_OPENAI_TOKENIZER)
        
        # Count tokens for each message
        token_count = 0
        for message in messages:
            # Add tokens for message role (3 tokens for role)
            token_count += 3
            
            # Add tokens for content
            content = message.get('content', '')
            if isinstance(content, str):
                token_count += len(encoding.encode(content))
        
        # Add tokens for the model's reply format (3 tokens)
        token_count += 3
        
        return token_count
    except Exception as e:
        logger.error(f"Error counting OpenAI chat tokens: {e}")
        # Fallback to a simple approximation
        total_chars = sum(len(m.get('content', '')) for m in messages if isinstance(m.get('content', ''), str))
        return total_chars // 4

def count_openai_audio_tokens(audio_size_bytes, duration_seconds=None):
    """
    Estimate tokens for OpenAI audio transcription
    
    Args:
        audio_size_bytes (int): Size of the audio file in bytes
        duration_seconds (float, optional): Duration of the audio in seconds
    
    Returns:
        int: Estimated number of tokens
    """
    # OpenAI charges per second of audio for Whisper models
    # If we have the duration, use that for a more accurate estimate
    if duration_seconds is not None:
        # Whisper charges per second, but we want to estimate tokens
        # Roughly 150 tokens per minute of audio (2.5 tokens per second)
        return int(duration_seconds * 2.5)
    else:
        # Rough estimate based on file size
        # Assuming 16kHz mono audio (16 bits per sample)
        # 16000 samples/sec * 2 bytes/sample = 32000 bytes/sec
        estimated_seconds = audio_size_bytes / 32000
        return int(estimated_seconds * 2.5)

def count_gemini_tokens(text, model="gemini-2.0-flash-lite"):
    """
    Estimate tokens for Google Gemini models
    
    Args:
        text (str): The text to count tokens for
        model (str): The Gemini model name
    
    Returns:
        int: Estimated number of tokens
    """
    # Gemini uses a different tokenization scheme than OpenAI
    # Without access to the actual tokenizer, we'll use an approximation
    # Based on Google's documentation, 1 token ≈ 4 characters for English text
    
    # For non-English text, the ratio might be different
    # For simplicity, we'll use a slightly more conservative estimate
    return len(text) // 3

def count_gemini_audio_tokens(audio_size_bytes, duration_seconds=None):
    """
    Estimate tokens for Gemini audio transcription
    
    Args:
        audio_size_bytes (int): Size of the audio file in bytes
        duration_seconds (float, optional): Duration of the audio in seconds
    
    Returns:
        int: Estimated number of tokens
    """
    # Similar to OpenAI, but Gemini might have different pricing
    # Using a conservative estimate
    if duration_seconds is not None:
        # Estimate 3 tokens per second for Gemini
        return int(duration_seconds * 3)
    else:
        # Rough estimate based on file size
        estimated_seconds = audio_size_bytes / 32000
        return int(estimated_seconds * 3)

def estimate_audio_duration(audio_size_bytes, format_type="webm"):
    """
    Estimate audio duration based on file size and format
    
    Args:
        audio_size_bytes (int): Size of the audio file in bytes
        format_type (str): Audio format (webm, mp3, etc.)
    
    Returns:
        float: Estimated duration in seconds
    """
    # Rough estimates based on common bitrates
    if format_type.lower() == "webm":
        # WebM with Opus typically uses ~32 kbps
        bits_per_second = 32000
    elif format_type.lower() == "mp3":
        # MP3 typically uses ~128 kbps
        bits_per_second = 128000
    else:
        # Default to a conservative estimate
        bits_per_second = 64000
    
    # Convert bytes to bits and estimate duration
    bits = audio_size_bytes * 8
    estimated_seconds = bits / bits_per_second
    
    return estimated_seconds
