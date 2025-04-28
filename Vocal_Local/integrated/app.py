"""
VocalLocal Web Service - Flask API for speech-to-text
"""

import os
import io
import tempfile
import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory, session
from werkzeug.utils import secure_filename
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24).hex())

# OpenAI API configuration
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    print("Warning: OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

# Configure upload settings
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'm4a', 'mp4', 'webm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024  # 30MB max upload size

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get language code from form
        language = request.form.get('language', 'en')
        
        # Get model from form or use default
        model = request.form.get('model', 'gpt-4o-mini-transcribe')
        
        # Process with OpenAI
        try:
            with open(filepath, 'rb') as audio_file:
                # Log request information for debugging
                print(f"Transcribing file: {filename}, size: {os.path.getsize(filepath)} bytes, format: {file.content_type}, model: {model}")
                
                response = openai.audio.transcriptions.create(
                    model=model,
                    file=audio_file,
                    language=language
                )
            
            # Remove temporary file
            os.remove(filepath)
            
            # Return results
            return jsonify({
                'text': response.text,
                'language': language,
                'model': model,
                'success': True
            })
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            
            # Log the detailed error
            import traceback
            error_details = traceback.format_exc()
            print(f"Transcription error: {str(e)}\n{error_details}")
            
            # Check for duration limit error
            error_message = str(e)
            if "audio duration" in error_message and "longer than" in error_message and "seconds" in error_message:
                return jsonify({
                    'error': 'Audio file exceeds the maximum duration limit of 25 minutes.',
                    'errorType': 'DurationLimitExceeded',
                    'details': 'Please upload a shorter audio file or split your recording into smaller segments.'
                }), 413  # 413 Payload Too Large
            
            return jsonify({
                'error': str(e),
                'errorType': type(e).__name__,
                'details': 'See server logs for more information'
            }), 500
    
    return jsonify({'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

@app.route('/api/languages', methods=['GET'])
def get_languages():
    # Dictionary of supported languages with their codes and native names
    supported_languages = {
        "English": {"code": "en", "native": "English"},
        "Spanish": {"code": "es", "native": "Español"},
        "French": {"code": "fr", "native": "Français"},
        "German": {"code": "de", "native": "Deutsch"},
        "Italian": {"code": "it", "native": "Italiano"},
        "Portuguese": {"code": "pt", "native": "Português"},
        "Dutch": {"code": "nl", "native": "Nederlands"},
        "Japanese": {"code": "ja", "native": "日本語"},
        "Chinese": {"code": "zh", "native": "中文"},
        "Korean": {"code": "ko", "native": "한국어"},
        "Russian": {"code": "ru", "native": "Русский"},
        "Arabic": {"code": "ar", "native": "العربية"},
        "Hindi": {"code": "hi", "native": "हिन्दी"},
        "Turkish": {"code": "tr", "native": "Türkçe"},
        "Swedish": {"code": "sv", "native": "Svenska"},
        "Polish": {"code": "pl", "native": "Polski"},
        "Norwegian": {"code": "no", "native": "Norsk"},
        "Finnish": {"code": "fi", "native": "Suomi"},
        "Danish": {"code": "da", "native": "Dansk"},
        "Ukrainian": {"code": "uk", "native": "Українська"},
        "Czech": {"code": "cs", "native": "Čeština"},
        "Romanian": {"code": "ro", "native": "Română"},
        "Hungarian": {"code": "hu", "native": "Magyar"},
        "Greek": {"code": "el", "native": "Ελληνικά"},
        "Hebrew": {"code": "he", "native": "עברית"},
        "Telugu": {"code": "te", "native": "తెలుగు"},
        "Thai": {"code": "th", "native": "ไทย"},
        "Vietnamese": {"code": "vi", "native": "Tiếng Việt"},
        "Indonesian": {"code": "id", "native": "Bahasa Indonesia"},
        "Malay": {"code": "ms", "native": "Bahasa Melayu"},
        "Bulgarian": {"code": "bg", "native": "Български"}
    }
    return jsonify(supported_languages)

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """
    Endpoint for converting text to speech using OpenAI's TTS service.
    
    Required JSON parameters:
    - text: The text to convert to speech
    - language: The language code (e.g., 'en', 'es', 'fr')
    
    Returns:
    - Audio file as response with appropriate content type
    """
    data = request.json
    
    if not data or 'text' not in data or 'language' not in data:
        return jsonify({'error': 'Missing required parameters: text and language'}), 400
    
    text = data['text']
    language = data['language']
    
    if not text.strip():
        return jsonify({'error': 'Empty text provided'}), 400
    
    try:
        # Map language code to appropriate voice
        # OpenAI voices: alloy, echo, fable, onyx, nova, shimmer
        voice_map = {
            # Default English voice (alloy is neutral)
            'en': 'alloy',
            
            # Romance languages (nova is good for these)
            'es': 'nova',  # Spanish
            'fr': 'nova',  # French
            'it': 'nova',  # Italian
            'pt': 'nova',  # Portuguese
            'ro': 'nova',  # Romanian
            
            # Germanic languages (onyx works well)
            'de': 'onyx',  # German
            'nl': 'onyx',  # Dutch
            'sv': 'onyx',  # Swedish
            'no': 'onyx',  # Norwegian
            'da': 'onyx',  # Danish
            
            # Asian languages (shimmer is clearer)
            'ja': 'shimmer',  # Japanese
            'zh': 'shimmer',  # Chinese
            'ko': 'shimmer',  # Korean
            
            # Slavic languages (echo has good clarity)
            'ru': 'echo',   # Russian
            'uk': 'echo',   # Ukrainian
            'cs': 'echo',   # Czech
            'pl': 'echo',   # Polish
            'bg': 'echo',   # Bulgarian
            
            # Other languages
            'ar': 'fable',  # Arabic
            'hi': 'fable',  # Hindi
            'tr': 'fable',  # Turkish
            'fi': 'onyx',   # Finnish
            'hu': 'echo',   # Hungarian
            'el': 'nova',   # Greek
            'he': 'fable',  # Hebrew
            'te': 'fable',  # Telugu
            'th': 'shimmer',  # Thai
            'vi': 'shimmer',  # Vietnamese
            'id': 'shimmer',  # Indonesian
            'ms': 'shimmer',  # Malay
        }
        
        # Get voice based on language or default to alloy
        voice = voice_map.get(language, 'alloy')
        
        # Log request for debugging
        print(f"TTS request: language={language}, voice={voice}, text_length={len(text)}")
        
        # Create a temporary file to store the audio
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.close()
        
        # Generate speech with OpenAI
        response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        # Save to the temporary file
        response.stream_to_file(temp_file.name)
        
        # Send the file as response
        return send_from_directory(
            os.path.dirname(temp_file.name),
            os.path.basename(temp_file.name),
            as_attachment=True,
            download_name="speech.mp3",
            mimetype="audio/mpeg"
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"TTS error: {str(e)}\n{error_details}")
        
        return jsonify({
            'error': str(e),
            'errorType': type(e).__name__,
            'details': 'See server logs for more information'
        }), 500

@app.route('/api/translate', methods=['POST'])
def translate_text():
    """
    Endpoint for translating text from one language to another.
    
    Required JSON parameters:
    - text: The text to translate
    - target_language: The language code to translate to (e.g., 'en', 'es', 'fr')
    
    Returns:
    - JSON with translated text
    """
    data = request.json
    
    if not data or 'text' not in data or 'target_language' not in data:
        return jsonify({'error': 'Missing required parameters: text and target_language'}), 400
    
    text = data['text']
    target_language = data['target_language']
    
    if not text.strip():
        return jsonify({'error': 'Empty text provided'}), 400
    
    try:
        # Use OpenAI API for translation
        response = openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": f"You are a professional translator. Translate the text into {target_language}. Only respond with the translation, nothing else."},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=5000
        )
        
        translated_text = response.choices[0].message.content
        
        return jsonify({
            'text': translated_text,
            'source_language': 'auto-detect',
            'target_language': target_language,
            'success': True
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Translation error: {str(e)}\n{error_details}")
        
        return jsonify({
            'error': str(e),
            'errorType': type(e).__name__,
            'details': 'See server logs for more information'
        }), 500

# For loading static assets
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)