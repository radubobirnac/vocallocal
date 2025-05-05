"""
VocalLocal Web Service - Flask API for speech-to-text
"""

import os
import io
import time
import tempfile
import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect
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

# Import token counter and metrics tracker
try:
    import tiktoken
except ImportError:
    # Install tiktoken if not available
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tiktoken"])
        import tiktoken
    except Exception:
        print("Failed to install tiktoken. Token counting will use approximations.")

# Import our custom modules
try:
    from token_counter import (
        count_openai_tokens, count_openai_chat_tokens, count_openai_audio_tokens,
        count_gemini_tokens, count_gemini_audio_tokens, estimate_audio_duration
    )
    from metrics_tracker import (
        metrics_tracker, track_translation_metrics, track_transcription_metrics
    )
    METRICS_AVAILABLE = True
    print("Metrics tracking enabled")
except ImportError as e:
    print(f"Metrics tracking not available: {str(e)}")
    METRICS_AVAILABLE = False

    # Create placeholder decorators if metrics tracking is not available
    def track_translation_metrics(func):
        return func

    def track_transcription_metrics(func):
        return func

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24).hex())

# Add security configurations
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Add security headers to all responses
@app.after_request
def add_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

# Add this before_request handler to ensure HTTPS
@app.before_request
def redirect_https():
    # Check if we're already using HTTPS
    if not request.is_secure:
        # Check if this is a Render deployment (they set X-Forwarded-Proto)
        if 'X-Forwarded-Proto' in request.headers:
            # If the forwarded protocol is http, redirect to https
            if request.headers.get('X-Forwarded-Proto') == 'http':
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)
        # For local development without X-Forwarded headers
        elif not request.is_secure and 'localhost' not in request.host and '127.0.0.1' not in request.host:
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)

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

