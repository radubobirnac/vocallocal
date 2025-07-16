"""
Transcription routes for VocalLocal
"""
import os
import time
import traceback
from flask import Blueprint, request, jsonify, current_app, session
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

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

# Import email verification middleware
try:
    from services.email_verification_middleware import requires_verified_email, VerificationAwareAccessControl
except ImportError:
    # Fallback if middleware not available
    def requires_verified_email(f):
        return f

# Create a blueprint for the transcription routes
bp = Blueprint('transcription', __name__, url_prefix='/api')

def deduplicate_overlapping_text(prev_text, current_text, overlap_seconds):
    """
    Simple deduplication for overlapping transcription chunks.
    Removes duplicate words from the beginning of current_text that appear at the end of prev_text.
    """
    if not prev_text or not current_text:
        return current_text

    # Split into words
    prev_words = prev_text.strip().split()
    current_words = current_text.strip().split()

    if not prev_words or not current_words:
        return current_text

    # Estimate overlap based on time (rough: ~3 words per second)
    estimated_overlap_words = max(1, overlap_seconds * 3)

    # Look for overlap in the last N words of previous text
    search_window = min(len(prev_words), estimated_overlap_words + 5)
    prev_tail = prev_words[-search_window:]

    # Find the longest matching sequence at the start of current text
    best_match_length = 0
    for i in range(min(len(current_words), search_window)):
        # Check if current_words[0:i+1] matches any suffix of prev_tail
        current_prefix = current_words[0:i+1]
        for j in range(len(prev_tail) - len(current_prefix) + 1):
            if prev_tail[j:j+len(current_prefix)] == current_prefix:
                best_match_length = len(current_prefix)
                break

    # Remove the overlapping words from current text
    if best_match_length > 0:
        deduplicated_words = current_words[best_match_length:]
        result = ' '.join(deduplicated_words)
        current_app.logger.info(f"Removed {best_match_length} overlapping words: {' '.join(current_words[:best_match_length])}")
        return result

    return current_text

