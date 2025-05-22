"""
Main routes for VocalLocal
"""
from flask import Blueprint, render_template, redirect, url_for, send_from_directory, current_app
from flask_login import current_user, login_required
from models.firebase_models import Transcription, Translation

# Create a blueprint for the main routes
bp = Blueprint('main', __name__)

@bp.route('/main')
def index():
    """Main index route - handles both authenticated and non-authenticated users."""
    if current_user.is_authenticated:
        # User is logged in, show the main application
        return render_template('index.html')
    else:
        # User is not logged in, redirect to login page
        return redirect(url_for('auth.login'))

@bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    transcriptions = {}
    translations = {}

    try:
        # Fetch user's transcription history
        transcriptions = Transcription.get_by_user(current_user.email, limit=20)
    except Exception as e:
        print(f"Error fetching transcriptions: {str(e)}")
        # Try to fetch without ordering if index is not defined
        try:
            user_id = current_user.email.replace('.', ',')
            transcriptions = Transcription.get_ref(f'transcriptions/{user_id}').get()
        except Exception as e2:
            print(f"Error fetching transcriptions without ordering: {str(e2)}")

    try:
        # Fetch user's translation history
        translations = Translation.get_by_user(current_user.email, limit=20)
    except Exception as e:
        print(f"Error fetching translations: {str(e)}")
        # Try to fetch without ordering if index is not defined
        try:
            user_id = current_user.email.replace('.', ',')
            translations = Translation.get_ref(f'translations/{user_id}').get()
        except Exception as e2:
            print(f"Error fetching translations without ordering: {str(e2)}")

    return render_template('profile.html',
                          user=current_user,
                          transcriptions=transcriptions if transcriptions else {},
                          translations=translations if translations else {})

@bp.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('static', path)
