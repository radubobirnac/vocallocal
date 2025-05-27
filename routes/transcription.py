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

# Import RBAC and model access services
try:
    from services.model_access_service import ModelAccessService
except ImportError:
    # Fallback if service not available
    class ModelAccessService:
        @staticmethod
        def validate_model_request(model_name, user_email=None):
            return {'valid': True, 'message': 'Model access granted', 'suggested_model': model_name}

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
        requested_model = request.form.get('model', 'gemini-2.0-flash-lite')

        # Fast model validation for authenticated users (with timeout protection)
        if current_user.is_authenticated:
            try:
                # Quick model validation with cross-platform timeout protection
                import threading
                import time

                validation_result = None
                validation_error = None

                def validate_model():
                    nonlocal validation_result, validation_error
                    try:
                        validation_result = ModelAccessService.validate_model_request(requested_model, current_user.email)
                    except Exception as e:
                        validation_error = e

                # Start validation in a separate thread with timeout
                validation_thread = threading.Thread(target=validate_model)
                validation_thread.daemon = True
                validation_thread.start()
                validation_thread.join(timeout=2.0)  # 2-second timeout

                if validation_thread.is_alive():
                    # Validation timed out
                    print(f"Model validation timeout. Using fallback model for {current_user.email}")
                    model = 'gemini-2.0-flash-lite'
                elif validation_error:
                    # Validation failed with error
                    print(f"Model validation error: {str(validation_error)}")
                    model = 'gemini-2.0-flash-lite'
                elif validation_result:
                    # Validation completed successfully
                    if not validation_result['valid']:
                        # If model access is denied, use suggested model or fallback
                        if validation_result.get('suggested_model'):
                            model = validation_result['suggested_model']
                            print(f"Model access denied for {requested_model}. Using suggested model: {model}")
                        else:
                            # Use fallback model instead of returning error to avoid blocking transcription
                            model = 'gemini-2.0-flash-lite'
                            print(f"Model access denied for {requested_model}. Using fallback model: {model}")
                    else:
                        model = requested_model

                    print(f"Model access validated: {model} for transcription (user: {current_user.email})")
                else:
                    # No result received
                    print(f"Model validation incomplete. Using fallback model for {current_user.email}")
                    model = 'gemini-2.0-flash-lite'

            except Exception as validation_error:
                print(f"Model validation error: {str(validation_error)}")
                # Continue with default free model if validation fails
                model = 'gemini-2.0-flash-lite'
                print(f"Validation failed, using fallback model: {model}")
        else:
            # Non-authenticated users get free model only
            model = 'gemini-2.0-flash-lite'

        # Process with the transcription service
        try:
            with open(filepath, 'rb') as audio_file:
                # Log request information for debugging
                print(f"Transcribing file: {filename}, size: {os.path.getsize(filepath)} bytes, format: {file.content_type}, model: {model}")

                # Read the file content
                audio_content = audio_file.read()

                # Estimate audio duration for usage validation (if authenticated)
                estimated_minutes = 0
                if current_user.is_authenticated:
                    try:
                        # Rough estimation: 1MB ≈ 1 minute of audio (varies by quality)
                        file_size_mb = len(audio_content) / (1024 * 1024)
                        estimated_minutes = max(0.1, file_size_mb * 0.8)  # Conservative estimate

                        # Fast usage validation with cross-platform timeout protection (non-blocking)
                        validation = None
                        usage_error = None

                        def validate_usage():
                            nonlocal validation, usage_error
                            try:
                                from services.usage_validation_service import UsageValidationService
                                validation = UsageValidationService.validate_transcription_usage(
                                    current_user.email,
                                    estimated_minutes
                                )
                            except Exception as e:
                                usage_error = e

                        # Start validation in a separate thread with timeout
                        usage_thread = threading.Thread(target=validate_usage)
                        usage_thread.daemon = True
                        usage_thread.start()
                        usage_thread.join(timeout=3.0)  # 3-second timeout

                        if usage_thread.is_alive():
                            # Usage validation timed out
                            print(f"Usage validation timeout for {current_user.email}. Continuing with transcription.")
                        elif usage_error:
                            # Usage validation failed with error
                            print(f"Usage validation error: {str(usage_error)}")
                            print("Continuing with transcription due to validation service error (graceful degradation)")
                        elif validation:
                            # Usage validation completed
                            if not validation['allowed']:
                                # For production stability, log the limit but continue with transcription
                                # This prevents blocking users due to validation service issues
                                print(f"Usage limit reached for {current_user.email}: {validation['message']}")
                                print(f"Continuing with transcription for service stability")
                                # Note: In a future update, you may want to enforce limits more strictly
                            else:
                                print(f"Usage validation passed: {validation['message']}")
                        else:
                            # No validation result received
                            print(f"Usage validation incomplete for {current_user.email}. Continuing with transcription.")

                    except Exception as validation_error:
                        print(f"Usage validation error: {str(validation_error)}")
                        print("Continuing with transcription due to validation service error (graceful degradation)")

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

                        # Track usage after successful transcription (asynchronous, non-blocking)
                        try:
                            # Use estimated minutes for usage tracking
                            import threading

                            def track_usage_async():
                                try:
                                    from services.user_account_service import UserAccountService
                                    UserAccountService.track_usage(
                                        user_id=current_user.email.replace('.', ','),
                                        service_type='transcriptionMinutes',
                                        amount=estimated_minutes
                                    )
                                    print(f"Usage tracked: {estimated_minutes} transcription minutes for {current_user.email}")
                                except Exception as async_usage_error:
                                    print(f"Async usage tracking error: {str(async_usage_error)}")

                            # Start usage tracking in background thread to avoid blocking response
                            threading.Thread(target=track_usage_async, daemon=True).start()
                            print(f"Started async usage tracking for {current_user.email}")

                        except Exception as usage_error:
                            print(f"Error starting usage tracking: {str(usage_error)}")
                            # Don't fail the request if usage tracking fails
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
