"""
Main routes for VocalLocal
"""
from flask import Blueprint, render_template, send_from_directory, request
from flask_login import current_user, login_required
# Import the Transcription and Translation classes
# Use a more robust approach to ensure they are available
import sys
import os
import importlib.util

# Define the Transcription and Translation classes globally to ensure they're available
# even if imports fail
class TranscriptionFallback:
    @staticmethod
    def get_by_user(email, limit=10):
        print(f"Using fallback Transcription class for {email}")
        return {}

    @staticmethod
    def get_ref(path):
        class RefObj:
            @staticmethod
            def get():
                return {}
        return RefObj()

class TranslationFallback:
    @staticmethod
    def get_by_user(email, limit=10):
        print(f"Using fallback Translation class for {email}")
        return {}

    @staticmethod
    def get_ref(path):
        class RefObj:
            @staticmethod
            def get():
                return {}
        return RefObj()

# Try to import the real classes
try:
    # Add the parent directory to sys.path to ensure imports work
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Try different import paths
    try:
        from models.firebase_models import Transcription, Translation
        print("Successfully imported Transcription and Translation from models.firebase_models")
    except ImportError:
        try:
            from vocallocal.models.firebase_models import Transcription, Translation
            print("Successfully imported Transcription and Translation from vocallocal.models.firebase_models")
        except ImportError:
            # Try to load the module directly from the file path
            try:
                module_path = os.path.join(parent_dir, 'models', 'firebase_models.py')
                spec = importlib.util.spec_from_file_location("firebase_models", module_path)
                firebase_models = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(firebase_models)
                Transcription = firebase_models.Transcription
                Translation = firebase_models.Translation
                print(f"Successfully imported Transcription and Translation from {module_path}")
            except (ImportError, AttributeError, FileNotFoundError) as e:
                print(f"Failed to import from file: {str(e)}")
                # Use fallback classes
                Transcription = TranscriptionFallback
                Translation = TranslationFallback
                print("Using fallback Transcription and Translation classes")
except Exception as e:
    print(f"Error importing Transcription and Translation: {str(e)}")
    # Use fallback classes
    Transcription = TranscriptionFallback
    Translation = TranslationFallback
    print("Using fallback Transcription and Translation classes due to exception")

# Create a blueprint for the main routes
bp = Blueprint('main', __name__)

@bp.route('/main')
def index():
    """Main index route - handles both authenticated and non-authenticated users."""
    if current_user.is_authenticated:
        # User is logged in, show the main application
        return render_template('index.html')
    else:
        # User is not logged in, show the home page
        return render_template('home.html')

@bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    # No longer fetching transcriptions and translations for the profile page
    # as they are now accessed exclusively through the History dropdown

    return render_template('profile.html',
                          user=current_user)

@bp.route('/history')
@login_required
def history():
    """History page for transcriptions and translations."""
    history_type = request.args.get('type', 'all')
    transcriptions = {}
    translations = {}

    print(f"Loading history page for user: {current_user.email}, type: {history_type}")

    try:
        # Fetch user's transcription history if needed
        if history_type in ['all', 'transcription']:
            print(f"Attempting to fetch transcriptions for user: {current_user.email}")
            transcriptions = Transcription.get_by_user(current_user.email, limit=50)
            print(f"Fetched transcriptions: {len(transcriptions) if transcriptions else 0} items")

            # Debug: Print the first transcription if available
            if transcriptions and len(transcriptions) > 0:
                first_key = list(transcriptions.keys())[0]
                print(f"First transcription: {transcriptions[first_key]}")
            else:
                print("No transcriptions found")

                # Check if the user's transcription path exists
                user_id = current_user.email.replace('.', ',')
                path_exists = Transcription.get_ref(f'transcriptions/{user_id}').get() is not None
                print(f"Transcription path exists: {path_exists}")
    except Exception as e:
        print(f"Error fetching transcriptions: {str(e)}")
        import traceback
        traceback.print_exc()

        # Try to fetch without ordering if index is not defined
        try:
            user_id = current_user.email.replace('.', ',')
            transcriptions = Transcription.get_ref(f'transcriptions/{user_id}').get()
            print(f"Fetched transcriptions without ordering: {len(transcriptions) if transcriptions else 0} items")
        except Exception as e2:
            print(f"Error fetching transcriptions without ordering: {str(e2)}")
            traceback.print_exc()

    try:
        # Fetch user's translation history if needed
        if history_type in ['all', 'translation']:
            print(f"Attempting to fetch translations for user: {current_user.email}")
            translations = Translation.get_by_user(current_user.email, limit=50)
            print(f"Fetched translations: {len(translations) if translations else 0} items")
    except Exception as e:
        print(f"Error fetching translations: {str(e)}")
        import traceback
        traceback.print_exc()

        # Try to fetch without ordering if index is not defined
        try:
            user_id = current_user.email.replace('.', ',')
            translations = Translation.get_ref(f'translations/{user_id}').get()
            print(f"Fetched translations without ordering: {len(translations) if translations else 0} items")
        except Exception as e2:
            print(f"Error fetching translations without ordering: {str(e2)}")
            traceback.print_exc()

    return render_template('history.html',
                          history_type=history_type,
                          transcriptions=transcriptions if transcriptions else {},
                          translations=translations if translations else {})

@bp.route('/try-it-free')
def try_it_free():
    """Try It Free page - allows users to test transcription without signing up."""
    return render_template('try_it_free.html')

@bp.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    try:
        # First try to serve from the static directory
        return send_from_directory('static', path)
    except Exception as e:
        # If that fails, try to serve from the vocallocal/static directory
        try:
            return send_from_directory('vocallocal/static', path)
        except Exception as e2:
            # If that also fails, try with a different path
            try:
                import os
                static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
                return send_from_directory(static_folder, path)
            except Exception as e3:
                print(f"Error serving static file {path}: {str(e3)}")
                return f"Static file {path} not found", 404
