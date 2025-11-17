/**
 * Bilingual Conversation Mode - Enhanced UI Implementation
 * Handles the new "Quick Conversation" interface with Hold to Record functionality
 * Updated: 2025-09-20 12:13 - Added comprehensive debugging
 */

// Prevent class redeclaration
if (typeof window.BilingualConversation === 'undefined') {
class BilingualConversation {
  constructor() {
    console.log('🎙️ BilingualConversation constructor called');

    this.isRecording = false;
    this.recording = null;
    this.recordingStartTime = null;
    this.timerInterval = null;
    this.keyPressCount = 0;
    this.keyPressTimer = null;
    this.lastTranscription = '';

    // Validate required functions are available
    this.validateRequiredFunctions();

    console.log('🎙️ Initializing elements...');
    this.initializeElements();

    console.log('🎙️ Setting up event listeners...');
    this.setupEventListeners();

    // Delay language population to ensure all scripts are loaded
    setTimeout(() => {
      this.populateLanguageDropdowns();
    }, 100);
  }

  validateRequiredFunctions() {
    const requiredFunctions = [
      'window.startRecording',
      'window.processAudioWithSmartRouting',
      'window.showStatus'
    ];

    const missingFunctions = [];
    for (const funcName of requiredFunctions) {
      const func = funcName.split('.').reduce((obj, prop) => obj && obj[prop], window);
      if (typeof func !== 'function') {
        missingFunctions.push(funcName);
      }
    }

    if (missingFunctions.length > 0) {
      console.warn(`⚠️ BilingualConversation: Missing functions: ${missingFunctions.join(', ')}`);
      console.warn('Some functionality may not work properly. Consider refreshing the page.');
    } else {
      console.log('✅ BilingualConversation: All required functions are available');
    }
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
    
    // Control buttons (play/stop buttons handled by main script.js)
    this.copyOriginalBtn = document.getElementById('copy-original');
    this.copyTranslationBtn = document.getElementById('copy-translation');
    
    // File input
    this.fileInput = document.getElementById('bilingual-file-input');
  }

  setupEventListeners() {
    console.log('🎙️ Setting up event listeners for BilingualConversation');

    // Hold to Record button - Enhanced with click-to-toggle functionality
    if (this.holdRecordBtn) {
      console.log('✅ Hold record button found, attaching event listeners');

      // Variables to track hold vs click behavior
      this.holdTimeout = null;
      this.isHoldMode = false;
      this.clickStartTime = null;

      // Click event for toggle functionality (like Basic mode)
      this.holdRecordBtn.addEventListener('click', (e) => {
        // Only process click if it wasn't a hold gesture
        if (!this.isHoldMode) {
          console.log('Hold button click event (toggle mode)');
          this.toggleHoldRecording();
        }
        // Reset hold mode flag
        this.isHoldMode = false;
      });

      // Mouse events for hold functionality
      this.holdRecordBtn.addEventListener('mousedown', (e) => {
        console.log('Hold button mousedown event');
        this.clickStartTime = Date.now();
        this.isHoldMode = false;

        // Set timeout to detect hold gesture (300ms threshold)
        this.holdTimeout = setTimeout(() => {
          console.log('Hold gesture detected');
          this.isHoldMode = true;
          this.startHoldRecording();
        }, 300);
      });

      this.holdRecordBtn.addEventListener('mouseup', (e) => {
        console.log('Hold button mouseup event');

        // Clear hold timeout
        if (this.holdTimeout) {
          clearTimeout(this.holdTimeout);
          this.holdTimeout = null;
        }

        // If we were in hold mode, stop the recording
        if (this.isHoldMode && this.isRecording) {
          this.stopHoldRecording();
        }
      });

      this.holdRecordBtn.addEventListener('mouseleave', (e) => {
        console.log('Hold button mouseleave event');

        // Clear hold timeout
        if (this.holdTimeout) {
          clearTimeout(this.holdTimeout);
          this.holdTimeout = null;
        }

        // If we were in hold mode, stop the recording
        if (this.isHoldMode && this.isRecording) {
          this.stopHoldRecording();
        }
      });

      // Touch events for mobile
      this.holdRecordBtn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        console.log('Hold button touchstart event');
        this.clickStartTime = Date.now();
        this.isHoldMode = false;

        // Set timeout to detect hold gesture (300ms threshold)
        this.holdTimeout = setTimeout(() => {
          console.log('Touch hold gesture detected');
          this.isHoldMode = true;
          this.startHoldRecording();
        }, 300);
      });

      this.holdRecordBtn.addEventListener('touchend', (e) => {
        e.preventDefault();
        console.log('Hold button touchend event');

        // Clear hold timeout
        if (this.holdTimeout) {
          clearTimeout(this.holdTimeout);
          this.holdTimeout = null;
        }

        // If we were in hold mode, stop the recording
        if (this.isHoldMode && this.isRecording) {
          this.stopHoldRecording();
        } else if (!this.isHoldMode) {
          // This was a tap, trigger toggle functionality
          this.toggleHoldRecording();
        }

        // Reset hold mode flag
        this.isHoldMode = false;
      });

      console.log('✅ Hold record button event listeners attached (click-to-toggle + hold-to-record)');
    } else {
      console.error('❌ Hold record button not found!');
    }

    // Manual Record button (toggle)
    if (this.manualRecordBtn) {
      console.log('✅ Manual record button found, attaching event listener');
      this.manualRecordBtn.addEventListener('click', () => this.toggleManualRecording());
      console.log('✅ Manual record button event listener attached');
    } else {
      console.error('❌ Manual record button not found!');
    }

    // Translate button
    if (this.translateBtn) {
      console.log('✅ Translate button found, attaching event listener');
      this.translateBtn.addEventListener('click', () => this.translateText());
      console.log('✅ Translate button event listener attached');
    } else {
      console.error('❌ Translate button not found!');
    }

    // Upload button
    if (this.uploadBtn) {
      console.log('✅ Upload button found, attaching event listener');
      this.uploadBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('Upload button clicked');
        if (this.fileInput) {
          this.fileInput.click();
        } else {
          console.error('File input not found');
        }
      });
      console.log('✅ Upload button event listener attached');
    } else {
      console.error('❌ Upload button not found!');
    }

    // Clear results button
    if (this.clearBtn) {
      this.clearBtn.addEventListener('click', () => this.clearResults());
    }

    // File input
    if (this.fileInput) {
      // Remove any existing event listeners to prevent duplicates
      this.fileInput.removeEventListener('change', this.handleFileUpload);
      this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
    }

    // Language change listeners with synchronization
    if (this.fromLanguageSelect) {
      this.fromLanguageSelect.addEventListener('change', (e) => {
        const language = e.target.value;
        console.log('🌍 Bilingual from-language changed to:', language);

        // Prevent invalid values
        if (!language || language === '0' || language === 'undefined') {
          console.warn('⚠️ Invalid from-language value, resetting to default');
          this.fromLanguageSelect.value = 'en';
          return;
        }

        // Save to preferences
        if (window.languagePreferences) {
          window.languagePreferences.saveLanguagePreference('source', language);
        }

        this.updateLanguageDisplays();
      });
    }
    if (this.toLanguageSelect) {
      this.toLanguageSelect.addEventListener('change', (e) => {
        const language = e.target.value;
        console.log('🌍 Bilingual to-language changed to:', language);

        // Prevent invalid values
        if (!language || language === '0' || language === 'undefined') {
          console.warn('⚠️ Invalid to-language value, resetting to default');
          this.toLanguageSelect.value = 'es';
          return;
        }

        // Save to preferences
        if (window.languagePreferences) {
          window.languagePreferences.saveLanguagePreference('target', language);
        }

        this.updateLanguageDisplays();
      });
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

    // Note: Play/Stop buttons are now handled by the main script.js TTS system
    // to prevent duplicate event listeners and multiple voices playing
  }

  // Toggle recording functionality (like Basic mode microphone button)
  async toggleHoldRecording() {
    if (this.isRecording) {
      console.log('Toggle: Stopping recording');
      await this.stopHoldRecording();
    } else {
      console.log('Toggle: Starting recording');
      await this.startHoldRecording();
    }
  }

  async startHoldRecording() {
    if (this.isRecording) return;

    try {
      console.log('Starting hold recording...');

      // Check if startRecording function is available
      if (typeof window.startRecording !== 'function') {
        throw new Error('startRecording function not available');
      }

      this.isRecording = true;
      this.holdRecordBtn.classList.add('recording');

      // Update button text based on mode
      if (this.isHoldMode) {
        this.holdRecordBtn.innerHTML = '<i class="fas fa-stop"></i><span>Recording... (Hold)</span>';
        window.showStatus?.('Recording started - hold to continue', 'info');
      } else {
        this.holdRecordBtn.innerHTML = '<i class="fas fa-stop"></i><span>Stop Recording</span>';
        window.showStatus?.('Recording started - click to stop', 'info');
      }

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

      console.log('Hold recording started successfully');
    } catch (error) {
      console.error('Error starting hold recording:', error);
      this.resetRecordingState();
      window.showStatus?.(`Failed to start recording: ${error.message}`, 'error');
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
      console.log('Starting manual recording...');

      // Check if startRecording function is available
      if (typeof window.startRecording !== 'function') {
        throw new Error('startRecording function not available');
      }

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

      console.log('Manual recording started successfully');
      window.showStatus?.('Recording started - click Stop to finish', 'info');
    } catch (error) {
      console.error('Error starting manual recording:', error);
      this.resetRecordingState();
      window.showStatus?.(`Failed to start recording: ${error.message}`, 'error');
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

    // Reset hold mode tracking variables
    this.isHoldMode = false;
    if (this.holdTimeout) {
      clearTimeout(this.holdTimeout);
      this.holdTimeout = null;
    }
  }

  resetManualRecordButton() {
    if (this.manualRecordBtn) {
      this.manualRecordBtn.classList.remove('recording');
      this.manualRecordBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Manual Record</span>';
    }
  }

  populateLanguageDropdowns() {
    // Check if languages are already loaded and properly formatted
    if (window.languages && Array.isArray(window.languages) && window.languages.length > 0) {
      console.log('Using existing window.languages:', window.languages.length, 'languages');
      this.populateSelect(this.fromLanguageSelect, window.languages);
      this.populateSelect(this.toLanguageSelect, window.languages);
      this.setDefaultLanguages();
      this.updateLanguageDisplays();
      return;
    }

    // Try to load languages from API
    console.log('Loading languages for bilingual conversation...');
    fetch('/api/languages')
      .then(response => response.json())
      .then(languages => {
        console.log('Languages loaded from API:', Object.keys(languages).length);

        // Convert the languages format to match what we expect
        window.languages = Object.entries(languages).map(([name, details]) => ({
          name: name,
          native: details.native,
          code: details.code
        }));

        this.populateSelect(this.fromLanguageSelect, window.languages);
        this.populateSelect(this.toLanguageSelect, window.languages);
        this.setDefaultLanguages();
        this.updateLanguageDisplays();
        console.log('✅ Bilingual conversation languages loaded from API');
      })
      .catch(error => {
        console.error('Error loading languages from API:', error);
        // Fallback to basic language set
        this.loadFallbackLanguages();
      });
  }

  setDefaultLanguages() {
    // Get saved language preferences or use defaults
    const sourceLanguage = window.languagePreferences ?
      window.languagePreferences.loadLanguagePreference('source', 'en') : 'en';
    const targetLanguage = window.languagePreferences ?
      window.languagePreferences.loadLanguagePreference('target', 'es') : 'es';

    console.log('🌍 Setting default languages:', { sourceLanguage, targetLanguage });

    if (this.fromLanguageSelect && this.fromLanguageSelect.options.length > 0) {
      // Check if the language exists in the dropdown
      const sourceOptionExists = Array.from(this.fromLanguageSelect.options).some(option => option.value === sourceLanguage);
      if (sourceOptionExists) {
        this.fromLanguageSelect.value = sourceLanguage;
        console.log('✅ Set from-language to:', sourceLanguage);
      } else {
        console.warn('⚠️ Source language not found in dropdown, using first option');
        this.fromLanguageSelect.value = this.fromLanguageSelect.options[0].value;
      }
    }

    if (this.toLanguageSelect && this.toLanguageSelect.options.length > 0) {
      // Check if the language exists in the dropdown
      const targetOptionExists = Array.from(this.toLanguageSelect.options).some(option => option.value === targetLanguage);
      if (targetOptionExists) {
        this.toLanguageSelect.value = targetLanguage;
        console.log('✅ Set to-language to:', targetLanguage);
      } else {
        console.warn('⚠️ Target language not found in dropdown, using second option or first if only one');
        this.toLanguageSelect.value = this.toLanguageSelect.options[this.toLanguageSelect.options.length > 1 ? 1 : 0].value;
      }
    }
  }

  loadFallbackLanguages() {
    // Basic language set as fallback
    const fallbackLanguages = [
      { name: 'English', native: 'English', code: 'en' },
      { name: 'Spanish', native: 'Español', code: 'es' },
      { name: 'French', native: 'Français', code: 'fr' },
      { name: 'German', native: 'Deutsch', code: 'de' },
      { name: 'Italian', native: 'Italiano', code: 'it' },
      { name: 'Portuguese', native: 'Português', code: 'pt' },
      { name: 'Chinese', native: '中文', code: 'zh' },
      { name: 'Japanese', native: '日本語', code: 'ja' },
      { name: 'Korean', native: '한국어', code: 'ko' },
      { name: 'Russian', native: 'Русский', code: 'ru' }
    ];

    window.languages = fallbackLanguages;
    this.populateSelect(this.fromLanguageSelect, fallbackLanguages);
    this.populateSelect(this.toLanguageSelect, fallbackLanguages);
    this.setDefaultLanguages();
    this.updateLanguageDisplays();
    console.log('✅ Fallback languages loaded for bilingual conversation');
  }

  populateSelect(selectElement, languages) {
    if (!selectElement || !languages || !Array.isArray(languages)) {
      console.warn('⚠️ Invalid parameters for populateSelect:', { selectElement: !!selectElement, languages: languages?.length });
      return;
    }

    console.log(`🔄 Populating ${selectElement.id} with ${languages.length} languages`);

    // Store current value to restore if possible
    const currentValue = selectElement.value;

    selectElement.innerHTML = '';
    languages.forEach(lang => {
      if (lang && lang.code && lang.name) {
        const option = document.createElement('option');
        option.value = lang.code;
        option.textContent = `${lang.name} (${lang.native || lang.name})`;
        selectElement.appendChild(option);
      } else {
        console.warn('⚠️ Invalid language object:', lang);
      }
    });

    // Restore previous value if it exists in the new options
    if (currentValue && Array.from(selectElement.options).some(option => option.value === currentValue)) {
      selectElement.value = currentValue;
      console.log(`✅ Restored previous value ${currentValue} for ${selectElement.id}`);
    }

    console.log(`✅ Populated ${selectElement.id} with ${selectElement.options.length} options`);
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
    console.log('handleFileUpload called');
    const file = event.target.files[0];
    if (!file) {
      console.log('No file selected');
      return;
    }

    console.log(`File selected: ${file.name}, size: ${file.size} bytes`);

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
    // Don't initialize immediately - wait for required functions to be available
    console.log('Bilingual mode content found, waiting for required functions...');

    // Check if bilingual mode should be enabled by default (from saved preferences)
    const bilingualToggle = document.getElementById('bilingual-mode');
    if (bilingualToggle) {
      // Wait for language preferences to load first
      setTimeout(() => {
        const shouldInitialize = bilingualToggle.checked ||
                                bilingualModeContent.style.display === 'block' ||
                                bilingualModeContent.style.display !== 'none';

        console.log('🔍 Bilingual mode initialization check:', {
          toggleChecked: bilingualToggle.checked,
          contentDisplay: bilingualModeContent.style.display,
          shouldInitialize: shouldInitialize
        });

        if (shouldInitialize) {
          console.log('🚀 Bilingual mode is default - initializing immediately');
          waitForScriptsAndInitialize();
        } else {
          console.log('⏸️ Bilingual mode not default - waiting for toggle');
        }
      }, 200); // Wait for language preferences to load
    } else {
      // No toggle found, initialize anyway
      waitForScriptsAndInitialize();
    }
  }
});

