"""
Text-to-Speech routes for VocalLocal
"""
import os
import traceback
from flask import Blueprint, request, jsonify, send_from_directory
from flask_login import login_required
from services.tts import TTSService

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
    print(f"TTS request: model={tts_model}, language={language}, text_length={len(text)}")

    if not text.strip():
        print("Empty text provided")
        return jsonify({'error': 'Empty text provided'}), 400

    try:
        # Use the TTS service to generate speech
        output_file_path = tts_service.synthesize(text, language, tts_model)

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
