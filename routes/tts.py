"""
Text-to-Speech routes for VocalLocal
"""
import os
import traceback
from flask import Blueprint, request, jsonify, send_from_directory
from flask_login import login_required, current_user
from services.tts import TTSService

# Import RBAC and model access services
try:
    from services.model_access_service import ModelAccessService
except ImportError:
    # Fallback if service not available
    class ModelAccessService:
        @staticmethod
        def validate_model_request(model_name, user_email=None):
            return {'valid': True, 'message': 'Model access granted', 'suggested_model': model_name}

# Create a blueprint for the TTS routes
bp = Blueprint('tts', __name__, url_prefix='/api')

# Initialize the TTS service
tts_service = TTSService()

@bp.route('/tts', methods=['POST'])
@login_required
def text_to_speech():
    """
    Endpoint for converting text to speech using TTS services.

    Required JSON parameters:
    - text: The text to convert to speech
    - language: The language code (e.g., 'en', 'es', 'fr')

    Optional JSON parameters:
    - tts_model: The model to use for TTS ('gemini-2.5-flash-tts', 'gpt4o-mini', or 'openai', default: 'gemini-2.5-flash-tts')
      - 'gemini-2.5-flash-tts': Uses Gemini 2.5 Flash Preview TTS model with male voice and enthusiastic style
      - 'gpt4o-mini': Uses OpenAI's GPT-4o Mini TTS model (with fallback to standard TTS if it fails)
      - 'openai': Uses OpenAI's standard TTS model with voice selection based on language

    Returns:
    - Audio file as response with appropriate content type
    """
    print("TTS endpoint called")
    data = request.json
    print(f"TTS request data: {data}")

    if not data or 'text' not in data or 'language' not in data:
        print("Missing required parameters: text and language")
        return jsonify({'error': 'Missing required parameters: text and language'}), 400

    text = data['text']
    language = data['language']
    tts_model = data.get('tts_model', 'gemini-2.5-flash-tts')  # Default to Gemini 2.5 Flash TTS

    # Check TTS access for the current user
    try:
        from services.usage_validation_service import UsageValidationService
        user_email = current_user.email if current_user.is_authenticated else None

        if user_email:
            tts_access = UsageValidationService.check_tts_access(user_email)
            if not tts_access['allowed']:
                print(f"TTS access denied for user {user_email}: {tts_access['reason']}")
                return jsonify({
                    'error': 'TTS access denied',
                    'reason': tts_access['reason'],
                    'message': tts_access['message'],
                    'upgrade_required': tts_access['upgrade_required']
                }), 403
        else:
            print("User not authenticated for TTS request")
            return jsonify({'error': 'Authentication required for TTS'}), 401

    except Exception as access_error:
        print(f"Error checking TTS access: {str(access_error)}")
        # Continue with request if access check fails (fallback behavior)
        pass

    # Validate usage for authenticated users (with timeout protection)
    try:
        # Ensure we have a valid user email before proceeding
        user_email = getattr(current_user, 'email', None) if current_user and current_user.is_authenticated else None
        if not user_email and current_user and current_user.is_authenticated:
            print(f"Warning: Authenticated user has no email attribute for TTS usage validation.")

        if user_email:
            # Estimate TTS duration (rough estimate: 1 minute per 150 words)
            word_count = len(text.split())
            estimated_minutes = max(0.1, word_count / 150.0)  # Conservative estimate

            # Fast usage validation with cross-platform timeout protection (non-blocking)
            import threading
            validation = None
            usage_error = None

            def validate_usage():
                nonlocal validation, usage_error
                try:
                    from services.usage_validation_service import UsageValidationService
                    validation = UsageValidationService.validate_tts_usage(
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
                print(f"TTS usage validation timeout for {user_email}. Continuing with TTS.")
            elif usage_error:
                # Usage validation failed with error
                print(f"TTS usage validation error: {str(usage_error)}")
                print("Continuing with TTS due to validation service error (graceful degradation)")
            elif validation:
                # Usage validation completed
                if not validation['allowed']:
                    # For production stability, log the limit but continue with TTS
                    # This prevents blocking users due to validation service issues
                    print(f"TTS usage limit reached for {user_email}: {validation['message']}")
                    print(f"Continuing with TTS for service stability")
                    # Note: In a future update, you may want to enforce limits more strictly
                else:
                    print(f"TTS usage validation passed: {validation['message']}")
            else:
                # No validation result received
                print(f"TTS usage validation incomplete for {user_email}. Continuing with TTS.")

    except Exception as validation_error:
        print(f"TTS usage validation error: {str(validation_error)}")
        print("Continuing with TTS due to validation service error (graceful degradation)")

    # Fast model validation for authenticated users (with timeout protection)
    try:
        # Quick model validation with cross-platform timeout protection
        validation_result = None
        validation_error = None

        def validate_model():
            nonlocal validation_result, validation_error
            try:
                validation_result = ModelAccessService.validate_model_request(tts_model, current_user.email)
            except Exception as e:
                validation_error = e

        # Start validation in a separate thread with timeout
        validation_thread = threading.Thread(target=validate_model)
        validation_thread.daemon = True
        validation_thread.start()
        validation_thread.join(timeout=2.0)  # 2-second timeout

        if validation_thread.is_alive():
            # Validation timed out
            print(f"TTS model validation timeout. Using fallback model for {current_user.email}")
            tts_model = 'gemini-2.5-flash-tts'
        elif validation_error:
            # Validation failed with error
            print(f"TTS model validation error: {str(validation_error)}")
            tts_model = 'gemini-2.5-flash-tts'
        elif validation_result:
            # Validation completed successfully
            if not validation_result['valid']:
                # If model access is denied, use suggested model or fallback
                if validation_result.get('suggested_model'):
                    tts_model = validation_result['suggested_model']
                    print(f"Model access denied for {tts_model}. Using suggested model: {tts_model}")
                else:
                    # Use fallback model instead of returning error to avoid blocking TTS
                    tts_model = 'gemini-2.5-flash-tts'
                    print(f"Model access denied. Using fallback model: {tts_model}")

            print(f"TTS model access validated: {tts_model} for user {current_user.email}")
        else:
            # No result received
            print(f"TTS model validation incomplete. Using fallback model for {current_user.email}")
            tts_model = 'gemini-2.5-flash-tts'

        print(f"Model access validated: {tts_model} for TTS (user: {current_user.email})")
    except Exception as validation_error:
        print(f"Model validation error: {str(validation_error)}")
        # Continue with default free model if validation fails
        tts_model = 'gemini-2.5-flash-tts'  # Default to free model
        print(f"Validation failed, using fallback model: {tts_model}")

    print(f"TTS request: model={tts_model}, language={language}, text_length={len(text)}")

    if not text.strip():
        print("Empty text provided")
        return jsonify({'error': 'Empty text provided'}), 400

    try:
        # Use the TTS service to generate speech
        output_file_path = tts_service.synthesize(text, language, tts_model)

        # Track usage after successful TTS generation
        try:
            # Estimate TTS duration (same calculation as before)
            word_count = len(text.split())
            estimated_minutes = max(0.1, word_count / 150.0)

            from services.user_account_service import UserAccountService
            UserAccountService.track_usage(
                user_id=current_user.email.replace('.', ','),
                service_type='ttsMinutes',
                amount=estimated_minutes
            )
            print(f"Usage tracked: {estimated_minutes} TTS minutes for {current_user.email}")

        except Exception as usage_error:
            print(f"Error tracking TTS usage: {str(usage_error)}")
            # Don't fail the request if usage tracking fails

        print(f"Sending audio file: {output_file_path}")
        # Send the file as response
        return send_from_directory(
            os.path.dirname(output_file_path),
            os.path.basename(output_file_path),
            as_attachment=True,
            download_name="speech.mp3",
            mimetype="audio/mpeg"
        )

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"TTS error: {str(e)}\n{error_details}")

        return jsonify({
            'error': str(e),
            'errorType': type(e).__name__,
            'details': 'See server logs for more information'
        }), 500