// Function to manage TTS button states in bilingual mode
function setBilingualTTSButtonState(type, isPlaying) {
  const playBtn = document.getElementById(`play-${type}`);
  const stopBtn = document.getElementById(`stop-${type}`);

  if (playBtn && stopBtn) {
    if (isPlaying) {
      playBtn.style.display = 'none';
      stopBtn.style.display = 'inline-flex';
    } else {
      playBtn.style.display = 'inline-flex';
      stopBtn.style.display = 'none';
    }
  }
}

// Initialize TTS button event listeners for bilingual mode
function initializeBilingualTTSButtons() {
  console.log('🎵 Initializing bilingual TTS buttons...');

  // Note: TTS button functionality is now handled by the main script.js
  // The buttons are already connected through the existing TTS system
  // We only need to ensure proper button state management through events

  console.log('🎵 Bilingual TTS buttons are handled by main script.js');

  // Listen for TTS events to manage button states
  document.addEventListener('tts-started', (event) => {
    const sourceId = event.detail?.sourceId;
    if (sourceId === 'bilingual-original-text') {
      setBilingualTTSButtonState('original', true);
    } else if (sourceId === 'bilingual-translation-text') {
      setBilingualTTSButtonState('translation', true);
    }
  });

  document.addEventListener('tts-stopped', (event) => {
    const sourceId = event.detail?.sourceId;
    if (sourceId === 'bilingual-original-text') {
      setBilingualTTSButtonState('original', false);
    } else if (sourceId === 'bilingual-translation-text') {
      setBilingualTTSButtonState('translation', false);
    }
  });

  document.addEventListener('tts-ended', (event) => {
    const sourceId = event.detail?.sourceId;
    if (sourceId === 'bilingual-original-text') {
      setBilingualTTSButtonState('original', false);
    } else if (sourceId === 'bilingual-translation-text') {
      setBilingualTTSButtonState('translation', false);
    }
  });
}

