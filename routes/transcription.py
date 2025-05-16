"""
Transcription routes for VocalLocal
"""
import os
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

                # Use the transcription service
                transcription = transcription_service.transcribe(audio_content, language, model)

                # Save transcription to Firebase if user is authenticated
                try:
                    if current_user.is_authenticated:
                        Transcription.save(
                            user_email=current_user.email,
                            text=transcription,
                            language=language,
                            model=model,
                            audio_duration=None  # Could estimate this
                        )
                except Exception as auth_error:
                    # Just log the error but continue - don't fail the transcription if saving to Firebase fails
                    print(f"Error saving transcription to Firebase: {str(auth_error)}")

                # Remove temporary file
                os.remove(filepath)

                # Return results
                return jsonify({
                    'text': transcription,
                    'language': language,
                    'model': model,
                    'success': True
                })
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
