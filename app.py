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
    # Dictionary of supported languages with their codes
    supported_languages = {
        "English": "en",
        "Spanish": "es",
        "French": "fr",
        "German": "de",
        "Italian": "it",
        "Portuguese": "pt",
        "Dutch": "nl",
        "Japanese": "ja",
        "Chinese": "zh",
        "Korean": "ko",
        "Russian": "ru",
        "Arabic": "ar",
        "Hindi": "hi",
        "Turkish": "tr",
        "Swedish": "sv",
        "Polish": "pl",
        "Norwegian": "no",
        "Finnish": "fi",
        "Danish": "da",
        "Ukrainian": "uk",
        "Czech": "cs",
        "Romanian": "ro",
        "Hungarian": "hu",
        "Greek": "el",
        "Hebrew": "he",
        "Thai": "th",
        "Vietnamese": "vi",
        "Indonesian": "id",
        "Malay": "ms",
        "Bulgarian": "bg"
    }
    return jsonify(supported_languages)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 