// Initialize bilingual conversation when DOM is ready
let bilingualConversation;

function initializeBilingualConversation() {
  console.log('🎙️ Initializing bilingual conversation...');

  // Check if bilingual mode is active
  const bilingualModeContent = document.getElementById('bilingual-mode-content');
  const bilingualModeToggle = document.getElementById('bilingual-mode');

  // More robust check for bilingual mode being active
  const isBilingualModeActive = bilingualModeContent && (
    bilingualModeToggle?.checked ||
    bilingualModeContent.style.display === 'block' ||
    (bilingualModeContent.style.display !== 'none' && bilingualModeContent.style.display !== '')
  );

  console.log('🔍 Bilingual mode activation check:', {
    contentExists: !!bilingualModeContent,
    toggleChecked: bilingualModeToggle?.checked,
    contentDisplay: bilingualModeContent?.style.display,
    isBilingualModeActive: isBilingualModeActive
  });

  if (isBilingualModeActive) {
    // Check if required functions are available before initializing
    const requiredFunctions = ['startRecording', 'processAudioWithSmartRouting', 'showStatus'];
    const missingFunctions = requiredFunctions.filter(func => typeof window[func] !== 'function');

    if (missingFunctions.length > 0) {
      console.log(`⏳ Waiting for functions: ${missingFunctions.join(', ')}`);
      return; // Don't initialize yet, let waitForScriptsAndInitialize handle the retry
    }

    if (!bilingualConversation && !window.bilingualConversation) {
      try {
        console.log('🚀 Creating new BilingualConversation instance...');
        bilingualConversation = new BilingualConversation();
        console.log('✅ Bilingual conversation initialized');

        // Make it globally available for debugging and integration
        window.bilingualConversation = bilingualConversation;

        // Verify the Hold to Record button is working
        setTimeout(() => {
          const holdBtn = document.getElementById('bilingual-hold-record-btn');
          if (holdBtn) {
            console.log('🔍 Hold to Record button found:', holdBtn);
            console.log('🔍 Button event listeners attached:', !!bilingualConversation.holdRecordBtn);
          } else {
            console.warn('⚠️ Hold to Record button not found in DOM');
          }
        }, 500);

      } catch (error) {
        console.error('❌ Error initializing bilingual conversation:', error);
        // Retry after a delay
        setTimeout(initializeBilingualConversation, 1000);
        return;
      }
    } else {
      console.log('✅ BilingualConversation already exists, skipping initialization');
    }

    // Initialize TTS buttons
    initializeBilingualTTSButtons();
  } else {
    console.log('⏸️ Bilingual mode not active, skipping initialization');
    console.log('- Content exists:', !!bilingualModeContent);
    console.log('- Toggle checked:', bilingualModeToggle?.checked);
    console.log('- Content display:', bilingualModeContent?.style.display);
  }
}

