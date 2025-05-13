"""
Base Service Class

This module provides a base class for all VocalLocal services with common
functionality such as logging, error handling, and metrics tracking.
"""

import os
import time
import logging
from typing import Any, Dict, Optional, Tuple, Union, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class ServiceError(Exception):
    """Base exception class for service errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)

class ProviderError(ServiceError):
    """Exception raised when a provider (OpenAI, Gemini) encounters an error"""
    def __init__(self, provider: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.provider = provider
        details = details or {}
        details['provider'] = provider
        super().__init__(f"{provider} error: {message}", details)

class ValidationError(ServiceError):
    """Exception raised when input validation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details['error_type'] = 'validation_error'
        super().__init__(f"Validation error: {message}", details)

class ConfigurationError(ServiceError):
    """Exception raised when there's a configuration issue"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details['error_type'] = 'configuration_error'
        super().__init__(f"Configuration error: {message}", details)

class AuthenticationError(ProviderError):
    """Exception raised when authentication fails with a provider"""
    def __init__(self, provider: str, message: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details['error_type'] = 'authentication_error'
        super().__init__(provider, f"Authentication error: {message}", details)

class RateLimitError(ProviderError):
    """Exception raised when a provider's rate limit is exceeded"""
    def __init__(self, provider: str, message: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details['error_type'] = 'rate_limit_error'
        super().__init__(provider, f"Rate limit exceeded: {message}", details)

class ResourceError(ServiceError):
    """Exception raised when a resource (file, network, etc.) is unavailable"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details['error_type'] = 'resource_error'
        super().__init__(f"Resource error: {message}", details)

class BaseService:
    """Base class for all services"""

    def __init__(self, service_name: str):
        """
        Initialize the base service.

        Args:
            service_name: Name of the service for logging purposes
        """
        self.logger = logging.getLogger(service_name)
        self.metrics = {}

    def _track_timing(self, operation: str) -> Callable:
        """
        Decorator to track timing of operations.

        Args:
            operation: Name of the operation being timed

        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.time() - start_time
                    self._record_metric(operation, 'time', elapsed)
                    self._record_metric(operation, 'success', 1)
                    return result
                except Exception as e:
                    elapsed = time.time() - start_time
                    self._record_metric(operation, 'time', elapsed)
                    self._record_metric(operation, 'error', 1)
                    raise
            return wrapper
        return decorator

    def _record_metric(self, operation: str, metric_type: str, value: Union[int, float]) -> None:
        """
        Record a metric for the given operation.

        Args:
            operation: Name of the operation
            metric_type: Type of metric (time, success, error, etc.)
            value: Value to record
        """
        if operation not in self.metrics:
            self.metrics[operation] = {}

        if metric_type not in self.metrics[operation]:
            self.metrics[operation][metric_type] = 0

        # For counters, increment; for timers, update the value
        if metric_type in ['success', 'error', 'retry', 'fallback']:
            self.metrics[operation][metric_type] += value
        else:
            self.metrics[operation][metric_type] = value

    def get_metrics(self) -> Dict[str, Dict[str, Union[int, float]]]:
        """
        Get all recorded metrics.

        Returns:
            Dictionary of metrics by operation and type
        """
        return self.metrics

    def with_retry(self, func: Callable, max_retries: int = 2,
                  initial_delay: float = 1.0, backoff_factor: float = 2.0,
                  operation: str = 'unknown') -> Any:
        """
        Execute a function with retry logic and exponential backoff.

        Args:
            func: Function to execute
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            backoff_factor: Factor to increase delay with each retry
            operation: Name of the operation for metrics

        Returns:
            Result of the function call

        Raises:
            AuthenticationError: If authentication fails (not retried)
            RateLimitError: If rate limit is exceeded (retried with longer delays)
            ServiceError: If all retry attempts fail
        """
        attempts = 0
        delay = initial_delay
        last_error = None

        while attempts <= max_retries:
            try:
                return func()
            except Exception as e:
                attempts += 1
                last_error = e

                # Don't retry authentication errors
                if isinstance(e, AuthenticationError):
                    self.logger.error(f"Authentication error in {operation}: {str(e)}")
                    self._record_metric(operation, 'auth_error', 1)
                    break

                # Check if we should retry
                if attempts <= max_retries:
                    # Use longer delay for rate limit errors
                    current_delay = delay
                    if isinstance(e, RateLimitError):
                        current_delay = delay * 2
                        self.logger.warning(f"Rate limit exceeded in {operation}, using longer delay: {current_delay}s")

                    self.logger.warning(
                        f"Retry attempt {attempts}/{max_retries} for {operation}: {str(e)}"
                    )
                    self._record_metric(operation, 'retry', 1)

                    # Sleep with exponential backoff
                    time.sleep(current_delay)
                    delay *= backoff_factor
                else:
                    self.logger.error(
                        f"All retry attempts failed for {operation}: {str(e)}"
                    )
                    break

        # If we get here, all retries failed
        if isinstance(last_error, ServiceError):
            # If it's already one of our error types, just re-raise it
            raise last_error
        else:
            # Convert to a ServiceError with context
            raise ServiceError(f"Operation {operation} failed after {max_retries} retries: {str(last_error)}", {
                "operation": operation,
                "attempts": attempts,
                "original_error": str(last_error),
                "error_type": type(last_error).__name__
            })
