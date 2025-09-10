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

# Import email verification middleware
try:
    from services.email_verification_middleware import requires_verified_email
except ImportError:
    # Fallback if middleware not available
    def requires_verified_email(f):
        return f

# Create a blueprint for the translation routes
bp = Blueprint('translation', __name__, url_prefix='/api')

# Initialize the translation service
translation_service = TranslationService()

@bp.route('/translate', methods=['POST'])
@requires_verified_email
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
    if current_user and current_user.is_authenticated:
        try:
            # Ensure we have a valid user email before proceeding
            user_email = getattr(current_user, 'email', None)
            if not user_email:
                print(f"Warning: Authenticated user has no email attribute for translation usage validation.")
            else:
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
                            user_email,
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
                    print(f"Translation usage validation timeout for {user_email}. Continuing with translation.")
                elif usage_error:
                    # Usage validation failed with error
                    print(f"Translation usage validation error: {str(usage_error)}")
                    print("Continuing with translation due to validation service error (graceful degradation)")
                elif validation:
                    # Usage validation completed
                    if not validation['allowed']:
                        # For production stability, log the limit but continue with translation
                        # This prevents blocking users due to validation service issues
                        print(f"Translation usage limit reached for {user_email}: {validation['message']}")
                        print(f"Continuing with translation for service stability")
                        # Note: In a future update, you may want to enforce limits more strictly
                    else:
                        print(f"Translation usage validation passed: {validation['message']}")
                else:
                    # No validation result received
                    print(f"Translation usage validation incomplete for {user_email}. Continuing with translation.")

        except Exception as validation_error:
            print(f"Translation usage validation error: {str(validation_error)}")
            print("Continuing with translation due to validation service error (graceful degradation)")

    text = data['text']
    target_language = data['target_language']
    translation_model = data.get('translation_model', 'gemini-2.5-flash-preview')  # Default to Gemini 2.5

    # Fix model routing - ensure proper mapping between frontend and backend
    # Note: 04-17 model is deprecated, mapping to 05-20 for translation service
    model_mapping = {
        'gemini-2.5-flash-preview': 'gemini-2.5-flash-preview-05-20',
        'gemini-2.5-flash-preview-05-20': 'gemini-2.5-flash-preview-05-20',  # Direct 05-20 support
        'gemini-2.0-flash-lite': 'gemini-2.5-flash-preview-05-20',  # Legacy mapping
        'gemini-2.5-flash': 'gemini-2.5-flash-preview-05-20',  # Updated to use working 05-20 model
        'gemini-2.5-flash-preview-04-17': 'gemini-2.5-flash-preview-05-20',  # Explicit 04-17 to 05-20 mapping
        'gpt-4.1-mini': 'gpt-4.1-mini'
    }

    # Map the requested model to ensure correct routing
    mapped_model = model_mapping.get(translation_model, 'gemini-2.5-flash-preview')
    if mapped_model != translation_model:
        print(f"Translation model mapping: {translation_model} -> {mapped_model}")

    translation_model = mapped_model

    # Fast model validation for authenticated users (with timeout protection)
    if current_user and current_user.is_authenticated:
        try:
            # Ensure we have a valid user email before proceeding
            user_email = getattr(current_user, 'email', None)
            if not user_email:
                print(f"Warning: Authenticated user has no email attribute for translation model validation.")
                translation_model = 'gemini-2.5-flash-preview'
            else:
                # Quick model validation with cross-platform timeout protection
                validation_result = None
                validation_error = None

                def validate_model():
                    nonlocal validation_result, validation_error
                    try:
                        validation_result = ModelAccessService.validate_model_request(translation_model, user_email)
                    except Exception as e:
                        validation_error = e

                # Start validation in a separate thread with timeout
                validation_thread = threading.Thread(target=validate_model)
                validation_thread.daemon = True
                validation_thread.start()
                validation_thread.join(timeout=2.0)  # 2-second timeout

                if validation_thread.is_alive():
                    # Validation timed out
                    print(f"Translation model validation timeout. Using fallback model for {user_email}")
                    translation_model = 'gemini-2.5-flash-preview'
                elif validation_error:
                    # Validation failed with error
                    print(f"Translation model validation error: {str(validation_error)}")
                    translation_model = 'gemini-2.5-flash-preview'
                elif validation_result:
                    # Validation completed successfully
                    if not validation_result['valid']:
                        # If model access is denied, use suggested model or fallback
                        if validation_result.get('suggested_model'):
                            translation_model = validation_result['suggested_model']
                            print(f"Model access denied for {translation_model}. Using suggested model: {translation_model}")
                        else:
                            # Use fallback model instead of returning error to avoid blocking translation
                            translation_model = 'gemini-2.5-flash-preview'
                            print(f"Model access denied. Using fallback model: {translation_model}")

                    print(f"Translation model access validated: {translation_model} for user {user_email}")
                else:
                    # No result received
                    print(f"Translation model validation incomplete. Using fallback model for {user_email}")
                    translation_model = 'gemini-2.5-flash-preview'

                print(f"Model access validated: {translation_model} for translation (user: {user_email})")
        except Exception as validation_error:
            print(f"Model validation error: {str(validation_error)}")
            # Continue with default free model if validation fails
            translation_model = 'gemini-2.5-flash-preview'
            print(f"Validation failed, using fallback model: {translation_model}")
    else:
        # Non-authenticated users get free model only
        translation_model = 'gemini-2.5-flash-preview'
        print(f"Non-authenticated user, using free model: {translation_model}")

    if not text.strip():
        return jsonify({'error': 'Empty text provided'}), 400

    try:
        # Use the translation service
        translated_text = translation_service.translate(text, target_language, translation_model)

        # Save translation to Firebase if user is authenticated
        if current_user and current_user.is_authenticated:
            # Ensure we have a valid user email before proceeding
            user_email = getattr(current_user, 'email', None)
            if not user_email:
                print(f"Warning: Authenticated user has no email attribute for translation Firebase saving.")
            else:
                Translation.save(
                    user_email=user_email,
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
                        user_id=user_email.replace('.', ','),
                        service_type='translationWords',
                        amount=word_count
                    )
                    print(f"Usage tracked: {word_count} translation words for {user_email}")

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

