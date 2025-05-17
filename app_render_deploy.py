"""
VocalLocal Web Service - Flask API for speech-to-text (Render Deployment Version)
"""
import os
import sys
import time
import tempfile
import logging
from flask import Flask, request, jsonify, g
from werkzeug.utils import secure_filename
from functools import wraps
from services.audio_chunker import RobustChunker
from services.firebase_service import FirebaseService
from services.google_api_service import GoogleAPIService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)

# Set maximum content length to 150MB
app.config['MAX_CONTENT_LENGTH'] = 150 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Initialize services
firebase_service = FirebaseService.get_instance()
google_api_service = GoogleAPIService.get_instance()

def authenticate(f):
    """Decorator to authenticate requests using Firebase."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication in development mode
        if os.environ.get('FLASK_ENV') == 'development':
            g.user_id = 'dev_user'
            return f(*args, **kwargs)
            
        # Get the ID token from the Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "No valid authentication token provided"}), 401
            
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            # Verify the ID token
            decoded_token = firebase_service.verify_id_token(id_token)
            if not decoded_token:
                return jsonify({"error": "Invalid authentication token"}), 401
                
            # Store user ID in Flask's g object for the current request
            g.user_id = decoded_token['uid']
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify({"error": "Invalid authentication token"}), 401
            
    return decorated_function

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "firebase_initialized": firebase_service.initialized,
        "gemini_available": google_api_service.gemini_available,
        "speech_available": getattr(google_api_service, 'speech_available', False),
        "translate_available": getattr(google_api_service, 'translate_available', False)
    })

@app.route('/upload', methods=['POST'])
@authenticate
def upload_file():
    """
    Handle file upload with efficient streaming and chunking.
    Requires authentication.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    # Check file size before processing
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if file_size > app.config['MAX_CONTENT_LENGTH']:
        return jsonify({
            "status": "error",
            "stage": "size_check",
            "error": "file exceeds 150MB"
        }), 413
    
    # Save file to temporary location
    filename = secure_filename(file.filename)
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(temp_path)
    
    # Create output directory
    output_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"chunks_{filename}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Process the file with RobustChunker
    chunker = RobustChunker(
        input_path=temp_path,
        output_dir=output_dir,
        chunk_seconds=300  # 5 minutes per chunk
    )
    
    success, chunk_files, error = chunker.chunk_audio()
    
    if not success:
        return jsonify({
            "status": "error",
            "stage": "processing",
            "error": error
        }), 500
    
    # Upload chunks to Firebase Storage
    chunk_urls = []
    user_id = g.user_id
    file_id = f"{user_id}_{int(time.time())}"
    
    for chunk_file in chunk_files:
        chunk_name = os.path.basename(chunk_file)
        storage_path = f"users/{user_id}/audio_chunks/{file_id}/{chunk_name}"
        url = firebase_service.upload_to_storage(chunk_file, storage_path)
        if url:
            chunk_urls.append({"name": chunk_name, "url": url})
    
    # Store metadata in Firestore
    metadata = {
        "original_filename": filename,
        "file_size": file_size,
        "chunk_count": len(chunk_files),
        "chunks": chunk_urls,
        "status": "chunked"
    }
    
    firebase_service.store_file_metadata(user_id, file_id, metadata)
    
    # Clean up temporary files
    try:
        os.remove(temp_path)
        for chunk_file in chunk_files:
            os.remove(chunk_file)
        os.rmdir(output_dir)
    except Exception as e:
        logger.warning(f"Cleanup error: {str(e)}")
    
    return jsonify({
        "status": "ok",
        "file_id": file_id,
        "chunks": [c["name"] for c in chunk_urls],
        "chunk_count": len(chunk_urls)
    })

@app.route('/transcribe/<file_id>', methods=['POST'])
@authenticate
def transcribe_file(file_id):
    """
    Transcribe an uploaded file using Google APIs.
    Requires authentication.
    """
    # Get transcription parameters
    data = request.json or {}
    language = data.get('language', 'en')
    model = data.get('model', 'gemini')  # 'gemini' or 'speech-to-text'
    
    # Get file metadata from Firestore
    user_id = g.user_id
    metadata = firebase_service.get_file_metadata(file_id)
    
    if not metadata:
        return jsonify({"error": "File not found"}), 404
        
    # Check if this is the user's file
    if metadata.get('user_id') != user_id:
        return jsonify({"error": "Unauthorized access to file"}), 403
    
    # Check if already transcribed
    if metadata.get('status') == 'transcribed':
        return jsonify({
            "status": "ok",
            "transcription": metadata.get('transcription', ''),
            "already_transcribed": True
        })
    
    # Download chunks for transcription
    chunks = metadata.get('chunks', [])
    transcriptions = []
    
    for chunk in chunks:
        # Download chunk from Firebase Storage
        blob = firebase_service.bucket.blob(f"users/{user_id}/audio_chunks/{file_id}/{chunk['name']}")
        temp_chunk_path = os.path.join(app.config['UPLOAD_FOLDER'], chunk['name'])
        blob.download_to_filename(temp_chunk_path)
        
        # Transcribe the chunk
        if model == 'gemini':
            transcription = google_api_service.transcribe_with_gemini(temp_chunk_path, language)
        else:
            transcription = google_api_service.transcribe_audio(temp_chunk_path, language)
            
        if transcription:
            transcriptions.append(transcription)
            
        # Clean up
        try:
            os.remove(temp_chunk_path)
        except:
            pass
    
    # Combine transcriptions
    full_transcription = " ".join(transcriptions)
    
    # Update metadata in Firestore
    firebase_service.update_file_metadata(file_id, {
        "status": "transcribed",
        "transcription": full_transcription,
        "transcription_model": model,
        "transcription_language": language
    })
    
    return jsonify({
        "status": "ok",
        "transcription": full_transcription
    })

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='VocalLocal Web Service')
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 5000)),
                        help='Port to run the server on')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Host to run the server on')
    parser.add_argument('--debug', action='store_true',
                        help='Run in debug mode')
    
    args = parser.parse_args()
    
    app.run(debug=args.debug, host=args.host, port=args.port)