# Helper function to get language name from language code
def get_language_name_from_code(language_code):
    # Dictionary mapping language codes to language names
    language_map = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "nl": "Dutch",
        "ja": "Japanese",
        "zh": "Chinese",
        "ko": "Korean",
        "ru": "Russian",
        "ar": "Arabic",
        "hi": "Hindi",
        "tr": "Turkish",
        "sv": "Swedish",
        "pl": "Polish",
        "no": "Norwegian",
        "fi": "Finnish",
        "da": "Danish",
        "uk": "Ukrainian",
        "cs": "Czech",
        "ro": "Romanian",
        "hu": "Hungarian",
        "el": "Greek",
        "he": "Hebrew",
        "te": "Telugu",
        "th": "Thai",
        "vi": "Vietnamese",
        "id": "Indonesian",
        "ms": "Malay",
        "bg": "Bulgarian",
        "ur": "Urdu",
        "bn": "Bengali",
        "fa": "Persian",
        "sw": "Swahili",
        "ta": "Tamil",
        "pa": "Punjabi",
        "mr": "Marathi",
        "gu": "Gujarati",
        "kn": "Kannada",
        "ml": "Malayalam",
        "ne": "Nepali",
        "si": "Sinhala",
        "km": "Khmer",
        "lo": "Lao",
        "my": "Burmese",
        "ps": "Pashto",
        "am": "Amharic",
        "az": "Azerbaijani",
        "kk": "Kazakh",
        "sr": "Serbian",
        "tg": "Tajik",
        "uz": "Uzbek",
        "yo": "Yoruba",
        "zu": "Zulu",
        "wuu": "Wu Chinese",
        "ha": "Hausa",
        "yue": "Cantonese",
        "or": "Odia",
        "as": "Assamese",
        "nan": "Min Nan Chinese",
        "ku": "Kurdish",
        "ig": "Igbo"
    }

    # Return the language name if found, otherwise return the code
    return language_map.get(language_code, language_code)

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
        model = request.form.get('model', 'gemini')

        # Process with OpenAI or Gemini based on the model
        try:
            with open(filepath, 'rb') as audio_file:
                # Log request information for debugging
                print(f"Transcribing file: {filename}, size: {os.path.getsize(filepath)} bytes, format: {file.content_type}, model: {model}")

                # Check if we should use Gemini
                if model.startswith('gemini-') or model == 'gemini':
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
        "Bulgarian": {"code": "bg", "native": "Български"},
        "Urdu": {"code": "ur", "native": "اردو"},
        "Bengali": {"code": "bn", "native": "বাংলা"},
        "Persian": {"code": "fa", "native": "فارسی"},
        "Swahili": {"code": "sw", "native": "Kiswahili"},
        "Tamil": {"code": "ta", "native": "தமிழ்"},
        "Punjabi": {"code": "pa", "native": "ਪੰਜਾਬੀ"},
        "Marathi": {"code": "mr", "native": "मराठी"},
        "Gujarati": {"code": "gu", "native": "ગુજરાતી"},
        "Kannada": {"code": "kn", "native": "ಕನ್ನಡ"},
        "Malayalam": {"code": "ml", "native": "മലയാളം"},
        "Nepali": {"code": "ne", "native": "नेपाली"},
        "Sinhala": {"code": "si", "native": "සිංහල"},
        "Khmer": {"code": "km", "native": "ខ្មែរ"},
        "Lao": {"code": "lo", "native": "ລາວ"},
        "Burmese": {"code": "my", "native": "မြန်မာ"},
        "Pashto": {"code": "ps", "native": "پښتو"},
        "Amharic": {"code": "am", "native": "አማርኛ"},
        "Azerbaijani": {"code": "az", "native": "Azərbaycan dili"},
        "Kazakh": {"code": "kk", "native": "Қазақ тілі"},
        "Serbian": {"code": "sr", "native": "Српски"},
        "Tajik": {"code": "tg", "native": "Тоҷикӣ"},
        "Uzbek": {"code": "uz", "native": "O'zbek"},
        "Yoruba": {"code": "yo", "native": "Yorùbá"},
        "Zulu": {"code": "zu", "native": "isiZulu"},
        "Wu Chinese": {"code": "wuu", "native": "吴语"},
        "Hausa": {"code": "ha", "native": "هَوُ"},
        "Cantonese": {"code": "yue", "native": "粵語"},
        "Odia": {"code": "or", "native": "ଓଡ଼ିଆ"},
        "Assamese": {"code": "as", "native": "অসমীয়া"},
        "Min Nan Chinese": {"code": "nan", "native": "閩南語"},
        "Kurdish": {"code": "ku", "native": "Kurdî"},
        "Igbo": {"code": "ig", "native": "Igbo"}
    }
    return jsonify(supported_languages)

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """
    Endpoint for converting text to speech using OpenAI's TTS services.

    Required JSON parameters:
    - text: The text to convert to speech
    - language: The language code (e.g., 'en', 'es', 'fr')

    Optional JSON parameters:
    - tts_model: The model to use for TTS ('gpt4o-mini' or 'openai', default: 'gpt4o-mini')
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
    tts_model = data.get('tts_model', 'gpt4o-mini')  # Default to GPT-4o Mini
    print(f"TTS request: model={tts_model}, language={language}, text_length={len(text)}")

    if not text.strip():
        print("Empty text provided")
        return jsonify({'error': 'Empty text provided'}), 400

    # Start timing for performance metrics
    start_time = time.time()
    char_count = len(text)

    try:
        # Create a temporary file to store the audio
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.close()
        print(f"Created temporary file: {temp_file.name}")

        # First attempt with the selected model
        model_used = tts_model
        fallback_used = False
        success = False

        if tts_model == 'gpt4o-mini':
            print("Using GPT-4o Mini TTS model")
            try:
                # Use the GPT-4o Mini TTS model
                tts_with_gpt4o_mini(text, language, temp_file.name)
                model_used = 'gpt4o-mini'
                success = True
            except Exception as e:
                print(f"GPT-4o Mini TTS error: {str(e)}")
                print("Falling back to standard OpenAI TTS")
                try:
                    # Fallback to standard OpenAI TTS
                    tts_with_openai(text, language, temp_file.name)
                    model_used = 'openai'
                    fallback_used = True
                    success = True
                except Exception as fallback_e:
                    print(f"Fallback OpenAI TTS error: {str(fallback_e)}")
                    return jsonify({
                        'error': str(e),
                        'errorType': type(e).__name__,
                        'details': 'TTS service error (both primary and fallback failed)'
                    }), 500
        else:  # OpenAI
            print("Using OpenAI TTS model")
            try:
                tts_with_openai(text, language, temp_file.name)
                success = True
            except Exception as e:
                print(f"OpenAI TTS error: {str(e)}")
                return jsonify({
                    'error': str(e),
                    'errorType': type(e).__name__,
                    'details': 'TTS service error'
                }), 500

        # Calculate performance metrics
        end_time = time.time()
        tts_time = end_time - start_time
        chars_per_second = char_count / tts_time if tts_time > 0 else 0

        # Log performance metrics
        print(f"TTS performance: model={model_used}, time={tts_time:.2f}s, chars={char_count}, chars/s={chars_per_second:.2f}, fallback={fallback_used}")

        # Track metrics if available
        if METRICS_AVAILABLE:
            # Estimate token usage (very rough estimate for TTS)
            estimated_tokens = char_count // 4  # Rough estimate
            try:
                # Initialize tts section if it doesn't exist
                if "tts" not in metrics_tracker.metrics:
                    metrics_tracker.metrics["tts"] = {}

                # Ensure both TTS models exist in metrics
                for model_key in ['gpt4o-mini', 'openai']:
                    if model_key not in metrics_tracker.metrics["tts"]:
                        metrics_tracker.metrics["tts"][model_key] = {
                            "calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0
                        }

                # Initialize model if not exists (redundant but safe)
                if model_used not in metrics_tracker.metrics["tts"]:
                    metrics_tracker.metrics["tts"][model_used] = {
                        "calls": 0, "tokens": 0, "chars": 0, "time": 0, "failures": 0
                    }

                # Update metrics directly
                metrics_tracker.metrics["tts"][model_used]["calls"] += 1
                metrics_tracker.metrics["tts"][model_used]["tokens"] += estimated_tokens
                metrics_tracker.metrics["tts"][model_used]["chars"] += char_count
                metrics_tracker.metrics["tts"][model_used]["time"] += tts_time

                # Save metrics
                metrics_tracker._save_metrics()

                print(f"TTS metrics tracked: model={model_used}, tokens={estimated_tokens}, chars={char_count}")
            except Exception as e:
                # If there's an error tracking metrics, just log it
                print(f"Warning: Could not track TTS metrics: {str(e)}")

        print(f"Sending audio file: {temp_file.name}")
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

def tts_with_openai(text, language, output_file_path):
    """Helper function to generate speech using OpenAI's TTS service"""
    # Use onyx voice for all languages
    voice = 'onyx'

    # Log request for debugging
    print(f"OpenAI TTS request: language={language}, voice={voice}, text_length={len(text)}")

    # Generate speech with OpenAI
    response = openai.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )

    # Save to the output file
    with open(output_file_path, 'wb') as f:
        for chunk in response.iter_bytes():
            f.write(chunk)

    return True