// Wait for both DOM and all scripts to be ready
function waitForScriptsAndInitialize() {
  // Check if required functions are available
  const requiredFunctions = ['startRecording', 'processAudioWithSmartRouting', 'showStatus'];
  const missingFunctions = requiredFunctions.filter(func => typeof window[func] !== 'function');

  if (missingFunctions.length === 0) {
    console.log('✅ All required functions available, initializing bilingual conversation');
    initializeBilingualConversation();
  } else {
    console.log(`⏳ Waiting for functions: ${missingFunctions.join(', ')}`);
    setTimeout(waitForScriptsAndInitialize, 500);
  }
}

// This initialization is now handled by the DOMContentLoaded event listener above
// No need for duplicate initialization logic here

// Also initialize when bilingual mode is toggled
document.addEventListener('change', (event) => {
  if (event.target && event.target.id === 'bilingual-mode') {
    // Conversation room check removed - Conversation Rooms feature has been removed

    if (event.target.checked) {
      console.log('🔄 Bilingual mode toggled ON - initializing BilingualConversation...');
      // Use the proper waiting mechanism to ensure functions are available
      setTimeout(waitForScriptsAndInitialize, 100);
    } else {
      console.log('🔄 Bilingual mode toggled OFF - cleaning up BilingualConversation...');
      // Clean up when switching to basic mode
      if (window.bilingualConversation) {
        window.bilingualConversation = null;
      }
    }
  }
});

