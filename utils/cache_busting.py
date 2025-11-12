"""
Cache busting utilities for VocalLocal Flask application.

This module provides utilities for implementing cache-busting strategies
to ensure users always get the latest version of static assets.
"""

import os
import hashlib
import time
from functools import lru_cache
from flask import current_app, url_for


class CacheBuster:
    """Cache busting utility class."""
    
    def __init__(self, app=None):
        self.app = app
        self._file_versions = {}
        self._last_check = {}
        self.check_interval = 300  # Check for file changes every 5 minutes
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the cache buster with Flask app."""
        self.app = app
        
        # Add template global function
        app.jinja_env.globals['versioned_url_for'] = self.versioned_url_for
        app.jinja_env.globals['static_version'] = self.get_file_version
        
        # Configure cache control headers
        @app.after_request
        def add_cache_headers(response):
            return self.add_cache_control_headers(response)
    
    def get_file_version(self, filename):
        """
        Get version string for a static file based on modification time.

        Args:
            filename (str): The filename relative to static folder

        Returns:
            str: Version string (timestamp or hash)
        """
        if not filename:
            return str(int(time.time()))

        # Force refresh for critical files to ensure latest version is served
        critical_files = [
            'script.js',
            'styles.css',
            'auth.css',
            'auth.js',
            'common.js',
            'js/bilingual-conversation.js',
            'js/usage-validation.js',
            'js/usage-enforcement.js',
            'js/usage-tracking-free.js',
            'js/plan-access-control.js',
            'js/language-preferences.js',
            'js/payment.js',
            'cache-manager.js',
            'mobile-nav.js',
            'navigation.js',
            'dashboard.js',
            'home.js',
            'history.js',
            'profile.js',
            'try_it_free.js'
        ]
        if filename in critical_files:
            current_time = time.time()
            try:
                static_folder = current_app.static_folder
                if static_folder:
                    file_path = os.path.join(static_folder, filename)
                    if os.path.exists(file_path):
                        # Use file modification time as version
                        mtime = os.path.getmtime(file_path)
                        version = str(int(mtime))
                        self._file_versions[filename] = version
                        self._last_check[filename] = current_time
                        return version
            except (OSError, IOError):
                pass
            # Fallback to current timestamp for critical files
            return str(int(current_time))

        # Check if we need to refresh the version
        current_time = time.time()
        if (filename not in self._last_check or
            current_time - self._last_check[filename] > self.check_interval):
            
            try:
                static_folder = current_app.static_folder
                if static_folder:
                    file_path = os.path.join(static_folder, filename)
                    if os.path.exists(file_path):
                        # Use file modification time as version
                        mtime = os.path.getmtime(file_path)
                        self._file_versions[filename] = str(int(mtime))
                    else:
                        # File doesn't exist, use current timestamp
                        self._file_versions[filename] = str(int(current_time))
                else:
                    self._file_versions[filename] = str(int(current_time))
                
                self._last_check[filename] = current_time
                
            except (OSError, IOError):
                # If we can't access the file, use current timestamp
                self._file_versions[filename] = str(int(current_time))
                self._last_check[filename] = current_time
        
        return self._file_versions.get(filename, str(int(current_time)))
    
    def versioned_url_for(self, endpoint, **values):
        """
        Generate a versioned URL for static files.
        
        Args:
            endpoint (str): The endpoint name
            **values: Additional values for url_for
            
        Returns:
            str: Versioned URL
        """
        if endpoint == 'static':
            filename = values.get('filename')
            if filename:
                version = self.get_file_version(filename)
                values['v'] = version
        
        return url_for(endpoint, **values)
    
    def add_cache_control_headers(self, response):
        """
        Add appropriate cache control headers to responses.
        
        Args:
            response: Flask response object
            
        Returns:
            Flask response object with cache headers
        """
        # Get the request path
        try:
            from flask import request
            request_path = request.path
        except:
            return response
        
        # Static files with version parameter - cache for 1 year
        if '/static/' in request_path and 'v=' in request.query_string.decode():
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            response.headers['Expires'] = time.strftime(
                '%a, %d %b %Y %H:%M:%S GMT',
                time.gmtime(time.time() + 31536000)
            )

        # Critical CSS/JS files without version - force revalidation
        elif '/static/' in request_path and any(critical in request_path for critical in [
            'styles.css', 'script.js', 'auth.css', 'auth.js', 'common.js',
            'bilingual-conversation.js', 'usage-validation.js', 'usage-enforcement.js',
            'usage-tracking-free.js', 'plan-access-control.js', 'language-preferences.js',
            'payment.js', 'cache-manager.js', 'mobile-nav.js', 'navigation.js',
            'dashboard.js', 'home.js', 'history.js', 'profile.js', 'try_it_free.js'
        ]):
            response.headers['Cache-Control'] = 'no-cache, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            response.headers['Last-Modified'] = time.strftime(
                '%a, %d %b %Y %H:%M:%S GMT',
                time.gmtime()
            )

        # Other static files without version - cache for 1 hour
        elif '/static/' in request_path:
            response.headers['Cache-Control'] = 'public, max-age=3600'
            response.headers['Expires'] = time.strftime(
                '%a, %d %b %Y %H:%M:%S GMT',
                time.gmtime(time.time() + 3600)
            )
        
        # HTML pages - no cache or short cache
        elif request_path.endswith('.html') or request_path == '/':
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        # API endpoints - no cache
        elif '/api/' in request_path:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response


# Global cache buster instance
cache_buster = CacheBuster()


def get_static_version(filename):
    """
    Convenience function to get static file version.
    
    Args:
        filename (str): Static file name
        
    Returns:
        str: Version string
    """
    return cache_buster.get_file_version(filename)


def versioned_static_url(filename):
    """
    Generate a versioned static file URL.
    
    Args:
        filename (str): Static file name
        
    Returns:
        str: Versioned URL
    """
    return cache_buster.versioned_url_for('static', filename=filename)