def tts_with_gpt4o_mini(text, language, output_file_path):
    """Helper function to generate speech using OpenAI's GPT-4o Mini TTS service"""
    # For GPT-4o Mini TTS, we'll use a simple approach without voice mapping
    # Just use 'alloy' voice for all languages

    # Log request for debugging
    print(f"GPT-4o Mini TTS request: language={language}, text_length={len(text)}")

    # Generate speech with OpenAI's GPT-4o Mini TTS
    response = openai.audio.speech.create(
        model="gpt-4o-mini-tts",  # Use the GPT-4o Mini TTS model
        voice="alloy",  # Use alloy voice for all languages
        input=text
    )

    # Save to the output file
    with open(output_file_path, 'wb') as f:
        for chunk in response.iter_bytes():
            f.write(chunk)

    return True

def tts_with_google(text, language, output_file_path):
    """Helper function to generate speech using Google's TTS service"""
    # Check if Gemini is available
    if not GEMINI_AVAILABLE:
        print("Google Generative AI module is not available. Cannot use Google for TTS.")
        return False

    try:
        # For now, we'll use a fallback to OpenAI TTS
        # This is a placeholder for the actual Google TTS implementation
        print(f"Google TTS request: language={language}, text_length={len(text)}")

        # In a real implementation, we would use Google Cloud Text-to-Speech API
        # For now, we'll fallback to OpenAI TTS
        print(f"Falling back to OpenAI TTS as Google TTS is not fully implemented yet")

        # Use OpenAI TTS instead
        return tts_with_openai(text, language, output_file_path)

    except Exception as e:
        print(f"Error in Google TTS: {str(e)}")
        return False

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

        # Translation prompt - Use the full language name instead of just the code
        language_name = get_language_name_from_code(target_language)
        translation_prompt = f"You are a professional translator. Translate the text into {language_name} (language code: {target_language}). Only respond with the translation, nothing else."

        # First attempt with the selected model
        if translation_model.startswith('gemini') or translation_model == 'gemini-2.0-flash-lite':
            try:
                translated_text = translate_with_gemini(text, target_language, translation_prompt, translation_model)
            except Exception as gemini_error:
                print(f"Gemini translation error: {str(gemini_error)}")
                # Fallback to OpenAI if Gemini fails
                try:
                    translated_text = translate_with_openai(text, target_language, translation_prompt)
                    model_used = 'gpt-4.1-mini'
                    fallback_used = True
                except Exception as openai_fallback_error:
                    # If both fail, re-raise the original error
                    raise gemini_error
        elif translation_model.startswith('gpt'):  # GPT models (like gpt-4.1-mini)
            try:
                translated_text = translate_with_openai(text, target_language, translation_prompt)
            except Exception as openai_error:
                print(f"OpenAI translation error: {str(openai_error)}")
                # Fallback to Gemini if OpenAI fails
                try:
                    # Default to standard Gemini model for fallback
                    translated_text = translate_with_gemini(text, target_language, translation_prompt, 'gemini-2.0-flash-lite')
                    model_used = 'gemini-2.0-flash-lite'
                    fallback_used = True
                except Exception as gemini_fallback_error:
                    # If both fail, re-raise the original error
                    raise openai_error
        else:  # Handle legacy model names (for backward compatibility)
            if translation_model == 'openai':
                try:
                    translated_text = translate_with_openai(text, target_language, translation_prompt)
                except Exception as openai_error:
                    print(f"OpenAI translation error: {str(openai_error)}")
                    # Fallback to Gemini if OpenAI fails
                    try:
                        translated_text = translate_with_gemini(text, target_language, translation_prompt, 'gemini-2.0-flash-lite')
                        model_used = 'gemini-2.0-flash-lite'
                        fallback_used = True
                    except Exception as gemini_fallback_error:
                        # If both fail, re-raise the original error
                        raise openai_error
            else:  # Default to Gemini for any other model name
                try:
                    translated_text = translate_with_gemini(text, target_language, translation_prompt, 'gemini-2.0-flash-lite')
                except Exception as gemini_error:
                    print(f"Gemini translation error: {str(gemini_error)}")
                    # Fallback to OpenAI if Gemini fails
                    try:
                        translated_text = translate_with_openai(text, target_language, translation_prompt)
                        model_used = 'gpt-4.1-mini'
                        fallback_used = True
                    except Exception as openai_fallback_error:
                        # If both fail, re-raise the original error
                        raise gemini_error

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

