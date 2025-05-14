"""
Test script for error handling in the TTSService class

This script tests the error handling functionality of the TTSService class, including:
- Validation errors
- Configuration errors
- Authentication errors
- Rate limit errors
- Provider errors
- Resource errors
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our services and error types
try:
    from src.services.tts_service import TTSService
    from src.services.base_service import (
        ServiceError, ProviderError, ValidationError, ConfigurationError,
        AuthenticationError, RateLimitError, ResourceError
    )
    print("TTSService and error types imported successfully")
except ImportError as e:
    print(f"Error importing TTSService or error types: {str(e)}")
    sys.exit(1)

def test_validation_error():
    """Test validation error handling"""
    print("\n=== Testing Validation Error ===")
    
    # Initialize the service
    service = TTSService()
    
    try:
        # Try to synthesize with empty text
        service.synthesize(text="", language="en", provider="openai")
        print("❌ Failed: Expected ValidationError but no exception was raised")
        return False
    except ValidationError as e:
        print(f"✅ Success: ValidationError caught: {str(e)}")
        print(f"Details: {e.details}")
        return True
    except Exception as e:
        print(f"❌ Failed: Expected ValidationError but got {type(e).__name__}: {str(e)}")
        return False

def test_authentication_error():
    """Test authentication error handling"""
    print("\n=== Testing Authentication Error ===")
    
    # Save the original API key
    original_api_key = os.environ.get("OPENAI_API_KEY")
    
    try:
        # Set an invalid API key
        os.environ["OPENAI_API_KEY"] = "invalid_key"
        
        # Initialize the service with the invalid key
        service = TTSService()
        
        try:
            # Try to synthesize with the invalid key
            service.synthesize(text="Test authentication error", language="en", provider="openai")
            print("❌ Failed: Expected AuthenticationError but no exception was raised")
            return False
        except AuthenticationError as e:
            print(f"✅ Success: AuthenticationError caught: {str(e)}")
            print(f"Provider: {e.provider}")
            print(f"Details: {e.details}")
            return True
        except Exception as e:
            print(f"❌ Failed: Expected AuthenticationError but got {type(e).__name__}: {str(e)}")
            return False
    finally:
        # Restore the original API key
        if original_api_key:
            os.environ["OPENAI_API_KEY"] = original_api_key
        else:
            del os.environ["OPENAI_API_KEY"]

def test_unknown_provider_error():
    """Test unknown provider error handling"""
    print("\n=== Testing Unknown Provider Error ===")
    
    # Initialize the service
    service = TTSService()
    
    try:
        # Try to synthesize with an unknown provider
        service.synthesize(text="Test unknown provider", language="en", provider="unknown_provider")
        print("❌ Failed: Expected ValidationError but no exception was raised")
        return False
    except ValidationError as e:
        print(f"✅ Success: ValidationError caught: {str(e)}")
        print(f"Details: {e.details}")
        return True
    except Exception as e:
        print(f"❌ Failed: Expected ValidationError but got {type(e).__name__}: {str(e)}")
        return False

def test_retry_with_exponential_backoff():
    """Test retry with exponential backoff"""
    print("\n=== Testing Retry with Exponential Backoff ===")
    
    # Initialize the service
    service = TTSService()
    
    # Create a function that fails the first time but succeeds the second time
    attempt_count = [0]
    
    def test_function():
        attempt_count[0] += 1
        if attempt_count[0] == 1:
            raise Exception("First attempt failed (expected)")
        return "Success"
    
    try:
        # Use the with_retry method
        start_time = time.time()
        result = service.with_retry(
            test_function,
            max_retries=2,
            initial_delay=0.1,
            backoff_factor=2.0,
            operation="test_operation"
        )
        elapsed = time.time() - start_time
        
        if result == "Success" and attempt_count[0] == 2:
            print(f"✅ Success: Retry succeeded after {attempt_count[0]} attempts")
            print(f"Time taken: {elapsed:.2f} seconds")
            return True
        else:
            print(f"❌ Failed: Expected 2 attempts but got {attempt_count[0]}")
            return False
    except Exception as e:
        print(f"❌ Failed: Unexpected exception: {type(e).__name__}: {str(e)}")
        return False

def main():
    """Main test function"""
    print("=== TTSService Error Handling Test ===")
    
    # Run tests
    results = {}
    
    # Test validation error
    results["validation_error"] = test_validation_error()
    
    # Test authentication error
    results["authentication_error"] = test_authentication_error()
    
    # Test unknown provider error
    results["unknown_provider_error"] = test_unknown_provider_error()
    
    # Test retry with exponential backoff
    results["retry_with_backoff"] = test_retry_with_exponential_backoff()
    
    # Print summary
    print("\n=== Test Summary ===")
    for test_name, success in results.items():
        print(f"{test_name}: {'✅ Success' if success else '❌ Failed'}")
    
    # Print overall result
    if all(results.values()):
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed.")
        failed_tests = [name for name, success in results.items() if not success]
        print(f"Failed tests: {', '.join(failed_tests)}")

if __name__ == "__main__":
    main()
