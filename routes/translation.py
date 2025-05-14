"""
Translation routes for VocalLocal
"""
import traceback
from flask import Blueprint, request, jsonify
from flask_login import current_user
from services.translation import TranslationService
from utils.language_utils import get_supported_languages
from models.firebase_models import Translation

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
    
    text = data['text']
    target_language = data['target_language']
    translation_model = data.get('translation_model', 'gemini-2.0-flash-lite')  # Default to Gemini
    
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