def transcribe_with_gemini(audio_data, language, model_type="gemini"):
    """Helper function to transcribe audio using Google Gemini"""
    # Start timing for metrics
    start_time = time.time()

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
        # For metrics tracking, use a simplified model name
        display_model = model_type

        # Handle model selection
        if model_type == 'gemini':
            # Use Gemini 2.0 Flash Lite for transcription
            model_name = "models/gemini-2.0-flash-lite"
            display_model = 'gemini-2.0-flash-lite'
            print(f"Using Gemini 2.0 Flash Lite model for transcription")
        elif 'gemini-2.5-flash-preview' in model_type:
            display_model = 'gemini-2.5-flash-preview'
        elif 'gemini-2.5-pro-preview' in model_type:
            # This model has been removed from the UI, but handle it in case it's still in localStorage
            print(f"Gemini 2.5 Pro Preview model is no longer supported for transcription")
            print(f"Falling back to Gemini 2.0 Flash Lite")
            model_name = "models/gemini-2.0-flash-lite"
            display_model = 'gemini-2.0-flash-lite'

        # Estimate audio duration for token counting
        audio_size = len(audio_data)
        estimated_duration = estimate_audio_duration(audio_size, "webm") if METRICS_AVAILABLE else None

        # Estimate token usage
        estimated_tokens = count_gemini_audio_tokens(audio_size, estimated_duration) if METRICS_AVAILABLE else audio_size // 100
        print(f"Estimated Gemini audio transcription token usage: {estimated_tokens} tokens (audio size: {audio_size} bytes, est. duration: {estimated_duration:.2f}s)")

        if model_name not in str(available_models):
            print(f"Warning: {model_name} not found in available models. Attempting to use it anyway.")

            # Try to find a suitable alternative
            if "gemini-pro" in available_models:
                print(f"Trying alternative model: gemini-pro")
                model_name = "gemini-pro"
                display_model = "gemini-pro"
            elif "gemini-1.5-pro" in available_models:
                print(f"Trying alternative model: gemini-1.5-pro")
                model_name = "gemini-1.5-pro"
                display_model = "gemini-1.5-pro"

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
        print(f"Successfully transcribed with {model_type}")

        # Manually track metrics with the correct model name
        if METRICS_AVAILABLE:
            # Calculate response time
            response_time = time.time() - start_time
            # Get character count
            char_count = len(transcription)
            # Track metrics with the display_model name
            metrics_tracker.track_transcription(
                display_model, estimated_tokens, char_count, response_time, True
            )
            print(f"Tracked metrics for model: {display_model}")

        return transcription

    except Exception as e:
        print(f"Error in Gemini transcription: {str(e)}")

        # Track the error in metrics
        if METRICS_AVAILABLE:
            # Calculate response time
            response_time = time.time() - start_time
            # Track metrics with the display_model name and mark as failure
            metrics_tracker.track_transcription(
                display_model, estimated_tokens, 0, response_time, False
            )
            print(f"Tracked error metrics for model: {display_model}")

        # Check if this is a model not found error
        if "not found" in str(e) or "not supported" in str(e):
            print("The Gemini 2.5 Flash Preview model does not support audio transcription yet.")
            print("This feature may be available in a future update.")

        # Fall back to OpenAI for transcription
        print("Falling back to OpenAI for transcription.")
        return transcribe_with_openai(audio_data, language)

