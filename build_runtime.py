#!/usr/bin/env python
"""
Build and runtime configuration script for VocalLocal.
This script handles environment setup, dependency checking, and runtime configuration.
"""
import os
import sys
import json
import signal
import inspect
import importlib
import subprocess
import unittest
import tempfile
import time
import threading
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("build_runtime")

class BuildRuntimeEngineer:
    """
    Automated build and runtime engineer for the VocalLocal stack.
    Handles environment setup, dependency checking, and runtime configuration.
    """
    
    def __init__(self):
        """Initialize the build and runtime engineer."""
        self.results = {
            "status": "pending",
            "steps": [],
            "gunicorn_cmd": "",
            "robust_chunker_kwargs": {},
            "tests_passed": False,
            "notes": ""
        }
        
        # Signal handling
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigterm)
        
    def _handle_sigterm(self, signum, frame):
        """Handle SIGTERM and SIGINT signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        # If we have a gRPC server, stop it gracefully
        try:
            if hasattr(self, 'grpc_server'):
                self.grpc_server.stop(grace=0)
        except:
            pass
        
        # Print final results
        self.results["status"] = "terminated"
        self.results["notes"] = f"Terminated by signal {signum}"
        print(json.dumps(self.results, indent=2))
        sys.exit(0)
        
    def _add_step_result(self, step, status, message="", details=None):
        """Add a step result to the results dictionary."""
        step_result = {
            "step": step,
            "status": status,
            "message": message
        }
        if details:
            step_result["details"] = details
            
        self.results["steps"].append(step_result)
        
        if status == "error":
            logger.error(f"Step '{step}' failed: {message}")
        else:
            logger.info(f"Step '{step}' {status}: {message}")
            
    def check_environment(self):
        """Check required environment variables."""
        required_vars = ["INPUT_PATH", "OUTPUT_DIR"]
        missing_vars = []
        
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
                
        if missing_vars:
            self._add_step_result(
                "check_environment", 
                "error", 
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
            return False
            
        # Set defaults for optional variables
        if not os.environ.get("CHUNK_SECONDS"):
            os.environ["CHUNK_SECONDS"] = "300"
            
        self._add_step_result(
            "check_environment", 
            "success", 
            "All required environment variables are present"
        )
        return True
        
    def patch_gunicorn_settings(self):
        """Patch Gunicorn settings to use gthread workers with appropriate timeouts."""
        current_args = os.environ.get("GUNICORN_CMD_ARGS", "")
        
        # Check if the required settings are already present
        required_settings = "--worker-class gthread --threads 4 --timeout 120 --graceful-timeout 120"
        settings_to_add = []
        
        for setting in required_settings.split():
            setting_name = setting.split()[0] if " " in setting else setting
            if setting_name not in current_args:
                settings_to_add.append(setting)
                
        if settings_to_add:
            new_args = f"{current_args} {' '.join(settings_to_add)}".strip()
            os.environ["GUNICORN_CMD_ARGS"] = new_args
            
            self._add_step_result(
                "patch_gunicorn_settings", 
                "success", 
                f"Updated Gunicorn settings: {new_args}"
            )
        else:
            self._add_step_result(
                "patch_gunicorn_settings", 
                "success", 
                "Gunicorn settings already contain required values"
            )
            
        self.results["gunicorn_cmd"] = os.environ.get("GUNICORN_CMD_ARGS", "")
        return True
        
    def check_dependencies(self):
        """Check and install required dependencies."""
        missing_deps = []
        
        # Check for tiktoken
        try:
            importlib.import_module("tiktoken")
        except ImportError:
            missing_deps.append("tiktoken>=0.9.0")
            
        # Install missing dependencies
        if missing_deps:
            try:
                for dep in missing_deps:
                    logger.info(f"Installing missing dependency: {dep}")
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--no-cache-dir", "--upgrade", dep],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    
                self._add_step_result(
                    "check_dependencies", 
                    "success", 
                    f"Installed missing dependencies: {', '.join(missing_deps)}"
                )
            except subprocess.CalledProcessError as e:
                self._add_step_result(
                    "check_dependencies", 
                    "error", 
                    f"Failed to install dependencies: {e.stderr}"
                )
                return False
        else:
            self._add_step_result(
                "check_dependencies", 
                "success", 
                "All required dependencies are installed"
            )
            
        return True
        
    def locate_robust_chunker(self):
        """Locate the RobustChunker class and determine the correct parameter names."""
        try:
            # Try to import from services.robust_chunker first
            try:
                RobustChunker = importlib.import_module("services.robust_chunker").RobustChunker
            except (ImportError, AttributeError):
                # Fall back to services.audio_chunker
                RobustChunker = importlib.import_module("services.audio_chunker").RobustChunker
                
            # Inspect the signature to determine the correct parameter names
            params = inspect.signature(RobustChunker).parameters
            kwargs = {}
            
            # Set chunk duration
            chunk_seconds = int(os.environ.get("CHUNK_SECONDS", 300))
            if "chunk_duration" in params:
                kwargs["chunk_duration"] = chunk_seconds
            elif "chunk_duration_seconds" in params:
                kwargs["chunk_duration_seconds"] = chunk_seconds
            else:
                self._add_step_result(
                    "locate_robust_chunker", 
                    "error", 
                    "RobustChunker accepts neither 'chunk_duration' nor 'chunk_duration_seconds'"
                )
                return False
                
            # Set other parameters if they exist in the signature
            if "max_retries" in params:
                kwargs["max_retries"] = 2
            if "retry_delay" in params:
                kwargs["retry_delay"] = 2
                
            self.results["robust_chunker_kwargs"] = kwargs
            self._add_step_result(
                "locate_robust_chunker", 
                "success", 
                f"Located RobustChunker with parameters: {kwargs}"
            )
            return True
            
        except Exception as e:
            self._add_step_result(
                "locate_robust_chunker", 
                "error", 
                f"Failed to locate RobustChunker: {str(e)}"
            )
            return False
            
    def run_unit_tests(self):
        """Run unit tests if they exist."""
        tests_dir = Path("tests/unit")
        if not tests_dir.exists():
            self._add_step_result(
                "run_unit_tests", 
                "skipped", 
                "Unit tests directory does not exist"
            )
            return True
            
        try:
            # Discover and run tests
            loader = unittest.TestLoader()
            suite = loader.discover(str(tests_dir))
            
            # Run tests with a custom test runner that captures results
            class CaptureTestResult(unittest.TextTestResult):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.test_results = []
                    
                def addSuccess(self, test):
                    super().addSuccess(test)
                    self.test_results.append((test, "success", ""))
                    
                def addError(self, test, err):
                    super().addError(test, err)
                    self.test_results.append((test, "error", str(err[1])))
                    
                def addFailure(self, test, err):
                    super().addFailure(test, err)
                    self.test_results.append((test, "failure", str(err[1])))
            
            runner = unittest.TextTestRunner(resultclass=CaptureTestResult)
            result = runner.run(suite)
            
            # Check if all tests passed
            if result.wasSuccessful():
                self.results["tests_passed"] = True
                self._add_step_result(
                    "run_unit_tests", 
                    "success", 
                    f"All {result.testsRun} tests passed"
                )
                return True
            else:
                # Collect failed test details
                failed_tests = []
                for test, status, message in result.test_results:
                    if status != "success":
                        failed_tests.append({
                            "test": test.id(),
                            "status": status,
                            "message": message
                        })
                        
                self._add_step_result(
                    "run_unit_tests", 
                    "error", 
                    f"{len(failed_tests)} tests failed",
                    {"failed_tests": failed_tests}
                )
                return False
                
        except Exception as e:
            self._add_step_result(
                "run_unit_tests", 
                "error", 
                f"Failed to run unit tests: {str(e)}"
            )
            return False
