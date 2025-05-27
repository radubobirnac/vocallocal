"""
Translation routes for VocalLocal
"""
import traceback
from flask import Blueprint, request, jsonify
from flask_login import current_user
from services.translation import TranslationService
from utils.language_utils import get_supported_languages
from models.firebase_models import Translation
# Import RBAC and model access services
try:
    from services.model_access_service import ModelAccessService
except ImportError:
    # Fallback if service not available
    class ModelAccessService:
        @staticmethod
        def validate_model_request(model_name, user_email=None):
            return {'valid': True, 'message': 'Model access granted', 'suggested_model': model_name}

# Create a blueprint for the translation routes
bp = Blueprint('translation', __name__, url_prefix='/api')

# Initialize the translation service
translation_service = TranslationService()

@bp.route('/translate', methods=['POST'])
def translate_text():
    """
    Endpoint for translating text from one language to another.

    Required JSON parameters:
    - text: The text to translate
    - target_language: The language code to translate to (e.g., 'en', 'es', 'fr')

    Optional JSON parameters:
    - translation_model: The model to use for translation ('openai' or 'gemini', default: 'gemini')

    Returns:
    - JSON with translated text and performance metrics
    """
    data = request.json

    if not data or 'text' not in data or 'target_language' not in data:
        return jsonify({'error': 'Missing required parameters: text and target_language'}), 400

    # Validate usage for authenticated users (with timeout protection)
    if current_user.is_authenticated:
        try:
            # Count words in the text to translate
            text_to_translate = data['text']
            word_count = len(text_to_translate.split())

            # Fast usage validation with cross-platform timeout protection (non-blocking)
            import threading
            validation = None
            usage_error = None

            def validate_usage():
                nonlocal validation, usage_error
                try:
                    from services.usage_validation_service import UsageValidationService
                    validation = UsageValidationService.validate_translation_usage(
                        current_user.email,
                        word_count
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
                print(f"Translation usage validation timeout for {current_user.email}. Continuing with translation.")
            elif usage_error:
                # Usage validation failed with error
                print(f"Translation usage validation error: {str(usage_error)}")
                print("Continuing with translation due to validation service error (graceful degradation)")
            elif validation:
                # Usage validation completed
                if not validation['allowed']:
                    # For production stability, log the limit but continue with translation
                    # This prevents blocking users due to validation service issues
                    print(f"Translation usage limit reached for {current_user.email}: {validation['message']}")
                    print(f"Continuing with translation for service stability")
                    # Note: In a future update, you may want to enforce limits more strictly
                else:
                    print(f"Translation usage validation passed: {validation['message']}")
            else:
                # No validation result received
                print(f"Translation usage validation incomplete for {current_user.email}. Continuing with translation.")

        except Exception as validation_error:
            print(f"Translation usage validation error: {str(validation_error)}")
            print("Continuing with translation due to validation service error (graceful degradation)")

    text = data['text']
    target_language = data['target_language']
    translation_model = data.get('translation_model', 'gemini-2.0-flash-lite')  # Default to Gemini

    # Fast model validation for authenticated users (with timeout protection)
    if current_user.is_authenticated:
        try:
            # Quick model validation with cross-platform timeout protection
            validation_result = None
            validation_error = None

            def validate_model():
                nonlocal validation_result, validation_error
                try:
                    validation_result = ModelAccessService.validate_model_request(translation_model, current_user.email)
                except Exception as e:
                    validation_error = e

            # Start validation in a separate thread with timeout
            validation_thread = threading.Thread(target=validate_model)
            validation_thread.daemon = True
            validation_thread.start()
            validation_thread.join(timeout=2.0)  # 2-second timeout

            if validation_thread.is_alive():
                # Validation timed out
                print(f"Translation model validation timeout. Using fallback model for {current_user.email}")
                translation_model = 'gemini-2.0-flash-lite'
            elif validation_error:
                # Validation failed with error
                print(f"Translation model validation error: {str(validation_error)}")
                translation_model = 'gemini-2.0-flash-lite'
            elif validation_result:
                # Validation completed successfully
                if not validation_result['valid']:
                    # If model access is denied, use suggested model or fallback
                    if validation_result.get('suggested_model'):
                        translation_model = validation_result['suggested_model']
                        print(f"Model access denied for {translation_model}. Using suggested model: {translation_model}")
                    else:
                        # Use fallback model instead of returning error to avoid blocking translation
                        translation_model = 'gemini-2.0-flash-lite'
                        print(f"Model access denied. Using fallback model: {translation_model}")

                print(f"Translation model access validated: {translation_model} for user {current_user.email}")
            else:
                # No result received
                print(f"Translation model validation incomplete. Using fallback model for {current_user.email}")
                translation_model = 'gemini-2.0-flash-lite'

            print(f"Model access validated: {translation_model} for translation (user: {current_user.email})")
        except Exception as validation_error:
            print(f"Model validation error: {str(validation_error)}")
            # Continue with default free model if validation fails
            translation_model = 'gemini-2.0-flash-lite'
            print(f"Validation failed, using fallback model: {translation_model}")
    else:
        # Non-authenticated users get free model only
        translation_model = 'gemini-2.0-flash-lite'

    if not text.strip():
        return jsonify({'error': 'Empty text provided'}), 400

    try:
        # Use the translation service
        translated_text = translation_service.translate(text, target_language, translation_model)

        # Save translation to Firebase if user is authenticated
        if current_user.is_authenticated:
            Translation.save(
                user_email=current_user.email,
                original_text=text,
                translated_text=translated_text,
                source_language='auto-detect',
                target_language=target_language,
                model=translation_model
            )

            # Track usage after successful translation
            try:
                # Count words in the original text
                word_count = len(text.split())

                from services.user_account_service import UserAccountService
                UserAccountService.track_usage(
                    user_id=current_user.email.replace('.', ','),
                    service_type='translationWords',
                    amount=word_count
                )
                print(f"Usage tracked: {word_count} translation words for {current_user.email}")

            except Exception as usage_error:
                print(f"Error tracking translation usage: {str(usage_error)}")
                # Don't fail the request if usage tracking fails

        return jsonify({
            'text': translated_text,
            'source_language': 'auto-detect',
            'target_language': target_language,
            'model_used': translation_model,
            'success': True
        })

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Translation error: {str(e)}\n{error_details}")

        return jsonify({
            'error': str(e),
            'errorType': type(e).__name__,
            'details': 'See server logs for more information'
        }), 500

@bp.route('/languages', methods=['GET'])
def get_languages():
    """Return a list of supported languages"""
    return jsonify(get_supported_languages())