def transcribe_with_openai(audio_data, language, model_type="gpt-4o-mini-transcribe"):
    """Helper function to transcribe audio using OpenAI"""
    # Start timing for metrics
    start_time = time.time()

    try:
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        # Estimate audio duration for token counting
        audio_size = len(audio_data)
        estimated_duration = estimate_audio_duration(audio_size, "webm") if METRICS_AVAILABLE else None

        # Estimate token usage
        estimated_tokens = count_openai_audio_tokens(audio_size, estimated_duration) if METRICS_AVAILABLE else audio_size // 100
        print(f"Estimated OpenAI audio transcription token usage: {estimated_tokens} tokens (audio size: {audio_size} bytes, est. duration: {estimated_duration:.2f}s)")

        # Open the file in binary mode
        with open(temp_file_path, 'rb') as audio_file:
            # Call the OpenAI API to transcribe the audio
            response = openai.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",  # Use GPT-4o Mini instead of Whisper
                file=audio_file,
                language=language if language != "auto" else None
            )

        # Clean up the temporary file
        os.remove(temp_file_path)

        # Extract the transcription from the response
        transcription = response.text

        print(f"OpenAI transcription completed: {len(transcription)} characters")

        # Manually track metrics with the correct model name
        if METRICS_AVAILABLE:
            # Calculate response time
            response_time = time.time() - start_time
            # Get character count
            char_count = len(transcription)
            # Track metrics with 'openai' as the model name
            metrics_tracker.track_transcription(
                'openai', estimated_tokens, char_count, response_time, True
            )
            print(f"Tracked metrics for model: openai")

        return transcription

    except Exception as e:
        print(f"Error in OpenAI transcription: {str(e)}")

        # Track the error in metrics
        if METRICS_AVAILABLE:
            # Calculate response time
            response_time = time.time() - start_time
            # Track metrics with 'openai' as the model name and mark as failure
            metrics_tracker.track_transcription(
                'openai', estimated_tokens, 0, response_time, False
            )
            print(f"Tracked error metrics for model: openai")

        raise e

