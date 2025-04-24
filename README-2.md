# VocalLocal

VocalLocal is a speech-to-text web service that enables seamless transcription and translation across multiple languages.

## Current Features

### Speech-to-Text Transcription
- Upload audio files in various formats (WAV, MP3, OGG, M4A, MP4, WEBM)
- Transcription powered by OpenAI's speech recognition models
- Support for 30+ languages including English, Spanish, French, German, Chinese, Arabic, and more
- Maximum file size: 30MB
- Maximum audio duration: 25 minutes

### Bilingual Mode
- Enables two-way conversations between speakers of different languages
- Audio from one speaker is transcribed and then translated to the other speaker's language
- Helps overcome language barriers in real-time conversations

### Translation Services
- Text-to-text translation between supported languages
- High-quality translations using OpenAI's language models
- Maintains context and nuance across languages

## Upcoming Features

### Browser Language Detection
- Automatic detection of user's browser language
- Personalized experience based on detected language preferences

### Language Preference Settings
- Allow users to select their preferred interface language
- Full localization of UI elements (e.g., if Telugu is selected, all website text will appear in Telugu)
- Persistent language preferences across sessions

## Technical Implementation

VocalLocal is built as a Flask web application with the following components:
- Backend API for handling audio uploads and processing
- Integration with OpenAI's speech-to-text and language models
- Secure file handling with proper validation and cleanup
- Responsive frontend interface

## Getting Started

1. Set up environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SECRET_KEY`: Secret key for Flask session security

2. Install dependencies:
   ```
   pip install flask openai python-dotenv
   ```

3. Run the application:
   ```
   python app.py
   ```

4. Access the web interface at http://localhost:5000

## API Endpoints

- `/api/transcribe`: POST endpoint for audio transcription
- `/api/languages`: GET endpoint for supported languages list
- `/api/translate`: POST endpoint for text translation 