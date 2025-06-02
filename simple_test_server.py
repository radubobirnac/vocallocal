#!/usr/bin/env python3
"""
Simple test server to test the chunk transcription endpoint
"""

from flask import Flask, request, jsonify
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({'message': 'Simple test server is running', 'status': 'ok'})

@app.route('/api/transcribe_chunk', methods=['POST'])
def test_transcribe_chunk():
    """Test endpoint for transcribe_chunk"""
    try:
        # Check if file is present
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Get parameters
        language = request.form.get('language', 'en')
        model = request.form.get('model', 'gemini-2.0-flash-lite')
        chunk_number = request.form.get('chunk_number', '0')
        element_id = request.form.get('element_id', 'basic-transcript')

        # Read audio data
        audio_data = audio_file.read()
        
        print(f"Received chunk {chunk_number}: {len(audio_data)} bytes, language: {language}, model: {model}")

        # For testing, just return a mock response
        return jsonify({
            'text': f'Mock transcription for chunk {chunk_number} ({len(audio_data)} bytes)',
            'chunk_number': int(chunk_number),
            'element_id': element_id,
            'status': 'completed'
        })

    except Exception as e:
        print(f"Error processing chunk: {str(e)}")
        return jsonify({
            'error': str(e),
            'chunk_number': int(request.form.get('chunk_number', '0')),
            'status': 'error'
        }), 500

if __name__ == '__main__':
    print("Starting simple test server on port 5002...")
    app.run(debug=True, port=5002, host='0.0.0.0')