def translate_with_openai(text, target_language, prompt, translation_model='gpt-4.1-mini'):
    """Helper function to translate text using OpenAI"""
    # Start timing for metrics
    start_time = time.time()

    # Get language name for better logging
    language_name = get_language_name_from_code(target_language)

    # Log translation request details
    print(f"OpenAI translation request:")
    print(f"  - Target language: {language_name} (code: {target_language})")
    print(f"  - Text length: {len(text)} characters")
    print(f"  - Prompt: {prompt}")

    # Handle legacy model name
    display_model = translation_model
    if translation_model == 'openai':
        display_model = 'gpt-4.1-mini'
        print(f"  - Converting legacy model name 'openai' to '{display_model}'")

    # Prepare messages
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": text}
    ]

    # Count tokens for logging and metrics
    model_name = "gpt-4.1-mini"
    input_tokens = count_openai_chat_tokens(messages, model_name) if METRICS_AVAILABLE else len(text) // 4

    # Make the API call
    response = openai.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.3,
        max_tokens=5000
    )

    # Get the response text
    translated_text = response.choices[0].message.content

    # Count output tokens for metrics
    output_tokens = count_openai_tokens(translated_text, model_name) if METRICS_AVAILABLE else len(translated_text) // 4

    # Log token usage and translation result
    total_tokens = input_tokens + output_tokens
    print(f"OpenAI translation completed:")
    print(f"  - Token usage: {total_tokens} tokens (input: {input_tokens}, output: {output_tokens})")
    print(f"  - Result length: {len(translated_text)} characters")
    print(f"  - First 100 chars: {translated_text[:100]}...")

    # Manually track metrics with the correct model name
    if METRICS_AVAILABLE:
        # Calculate response time
        response_time = time.time() - start_time
        # Get character count
        char_count = len(translated_text)
        # Track metrics with the display_model name
        metrics_tracker.track_translation(
            display_model, total_tokens, char_count, response_time, True
        )
        print(f"Tracked metrics for model: {display_model}")

    return translated_text

def translate_with_gemini(text, target_language, prompt, translation_model='gemini-2.0-flash-lite'):
    """Helper function to translate text using Google Gemini"""
    # Start timing for metrics
    start_time = time.time()

    # Get language name for better logging
    language_name = get_language_name_from_code(target_language)

    # Log translation request details
    print(f"Gemini translation request:")
    print(f"  - Target language: {language_name} (code: {target_language})")
    print(f"  - Text length: {len(text)} characters")
    print(f"  - Prompt: {prompt}")
    print(f"  - Requested model: {translation_model}")

    # Handle legacy model name
    if translation_model == 'gemini':
        translation_model = 'gemini-2.0-flash-lite'
        print(f"  - Converting legacy model name 'gemini' to '{translation_model}'")

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
        model_name = "models/gemini-2.0-flash-lite"  # Default model
        display_model = translation_model  # For metrics tracking

        if 'gemini-2.5-flash' in translation_model or translation_model == 'gemini-2.5-flash':
            # Use the full model name from the available models list
            model_name = "models/gemini-2.5-flash-preview-04-17"
            display_model = "gemini-2.5-flash"
            print(f"Using Gemini 2.5 Flash Preview model for translation")
        elif 'gemini-2.5-pro' in translation_model:
            # Use the full model name from the available models list
            model_name = "models/gemini-2.5-pro-preview-03-25"
            display_model = "gemini-2.5-pro"
            print(f"Using Gemini 2.5 Pro Preview model for translation")
        elif translation_model == 'gemini-2.0-flash-lite' or translation_model == 'gemini':
            model_name = "models/gemini-2.0-flash-lite"
            display_model = "gemini-2.0-flash-lite"
            print(f"Using Gemini 2.0 Flash Lite model for translation")
        else:
            # For any other model name, default to Gemini 2.0 Flash Lite
            model_name = "models/gemini-2.0-flash-lite"
            display_model = "gemini-2.0-flash-lite"
            print(f"Unknown model '{translation_model}', defaulting to Gemini 2.0 Flash Lite for translation")

        # Count input tokens for metrics
        input_prompt = f"{prompt}\n\nText to translate: {text}"
        input_tokens = count_gemini_tokens(input_prompt, model_name) if METRICS_AVAILABLE else len(input_prompt) // 3

        # Initialize the Gemini model
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )

        # Create the prompt with system and user messages
        chat = model.start_chat(history=[])
        response = chat.send_message(input_prompt)

        translated_text = response.text

        # Count output tokens for metrics
        output_tokens = count_gemini_tokens(translated_text, model_name) if METRICS_AVAILABLE else len(translated_text) // 3

        # Log token usage and translation result
        total_tokens = input_tokens + output_tokens
        print(f"Gemini translation completed:")
        print(f"  - Model used: {model_name}")
        print(f"  - Token usage: {total_tokens} tokens (input: {input_tokens}, output: {output_tokens})")
        print(f"  - Result length: {len(translated_text)} characters")
        print(f"  - First 100 chars: {translated_text[:100]}...")

        # Manually track metrics with the correct model name
        if METRICS_AVAILABLE:
            # Calculate response time
            response_time = time.time() - start_time
            # Get character count
            char_count = len(translated_text)
            # Track metrics with the display_model name
            metrics_tracker.track_translation(
                display_model, total_tokens, char_count, response_time, True
            )
            print(f"Tracked metrics for model: {display_model}")

        return translated_text
    except Exception as e:
        print(f"Error using Gemini API: {str(e)}. Falling back to OpenAI for translation.")
        print(f"  - Target language: {language_name} (code: {target_language})")
        print(f"  - Requested model: {translation_model}")

        # Track the error in metrics
        if METRICS_AVAILABLE:
            # Calculate response time
            response_time = time.time() - start_time
            # Track metrics with the display_model name and mark as failure
            metrics_tracker.track_translation(
                display_model, 0, 0, response_time, False
            )
            print(f"Tracked error metrics for model: {display_model}")

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

