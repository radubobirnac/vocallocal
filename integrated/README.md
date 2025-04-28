# VocalLocal - Multilingual Speech-to-Text Transcription Tool

VocalLocal is a modern, responsive web application that provides accurate multilingual speech-to-text transcription. Using OpenAI's advanced audio models, it converts spoken language from microphone recordings or audio files into written text, with support for over 30 languages.

## Features

- **Real-time Transcription**: Record directly from your microphone and get immediate results
- **File Upload Support**: Process pre-recorded audio files in various formats (WAV, MP3, OGG, M4A, MP4, WEBM)
- **Multilingual Capabilities**: Support for 30+ languages with native language names
- **Flexible Model Selection**: Choose between faster or more accurate transcription models
- **Easy Copying**: One-click copying of transcription results
- **Bilingual Mode**: Facilitate conversations between speakers of different languages
- **Text-to-Speech Playback**: Listen to transcriptions and translations
- **Responsive Design**: Works well on both desktop and mobile devices
- **Modern UI**: Clean, intuitive user interface with a professional look and feel

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **API Integration**: OpenAI Speech-to-Text and Text-to-Speech APIs
- **Design**: Modern UI components with a clean, responsive layout

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Installation

1. Clone the repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Set your OpenAI API key:
   ```
   export OPENAI_API_KEY="your-api-key-here"
   ```
   Or create a `.env` file with:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

### Running the Application

Start the application:
```
python app.py
```

Navigate to `http://localhost:5000` in your web browser to use the application.

## Usage

### Basic Mode

1. Select your language from the dropdown menu
2. Choose a transcription model (fast or accurate)
3. Click the microphone button to start recording
4. Speak clearly into your microphone
5. Click the button again to stop recording
6. The transcription will appear in the text area
7. Use the copy button to copy the transcription to your clipboard
8. Use the play button to hear the transcription spoken back to you

### Bilingual Mode

1. Toggle "Bilingual Mode" on
2. Set up the language for each speaker
3. Each speaker can record, transcribe, and translate their speech
4. Translations will automatically appear for the other speaker
5. Enable "Read translations aloud" to automatically hear translations

### File Upload

1. Click "Choose File" to select an audio file from your device
2. Select the appropriate language and model
3. Click "Transcribe" to process the file
4. The transcription will appear in the text area

## Limitations

- Audio quality significantly affects transcription accuracy
- Background noise may impact results
- Maximum file size of 30MB per upload
- Some rare languages or dialects may have lower accuracy
- Recordings are limited to 25 minutes maximum duration
- Speaking in multiple languages at once may result in mixed results

## Privacy

Audio data is processed securely and is not stored permanently. Recordings are only kept temporarily during the transcription process and are deleted immediately afterward. Transcribed text remains in your browser and is not saved on our servers.

## License

This project is licensed under the MIT License.

---

Built with ❤️ using Flask and OpenAI's speech recognition technology.