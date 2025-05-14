"""
Current TTS implementation extracted from app.py
This file is for reference only and is not meant to be executed.
"""

@app.route('/api/tts', methods=['POST'])
@login_required
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
