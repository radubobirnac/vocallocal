"""
Metrics Tracker Module for VocalLocal

This module tracks usage metrics for AI models, including:
- Token usage
- Response times
- Character counts
- Success/failure rates
"""

import time
import json
import os
import logging
from datetime import datetime
from functools import wraps

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File to store metrics
METRICS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'metrics.json')

# Ensure the data directory exists
os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)

class MetricsTracker:
    """Class to track and store metrics for AI model usage"""

    def __init__(self):
        """Initialize the metrics tracker"""
        self.metrics = self._load_metrics()

    def _load_metrics(self):
        """Load metrics from file or initialize if not exists"""
        try:
            if os.path.exists(METRICS_FILE):
                with open(METRICS_FILE, 'r') as f:
                    return json.load(f)
            else:
                return {
                    "translation": {
                        "openai": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0},
                        "gemini": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0},
                        "gemini-2.5-flash": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0},
                        "gemini-2.5-pro": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0}
                    },
                    "transcription": {
                        "openai": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0},
                        "gemini-2.0-flash-lite": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0},
                        "gemini-2.5-flash-preview": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0},
                        "gemini-2.5-pro-preview": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0}
                    },
                    "tts": {
                        "openai": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0},
                        "gpt4o-mini": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0}
                    },
                    "daily_usage": {},
                    "hourly_usage": {}
                }
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
            return {
                "translation": {},
                "transcription": {},
                "tts": {},
                "daily_usage": {},
                "hourly_usage": {}
            }

    def _save_metrics(self):
        """Save metrics to file"""
        try:
            with open(METRICS_FILE, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

    def track_translation(self, model, tokens_used, char_count, response_time, success=True):
        """
        Track metrics for a translation request

        Args:
            model (str): The model used (openai, gemini, etc.)
            tokens_used (int): Number of tokens used
            char_count (int): Number of characters processed
            response_time (float): Time taken in seconds
            success (bool): Whether the request was successful
        """
        # Initialize model if not exists
        if model not in self.metrics["translation"]:
            self.metrics["translation"][model] = {
                "calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0
            }

        # Update metrics
        self.metrics["translation"][model]["calls"] += 1
        self.metrics["translation"][model]["tokens"] += tokens_used
        self.metrics["translation"][model]["chars"] += char_count
        self.metrics["translation"][model]["time"] += response_time

        if not success:
            self.metrics["translation"][model]["failures"] += 1

        # Update daily and hourly usage
        self._update_time_based_metrics("translation", model, tokens_used)

        # Save metrics
        self._save_metrics()

        # Log the metrics
        logger.info(f"Translation metrics - Model: {model}, Tokens: {tokens_used}, "
                   f"Chars: {char_count}, Time: {response_time:.2f}s, Success: {success}")

    def track_transcription(self, model, tokens_used, char_count, response_time, success=True):
        """
        Track metrics for a transcription request

        Args:
            model (str): The model used (openai, gemini, etc.)
            tokens_used (int): Number of tokens used
            char_count (int): Number of characters processed
            response_time (float): Time taken in seconds
            success (bool): Whether the request was successful
        """
        # Initialize model if not exists
        if model not in self.metrics["transcription"]:
            self.metrics["transcription"][model] = {
                "calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0
            }

        # Update metrics
        self.metrics["transcription"][model]["calls"] += 1
        self.metrics["transcription"][model]["tokens"] += tokens_used
        self.metrics["transcription"][model]["chars"] += char_count
        self.metrics["transcription"][model]["time"] += response_time

        if not success:
            self.metrics["transcription"][model]["failures"] += 1

        # Update daily and hourly usage
        self._update_time_based_metrics("transcription", model, tokens_used)

        # Save metrics
        self._save_metrics()

        # Log the metrics
        logger.info(f"Transcription metrics - Model: {model}, Tokens: {tokens_used}, "
                   f"Chars: {char_count}, Time: {response_time:.2f}s, Success: {success}")

    def track_tts(self, model, tokens_used, char_count, response_time, success=True):
        """
        Track metrics for a text-to-speech request

        Args:
            model (str): The model used (openai, gemini, etc.)
            tokens_used (int): Number of tokens used
            char_count (int): Number of characters processed
            response_time (float): Time taken in seconds
            success (bool): Whether the request was successful
        """
        # Initialize tts section if it doesn't exist
        if "tts" not in self.metrics:
            self.metrics["tts"] = {}

        # Initialize model if not exists
        if model not in self.metrics["tts"]:
            self.metrics["tts"][model] = {
                "calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0
            }

        # Update metrics
        self.metrics["tts"][model]["calls"] += 1
        self.metrics["tts"][model]["tokens"] += tokens_used
        self.metrics["tts"][model]["chars"] += char_count
        self.metrics["tts"][model]["time"] += response_time

        if not success:
            self.metrics["tts"][model]["failures"] += 1

        # Update daily and hourly usage
        self._update_time_based_metrics("tts", model, tokens_used)

        # Save metrics
        self._save_metrics()

        # Log the metrics
        logger.info(f"TTS metrics - Model: {model}, Tokens: {tokens_used}, "
                   f"Chars: {char_count}, Time: {response_time:.2f}s, Success: {success}")

    def _update_time_based_metrics(self, operation_type, model, tokens_used):
        """Update daily and hourly usage metrics"""
        # Get current date and hour
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        hour_str = now.strftime("%Y-%m-%d-%H")

        # Update daily usage
        if date_str not in self.metrics["daily_usage"]:
            self.metrics["daily_usage"][date_str] = {}

        if operation_type not in self.metrics["daily_usage"][date_str]:
            self.metrics["daily_usage"][date_str][operation_type] = {}

        if model not in self.metrics["daily_usage"][date_str][operation_type]:
            self.metrics["daily_usage"][date_str][operation_type][model] = 0

        self.metrics["daily_usage"][date_str][operation_type][model] += tokens_used

        # Update hourly usage
        if hour_str not in self.metrics["hourly_usage"]:
            self.metrics["hourly_usage"][hour_str] = {}

        if operation_type not in self.metrics["hourly_usage"][hour_str]:
            self.metrics["hourly_usage"][hour_str][operation_type] = {}

        if model not in self.metrics["hourly_usage"][hour_str][operation_type]:
            self.metrics["hourly_usage"][hour_str][operation_type][model] = 0

        self.metrics["hourly_usage"][hour_str][operation_type][model] += tokens_used

    def get_metrics(self):
        """Get all metrics"""
        return self.metrics

    def get_model_metrics(self, operation_type, model):
        """Get metrics for a specific model"""
        if operation_type in self.metrics and model in self.metrics[operation_type]:
            return self.metrics[operation_type][model]
        return None

    def get_daily_usage(self, date_str=None):
        """Get daily usage metrics for a specific date or today"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        if date_str in self.metrics["daily_usage"]:
            return self.metrics["daily_usage"][date_str]
        return {}

    def get_hourly_usage(self, hour_str=None):
        """Get hourly usage metrics for a specific hour or current hour"""
        if hour_str is None:
            hour_str = datetime.now().strftime("%Y-%m-%d-%H")

        if hour_str in self.metrics["hourly_usage"]:
            return self.metrics["hourly_usage"][hour_str]
        return {}

    def reset_metrics(self):
        """Reset all metrics to zero"""
        # Create a fresh metrics structure
        self.metrics = {
            "translation": {
                "openai": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0},
                "gemini": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0},
                "gemini-2.5-flash": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0},
                "gemini-2.5-pro": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0}
            },
            "transcription": {
                "openai": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0},
                "gemini-2.0-flash-lite": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0},
                "gemini-2.5-flash-preview": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0},
                "gemini-2.5-pro-preview": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0}
            },
            "tts": {
                "openai": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0},
                "gpt4o-mini": {"calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0}
            },
            "daily_usage": {},
            "hourly_usage": {}
        }

        # Save the reset metrics
        self._save_metrics()

        logger.info("All metrics have been reset to zero")

# Create a singleton instance
metrics_tracker = MetricsTracker()

# Decorator for tracking translation metrics
def track_translation_metrics(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        success = True
        tokens_used = 0
        result = None

        try:
            result = func(*args, **kwargs)

            # Extract model name from kwargs or use default
            model = kwargs.get('translation_model', 'unknown')

            # Log the original model name for debugging
            logger.info(f"Original translation model name: {model}")

            # Categorize models
            if model.startswith('gpt') or model == 'openai':
                model = 'openai'
            # Categorize Gemini models
            elif model == 'gemini' or 'gemini-2.0' in model or model == 'models/gemini-2.0-flash-lite':
                model = 'gemini'
            elif 'gemini-2.5-flash' in model or model == 'models/gemini-2.5-flash-preview-04-17':
                model = 'gemini-2.5-flash'
            elif 'gemini-2.5-pro' in model or model == 'models/gemini-2.5-pro-preview-03-25':
                model = 'gemini-2.5-pro'

            # Log the categorized model name for debugging
            logger.info(f"Categorized translation model name: {model}")

            # Get character count from the first argument (text)
            char_count = len(args[0]) if args else 0

            # Estimate tokens used based on character count
            # For translation, tokens are typically fewer than characters
            # A better estimate is about 1 token per 3-4 characters
            tokens_used = max(1, char_count // 4)  # Ensure at least 1 token

        except Exception as e:
            success = False
            logger.error(f"Error in translation: {e}")
            raise
        finally:
            end_time = time.time()
            response_time = end_time - start_time

            # Only track metrics if we have a model name
            if 'model' in locals():
                metrics_tracker.track_translation(
                    model, tokens_used, char_count, response_time, success
                )

        return result
    return wrapper

# Decorator for tracking transcription metrics
def track_transcription_metrics(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        success = True
        tokens_used = 0
        char_count = 0
        result = None

        try:
            result = func(*args, **kwargs)

            # Extract model name from kwargs or args - check multiple possible parameter names
            model = kwargs.get('model') or kwargs.get('model_type') or kwargs.get('model_name')

            # If not in kwargs, try to get from args (positional parameters)
            if not model and len(args) >= 3:
                model = args[2]  # Third parameter is typically the model

            # Default to unknown if still not found
            if not model:
                model = 'unknown'

            # Log the original model name for debugging
            logger.info(f"Original transcription model name: {model}")

            # Categorize OpenAI models
            if model.startswith('gpt') or model.startswith('whisper') or model == 'openai':
                model = 'openai'
            # Categorize Gemini models
            elif model == 'gemini' or 'gemini-2.0' in model or model == 'models/gemini-2.0-flash-lite':
                model = 'gemini-2.0-flash-lite'
            elif 'gemini-2.5-flash' in model or model == 'models/gemini-2.5-flash-preview-04-17':
                model = 'gemini-2.5-flash-preview'
            elif 'gemini-2.5-pro' in model or model == 'models/gemini-2.5-pro-preview-03-25':
                model = 'gemini-2.5-pro-preview'

            # Log the categorized model name for debugging
            logger.info(f"Categorized transcription model name: {model}")

            # Get character count from the result
            char_count = len(result) if result else 0

            # For transcription, tokens should be roughly proportional to output characters
            # For most models, 1 token is approximately 3-4 characters
            # We'll use a more conservative estimate for transcription
            tokens_used = max(1, char_count // 3)  # Ensure at least 1 token

        except Exception as e:
            success = False
            logger.error(f"Error in transcription: {e}")
            raise
        finally:
            end_time = time.time()
            response_time = end_time - start_time

            # Only track metrics if we have a model name
            if 'model' in locals():
                metrics_tracker.track_transcription(
                    model, tokens_used, char_count, response_time, success
                )

        return result
    return wrapper