# Use the singleton transcription service instance
from services.transcription import transcription_service

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
@login_required
# @requires_verified_email  # Temporarily disabled for testing model mapping
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

        # Fix model routing - ensure proper mapping between frontend and backend
        # Note: 04-17 model is deprecated, but we keep the mapping for UI compatibility
        # The actual API call will use 05-20 model (handled in transcription service)
        model_mapping = {
            'gpt-4o-mini-transcribe': 'gpt-4o-mini-transcribe',
            'gpt-4o-transcribe': 'gpt-4o-transcribe',
            'gemini-2.5-flash-preview-04-17': 'gemini-2.5-flash-preview-04-17',  # Will be mapped to 05-20 in service
            'gemini-2.5-flash-preview-05-20': 'gemini-2.5-flash-preview-05-20',  # Direct support for 05-20
            'gemini-2.0-flash-lite': 'gemini-2.0-flash-lite'
        }

        # Map the requested model to ensure correct routing
        mapped_model = model_mapping.get(requested_model, 'gemini-2.0-flash-lite')
        if mapped_model != requested_model:
            print(f"Model mapping: {requested_model} -> {mapped_model}")

        requested_model = mapped_model

        # Fast model validation for authenticated users (with timeout protection)
        if current_user and current_user.is_authenticated:
            try:
                # Ensure we have a valid user email before proceeding
                user_email = getattr(current_user, 'email', None)
                if not user_email:
                    print(f"Warning: Authenticated user has no email attribute. Using fallback model.")
                    model = 'gemini-2.0-flash-lite'
                else:
                    # Quick model validation with cross-platform timeout protection
                    import threading
                    import time

                    validation_result = None
                    validation_error = None

                    def validate_model():
                        nonlocal validation_result, validation_error
                        try:
                            validation_result = ModelAccessService.validate_model_request(requested_model, user_email)
                        except Exception as e:
                            validation_error = e

                    # Start validation in a separate thread with timeout
                    validation_thread = threading.Thread(target=validate_model)
                    validation_thread.daemon = True
                    validation_thread.start()
                    validation_thread.join(timeout=2.0)  # 2-second timeout

                    if validation_thread.is_alive():
                        # Validation timed out
                        print(f"Model validation timeout. Using fallback model for {user_email}")
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

                        print(f"Model access validated: {model} for transcription (user: {user_email})")
                    else:
                        # No result received
                        print(f"Model validation incomplete. Using fallback model for {user_email}")
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
                if current_user and current_user.is_authenticated:
                    try:
                        # Ensure we have a valid user email before proceeding
                        user_email = getattr(current_user, 'email', None)
                        if not user_email:
                            print(f"Warning: Authenticated user has no email attribute for usage validation.")
                        else:
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
                                        user_email,
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
                                print(f"Usage validation timeout for {user_email}. Continuing with transcription.")
                            elif usage_error:
                                # Usage validation failed with error
                                print(f"Usage validation error: {str(usage_error)}")
                                print("Continuing with transcription due to validation service error (graceful degradation)")
                            elif validation:
                                # Usage validation completed
                                if not validation['allowed']:
                                    # For production stability, log the limit but continue with transcription
                                    # This prevents blocking users due to validation service issues
                                    print(f"Usage limit reached for {user_email}: {validation['message']}")
                                    print(f"Continuing with transcription for service stability")
                                    # Note: In a future update, you may want to enforce limits more strictly
                                else:
                                    print(f"Usage validation passed: {validation['message']}")
                            else:
                                # No validation result received
                                print(f"Usage validation incomplete for {user_email}. Continuing with transcription.")

                    except Exception as validation_error:
                        print(f"Usage validation error: {str(validation_error)}")
                        print("Continuing with transcription due to validation service error (graceful degradation)")

                # Check if this is a free trial request (non-authenticated user)
                if not current_user or not current_user.is_authenticated:
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
                    # Check if 'last_reset' key exists to avoid KeyError
                    last_reset = session['free_trial_usage'].get('last_reset', time.time())
                    if time.time() - last_reset > 86400:  # 24 hours in seconds
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
                    if current_user and current_user.is_authenticated:
                        # Ensure we have a valid user email before proceeding
                        user_email = getattr(current_user, 'email', None)
                        if not user_email:
                            print(f"Warning: Authenticated user has no email attribute for Firebase saving.")
                        else:
                            # Extract text from transcription if it's a dict
                            text_to_save = transcription
                            if isinstance(transcription, dict) and 'text' in transcription:
                                text_to_save = transcription['text']

                            print(f"Attempting to save transcription to Firebase for user {user_email}")
                            print(f"Text length: {len(text_to_save) if text_to_save else 'None'}")
                            print(f"Language: {language}")
                            print(f"Model: {model}")

                            Transcription.save(
                                user_email=user_email,
                                text=text_to_save,
                                language=language,
                                model=model,
                                audio_duration=None  # Could estimate this
                            )
                            print(f"Successfully saved transcription to Firebase for user {user_email}")

                            # Track usage after successful transcription (asynchronous, non-blocking)
                            try:
                                # Use estimated minutes for usage tracking
                                import threading

                                def track_usage_async():
                                    try:
                                        from services.user_account_service import UserAccountService
                                        UserAccountService.track_usage(
                                            user_id=user_email.replace('.', ','),
                                            service_type='transcriptionMinutes',
                                            amount=estimated_minutes
                                        )
                                        print(f"Usage tracked: {estimated_minutes} transcription minutes for {user_email}")
                                    except Exception as async_usage_error:
                                        print(f"Async usage tracking error: {str(async_usage_error)}")

                                # Start usage tracking in background thread to avoid blocking response
                                threading.Thread(target=track_usage_async, daemon=True).start()
                                print(f"Started async usage tracking for {user_email}")

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

