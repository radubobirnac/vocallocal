"""
Comprehensive error handling utilities for VocalLocal application.
"""
import logging
import traceback
from functools import wraps
from flask import jsonify, render_template, request, current_app

logger = logging.getLogger(__name__)

class VocalLocalError(Exception):
    """Base exception class for VocalLocal application."""
    def __init__(self, message, error_code=None, status_code=500):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code

class FirebaseError(VocalLocalError):
    """Firebase-related errors."""
    def __init__(self, message, error_code="FIREBASE_ERROR"):
        super().__init__(message, error_code, 503)

class ImportError(VocalLocalError):
    """Import-related errors."""
    def __init__(self, message, error_code="IMPORT_ERROR"):
        super().__init__(message, error_code, 500)

class NavigationError(VocalLocalError):
    """Navigation-related errors."""
    def __init__(self, message, error_code="NAVIGATION_ERROR"):
        super().__init__(message, error_code, 400)

def handle_errors(f):
    """Decorator to handle errors in route functions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except VocalLocalError as e:
            logger.error(f"VocalLocal error in {f.__name__}: {e.message}")
            if request.is_json:
                return jsonify({
                    'error': e.message,
                    'error_code': e.error_code,
                    'status': 'error'
                }), e.status_code
            else:
                return render_template('error.html',
                                     error=e.message,
                                     error_code=e.error_code), e.status_code
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            if request.is_json:
                return jsonify({
                    'error': 'An unexpected error occurred',
                    'error_code': 'INTERNAL_ERROR',
                    'status': 'error'
                }), 500
            else:
                return render_template('error.html',
                                     error='An unexpected error occurred',
                                     error_code='INTERNAL_ERROR'), 500
    return decorated_function

def safe_import(module_name, fallback=None):
    """Safely import a module with fallback."""
    try:
        return __import__(module_name)
    except ImportError as e:
        logger.warning(f"Failed to import {module_name}: {str(e)}")
        if fallback:
            logger.info(f"Using fallback for {module_name}")
            return fallback
        raise ImportError(f"Failed to import {module_name} and no fallback provided")

def safe_firebase_operation(operation, fallback_result=None, error_message="Firebase operation failed"):
    """Safely execute a Firebase operation with fallback."""
    try:
        return operation()
    except Exception as e:
        logger.error(f"{error_message}: {str(e)}")
        if fallback_result is not None:
            logger.info("Using fallback result for Firebase operation")
            return fallback_result
        raise FirebaseError(error_message)

def register_error_handlers(app):
    """Register global error handlers for the Flask app."""

    @app.errorhandler(404)
    def not_found_error(error):
        if request.is_json:
            return jsonify({
                'error': 'Resource not found',
                'error_code': 'NOT_FOUND',
                'status': 'error'
            }), 404
        return render_template('error.html',
                             error='Page not found',
                             error_code='NOT_FOUND'), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        if request.is_json:
            return jsonify({
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR',
                'status': 'error'
            }), 500
        return render_template('error.html',
                             error='Internal server error',
                             error_code='INTERNAL_ERROR'), 500

    @app.errorhandler(VocalLocalError)
    def handle_vocal_local_error(error):
        logger.error(f"VocalLocal error: {error.message}")
        if request.is_json:
            return jsonify({
                'error': error.message,
                'error_code': error.error_code,
                'status': 'error'
            }), error.status_code
        return render_template('error.html',
                             error=error.message,
                             error_code=error.error_code), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.error(f"Unexpected error: {str(error)}")
        logger.error(traceback.format_exc())
        if request.is_json:
            return jsonify({
                'error': 'An unexpected error occurred',
                'error_code': 'UNEXPECTED_ERROR',
                'status': 'error'
            }), 500
        return render_template('error.html',
                             error='An unexpected error occurred',
                             error_code='UNEXPECTED_ERROR'), 500

class SafeFirebaseService:
    """Wrapper for Firebase service with built-in error handling."""

    def __init__(self):
        self.service = None
        self.initialized = False
        self._initialize()

    def _initialize(self):
        """Initialize Firebase service safely."""
        try:
            from services.firebase_service import FirebaseService
            self.service = FirebaseService()
            self.initialized = self.service.initialized
            logger.info("SafeFirebaseService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SafeFirebaseService: {str(e)}")
            self.initialized = False

    def get_ref(self, path):
        """Get Firebase reference safely."""
        if not self.initialized or not self.service:
            logger.warning("Firebase service not available, returning mock reference")
            return MockFirebaseRef()

        try:
            ref = self.service.get_ref(path)
            if ref is None:
                logger.warning(f"Firebase reference for {path} is None, returning mock reference")
                return MockFirebaseRef()
            return ref
        except Exception as e:
            logger.error(f"Error getting Firebase reference for {path}: {str(e)}")
            return MockFirebaseRef()

    def upload_to_storage(self, file_path, destination_path):
        """Upload to storage safely."""
        if not self.initialized or not self.service:
            logger.warning("Firebase service not available for storage upload")
            return None

        try:
            return self.service.upload_to_storage(file_path, destination_path)
        except Exception as e:
            logger.error(f"Error uploading to storage: {str(e)}")
            return None

class MockFirebaseRef:
    """Mock Firebase reference for fallback."""

    def get(self):
        return {}

    def set(self, data):
        logger.info(f"Mock Firebase set called with data: {data}")
        return True

    def push(self, data):
        logger.info(f"Mock Firebase push called with data: {data}")
        return MockFirebaseRef()

    def child(self, path):
        return MockFirebaseRef()
