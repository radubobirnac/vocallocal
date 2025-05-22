"""
Admin routes for VocalLocal
"""
import traceback
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from flask_login import current_user
from models.firebase_models import User, UserActivity, Transcription, Translation

# Create a blueprint for the admin routes
bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Admin dashboard for viewing metrics"""
    today_date = datetime.now().strftime("%Y-%m-%d")
    return render_template('admin_dashboard.html', today_date=today_date)

@bp.route('/user-usage', methods=['GET'])
def user_usage():
    """Admin dashboard for viewing user-specific usage metrics"""
    # Check if already authenticated with special admin credentials
    if session.get('special_admin_auth') != True:
        return redirect(url_for('admin.users'))

    # Get all users from Firebase
    users = User.get_all_users()

    # Get user transcriptions and translations
    user_data = {}
    for user in users:
        email = user.get('email')
        if not email:
            continue

        # Get user's transcriptions
        transcriptions = Transcription.get_by_user(email, limit=1000)

        # Get user's translations
        translations = Translation.get_by_user(email, limit=1000)

        # Calculate usage statistics
        transcription_count = len(transcriptions) if transcriptions else 0
        translation_count = len(translations) if translations else 0

        # Calculate total text length as a proxy for token usage
        transcription_chars = sum(len(t.get('text', '')) for t in transcriptions.values()) if transcriptions else 0
        translation_chars = sum(len(t.get('translated_text', '')) for t in translations.values()) if translations else 0

        # Store user data
        user_data[email] = {
            'username': user.get('username', email.split('@')[0]),
            'transcription_count': transcription_count,
            'translation_count': translation_count,
            'transcription_chars': transcription_chars,
            'translation_chars': translation_chars,
            'total_operations': transcription_count + translation_count,
            'total_chars': transcription_chars + translation_chars
        }

    return render_template('admin_user_usage.html', user_data=user_data)

@bp.route('/logout', methods=['GET'])
def logout():
    """Logout from special admin session"""
    if 'special_admin_auth' in session:
        session.pop('special_admin_auth')
        flash("You have been logged out from the admin area.", "info")
    return redirect(url_for('main.index'))

@bp.route('/users', methods=['GET', 'POST'])
def users():
    """Admin dashboard for viewing registered users with special authentication"""
    # Check if already authenticated with special admin credentials
    if session.get('special_admin_auth') == True:
        # User is authenticated with special admin credentials
        # Get all users from Firebase
        users = User.get_all_users()

        # Get recent user activities
        activities = []
        try:
            activities_data = UserActivity.get_ref('user_activities').order_by_child('timestamp').limit_to_last(50).get()
            if activities_data:
                for activity_id, activity in activities_data.items():
                    activities.append(activity)
                # Sort activities by timestamp (newest first)
                activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        except Exception as e:
            print(f"Error fetching user activities: {str(e)}")

        return render_template('admin_users.html', users=users, activities=activities)

    # Not authenticated with special admin credentials yet
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check for specific credentials
        if username == 'Radu' and password == 'Fasteasy':
            # Set session variable to indicate special admin authentication
            session['special_admin_auth'] = True

            # Log this special admin login
            if current_user.is_authenticated:
                user_email = current_user.email
            else:
                user_email = 'special_admin@vocallocal.com'

            UserActivity.log(
                user_email=user_email,
                activity_type='admin_login',
                details='Special admin authentication'
            )

            # Redirect to the same page to show the admin dashboard
            return redirect(url_for('admin.users'))
        else:
            flash("Invalid admin credentials. Please try again.", "danger")

    # Show the admin login form
    return render_template('admin_login.html')

@bp.route('/api/metrics', methods=['GET'])
def get_metrics():
    """API endpoint to get metrics data"""
    try:
        # Import metrics tracker
        from metrics_tracker import metrics_tracker

        # Get metrics from the tracker
        metrics_data = metrics_tracker.get_metrics()

        return jsonify(metrics_data)
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Metrics API error: {str(e)}\n{error_details}")

        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/api/reset-metrics', methods=['POST'])
def reset_metrics():
    """API endpoint to reset all metrics data"""
    try:
        # Import metrics tracker
        from metrics_tracker import metrics_tracker

        # Reset all metrics
        metrics_tracker.reset_metrics()

        return jsonify({
            'status': 'success',
            'message': 'All metrics have been reset successfully'
        })
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Metrics reset error: {str(e)}\n{error_details}")

        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/api/test-translations', methods=['GET'])
def test_translations():
    """Debug endpoint to test translations for all supported languages"""
    # Sample text to translate (English)
    sample_text = "Hello, this is a test of the translation system. We are checking if all languages work correctly."

    # Get the translation model from query parameter or default to gemini
    translation_model = request.args.get('model', 'gemini-2.0-flash-lite')

    # Import necessary modules
    from services.translation import TranslationService
    from utils.language_utils import get_supported_languages, get_language_name_from_code

    # Initialize the translation service
    translation_service = TranslationService()

    # Get all supported languages
    languages = get_supported_languages()

    results = {}

    # Test translation to each language
    for lang_name, lang_details in languages.items():
        lang_code = lang_details['code']
        if lang_code == 'en':  # Skip English as it's our source
            continue

        try:
            # Get the language name for better prompting
            language_name = get_language_name_from_code(lang_code)

            # Translate using the service
            translated_text = translation_service.translate(sample_text, lang_code, translation_model)

            # Store result
            results[lang_code] = {
                'language': lang_name,
                'success': True,
                'translation': translated_text,
                'native_name': lang_details['native']
            }

        except Exception as e:
            # Log error
            print(f"Error translating to {lang_name} ({lang_code}): {str(e)}")

            # Store error
            results[lang_code] = {
                'language': lang_name,
                'success': False,
                'error': str(e),
                'native_name': lang_details['native']
            }

    # Return all results
    return jsonify({
        'model': translation_model,
        'source_text': sample_text,
        'results': results
    })