@app.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    """Admin dashboard for viewing metrics"""
    from datetime import datetime
    today_date = datetime.now().strftime("%Y-%m-%d")
    return render_template('admin_dashboard.html', today_date=today_date)

@app.route('/api/admin/metrics', methods=['GET'])
def get_metrics():
    """API endpoint to get metrics data"""
    if not METRICS_AVAILABLE:
        return jsonify({
            'status': 'error',
            'message': 'Metrics tracking is not available'
        }), 500

    try:
        # Get metrics from the tracker
        metrics_data = metrics_tracker.get_metrics()

        return jsonify(metrics_data)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Metrics API error: {str(e)}\n{error_details}")

        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/admin/reset-metrics', methods=['POST'])
def reset_metrics():
    """API endpoint to reset all metrics data"""
    if not METRICS_AVAILABLE:
        return jsonify({
            'status': 'error',
            'message': 'Metrics tracking is not available'
        }), 500

    try:
        # Reset all metrics
        metrics_tracker.reset_metrics()

        return jsonify({
            'status': 'success',
            'message': 'All metrics have been reset successfully'
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Metrics reset error: {str(e)}\n{error_details}")

        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/admin/test-translations', methods=['GET'])
def test_translations():
    """Debug endpoint to test translations for all supported languages"""
    # Sample text to translate (English)
    sample_text = "Hello, this is a test of the translation system. We are checking if all languages work correctly."

    # Get the translation model from query parameter or default to gemini
    translation_model = request.args.get('model', 'gemini')

    # Get all supported languages
    languages_response = get_languages()
    languages = languages_response.json

    results = {}

    # Test translation to each language
    for lang_name, lang_details in languages.items():
        lang_code = lang_details['code']
        if lang_code == 'en':  # Skip English as it's our source
            continue

        try:
            # Get the language name for better prompting
            language_name = get_language_name_from_code(lang_code)

            # Create translation prompt
            translation_prompt = f"You are a professional translator. Translate the text into {language_name} (language code: {lang_code}). Only respond with the translation, nothing else."

            # Translate based on selected model
            if translation_model.startswith('gemini'):
                translated_text = translate_with_gemini(sample_text, lang_code, translation_prompt, translation_model)
            else:
                translated_text = translate_with_openai(sample_text, lang_code, translation_prompt)

            # Store result
            results[lang_code] = {
                'language': lang_name,
                'success': True,
                'translation': translated_text,
                'native_name': lang_details['native']
            }

        except Exception as e:
            # Log error
            print(f"Error translating to {lang_name} ({lang_code}): {str(e)}")

            # Store error
            results[lang_code] = {
                'language': lang_name,
                'success': False,
                'error': str(e),
                'native_name': lang_details['native']
            }

    # Return all results
    return jsonify({
        'model': translation_model,
        'source_text': sample_text,
        'results': results
    })

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
