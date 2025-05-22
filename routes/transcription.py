"""
Transcription routes for VocalLocal
"""
import os
import time
import traceback
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from services.transcription import TranscriptionService
from config import Config
from models.firebase_models import Transcription

# Create a blueprint for the transcription routes
bp = Blueprint('transcription', __name__, url_prefix='/api')

# Initialize the transcription service
transcription_service = TranscriptionService()

def safe_remove_file(filepath, max_retries=3, retry_delay=0.5):
    """Safely remove a file with retries for Windows file locking issues"""
    for attempt in range(max_retries):
        try:
            os.remove(filepath)
            return True
        except PermissionError:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                # Log the error but don't crash
                print(f"Warning: Could not remove temporary file {filepath} after {max_retries} attempts")
                return False

@bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Endpoint for transcribing audio files"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and Config.allowed_file(file.filename):
        # Save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Get language code from form
        language = request.form.get('language', 'en')

        # Get model from form or use default
        model = request.form.get('model', 'gemini-2.0-flash-lite')

        # Process with the transcription service
        try:
            with open(filepath, 'rb') as audio_file:
                # Log request information for debugging
                print(f"Transcribing file: {filename}, size: {os.path.getsize(filepath)} bytes, format: {file.content_type}, model: {model}")

                # Read the file content
                audio_content = audio_file.read()

                # Check if this is a free trial request (non-authenticated user)
                if not current_user.is_authenticated:
                    # Check file size for free trial (max 25MB)
                    file_size_mb = len(audio_content) / (1024 * 1024)
                    if file_size_mb > 25:
                        return jsonify({
                            'error': 'File size exceeds the free trial limit of 25MB.',
                            'errorType': 'FreeTrial_FileSizeLimitExceeded',
                            'details': 'Please sign up for a full account to process larger files.'
                        }), 413

                    # Check audio duration for free trial (estimate based on file size)
                    # Rough estimate: ~1MB per minute for compressed audio
                    estimated_duration_minutes = file_size_mb
                    if estimated_duration_minutes > 3:
                        return jsonify({
                            'error': 'Audio duration exceeds the free trial limit of 3 minutes.',
                            'errorType': 'FreeTrial_DurationLimitExceeded',
                            'details': 'Please sign up for a full account to process longer recordings.'
                        }), 413

                    # Track free trial usage with session
                    from flask import session
                    import time

                    # Initialize session tracking if not exists
                    if 'free_trial_usage' not in session:
                        session['free_trial_usage'] = {
                            'total_duration': 0,
                            'last_reset': time.time(),
                            'requests': 0
                        }

                    # Reset usage if it's been more than 24 hours since last reset
                    if time.time() - session['free_trial_usage']['last_reset'] > 86400:  # 24 hours in seconds
                        session['free_trial_usage'] = {
                            'total_duration': 0,
                            'last_reset': time.time(),
                            'requests': 0
                        }

                    # Add current estimated duration to total
                    session['free_trial_usage']['total_duration'] += estimated_duration_minutes
                    session['free_trial_usage']['requests'] += 1

                    # Check if total duration exceeds limit (3 minutes)
                    if session['free_trial_usage']['total_duration'] > 3:
                        return jsonify({
                            'error': 'You have exceeded the free trial limit of 3 minutes per day.',
                            'errorType': 'FreeTrial_DailyLimitExceeded',
                            'details': 'Please sign up for a full account to continue using VocalLocal.',
                            'usage': session['free_trial_usage']
                        }), 429  # 429 Too Many Requests

                # Use the transcription service
                transcription = transcription_service.transcribe(audio_content, language, model)

                # Check if this is a background processing job
                if isinstance(transcription, dict) and transcription.get('status') == 'processing':
                    # Return the job ID for background processing
                    return jsonify(transcription)

                # Save transcription to Firebase if user is authenticated
                try:
                    if current_user.is_authenticated:
                        # Extract text from transcription if it's a dict
                        text_to_save = transcription
                        if isinstance(transcription, dict) and 'text' in transcription:
                            text_to_save = transcription['text']

                        print(f"Attempting to save transcription to Firebase for user {current_user.email}")
                        print(f"Text length: {len(text_to_save) if text_to_save else 'None'}")
                        print(f"Language: {language}")
                        print(f"Model: {model}")

                        Transcription.save(
                            user_email=current_user.email,
                            text=text_to_save,
                            language=language,
                            model=model,
                            audio_duration=None  # Could estimate this
                        )
                        print(f"Successfully saved transcription to Firebase for user {current_user.email}")
                except Exception as auth_error:
                    # Just log the error but continue - don't fail the transcription if saving to Firebase fails
                    print(f"Error saving transcription to Firebase: {str(auth_error)}")
                    import traceback
                    traceback.print_exc()

                # Remove temporary file
                safe_remove_file(filepath)

                # For regular processing, ensure consistent format and return
                if isinstance(transcription, str):
                    return jsonify({"text": transcription})
                else:
                    return jsonify(transcription)
        except Exception as e:
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)

            # Log the detailed error
            error_details = traceback.format_exc()
            print(f"Transcription error: {str(e)}\n{error_details}")

            # Check for specific error types
            error_message = str(e).lower()

            # Check for duration limit error
            if "audio duration" in error_message and "longer than" in error_message and "seconds" in error_message:
                return jsonify({
                    'error': 'Audio file exceeds the maximum duration limit of 25 minutes.',
                    'errorType': 'DurationLimitExceeded',
                    'details': 'Please upload a shorter audio file or split your recording into smaller segments.'
                }), 413  # 413 Payload Too Large

            # Check for memory-related errors
            elif "memory" in error_message or "sigkill" in error_message or "out of memory" in error_message:
                # Get file size for better error message
                file_size_mb = os.path.getsize(filepath) / (1024 * 1024) if os.path.exists(filepath) else "unknown"

                return jsonify({
                    'error': f'Server memory limit exceeded while processing {file_size_mb:.1f}MB file.',
                    'errorType': 'MemoryLimitExceeded',
                    'details': 'Please try a smaller file (under 20MB) or split your audio into smaller segments.'
                }), 413  # 413 Payload Too Large

            # Check for file size errors
            elif "size" in error_message and "limit" in error_message:
                return jsonify({
                    'error': 'File size exceeds the maximum limit.',
                    'errorType': 'FileSizeLimitExceeded',
                    'details': 'Please upload a smaller file or split your audio into smaller segments.'
                }), 413  # 413 Payload Too Large

            # Check for timeout errors
            elif "timeout" in error_message or "deadline" in error_message:
                return jsonify({
                    'error': 'Request timed out while processing the audio file.',
                    'errorType': 'RequestTimeout',
                    'details': 'Please try a smaller file or split your audio into smaller segments.'
                }), 408  # 408 Request Timeout

            # Generic error response
            return jsonify({
                'error': str(e),
                'errorType': type(e).__name__,
                'details': 'See server logs for more information'
            }), 500

    return jsonify({'error': f'Invalid file type. Allowed types: {", ".join(Config.ALLOWED_EXTENSIONS)}'}), 400

@bp.route('/api/transcription_status/<job_id>', methods=['GET'])
def transcription_status(job_id):
    """Check the status of a background transcription job"""
    from services.transcription import transcription_service

    # Get the job status
    status = transcription_service.get_job_status(job_id)

    # Log the status for debugging
    current_app.logger.info(f"Job status for {job_id}: {status}")

    # If the job is completed and the user is authenticated, save to Firebase
    if status.get('status') == 'completed' and current_user.is_authenticated:
        try:
            # Extract result from status
            result = status.get('result')
            if result:
                # Get text from result
                text_to_save = result
                if isinstance(result, dict) and 'text' in result:
                    text_to_save = result['text']

                # Get language and model from request parameters if available
                language = request.args.get('language', 'en')
                model = request.args.get('model', 'gemini-2.0-flash-lite')

                # Save to Firebase
                Transcription.save(
                    user_email=current_user.email,
                    text=text_to_save,
                    language=language,
                    model=model,
                    audio_duration=None
                )
                current_app.logger.info(f"Saved background transcription to Firebase for user {current_user.email}")
        except Exception as e:
            current_app.logger.error(f"Error saving background transcription to Firebase: {str(e)}")

    return jsonify(status)
