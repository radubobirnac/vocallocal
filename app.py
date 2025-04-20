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
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'm4a', 'webm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

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
        
        # Process with OpenAI
        try:
            with open(filepath, 'rb') as audio_file:
                response = openai.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",
                    file=audio_file,
                    language=language
                )
            
            # Remove temporary file
            os.remove(filepath)
            
            # Return results
            return jsonify({
                'text': response.text,
                'language': language,
                'success': True
            })
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

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
        "Thai": {"code": "th", "native": "ไทย"},
        "Vietnamese": {"code": "vi", "native": "Tiếng Việt"},
        "Indonesian": {"code": "id", "native": "Bahasa Indonesia"},
        "Malay": {"code": "ms", "native": "Bahasa Melayu"},
        "Bulgarian": {"code": "bg", "native": "Български"}
    }
    return jsonify(supported_languages)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 