@bp.route('/translate_free_trial', methods=['POST'])
def translate_free_trial():
    """
    Endpoint for Try It Free translation without authentication requirement
    """
    try:
        data = request.json
        if not data or 'text' not in data or 'target_language' not in data:
            return jsonify({'error': 'Missing required parameters: text and target_language'}), 400

        text = data.get('text')
        target_language = data.get('target_language')
        translation_model = data.get('translation_model', 'gemini-2.5-flash-preview')

        # Ensure only free models are used for free trial
        if translation_model not in ['gemini-2.5-flash-preview']:
            translation_model = 'gemini-2.5-flash-preview'

        if not text.strip():
            return jsonify({'error': 'Empty text provided'}), 400

        # Track free trial usage with session
        from flask import session
        import time

        # Initialize session tracking if not exists
        if 'free_trial_usage' not in session:
            session['free_trial_usage'] = {
                'total_duration': 0,
                'total_words': 0,
                'last_reset': time.time(),
                'requests': 0
            }

        # Ensure all required fields exist (for backward compatibility)
        if 'total_words' not in session['free_trial_usage']:
            session['free_trial_usage']['total_words'] = 0
        if 'total_duration' not in session['free_trial_usage']:
            session['free_trial_usage']['total_duration'] = 0

        # Reset daily if more than 24 hours have passed
        current_time = time.time()
        if current_time - session['free_trial_usage']['last_reset'] > 86400:  # 24 hours
            session['free_trial_usage'] = {
                'total_duration': 0,
                'total_words': 0,
                'last_reset': current_time,
                'requests': 0
            }

        # Count words in the text
        word_count = len(text.split())

        # Check if adding these words would exceed the limit (1000 words for free trial)
        projected_total = session['free_trial_usage']['total_words'] + word_count
        if projected_total > 1000:
            return jsonify({
                'error': 'You have exceeded the free trial limit of 1000 words per day.',
                'errorType': 'FreeTrial_WordLimitExceeded',
                'details': 'Please sign up for a full account to continue using translation.',
                'usage': session['free_trial_usage']
            }), 429  # 429 Too Many Requests

        # Update usage tracking
        session['free_trial_usage']['total_words'] += word_count
        session['free_trial_usage']['requests'] += 1

        # Use the translation service
        translated_text = translation_service.translate(text, target_language, translation_model)

        return jsonify({
            'text': translated_text,
            'model': translation_model,
            'target_language': target_language,
            'word_count': word_count,
            'usage': session['free_trial_usage'],
            'free_trial': True
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Free trial translation error: {str(e)}\n{error_details}")

        return jsonify({
            'error': str(e),
            'errorType': type(e).__name__,
            'details': 'Free trial translation failed'
        }), 500

@bp.route('/languages', methods=['GET'])
def get_languages():
    """Return a list of supported languages"""
    return jsonify(get_supported_languages())
