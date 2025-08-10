/**
 * Bilingual Conversation Mode - Enhanced UI Implementation
 * Handles the new "Quick Conversation" interface with Hold to Record functionality
 */

class BilingualConversation {
  constructor() {
    this.isRecording = false;
    this.recording = null;
    this.recordingStartTime = null;
    this.timerInterval = null;
    this.keyPressCount = 0;
    this.keyPressTimer = null;
    this.lastTranscription = '';
    
    this.initializeElements();
    this.setupEventListeners();
    this.populateLanguageDropdowns();
  }

  initializeElements() {
    // Main elements
    this.holdRecordBtn = document.getElementById('bilingual-hold-record-btn');
    this.manualRecordBtn = document.getElementById('bilingual-manual-record');
    this.translateBtn = document.getElementById('bilingual-translate-btn');
    this.uploadBtn = document.getElementById('bilingual-upload-btn');
    this.clearBtn = document.getElementById('bilingual-clear-results');
    
    // Language selectors
    this.fromLanguageSelect = document.getElementById('bilingual-from-language');
    this.toLanguageSelect = document.getElementById('bilingual-to-language');
    
    // Timer and display elements
    this.timer = document.getElementById('bilingual-recording-timer');
    this.originalLanguageDisplay = document.getElementById('original-language-display');
    this.translationLanguageDisplay = document.getElementById('translation-language-display');
    
    // Result elements
    this.originalTextArea = document.getElementById('bilingual-original-text');
    this.translationTextArea = document.getElementById('bilingual-translation-text');
    
    // Control buttons
    this.playOriginalBtn = document.getElementById('play-original');
    this.stopOriginalBtn = document.getElementById('stop-original');
    this.copyOriginalBtn = document.getElementById('copy-original');
    this.playTranslationBtn = document.getElementById('play-translation');
    this.stopTranslationBtn = document.getElementById('stop-translation');
    this.copyTranslationBtn = document.getElementById('copy-translation');
    
    // File input
    this.fileInput = document.getElementById('bilingual-file-input');
  }

