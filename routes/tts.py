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

    # Validate usage for authenticated users
    try:
        # Estimate TTS duration (rough estimate: 1 minute per 150 words)
        word_count = len(text.split())
        estimated_minutes = max(0.1, word_count / 150.0)  # Conservative estimate

        # Validate usage before processing
        from services.usage_validation_service import UsageValidationService
        validation = UsageValidationService.validate_tts_usage(
            current_user.email,
            estimated_minutes
        )

        if not validation['allowed']:
            return jsonify({
                'error': validation['message'],
                'errorType': 'UsageLimitExceeded',
                'details': {
                    'service': 'tts',
                    'requested': estimated_minutes,
                    'limit': validation.get('limit', 0),
                    'used': validation.get('used', 0),
                    'remaining': validation.get('remaining', 0),
                    'plan_type': validation.get('plan_type', 'free'),
                    'upgrade_required': validation.get('upgrade_required', False)
                }
            }), 429  # 429 Too Many Requests

        print(f"TTS usage validation passed: {validation['message']}")

    except Exception as validation_error:
        print(f"TTS usage validation error: {str(validation_error)}")
        # Continue with TTS if validation fails (graceful degradation)

    # Validate model access for authenticated users using RBAC
    try:
        validation_result = ModelAccessService.validate_model_request(tts_model, current_user.email)

        if not validation_result['valid']:
            # If model access is denied, check if we have a suggested model
            if validation_result.get('suggested_model'):
                tts_model = validation_result['suggested_model']
                print(f"Model access denied for {tts_model}. Using suggested model: {tts_model}")
            else:
                return jsonify({
                    'error': 'Model access denied',
                    'errorType': 'ModelAccessDenied',
                    'details': validation_result['message'],
                    'status': 'access_denied'
                }), 403

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
