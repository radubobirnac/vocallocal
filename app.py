"""
VocalLocal Web Service - Flask API for speech-to-text
"""

import os
import sys
import subprocess
import tempfile
from flask import Flask, redirect, url_for, flash, render_template, jsonify, send_from_directory
from config import Config
import jinja2

# Try to import Google Generative AI, install if missing
try:
    # Print debug information about the Python path
    print("Python path:")
    for path in sys.path:
        print(f"  {path}")

    # Try to import the module
    print("Attempting to import google.generativeai...")
    try:
        import google.generativeai as genai
        GEMINI_AVAILABLE = True
        print("Google Generative AI module loaded successfully")
    except ImportError as e:
        print(f"Google Generative AI module not available: {str(e)}")
        print("Attempting to install Google Generative AI module...")

        # Try to install the package
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai>=0.8.5"])
            subprocess.check_call([sys.executable, "-m", "pip", "install",
                                  "google-api-core", "google-api-python-client", "google-auth",
                                  "google-auth-httplib2", "google-auth-oauthlib",
                                  "googleapis-common-protos", "protobuf"])

            # Try importing again
            import google.generativeai as genai
            GEMINI_AVAILABLE = True
            print("Google Generative AI module installed and loaded successfully")
        except Exception as install_error:
            print(f"Failed to install Google Generative AI module: {str(install_error)}")
            GEMINI_AVAILABLE = False
            print("Gemini features will be disabled.")

            # Create a placeholder for genai
            class GenaiPlaceholder:
                def configure(self, **kwargs):
                    pass
            genai = GenaiPlaceholder()
except Exception as outer_e:
    print(f"Unexpected error: {str(outer_e)}")
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
    except Exception:
        print("Failed to install tiktoken. Token counting will use approximations.")

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
    print(f"Metrics tracking not available: {str(e)}")
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

