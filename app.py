"""
VocalLocal Web Service - Main Application
"""

import os
import sys
import subprocess
import tempfile
from flask import Flask, redirect, url_for, flash, render_template, jsonify, send_from_directory
from config import Config
import jinja2

# Try to import Google Generative AI, install if missing
GEMINI_AVAILABLE = False
try:
    # Try to import the module
    print("Attempting to import google.generativeai...")
    try:
        import google.generativeai as genai
        GEMINI_AVAILABLE = True
        print("Google Generative AI module loaded successfully")
    except ImportError as e:
        print(f"Google Generative AI module not available: {str(e)}")
        print("Attempting to install Google Generative AI module...")
        try:
            # Install the required packages
            subprocess.check_call([sys.executable, "-m", "pip", "install", 
                                  "google-generativeai", "google-cloud-aiplatform",
                                  "googleapis-common-protos", "protobuf"])

            # Try importing again
            import google.generativeai as genai
            GEMINI_AVAILABLE = True
            print("Google Generative AI module installed and loaded successfully")
        except Exception as install_error:
            print(f"Failed to install Google Generative AI module: {str(install_error)}")
            GEMINI_AVAILABLE = False

            # Create a placeholder for genai
            class GenaiPlaceholder:
                def configure(self, **kwargs):
                    pass
            genai = GenaiPlaceholder()
except Exception as outer_e:
    print(f"Outer exception during Google Generative AI import: {str(outer_e)}")
    GEMINI_AVAILABLE = False

    # Create a placeholder for genai
    class GenaiPlaceholder:
        def configure(self, **kwargs):
            pass
    genai = GenaiPlaceholder()

# Import token counter and metrics tracker
try:
    import tiktoken
except ImportError:
    # Install tiktoken if not available
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tiktoken"])
        import tiktoken
    except Exception as e:
        print(f"Failed to install tiktoken: {e}")

# Import our custom modules
try:
    from token_counter import (
        count_openai_tokens, count_openai_chat_tokens, count_openai_audio_tokens,
        count_gemini_tokens, count_gemini_audio_tokens, estimate_audio_duration
    )
    from metrics_tracker import metrics_tracker
    METRICS_AVAILABLE = True
    print("Metrics tracking enabled")
except ImportError as e:
    print(f"Metrics tracking not available: {e}")
    METRICS_AVAILABLE = False

# Initialize Flask application
import os
static_folder = os.path.join(os.path.dirname(__file__), 'static')
template_folder = os.path.join(os.path.dirname(__file__), 'templates')
app = Flask(__name__, static_folder=static_folder, template_folder=template_folder)
app.secret_key = Config.SECRET_KEY

# Initialize cache busting system
from utils.cache_busting import cache_buster
cache_buster.init_app(app)

# Configure upload settings
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
# No MAX_CONTENT_LENGTH set to allow larger files
# API-specific limits are handled in the service layer

# Configure Stripe settings
app.config['STRIPE_PUBLISHABLE_KEY'] = Config.STRIPE_PUBLISHABLE_KEY
app.config['STRIPE_SECRET_KEY'] = Config.STRIPE_SECRET_KEY
app.config['STRIPE_WEBHOOK_SECRET'] = Config.STRIPE_WEBHOOK_SECRET

# Set up comprehensive error handling
try:
    from utils.error_handler import register_error_handlers
    register_error_handlers(app)
    print("Error handlers registered successfully")
except ImportError as e:
    print(f"Warning: Could not import error handlers: {e}")

# Initialize Firebase with error handling
try:
    from firebase_config import initialize_firebase
    initialize_firebase()
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Warning: Firebase initialization failed: {e}")
    print("Application will continue with limited functionality")

# Initialize authentication
try:
    import auth
    auth.init_app(app)
    print("Authentication initialized successfully")
except Exception as e:
    print(f"Warning: Authentication initialization failed: {e}")

# Define a simple index route at the root level
@app.route('/')
def index():
    """Main index route - handles both authenticated and non-authenticated users."""
    from flask_login import current_user
    if current_user.is_authenticated:
        # User is logged in, show the main application
        return render_template('index.html')
    else:
        # User is not logged in, show the home page
        return render_template('home.html')

# Register routes for auth directly at the root level
@app.route('/auth/google')
def root_google_login():
    """Redirect to the auth blueprint's Google login route."""
    return redirect(url_for('auth.google_login'))

@app.route('/auth/callback')
def root_auth_callback():
    """Handle the Google OAuth callback directly."""
    try:
        # Import the callback handler function
        from auth import _handle_google_callback

        # Call the handler function directly
        return _handle_google_callback()
    except Exception as e:
        print(f"Error in root_auth_callback: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash("Error during authentication. Please try again.", "danger")
        return redirect(url_for('auth.login'))

# Add missing routes that were showing 404
@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'VocalLocal'})