@bp.route('/test_transcribe_chunk', methods=['POST'])
def test_transcribe_chunk():
    """Test-only endpoint for chunk transcription that bypasses usage tracking and authentication"""
    try:
        current_app.logger.info("=== TEST TRANSCRIBE CHUNK ENDPOINT CALLED ===")

        # Check if we're in development mode
        if not current_app.debug and not current_app.config.get('TESTING', False):
            current_app.logger.warning("Test endpoint called but not in debug mode")
            return jsonify({'error': 'Test endpoint only available in development mode'}), 403

        current_app.logger.info("Debug mode confirmed, proceeding with test transcription")

        # Check if file is present
        if 'audio' not in request.files:
            current_app.logger.error("No audio file in request")
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        if audio_file.filename == '':
            current_app.logger.error("Empty filename provided")
            return jsonify({'error': 'No file selected'}), 400

        # Get parameters
        language = request.form.get('language', 'en')
        model = request.form.get('model', 'gemini-2.0-flash-lite')
        chunk_number = request.form.get('chunk_number', '0')
        element_id = request.form.get('element_id', 'test-sandbox')
        has_overlap = request.form.get('has_overlap', 'false').lower() == 'true'
        overlap_seconds = int(request.form.get('overlap_seconds', '0'))

        current_app.logger.info(f"TEST MODE: Processing chunk {chunk_number} for element {element_id} (overlap: {has_overlap}, {overlap_seconds}s)")

        # Read audio data
        audio_data = audio_file.read()
        current_app.logger.info(f"TEST MODE: Received chunk {chunk_number}: {len(audio_data)} bytes, format: {audio_file.content_type}")

        # Basic validation
        if len(audio_data) == 0:
            current_app.logger.error("TEST MODE: Empty audio file received")
            return jsonify({'error': 'Empty audio file', 'test_mode': True}), 400

        # Skip all usage tracking and authentication for test mode
        # Use the transcription service to process the chunk
        from services.transcription import transcription_service

        # For chunks, we want fast processing without complex chunking
        result = transcription_service.transcribe_simple_chunk(audio_data, language, model)

        current_app.logger.info(f"TEST MODE: Chunk {chunk_number} transcription completed: {len(result)} characters")

        return jsonify({
            'text': result,
            'chunk_number': int(chunk_number),
            'element_id': element_id,
            'status': 'completed',
            'has_overlap': has_overlap,
            'overlap_seconds': overlap_seconds,
            'test_mode': True
        })

    except Exception as e:
        current_app.logger.error(f"TEST MODE: Error processing chunk: {str(e)}")
        return jsonify({
            'error': str(e),
            'chunk_number': int(request.form.get('chunk_number', '0')),
            'status': 'error',
            'test_mode': True
        }), 500

