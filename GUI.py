"""
VocalLocal - Speech-to-Text and Translation Application
with GUI Interface
"""

import os
import io
import time
import datetime
import wave
import sys
import threading
import openai
import numpy as np
import sounddevice as sd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, QTextEdit, 
                           QLabel, QComboBox, QVBoxLayout, QHBoxLayout, QGroupBox,
                           QStatusBar, QMessageBox, QFileDialog, QLineEdit, QInputDialog,
                           QRadioButton, QButtonGroup, QProgressBar, QSpinBox)
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QIcon
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration constants
API_KEY = os.getenv('OPENAI_API_KEY')
if not API_KEY:
    raise ValueError("OpenAI API key not found. Please set it in your .env file.")

SAMPLE_RATE = 44100
CHANNELS = 1
MAX_RECORD_TIME = 120  # seconds
TRANSCRIPTS_DIR = "transcripts"

# Dictionary of supported languages with their codes
SUPPORTED_LANGUAGES = {
    "Telugu": "te",
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

# Signal class for inter-thread communication
class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)

# Audio Recorder class
class AudioRecorder(QObject):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self.recording = False
        self.audio_data = []
        self.start_time = 0
        self.timer = None
        self.max_duration = MAX_RECORD_TIME

    def start_recording(self, duration=None):
        """Start recording audio"""
        self.audio_data = []
        self.recording = True
        self.start_time = time.time()
        
        if duration:
            self.max_duration = duration
        else:
            self.max_duration = MAX_RECORD_TIME
            
        # Start a thread to record audio
        threading.Thread(target=self._record_audio, daemon=True).start()
        
    def stop_recording(self):
        """Stop recording audio"""
        self.recording = False
        
    def _record_audio(self):
        """Record audio data in a separate thread"""
        try:
            # Start recording
            self.signals.status.emit("Recording started")
            
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=self._audio_callback):
                while self.recording and (time.time() - self.start_time) < self.max_duration:
                    # Update progress every 100ms
                    elapsed = time.time() - self.start_time
                    progress = int((elapsed / self.max_duration) * 100)
                    self.signals.progress.emit(progress)
                    self.signals.status.emit(f"Recording: {elapsed:.1f}s / {self.max_duration}s")
                    time.sleep(0.1)
            
            # Create WAV data from recorded audio
            if self.audio_data:
                wav_data = self._create_wav_data()
                self.signals.finished.emit(wav_data)
                self.signals.status.emit("Recording finished")
            else:
                self.signals.error.emit("No audio data recorded")
                
        except Exception as e:
            self.signals.error.emit(f"Recording error: {str(e)}")
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio input"""
        if self.recording:
            # Convert to int16 and append to audio data
            audio_chunk = (indata * 32767).astype(np.int16)
            self.audio_data.append(audio_chunk.copy())
    
    def _create_wav_data(self):
        """Convert recorded audio to WAV format"""
        if not self.audio_data:
            return None
            
        # Combine all audio chunks
        audio_data_combined = np.vstack(self.audio_data)
        
        # Convert to bytes
        byte_io = io.BytesIO()
        with wave.open(byte_io, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # 2 bytes for int16
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data_combined.tobytes())
        
        # Return WAV data as bytes
        byte_io.seek(0)
        return byte_io.read()

# API Wrapper class
class OpenAIAPI(QObject):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self.initialize_api()
        
    def initialize_api(self):
        """Initialize OpenAI API"""
        openai.api_key = API_KEY
        os.environ["OPENAI_API_KEY"] = API_KEY
        
    def transcribe_audio(self, audio_data, model="gpt-4o-mini-transcribe", language="en"):
        """Transcribe audio using OpenAI API in a separate thread"""
        # Start a thread to transcribe audio
        threading.Thread(
            target=self._transcribe_thread, 
            args=(audio_data, model, language),
            daemon=True
        ).start()
        
    def _transcribe_thread(self, audio_data, model, language):
        """Thread function for transcription"""
        try:
            self.signals.status.emit(f"Transcribing with {model}...")
            
            # Prepare audio file for API
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"
            
            # Send to API with specified language
            response = openai.audio.transcriptions.create(
                model=model,
                file=audio_file,
                language=language
            )
            
            # Return transcription
            result = {
                "text": response.text,
                "model": model,
                "language": language
            }
            self.signals.finished.emit(result)
            self.signals.status.emit(f"Transcription with {model} completed")
            
        except Exception as e:
            self.signals.error.emit(f"Error transcribing with {model}: {str(e)}")
    
    def translate_text(self, text, target_language):
        """Translate text to target language using OpenAI API in a separate thread"""
        # Start a thread to translate text
        threading.Thread(
            target=self._translate_thread, 
            args=(text, target_language),
            daemon=True
        ).start()
    
    def _translate_thread(self, text, target_language):
        """Thread function for translation"""
        try:
            language_name = next((name for name, code in SUPPORTED_LANGUAGES.items() 
                                if code == target_language), target_language)
            
            self.signals.status.emit(f"Translating to {language_name}...")
            
            # Call OpenAI API for translation
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are a translator. Translate the text to {language_name}."},
                    {"role": "user", "content": text}
                ]
            )
            
            # Return translation
            result = {
                "text": response.choices[0].message.content,
                "target_language": target_language
            }
            self.signals.finished.emit(result)
            self.signals.status.emit(f"Translation to {language_name} completed")
            
        except Exception as e:
            self.signals.error.emit(f"Error translating: {str(e)}")

# Main application window
class VocalLocalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recorder = AudioRecorder()
        self.api = OpenAIAPI()
        
        # Connect signals
        self.recorder.signals.finished.connect(self.on_recording_finished)
        self.recorder.signals.error.connect(self.show_error)
        self.recorder.signals.progress.connect(self.update_progress)
        self.recorder.signals.status.connect(self.update_status)
        
        self.api.signals.finished.connect(self.on_api_finished)
        self.api.signals.error.connect(self.show_error)
        self.api.signals.status.connect(self.update_status)
        
        # App state
        self.recorded_audio = None
        self.transcription = None
        self.translation = None
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("VocalLocal - Speech to Text & Translation")
        self.setMinimumSize(800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("VocalLocal")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Description
        description = QLabel("Speech-to-Text and Translation App")
        description.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(description)
        
        # Language selection
        language_group = QGroupBox("Language Settings")
        language_layout = QVBoxLayout()
        
        # Input language
        input_lang_layout = QHBoxLayout()
        input_lang_layout.addWidget(QLabel("Input Language:"))
        self.input_language = QComboBox()
        for lang in sorted(SUPPORTED_LANGUAGES.keys()):
            self.input_language.addItem(lang)
        self.input_language.setCurrentText("English")  # Default
        input_lang_layout.addWidget(self.input_language)
        language_layout.addLayout(input_lang_layout)
        
        # Translation language (only shown when translation is enabled)
        self.translate_group = QGroupBox("Translation")
        self.translate_group.setCheckable(True)
        self.translate_group.setChecked(False)
        translate_layout = QHBoxLayout()
        translate_layout.addWidget(QLabel("Translate to:"))
        self.translate_language = QComboBox()
        for lang in sorted(SUPPORTED_LANGUAGES.keys()):
            self.translate_language.addItem(lang)
        translate_layout.addWidget(self.translate_language)
        self.translate_group.setLayout(translate_layout)
        language_layout.addWidget(self.translate_group)
        
        language_group.setLayout(language_layout)
        main_layout.addWidget(language_group)
        
        # Model selection
        model_group = QGroupBox("Transcription Model")
        model_layout = QHBoxLayout()
        
        self.model_buttons = QButtonGroup()
        self.mini_model = QRadioButton("gpt-4o-mini-transcribe (Faster)")
        self.full_model = QRadioButton("gpt-4o-transcribe (Better Quality)")
        self.mini_model.setChecked(True)
        self.model_buttons.addButton(self.mini_model)
        self.model_buttons.addButton(self.full_model)
        
        model_layout.addWidget(self.mini_model)
        model_layout.addWidget(self.full_model)
        model_group.setLayout(model_layout)
        main_layout.addWidget(model_group)
        
        # Recording controls
        recording_group = QGroupBox("Recording")
        recording_layout = QVBoxLayout()
        
        # Duration options
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (seconds):"))
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, MAX_RECORD_TIME)
        self.duration_input.setValue(10)
        duration_layout.addWidget(self.duration_input)
        recording_layout.addLayout(duration_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        recording_layout.addWidget(self.progress_bar)
        
        # Record buttons
        button_layout = QHBoxLayout()
        
        self.record_button = QPushButton("Record")
        self.record_button.clicked.connect(self.start_recording)
        button_layout.addWidget(self.record_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        recording_layout.addLayout(button_layout)
        recording_group.setLayout(recording_layout)
        main_layout.addWidget(recording_group)
        
        # Processing buttons
        processing_layout = QHBoxLayout()
        
        self.transcribe_button = QPushButton("Transcribe Audio")
        self.transcribe_button.clicked.connect(self.transcribe_audio)
        self.transcribe_button.setEnabled(False)
        processing_layout.addWidget(self.transcribe_button)
        
        self.translate_button = QPushButton("Translate Transcription")
        self.translate_button.clicked.connect(self.translate_text)
        self.translate_button.setEnabled(False)
        processing_layout.addWidget(self.translate_button)
        
        main_layout.addLayout(processing_layout)
        
        # Results area
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        
        # Transcription result
        transcription_layout = QVBoxLayout()
        transcription_layout.addWidget(QLabel("Transcription:"))
        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        transcription_layout.addWidget(self.transcription_text)
        results_layout.addLayout(transcription_layout)
        
        # Translation result
        translation_layout = QVBoxLayout()
        translation_layout.addWidget(QLabel("Translation:"))
        self.translation_text = QTextEdit()
        self.translation_text.setReadOnly(True)
        translation_layout.addWidget(self.translation_text)
        results_layout.addLayout(translation_layout)
        
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)
        
        # Save buttons
        save_layout = QHBoxLayout()
        
        self.save_transcription_button = QPushButton("Save Transcription")
        self.save_transcription_button.clicked.connect(lambda: self.save_text(self.transcription_text.toPlainText(), "transcription"))
        self.save_transcription_button.setEnabled(False)
        save_layout.addWidget(self.save_transcription_button)
        
        self.save_translation_button = QPushButton("Save Translation")
        self.save_translation_button.clicked.connect(lambda: self.save_text(self.translation_text.toPlainText(), "translation"))
        self.save_translation_button.setEnabled(False)
        save_layout.addWidget(self.save_translation_button)
        
        main_layout.addLayout(save_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create transcripts directory if it doesn't exist
        if not os.path.exists(TRANSCRIPTS_DIR):
            os.makedirs(TRANSCRIPTS_DIR)
    
    def start_recording(self):
        """Start recording audio"""
        duration = self.duration_input.value()
        self.progress_bar.setValue(0)
        self.record_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.transcribe_button.setEnabled(False)
        self.translate_button.setEnabled(False)
        self.save_transcription_button.setEnabled(False)
        self.save_translation_button.setEnabled(False)
        
        # Clear results
        self.transcription_text.clear()
        self.translation_text.clear()
        
        # Start recording
        self.recorder.start_recording(duration)
    
    def stop_recording(self):
        """Stop recording audio"""
        self.recorder.stop_recording()
        self.record_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def on_recording_finished(self, wav_data):
        """Handle recording finished signal"""
        self.recorded_audio = wav_data
        self.record_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.transcribe_button.setEnabled(True)
        self.update_status("Recording completed. Ready to transcribe.")
    
    def transcribe_audio(self):
        """Transcribe the recorded audio"""
        if not self.recorded_audio:
            self.show_error("No audio recorded")
            return
        
        # Get selected language
        lang_name = self.input_language.currentText()
        lang_code = SUPPORTED_LANGUAGES[lang_name]
        
        # Get selected model
        model = "gpt-4o-mini-transcribe" if self.mini_model.isChecked() else "gpt-4o-transcribe"
        
        # Disable buttons while processing
        self.transcribe_button.setEnabled(False)
        self.translate_button.setEnabled(False)
        
        # Clear previous results
        self.transcription_text.clear()
        self.translation_text.clear()
        
        # Start transcription
        self.api.transcribe_audio(self.recorded_audio, model, lang_code)
    
    def translate_text(self):
        """Translate the transcribed text"""
        text = self.transcription_text.toPlainText()
        if not text:
            self.show_error("No transcription to translate")
            return
        
        # Get selected target language
        target_lang_name = self.translate_language.currentText()
        target_lang_code = SUPPORTED_LANGUAGES[target_lang_name]
        
        # Disable buttons while processing
        self.translate_button.setEnabled(False)
        
        # Clear previous translation
        self.translation_text.clear()
        
        # Start translation
        self.api.translate_text(text, target_lang_code)
    
    def on_api_finished(self, result):
        """Handle API response"""
        if "model" in result:  # Transcription result
            self.transcription = result["text"]
            self.transcription_text.setText(result["text"])
            self.save_transcription_button.setEnabled(True)
            
            # Enable translation button if translation is enabled
            if self.translate_group.isChecked():
                self.translate_button.setEnabled(True)
                # Auto-translate if enabled
                self.translate_text()
            
            # Re-enable transcribe button
            self.transcribe_button.setEnabled(True)
            
        elif "target_language" in result:  # Translation result
            self.translation = result["text"]
            self.translation_text.setText(result["text"])
            self.save_translation_button.setEnabled(True)
            self.translate_button.setEnabled(True)
    
    def save_text(self, text, text_type):
        """Save text to file"""
        if not text:
            self.show_error(f"No {text_type} to save")
            return
        
        # Generate filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"{TRANSCRIPTS_DIR}/{text_type}_{timestamp}.txt"
        
        # Ask for filename
        filename, _ = QFileDialog.getSaveFileName(
            self, f"Save {text_type.capitalize()}", 
            default_filename, 
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(text)
                self.update_status(f"{text_type.capitalize()} saved to {filename}")
            except Exception as e:
                self.show_error(f"Error saving file: {str(e)}")
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        """Update status bar"""
        self.status_bar.showMessage(message)
    
    def show_error(self, message):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)
        self.update_status(f"Error: {message}")

# Application entry point
def main():
    app = QApplication(sys.argv)
    window = VocalLocalApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()