@app.route('/api/health')
def api_health_check():
    """API health check endpoint."""
    return jsonify({'status': 'healthy', 'api': 'VocalLocal API'})

@app.route('/pricing')
def pricing():
    """Pricing page."""
    return render_template('pricing.html')

@app.route('/transcribe')
def transcribe():
    """Transcribe page."""
    return render_template('transcribe.html')

@app.route('/translate')
def translate():
    """Translate page."""
    return render_template('translate.html')

# Register blueprints
from routes import main, transcription, translation, tts, admin, interpretation, usage_tracking, user, payment

app.register_blueprint(main.bp)
app.register_blueprint(transcription.bp)
app.register_blueprint(translation.bp)
app.register_blueprint(tts.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(interpretation.bp)
app.register_blueprint(usage_tracking.bp)
app.register_blueprint(user.bp)
app.register_blueprint(payment.bp)

# Register auth blueprint without URL prefix to make /login work
from auth import auth_bp
# Remove the URL prefix so /login works directly
auth_bp.url_prefix = None
app.register_blueprint(auth_bp, name='auth_blueprint')

# Import the transcription service for the status endpoint
from services.transcription import transcription_service
from models.firebase_models import Transcription, Translation

@app.route('/api/transcription_status/<job_id>', methods=['GET'])
def transcription_status(job_id):
    """Check the status of a background transcription job"""
    status = transcription_service.get_job_status(job_id)
    return jsonify(status)

# Add API route for user available models
@app.route('/test-sandbox')
def test_sandbox():
    """Test sandbox page for development and testing"""
    return send_from_directory('static', 'test_sandbox.html')

@app.route('/progressive-test')
def progressive_test():
    """Progressive recording test page with 7-minute chunks and 10-second overlap"""
    return send_from_directory('static', 'progressive_test.html')

@app.route('/test-chunking-fix')
def test_chunking_fix():
    """Test chunking fix page"""
    return send_from_directory('.', 'test_chunking_fix.html')

@app.route('/debug-test')
def debug_test():
    """Simple debug test to verify server is working"""
    return """
    <html>
        <head><title>VocalLocal Debug Test</title></head>
        <body>
            <h1>🎉 SUCCESS! Your Flask server is working!</h1>
            <p>Server is running properly on HTTPS.</p>
            <h2>Available Test URLs:</h2>
            <ul>
                <li><a href="/progressive-test">🎤 Progressive Recording Test (NEW!)</a> - 7-minute chunks with 10s overlap</li>
                <li><a href="/test-sandbox">Test Sandbox (OLD)</a></li>
                <li><a href="/test-chunking-fix">Test Chunking Fix</a></li>
                <li><a href="/">Main App</a></li>
            </ul>
            <h2>Static Files Test:</h2>
            <p>CSS: <link rel="stylesheet" href="/static/styles.css"></p>
            <p>JS: <script src="/static/script.js"></script></p>
        </body>
    </html>
    """

@app.route('/privacy')
def privacy():
    """Privacy policy and ethical guidelines page"""
    return render_template('privacy.html')

@app.route('/debug-recording')
def debug_recording():
    """Debug page for recording issues"""
    return send_from_directory('.', 'debug_recording.html')

if __name__ == '__main__':
    import argparse
    import webbrowser
    from threading import Timer
    import json

    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='VocalLocal Web Service')
    parser.add_argument('--port', type=int, default=Config.PORT,
                        help=f'Port to run the server on (default: {Config.PORT})')
    parser.add_argument('--host', type=str, default=Config.HOST,
                        help=f'Host to run the server on (default: {Config.HOST})')
    parser.add_argument('--debug', action='store_true', default=Config.DEBUG,
                        help=f'Run in debug mode (default: {Config.DEBUG})')
    parser.add_argument('--secure', action='store_true', default=False,
                        help='Run with HTTPS (default: False)')
    parser.add_argument('--open-browser', action='store_true', default=False,
                        help='Automatically open browser (default: False)')

    # Parse arguments
    args = parser.parse_args()

    # Function to open browser
    def open_browser():
        protocol = "https" if args.secure else "http"
        url = f"{protocol}://localhost:{args.port}"
        print(f"Opening browser at {url}")
        webbrowser.open_new(url)

    # Print startup message
    protocol = "https" if args.secure else "http"
    print(f"Starting VocalLocal on {protocol}://localhost:{args.port}")
    print(f"Press Ctrl+C to quit")

    # Open browser after a short delay only if --open-browser flag is set
    if args.open_browser:
        Timer(1.5, open_browser).start()
        print("Browser will open automatically in a moment...")
    else:
        print(f"Access the application at {protocol}://localhost:{args.port}")

    # Run the application
    app.run(debug=args.debug, host=args.host, port=args.port)
