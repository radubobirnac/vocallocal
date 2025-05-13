"""
Base service class for VocalLocal
"""
import time

class BaseService:
    """Base class for all services with common functionality"""
    
    def __init__(self):
        """Initialize the service"""
        self.metrics_available = False
        try:
            # Import metrics tracker if available
            from metrics_tracker import metrics_tracker
            self.metrics_tracker = metrics_tracker
            self.metrics_available = True
        except ImportError:
            self.metrics_tracker = None
            print("Metrics tracking not available")
    
    def track_metrics(self, service_type, model, tokens, chars, time_taken, success):
        """
        Track metrics for the service call
        
        Args:
            service_type: Type of service (transcription, translation, tts)
            model: Model used for the service
            tokens: Number of tokens used
            chars: Number of characters processed
            time_taken: Time taken for the operation
            success: Whether the operation was successful
        
        Returns:
            True if metrics were tracked, False otherwise
        """
        if self.metrics_available:
            try:
                # Initialize service section if it doesn't exist
                if service_type not in self.metrics_tracker.metrics:
                    self.metrics_tracker.metrics[service_type] = {}
                
                # Initialize model if it doesn't exist
                if model not in self.metrics_tracker.metrics[service_type]:
                    self.metrics_tracker.metrics[service_type][model] = {
                        "calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0
                    }
                
                # Update metrics
                self.metrics_tracker.metrics[service_type][model]["calls"] += 1
                self.metrics_tracker.metrics[service_type][model]["tokens"] += tokens
                self.metrics_tracker.metrics[service_type][model]["chars"] += chars
                self.metrics_tracker.metrics[service_type][model]["time"] += time_taken
                
                if not success:
                    self.metrics_tracker.metrics[service_type][model]["failures"] += 1
                
                # Save metrics
                self.metrics_tracker._save_metrics()
                
                return True
            except Exception as e:
                print(f"Warning: Could not track metrics: {str(e)}")
                return False
        return False
    
    def measure_execution_time(self, func, *args, **kwargs):
        """
        Measure the execution time of a function
        
        Args:
            func: Function to measure
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Tuple of (result, execution_time)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time
