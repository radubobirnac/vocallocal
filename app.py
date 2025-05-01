"""
VocalLocal Web Service - Flask API for speech-to-text
"""

import os
import io
import time
import tempfile
import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory, session
from werkzeug.utils import secure_filename
import openai
from dotenv import load_dotenv

# Try to import Google Generative AI, install if missing
try:
    # Print debug information about the Python path
    import sys
    import subprocess
    print("Python path:")
    for path in sys.path:
        print(f"  {path}")

    # Try to import the module
    print("Attempting to import google.generativeai...")
    try:
        import google.generativeai as genai
        GEMINI_AVAILABLE = True
        print("Google Generative AI module loaded successfully")
    except ImportError as e:
        print(f"Google Generative AI module not available: {str(e)}")
        print("Attempting to install Google Generative AI module...")

        # Try to install the package
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai>=0.8.5"])
            subprocess.check_call([sys.executable, "-m", "pip", "install",
                                  "google-api-core", "google-api-python-client", "google-auth",
                                  "google-auth-httplib2", "google-auth-oauthlib",
                                  "googleapis-common-protos", "protobuf"])

            # Try importing again
            import google.generativeai as genai
            GEMINI_AVAILABLE = True
            print("Google Generative AI module installed and loaded successfully")
        except Exception as install_error:
            print(f"Failed to install Google Generative AI module: {str(install_error)}")
            GEMINI_AVAILABLE = False
            print("Gemini features will be disabled.")

            # Create a placeholder for genai
            class GenaiPlaceholder:
                def configure(self, **kwargs):
                    pass
            genai = GenaiPlaceholder()
except Exception as outer_e:
    print(f"Unexpected error: {str(outer_e)}")
    GEMINI_AVAILABLE = False

    # Create a placeholder for genai
    class GenaiPlaceholder:
        def configure(self, **kwargs):
            pass
    genai = GenaiPlaceholder()

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24).hex())