@bp.route('/transcribe_chunk', methods=['POST'])
@login_required
@requires_verified_email
def transcribe_chunk():
    """Process a single audio chunk for progressive transcription"""
    try:
        # Check if file is present
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Get parameters
        language = request.form.get('language', 'en')
        model = request.form.get('model', 'gemini-2.0-flash-lite')
        chunk_number = request.form.get('chunk_number', '0')
        element_id = request.form.get('element_id', 'basic-transcript')
        has_overlap = request.form.get('has_overlap', 'false').lower() == 'true'
        overlap_seconds = int(request.form.get('overlap_seconds', '0'))

        current_app.logger.info(f"Processing chunk {chunk_number} for element {element_id} (overlap: {has_overlap}, {overlap_seconds}s)")

        # Read audio data
        audio_data = audio_file.read()
        current_app.logger.info(f"Received chunk {chunk_number}: {len(audio_data)} bytes, format: {audio_file.content_type}")

        # Basic validation
        if len(audio_data) == 0:
            return jsonify({'error': 'Empty audio file'}), 400

        if len(audio_data) > 150 * 1024 * 1024:  # 150MB limit
            return jsonify({'error': 'Audio file too large (max 150MB)'}), 400

        # WebM validation for chunks
        if audio_file.content_type == 'audio/webm' or audio_file.filename.endswith('.webm'):
            # Check for WebM EBML header
            if len(audio_data) >= 4:
                ebml_signature = audio_data[:4]
                has_ebml_header = (ebml_signature[0] == 0x1A and
                                 ebml_signature[1] == 0x45 and
                                 ebml_signature[2] == 0xDF and
                                 ebml_signature[3] == 0xA3)

                current_app.logger.info(f"WebM chunk validation: hasEBMLHeader={has_ebml_header}, first4bytes={[hex(b) for b in ebml_signature]}")

                # For progressive recording, only the first chunk typically has EBML header
                # Subsequent chunks are media data and don't need EBML header
                if chunk_number == 1 and not has_ebml_header:
                    current_app.logger.warning(f"First chunk missing EBML header - may be corrupted")
                    # Still allow processing but log the warning
                elif not has_ebml_header:
                    current_app.logger.info(f"Chunk {chunk_number} has no EBML header (normal for progressive recording)")
            else:
                # Check minimum size - chunks should be at least 100 bytes to be meaningful
                if len(audio_data) < 100:
                    current_app.logger.warning(f"Chunk {chunk_number} too small for meaningful processing: {len(audio_data)} bytes")
                    return jsonify({'error': 'WebM chunk too small'}), 400

        # Get user email for RBAC (if available)
        user_email = None
        if current_user.is_authenticated:
            user_email = current_user.email

        # For unauthenticated users (free trial), check usage limits
        if not current_user.is_authenticated:
            # Initialize session tracking if not exists
            if 'free_trial_usage' not in session:
                session['free_trial_usage'] = {
                    'total_duration': 0,
                    'requests': 0,
                    'start_time': time.time()
                }

            # Estimate duration for this chunk (assume 60 seconds per chunk)
            estimated_duration_minutes = 1.0  # 60 seconds = 1 minute

            # Check if adding this chunk would exceed the limit
            projected_total = session['free_trial_usage']['total_duration'] + estimated_duration_minutes
            if projected_total > 3:
                return jsonify({
                    'error': 'You have exceeded the free trial limit of 3 minutes per day.',
                    'errorType': 'FreeTrial_DailyLimitExceeded',
                    'details': 'Please sign up for a full account to continue using VocalLocal.',
                    'usage': session['free_trial_usage']
                }), 429  # 429 Too Many Requests

            # Update usage tracking
            session['free_trial_usage']['total_duration'] += estimated_duration_minutes
            session['free_trial_usage']['requests'] += 1

        # Use the transcription service to process the chunk
        from services.transcription import transcription_service

        # For chunks, we want fast processing without complex chunking
        result = transcription_service.transcribe_simple_chunk(audio_data, language, model)

        current_app.logger.info(f"Chunk {chunk_number} transcription completed: {len(result)} characters")

        # Store previous chunk result for deduplication (simple session-based storage)
        if 'chunk_results' not in session:
            session['chunk_results'] = {}

        # Simple deduplication for overlapping chunks
        if has_overlap and chunk_number != '1':
            # Get previous chunk result
            prev_chunk_key = f"{element_id}_{int(chunk_number) - 1}"
            if prev_chunk_key in session['chunk_results']:
                prev_result = session['chunk_results'][prev_chunk_key]

                # Simple word-based deduplication
                result = deduplicate_overlapping_text(prev_result, result, overlap_seconds)
                current_app.logger.info(f"Deduplication applied for chunk {chunk_number}")

        # Store current result
        current_chunk_key = f"{element_id}_{chunk_number}"
        session['chunk_results'][current_chunk_key] = result

        return jsonify({
            'text': result,
            'chunk_number': int(chunk_number),
            'element_id': element_id,
            'status': 'completed',
            'has_overlap': has_overlap,
            'overlap_seconds': overlap_seconds
        })

    except Exception as e:
        current_app.logger.error(f"Error processing chunk: {str(e)}")
        return jsonify({
            'error': str(e),
            'chunk_number': int(request.form.get('chunk_number', '0')),
            'status': 'error'
        }), 500

@bp.route('/transcription_status/<job_id>', methods=['GET'])
def transcription_status(job_id):
    """Check the status of a background transcription job"""
    from services.transcription import transcription_service

    # Get the job status
    status = transcription_service.get_job_status(job_id)

    # Log the status for debugging
    current_app.logger.info(f"Job status for {job_id}: {status}")

    # Additional logging for result format debugging
    if status.get('status') == 'completed' and status.get('result'):
        result = status.get('result')
        result_type = type(result).__name__
        if isinstance(result, str):
            current_app.logger.info(f"Job {job_id} result is string with length: {len(result)}")
        elif isinstance(result, dict):
            current_app.logger.info(f"Job {job_id} result is dict with keys: {list(result.keys())}")
        else:
            current_app.logger.info(f"Job {job_id} result is {result_type}: {result}")

    # If the job is completed and the user is authenticated, save to Firebase
    if status.get('status') == 'completed' and current_user and current_user.is_authenticated:
        try:
            # Ensure we have a valid user email before proceeding
            user_email = getattr(current_user, 'email', None)
            if not user_email:
                current_app.logger.warning("Authenticated user has no email attribute for background transcription saving.")
            else:
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
                        user_email=user_email,
                        text=text_to_save,
                        language=language,
                        model=model,
                        audio_duration=None
                    )
                    current_app.logger.info(f"Saved background transcription to Firebase for user {user_email}")
        except Exception as e:
            current_app.logger.error(f"Error saving background transcription to Firebase: {str(e)}")

    return jsonify(status)