  setupEventListeners() {
    // Hold to Record button
    if (this.holdRecordBtn) {
      this.holdRecordBtn.addEventListener('mousedown', () => {
        console.log('Hold button mousedown event');
        this.startHoldRecording();
      });
      this.holdRecordBtn.addEventListener('mouseup', () => {
        console.log('Hold button mouseup event');
        this.stopHoldRecording();
      });
      this.holdRecordBtn.addEventListener('mouseleave', () => {
        console.log('Hold button mouseleave event');
        this.stopHoldRecording();
      });

      // Touch events for mobile
      this.holdRecordBtn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        console.log('Hold button touchstart event');
        this.startHoldRecording();
      });
      this.holdRecordBtn.addEventListener('touchend', (e) => {
        e.preventDefault();
        console.log('Hold button touchend event');
        this.stopHoldRecording();
      });
    }

    // Manual Record button (toggle)
    if (this.manualRecordBtn) {
      this.manualRecordBtn.addEventListener('click', () => this.toggleManualRecording());
    }

    // Translate button
    if (this.translateBtn) {
      this.translateBtn.addEventListener('click', () => this.translateText());
    }

    // Upload button
    if (this.uploadBtn) {
      this.uploadBtn.addEventListener('click', () => this.fileInput?.click());
    }

    // Clear results button
    if (this.clearBtn) {
      this.clearBtn.addEventListener('click', () => this.clearResults());
    }

    // File input
    if (this.fileInput) {
      this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
    }

    // Language change listeners
    if (this.fromLanguageSelect) {
      this.fromLanguageSelect.addEventListener('change', () => this.updateLanguageDisplays());
    }
    if (this.toLanguageSelect) {
      this.toLanguageSelect.addEventListener('change', () => this.updateLanguageDisplays());
    }

    // Copy buttons
    if (this.copyOriginalBtn) {
      this.copyOriginalBtn.addEventListener('click', () => this.copyToClipboard(this.originalTextArea.value));
    }
    if (this.copyTranslationBtn) {
      this.copyTranslationBtn.addEventListener('click', () => this.copyToClipboard(this.translationTextArea.value));
    }

    // Double Enter key listener
    document.addEventListener('keydown', (e) => this.handleKeyPress(e));

    // Play/Stop buttons (will integrate with existing TTS system)
    if (this.playOriginalBtn) {
      this.playOriginalBtn.addEventListener('click', () => this.playText('bilingual-original-text'));
    }
    if (this.stopOriginalBtn) {
      this.stopOriginalBtn.addEventListener('click', () => this.stopText('bilingual-original-text'));
    }
    if (this.playTranslationBtn) {
      this.playTranslationBtn.addEventListener('click', () => this.playText('bilingual-translation-text'));
    }
    if (this.stopTranslationBtn) {
      this.stopTranslationBtn.addEventListener('click', () => this.stopText('bilingual-translation-text'));
    }
  }

  async startHoldRecording() {
    if (this.isRecording) return;
    
    try {
      this.isRecording = true;
      this.holdRecordBtn.classList.add('recording');
      this.holdRecordBtn.innerHTML = '<i class="fas fa-stop"></i><span>Recording...</span>';
      
      this.recordingStartTime = Date.now();
      this.startTimer();
      
      // Start recording using existing recording infrastructure
      this.recording = await window.startRecording({
        recordButton: this.holdRecordBtn
      });

      // Set up event listener for when recording stops
      if (this.recording && this.recording.mediaRecorder) {
        this.recording.mediaRecorder.addEventListener('stop', () => {
          console.log('MediaRecorder stopped event fired');
          // Don't auto-process here for hold recording - it's handled in stopHoldRecording
        });
      }

      console.log('Hold recording started');
    } catch (error) {
      console.error('Error starting hold recording:', error);
      this.resetRecordingState();
      window.showStatus?.('Failed to start recording. Please check microphone permissions.', 'error');
    }
  }

  async stopHoldRecording() {
    console.log('stopHoldRecording called, isRecording:', this.isRecording);
    if (!this.isRecording) return;

    this.isRecording = false;
    this.stopTimer();
    this.resetRecordingButton();

    if (this.recording) {
      try {
        // Stop the recording and automatically process
        console.log('Stopping MediaRecorder...');
        this.recording.mediaRecorder.stop();

        // CRITICAL: Stop all tracks in the stream to clear browser recording indicator
        if (this.recording.stream) {
          console.log('Stopping media stream tracks...');
          this.recording.stream.getTracks().forEach(track => {
            track.stop();
            console.log('Stopped track:', track.kind);
          });
        }

        console.log('Hold recording stopped, scheduling processing...');

        // Wait for recording to be processed and then transcribe + translate
        setTimeout(async () => {
          console.log('Processing timeout triggered for hold recording');
          await this.processRecordingAndTranslate();
        }, 500);
      } catch (error) {
        console.error('Error stopping recording:', error);
      }
    } else {
      console.error('No recording object available to stop');
    }
  }

  async toggleManualRecording() {
    if (this.isRecording) {
      await this.stopManualRecording();
    } else {
      await this.startManualRecording();
    }
  }

  async startManualRecording() {
    try {
      this.isRecording = true;
      this.manualRecordBtn.classList.add('recording');
      this.manualRecordBtn.innerHTML = '<i class="fas fa-stop"></i><span>Stop Recording</span>';
      
      this.recordingStartTime = Date.now();
      this.startTimer();
      
      this.recording = await window.startRecording({
        recordButton: this.manualRecordBtn
      });

      // Set up event listener for when recording stops
      if (this.recording && this.recording.mediaRecorder) {
        this.recording.mediaRecorder.addEventListener('stop', () => {
          console.log('MediaRecorder stopped event fired for manual recording');
          // Don't auto-process here - it's handled in stopManualRecording
        });
      }

      console.log('Manual recording started');
    } catch (error) {
      console.error('Error starting manual recording:', error);
      this.resetRecordingState();
      window.showStatus?.('Failed to start recording. Please check microphone permissions.', 'error');
    }
  }

  async stopManualRecording() {
    if (!this.isRecording) return;

    this.isRecording = false;
    this.stopTimer();
    this.resetManualRecordButton();

    if (this.recording) {
      try {
        this.recording.mediaRecorder.stop();

        // CRITICAL: Stop all tracks in the stream to clear browser recording indicator
        if (this.recording.stream) {
          console.log('Stopping media stream tracks for manual recording...');
          this.recording.stream.getTracks().forEach(track => {
            track.stop();
            console.log('Stopped track:', track.kind);
          });
        }

        console.log('Manual recording stopped');

        // Wait for recording to be processed and then transcribe + translate
        setTimeout(async () => {
          await this.processRecordingAndTranslate();
        }, 500);
      } catch (error) {
        console.error('Error stopping recording:', error);
      }
    }
  }

  handleKeyPress(event) {
    // Only handle Enter key when bilingual mode is active and we're recording
    const bilingualMode = document.getElementById('bilingual-mode-content');
    const bilingualModeToggle = document.getElementById('bilingual-mode');

    // Check if bilingual mode is active
    const isBilingualModeActive = bilingualModeToggle && bilingualModeToggle.checked;
    if (!isBilingualModeActive || !this.isRecording) return;

    if (event.key === 'Enter') {
      this.keyPressCount++;
      console.log(`Enter key pressed, count: ${this.keyPressCount}`);

      // Clear previous timer
      if (this.keyPressTimer) {
        clearTimeout(this.keyPressTimer);
      }

      // Set timer to reset count after 500ms
      this.keyPressTimer = setTimeout(() => {
        this.keyPressCount = 0;
      }, 500);

      // If double Enter detected and recording
      if (this.keyPressCount === 2) {
        event.preventDefault();
        console.log('Double Enter detected, stopping recording and processing...');
        this.stopRecordingAndProcess();
        this.keyPressCount = 0;
      }
    }
  }

  async stopRecordingAndProcess() {
    if (!this.isRecording) return;

    // Stop recording first
    if (this.recording) {
      this.recording.mediaRecorder.stop();

      // CRITICAL: Stop all tracks in the stream to clear browser recording indicator
      if (this.recording.stream) {
        console.log('Stopping media stream tracks (double Enter)...');
        this.recording.stream.getTracks().forEach(track => {
          track.stop();
          console.log('Stopped track:', track.kind);
        });
      }
    }

    this.isRecording = false;
    this.stopTimer();
    this.resetRecordingButton();
    this.resetManualRecordButton();

    // Wait for recording to be processed and then transcribe + translate
    setTimeout(async () => {
      await this.processRecordingAndTranslate();
    }, 500);
  }

  async processRecordingAndTranslate() {
    console.log('processRecordingAndTranslate called');
    console.log('Recording object:', this.recording);
    console.log('Audio chunks length:', this.recording?.audioChunks?.length);

    if (!this.recording || !this.recording.audioChunks.length) {
      console.error('No recording or audio chunks available');
      window.showStatus?.('No audio recorded', 'error');
      return;
    }

    try {
      window.showStatus?.('Processing audio...', 'info');

      // Create form data for transcription
      const formData = new FormData();
      formData.append('language', this.fromLanguageSelect.value);
      formData.append('model', this.getSelectedTranscriptionModel());

      console.log('Form data prepared:', {
        language: this.fromLanguageSelect.value,
        model: this.getSelectedTranscriptionModel(),
        audioChunksCount: this.recording.audioChunks.length,
        mimeType: this.recording.mediaRecorder.mimeType
      });

      // Process audio with smart routing
      const result = await window.processAudioWithSmartRouting(
        this.recording.audioChunks,
        this.recording.mediaRecorder.mimeType,
        formData
      );

      console.log('Transcription result:', result);

      if (result.text) {
        this.lastTranscription = result.text;
        this.originalTextArea.value = result.text;
        window.showStatus?.('Transcription complete! Translating...', 'success');

        // Automatically translate
        await this.translateText();
      } else {
        console.error('No text in transcription result');
        window.showStatus?.('Transcription failed. Please try again.', 'error');
      }
    } catch (error) {
      console.error('Error processing recording:', error);
      window.showStatus?.('Error processing audio. Please try again.', 'error');
    }
  }

  async translateText() {
    const textToTranslate = this.originalTextArea.value.trim();
    if (!textToTranslate) {
      window.showStatus?.('No text to translate', 'error');
      return;
    }

    try {
      window.showStatus?.('Translating...', 'info');

      // Get the selected translation model (similar to existing code)
      const translationModelSelect = document.getElementById('translation-model-select');
      const translationModel = translationModelSelect ? translationModelSelect.value : 'gemini-2.0-flash-lite';

      const response = await fetch('/api/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: textToTranslate,
          target_language: this.toLanguageSelect.value,
          translation_model: translationModel
        })
      });

      if (!response.ok) {
        throw new Error(`Translation failed: ${response.status}`);
      }

      const result = await response.json();

      // Use the correct response property (result.text, not result.translation)
      if (result.text) {
        this.translationTextArea.value = result.text;
        window.showStatus?.('Translation complete!', 'success');

        // Log performance metrics if available
        if (result.performance) {
          console.log(`Translation performance: ${result.performance.time_seconds}s, ${result.performance.characters_per_second} chars/s`);
        }
      } else {
        window.showStatus?.('Translation failed. Please try again.', 'error');
      }
    } catch (error) {
      console.error('Error translating text:', error);
      window.showStatus?.('Translation error. Please try again.', 'error');
    }
  }

  startTimer() {
    this.timerInterval = setInterval(() => {
      const elapsed = (Date.now() - this.recordingStartTime) / 1000;
      const minutes = Math.floor(elapsed / 60);
      const seconds = Math.floor(elapsed % 60);
      const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      
      if (this.timer) {
        this.timer.textContent = timeString;
      }
    }, 1000);
  }

  stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  resetRecordingState() {
    this.isRecording = false;

    // Clean up media streams if they exist
    if (this.recording && this.recording.stream) {
      console.log('Cleaning up media stream in resetRecordingState...');
      this.recording.stream.getTracks().forEach(track => {
        track.stop();
        console.log('Stopped track in reset:', track.kind);
      });
    }

    this.recording = null;
    this.stopTimer();
    this.resetRecordingButton();
    this.resetManualRecordButton();

    if (this.timer) {
      this.timer.textContent = '00:00';
    }
  }

  resetRecordingButton() {
    if (this.holdRecordBtn) {
      this.holdRecordBtn.classList.remove('recording');
      this.holdRecordBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Hold to Record</span>';
    }
  }

  resetManualRecordButton() {
    if (this.manualRecordBtn) {
      this.manualRecordBtn.classList.remove('recording');
      this.manualRecordBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Manual Record</span>';
    }
  }

  populateLanguageDropdowns() {
    // Use existing language data from the main script
    if (window.languages) {
      this.populateSelect(this.fromLanguageSelect, window.languages);
      this.populateSelect(this.toLanguageSelect, window.languages);

      // Set default values
      if (this.fromLanguageSelect) {
        this.fromLanguageSelect.value = 'en';
      }
      if (this.toLanguageSelect) {
        this.toLanguageSelect.value = 'es';
      }

      this.updateLanguageDisplays();
    }
  }

  populateSelect(selectElement, languages) {
    if (!selectElement || !languages) return;

    selectElement.innerHTML = '';
    languages.forEach(lang => {
      const option = document.createElement('option');
      option.value = lang.code;
      option.textContent = `${lang.name} (${lang.native})`;
      selectElement.appendChild(option);
    });
  }

  updateLanguageDisplays() {
    if (this.fromLanguageSelect && this.originalLanguageDisplay) {
      const selectedOption = this.fromLanguageSelect.selectedOptions[0];
      if (selectedOption) {
        this.originalLanguageDisplay.textContent = selectedOption.textContent;
      }
    }

    if (this.toLanguageSelect && this.translationLanguageDisplay) {
      const selectedOption = this.toLanguageSelect.selectedOptions[0];
      if (selectedOption) {
        this.translationLanguageDisplay.textContent = selectedOption.textContent;
      }
    }
  }

  getSelectedTranscriptionModel() {
    // Get the selected transcription model from the main interface
    const modelSelect = document.getElementById('global-transcription-model');
    return modelSelect ? modelSelect.value : 'gemini-2.0-flash-lite';
  }

  async handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    try {
      window.showStatus?.(`Processing uploaded file: ${file.name}`, 'info');

      const formData = new FormData();
      formData.append('file', file);
      formData.append('language', this.fromLanguageSelect.value);
      formData.append('model', this.getSelectedTranscriptionModel());

      const response = await fetch('/api/transcribe', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (result.text) {
        this.originalTextArea.value = result.text;
        window.showStatus?.('File transcription complete!', 'success');

        // Automatically translate
        await this.translateText();
      } else {
        window.showStatus?.('File transcription failed. Please try again.', 'error');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      window.showStatus?.('File upload error. Please try again.', 'error');
    }

    // Reset file input
    event.target.value = '';
  }

  clearResults() {
    if (this.originalTextArea) {
      this.originalTextArea.value = '';
    }
    if (this.translationTextArea) {
      this.translationTextArea.value = '';
    }
    if (this.timer) {
      this.timer.textContent = '00:00';
    }

    this.lastTranscription = '';
    window.showStatus?.('Results cleared', 'info');
  }

  async copyToClipboard(text) {
    if (!text) {
      window.showStatus?.('No text to copy', 'error');
      return;
    }

    try {
      await navigator.clipboard.writeText(text);
      window.showStatus?.('Text copied to clipboard', 'success');
    } catch (error) {
      console.error('Error copying to clipboard:', error);
      window.showStatus?.('Failed to copy text', 'error');
    }
  }

  playText(elementId) {
    // Integrate with existing TTS system
    const textArea = document.getElementById(elementId);
    if (textArea && textArea.value.trim() && window.speakText) {
      // Determine language based on which text area is being played
      let langCode = 'en';
      if (elementId === 'bilingual-translation-text') {
        langCode = this.toLanguageSelect ? this.toLanguageSelect.value : 'es';
      } else if (elementId === 'bilingual-original-text') {
        langCode = this.fromLanguageSelect ? this.fromLanguageSelect.value : 'en';
      }

      window.speakText(elementId, textArea.value, langCode);
    } else {
      console.warn('TTS system not available or no text to play');
    }
  }

  stopText(elementId) {
    // Stop TTS playback
    if (window.stopSpeakText) {
      window.stopSpeakText(elementId);
    } else {
      console.warn('TTS stop function not available');
    }
  }
}

// Initialize bilingual conversation when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Only initialize if bilingual mode elements exist
  const bilingualModeContent = document.getElementById('bilingual-mode-content');
  if (bilingualModeContent) {
    window.bilingualConversation = new BilingualConversation();
    console.log('Bilingual Conversation mode initialized');
  }
});