# OpenAI API configuration
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    print("Warning: OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

# Google Gemini API configuration
gemini_api_key = os.getenv('Gemini_Api_Key') or os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    print("Warning: Gemini API key not found. Set Gemini_Api_Key or GEMINI_API_KEY environment variable.")
elif GEMINI_AVAILABLE:
    genai.configure(api_key=gemini_api_key)
    print("Gemini API configured successfully")

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

        # Process with OpenAI or Gemini based on the model
        try:
            with open(filepath, 'rb') as audio_file:
                # Log request information for debugging
                print(f"Transcribing file: {filename}, size: {os.path.getsize(filepath)} bytes, format: {file.content_type}, model: {model}")

                # Check if we should use Gemini
                if model.startswith('gemini-'):
                    try:
                        # Read the file content
                        audio_content = audio_file.read()

                        # Use Gemini for transcription with the selected model
                        model_name = model
                        print(f"Attempting to use {model_name} for transcription")

                        transcription = transcribe_with_gemini(audio_content, language, model_name)

                        # Create a response object similar to OpenAI's
                        response = type('obj', (object,), {
                            'text': transcription
                        })

                        # Log success
                        print(f"Successfully transcribed with {model_name}")

                    except Exception as gemini_error:
                        # Log the error
                        print(f"Gemini transcription failed: {str(gemini_error)}")
                        print(f"Falling back to OpenAI GPT-4o Mini for transcription")

                        # Rewind the file pointer to the beginning
                        audio_file.seek(0)

                        # Fallback to OpenAI
                        response = openai.audio.transcriptions.create(
                            model="gpt-4o-mini-transcribe",  # Fallback to the mini model
                            file=audio_file,
                            language=language
                        )
                else:
                    # Use OpenAI for transcription
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
    translation_model = data.get('translation_model', 'gemini')  # Default to Gemini

    if not text.strip():
        return jsonify({'error': 'Empty text provided'}), 400

    # Start timing for performance metrics
    start_time = time.time()
    char_count = len(text)

    try:
        translated_text = None
        model_used = translation_model
        fallback_used = False

        # Translation prompt
        translation_prompt = f"You are a professional translator. Translate the text into {target_language}. Only respond with the translation, nothing else."

        # First attempt with the selected model
        if translation_model.startswith('gemini'):
            try:
                translated_text = translate_with_gemini(text, target_language, translation_prompt, translation_model)
            except Exception as gemini_error:
                print(f"Gemini translation error: {str(gemini_error)}")
                # Fallback to OpenAI if Gemini fails
                try:
                    translated_text = translate_with_openai(text, target_language, translation_prompt)
                    model_used = 'openai'
                    fallback_used = True
                except Exception as openai_fallback_error:
                    # If both fail, re-raise the original error
                    raise gemini_error
        else:  # OpenAI
            try:
                translated_text = translate_with_openai(text, target_language, translation_prompt)
            except Exception as openai_error:
                print(f"OpenAI translation error: {str(openai_error)}")
                # Fallback to Gemini if OpenAI fails
                try:
                    # Default to standard Gemini model for fallback
                    translated_text = translate_with_gemini(text, target_language, translation_prompt, 'gemini')
                    model_used = 'gemini'
                    fallback_used = True
                except Exception as gemini_fallback_error:
                    # If both fail, re-raise the original error
                    raise openai_error

        # Calculate performance metrics
        end_time = time.time()
        translation_time = end_time - start_time
        chars_per_second = char_count / translation_time if translation_time > 0 else 0

        # Log performance metrics
        print(f"Translation performance: model={model_used}, time={translation_time:.2f}s, chars={char_count}, chars/s={chars_per_second:.2f}, fallback={fallback_used}")

        return jsonify({
            'text': translated_text,
            'source_language': 'auto-detect',
            'target_language': target_language,
            'model_used': model_used,
            'fallback_used': fallback_used,
            'performance': {
                'time_seconds': round(translation_time, 2),
                'character_count': char_count,
                'characters_per_second': round(chars_per_second, 2)
            },
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

def transcribe_with_gemini(audio_data, language, model_type="gemini-2.5-pro-preview-03-25"):
    """Helper function to transcribe audio using Google Gemini"""
    # Check if Gemini is available
    if not GEMINI_AVAILABLE:
        print("Google Generative AI module is not available. Cannot use Gemini for transcription.")
        print("Falling back to OpenAI for transcription.")
        return transcribe_with_openai(audio_data, language)

    try:
        # First, let's list available models to see what we can use
        try:
            all_models = list(genai.list_models())
            available_models = [m.name for m in all_models]
            print(f"Available Gemini models: {available_models}")

            # Print model capabilities
            for model in all_models:
                print(f"Model: {model.name}")
                print(f"  - Supported generation methods: {model.supported_generation_methods}")
                print(f"  - Input token limit: {model.input_token_limit}")
                print(f"  - Output token limit: {model.output_token_limit}")
                print(f"  - Temperature range: {model.temperature_range}")
                print(f"  - Supports audio input: {'audio' in str(model.input_mime_types).lower()}")
        except Exception as list_error:
            print(f"Could not list available models: {str(list_error)}")
            available_models = []

        # Configure the model
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 0,
            "max_output_tokens": 8192,
        }

        # Check if the model is available
        model_name = model_type
        if model_name not in str(available_models):
            print(f"Warning: {model_name} not found in available models. Attempting to use it anyway.")

            # Try to find a suitable alternative
            if "gemini-pro" in available_models:
                print(f"Trying alternative model: gemini-pro")
                model_name = "gemini-pro"
            elif "gemini-1.5-pro" in available_models:
                print(f"Trying alternative model: gemini-1.5-pro")
                model_name = "gemini-1.5-pro"

        # Initialize the Gemini model
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )

        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        # Prepare the prompt
        prompt = f"Please transcribe the following audio file. The language is {language}."

        # For Gemini, we need to encode the audio file as base64
        import base64
        with open(temp_file_path, 'rb') as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')

        # Clean up the temporary file
        os.remove(temp_file_path)

        # Create a multimodal content message with the audio
        response = model.generate_content([
            prompt,
            {"mime_type": "audio/mp3", "data": audio_base64}
        ])

        # Extract the transcription from the response
        transcription = response.text

        print(f"Gemini transcription completed: {len(transcription)} characters")

        return transcription

    except Exception as e:
        print(f"Error in Gemini transcription: {str(e)}")

        # Check if this is a model not found error
        if "not found" in str(e) or "not supported" in str(e):
            print("The Gemini 2.5 Flash Preview model does not support audio transcription yet.")
            print("This feature may be available in a future update.")

        # Fall back to OpenAI for transcription
        print("Falling back to OpenAI for transcription.")
        return transcribe_with_openai(audio_data, language)

def transcribe_with_openai(audio_data, language):
    """Helper function to transcribe audio using OpenAI"""
    try:
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        # Open the file in binary mode
        with open(temp_file_path, 'rb') as audio_file:
            # Call the OpenAI API to transcribe the audio
            response = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language if language != "auto" else None
            )

        # Clean up the temporary file
        os.remove(temp_file_path)

        # Extract the transcription from the response
        transcription = response.text

        print(f"OpenAI transcription completed: {len(transcription)} characters")

        return transcription

    except Exception as e:
        print(f"Error in OpenAI transcription: {str(e)}")
        raise e