// Make the class available globally for debugging
window.BilingualConversation = BilingualConversation;

// Make the initialization function available globally
window.waitForScriptsAndInitialize = waitForScriptsAndInitialize;

// Force initialization function for debugging and fallback
window.forceBilingualConversationInit = function() {
  console.log('🔧 Force initializing BilingualConversation...');

  // Clear any existing instance
  if (window.bilingualConversation) {
    window.bilingualConversation = null;
  }

  // Force initialization regardless of mode state
  const bilingualModeContent = document.getElementById('bilingual-mode-content');
  if (bilingualModeContent) {
    bilingualModeContent.style.display = 'block';
  }

  // Initialize
  initializeBilingualConversation();

  return window.bilingualConversation;
};

// Debug function to test Hold to Record button
window.testHoldToRecordButton = function() {
  console.log('🧪 Testing Hold to Record Button...');

  const holdBtn = document.getElementById('bilingual-hold-record-btn');
  const bilingualMode = document.getElementById('bilingual-mode-content');
  const bilingualToggle = document.getElementById('bilingual-mode');

  console.log('Button element:', holdBtn);
  console.log('Bilingual mode content:', bilingualMode?.style.display);
  console.log('Bilingual toggle checked:', bilingualToggle?.checked);
  console.log('BilingualConversation instance:', window.bilingualConversation);

  if (window.bilingualConversation) {
    console.log('Hold record button reference:', window.bilingualConversation.holdRecordBtn);
    console.log('Is recording:', window.bilingualConversation.isRecording);
  }

  if (holdBtn) {
    console.log('✅ Button found - testing click...');
    holdBtn.click();
  } else {
    console.error('❌ Hold to Record button not found!');
  }
};

} // End of BilingualConversation class guard