# Add a global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    import traceback
    app.logger.error(traceback.format_exc())

    # Try to render the error template, but have a fallback if it's missing
    try:
        return render_template('error.html', error=str(e)), 500
    except jinja2.exceptions.TemplateNotFound:
        # Fallback for missing template
        return f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>An error occurred</h1>
                <p>{str(e)}</p>
                <p><a href="/">Return to home</a></p>
            </body>
        </html>
        """, 500

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
from routes import main, transcription, translation, tts, admin, interpretation, usage_tracking

app.register_blueprint(main.bp)
app.register_blueprint(transcription.bp)
app.register_blueprint(translation.bp)
app.register_blueprint(tts.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(interpretation.bp)
app.register_blueprint(usage_tracking.bp)

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

@app.route('/api/user/available-models', methods=['GET'])
def get_user_available_models():
    """API endpoint to get available models for the current user"""
    try:
        from services.model_access_service import ModelAccessService
        from flask_login import current_user

        if not current_user.is_authenticated:
            # Return free models for non-authenticated users
            return jsonify({
                'transcription_models': [
                    {'value': 'gemini-2.0-flash-lite', 'label': 'Gemini 2.0 Flash Lite', 'free': True}
                ],
                'translation_models': [
                    {'value': 'gemini-2.0-flash-lite', 'label': 'Gemini 2.0 Flash Lite', 'free': True}
                ],
                'user_role': None,
                'has_premium_access': False
            })

        # Get user's available models
        available_models = ModelAccessService.get_available_models(current_user.email)
        user_role = getattr(current_user, 'role', 'normal_user')

        # Define authorized models by category
        authorized_models = {
            'transcription': [
                {'value': 'gemini-2.0-flash-lite', 'label': 'Gemini 2.0 Flash Lite', 'free': True},
                {'value': 'gpt-4o-mini-transcribe', 'label': 'OpenAI GPT-4o Mini', 'free': False},
                {'value': 'gpt-4o-transcribe', 'label': 'OpenAI GPT-4o', 'free': False},
                {'value': 'gemini-2.5-flash-preview-04-17', 'label': 'Gemini 2.5 Flash Preview', 'free': False}
            ],
            'translation': [
                {'value': 'gemini-2.0-flash-lite', 'label': 'Gemini 2.0 Flash Lite', 'free': True},
                {'value': 'gemini-2.5-flash', 'label': 'Gemini 2.5 Flash Preview', 'free': False},
                {'value': 'gpt-4.1-mini', 'label': 'GPT-4.1 Mini', 'free': False}
            ]
        }

        # Build response with authorized models only
        transcription_models = []
        translation_models = []

        # Add transcription models based on user access
        for model in authorized_models['transcription']:
            if model['free'] or user_role in ['admin', 'super_user']:
                transcription_models.append(model)
            elif user_role == 'normal_user':
                # Add locked premium models for normal users
                locked_model = model.copy()
                locked_model['label'] += ' 🔒'
                locked_model['locked'] = True
                transcription_models.append(locked_model)

        # Add translation models based on user access
        for model in authorized_models['translation']:
            if model['free'] or user_role in ['admin', 'super_user']:
                translation_models.append(model)
            elif user_role == 'normal_user':
                # Add locked premium models for normal users
                locked_model = model.copy()
                locked_model['label'] += ' 🔒'
                locked_model['locked'] = True
                translation_models.append(locked_model)

        return jsonify({
            'transcription_models': transcription_models,
            'translation_models': translation_models,
            'user_role': user_role,
            'has_premium_access': user_role in ['admin', 'super_user'],
            'restrictions': available_models.get('restrictions', {})
        })

    except Exception as e:
        print(f"Error getting available models: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to get available models',
            'details': str(e)
        }), 500

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

    # Check if we should use HTTPS based on OAuth.json
    oauth_file_path = os.path.join(os.path.dirname(__file__), 'Oauth.json')
    if os.path.exists(oauth_file_path) and not args.secure:
        try:
            with open(oauth_file_path, 'r') as f:
                oauth_data = json.load(f)

            # Check if redirect URIs use HTTPS
            if 'web' in oauth_data and 'redirect_uris' in oauth_data['web']:
                for uri in oauth_data['web']['redirect_uris']:
                    if uri.startswith('https://'):
                        print("OAuth.json contains HTTPS redirect URIs. Enabling secure mode.")
                        args.secure = True
                        break
        except Exception as e:
            print(f"Error reading OAuth.json: {str(e)}")

    # Function to open browser
    def open_browser():
        protocol = "https" if args.secure else "http"
        url = f"{protocol}://localhost:{args.port}"
        print(f"Opening browser at {url}")
        webbrowser.open_new(url)

    # Check if secure mode is enabled
    ssl_context = None
    if args.secure:
        # Check if certificates exist
        import os
        os.makedirs('ssl', exist_ok=True)
        if not (os.path.exists('ssl/cert.pem') and os.path.exists('ssl/key.pem')):
            print("SSL certificates not found. Generating self-signed certificates...")
            try:
                from OpenSSL import crypto
                # Generate a key pair
                key = crypto.PKey()
                key.generate_key(crypto.TYPE_RSA, 2048)

                # Create a self-signed cert
                cert = crypto.X509()
                cert.get_subject().CN = "localhost"
                cert.set_serial_number(1000)
                cert.gmtime_adj_notBefore(0)
                cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for a year
                cert.set_issuer(cert.get_subject())
                cert.set_pubkey(key)
                cert.sign(key, 'sha256')

                # Write to disk
                with open("ssl/cert.pem", "wb") as f:
                    f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
                with open("ssl/key.pem", "wb") as f:
                    f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

                print("Self-signed certificates generated in ssl/ directory")
            except ImportError:
                print("PyOpenSSL not installed. Please run 'pip install pyopenssl' or use --secure=False")
                exit(1)
            except Exception as e:
                print(f"Error generating certificates: {str(e)}")
                exit(1)

        ssl_context = ('ssl/cert.pem', 'ssl/key.pem')
        print("Running with HTTPS enabled")

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
    app.run(debug=args.debug, host=args.host, port=args.port, ssl_context=ssl_context)