def translate_with_openai(text, target_language, prompt):
    """Helper function to translate text using OpenAI"""
    response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.3,
        max_tokens=5000
    )

    return response.choices[0].message.content

def translate_with_gemini(text, target_language, prompt, translation_model='gemini'):
    """Helper function to translate text using Google Gemini"""
    # Check if Gemini is available
    if not GEMINI_AVAILABLE:
        print("Google Generative AI module is not available. Falling back to OpenAI for translation.")
        return translate_with_openai(text, target_language, prompt)

    try:
        # Configure the model
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 0,
            "max_output_tokens": 8192,
        }

        # Select the appropriate model based on the translation_model parameter
        model_name = "gemini-2.0-flash-lite"  # Default model

        if 'gemini-2.5-flash-preview' in translation_model:
            # Use the full model name from the available models list
            model_name = "models/gemini-2.5-flash-preview-04-17"
            print(f"Using Gemini 2.5 Flash Preview model for translation")
        elif 'gemini-2.5-pro-preview' in translation_model:
            # Use the full model name from the available models list
            model_name = "models/gemini-2.5-pro-preview-03-25"
            print(f"Using Gemini 2.5 Pro Preview model for translation")
        else:
            print(f"Using Gemini 2.0 Flash Lite model for translation")

        # Initialize the Gemini model
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )

        # Create the prompt with system and user messages
        chat = model.start_chat(history=[])
        response = chat.send_message(
            f"{prompt}\n\nText to translate: {text}"
        )

        return response.text
    except Exception as e:
        print(f"Error using Gemini API: {str(e)}. Falling back to OpenAI for translation.")
        return translate_with_openai(text, target_language, prompt)

# For loading static assets
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/test-openai', methods=['GET'])
def test_openai_api():
    """
    Test endpoint to verify OpenAI API key is working
    """
    try:
        # Print the API key length (not the actual key) for debugging
        api_key = os.getenv('OPENAI_API_KEY', '')
        print(f"API key length: {len(api_key)}")

        if not api_key:
            return jsonify({
                'status': 'error',
                'message': 'OpenAI API key is not set'
            }), 500

        # Try a simple API call to verify the key works
        response = openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ],
            max_tokens=5
        )

        return jsonify({
            'status': 'success',
            'message': 'OpenAI API key is working correctly',
            'model': response.model
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"OpenAI API test error: {str(e)}\n{error_details}")

        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    import argparse

    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='VocalLocal Web Service')
    parser.add_argument('--port', type=int, default=5001,
                        help='Port to run the server on (default: 5001)')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Host to run the server on (default: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true', default=True,
                        help='Run in debug mode (default: True)')

    # Parse arguments
    args = parser.parse_args()

    # Print startup message
    print(f"Starting VocalLocal on http://localhost:{args.port}")
    print(f"Press Ctrl+C to quit")

    # Run the application
    app.run(debug=args.debug, host=args.host, port=args.port)