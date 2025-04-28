document.addEventListener('DOMContentLoaded', () => {
  // ========================
  // Utility Functions
  // ========================
  
  // Show status message
  function showStatus(message, type = 'info', persistent = false) {
    const statusEl = document.getElementById('status');
    if (!statusEl) return;
    
    statusEl.textContent = message;
    statusEl.className = `status status-${type}`;
    statusEl.style.display = 'block';
    
    if (!persistent) {
      setTimeout(() => {
        statusEl.style.display = 'none';
      }, 3000);
    }
  }
  
  // Copy text to clipboard
  function copyTextToClipboard(text, successMessage) {
    if (!text || text.trim() === '') {
      showStatus('No text to copy', 'warning');
      return;
    }
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text)
        .then(() => showStatus(successMessage, 'success'))
        .catch(err => showStatus('Failed to copy: ' + err, 'error'));
    } else {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      
      try {
        const successful = document.execCommand('copy');
        if (successful) {
          showStatus(successMessage, 'success');
        } else {
          showStatus('Copy failed. Please try selecting and copying manually.', 'warning');
        }
      } catch (err) {
        showStatus('Copy failed. Please try selecting and copying manually.', 'warning');
      }
      
      document.body.removeChild(textarea);
    }
  }
  
  // Speak text using TTS
  function speakText(text, langCode) {
    if (!text || text.trim() === '') {
      showStatus('No text to speak', 'warning');
      return;
    }
    
    showStatus('Generating audio...', 'info');
    
    // Call our backend TTS API
    fetch('/api/tts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text,
        language: langCode
      })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('TTS service error');
      }
      return response.blob();
    })
    .then(audioBlob => {
      // Create audio element to play the response
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      // Set playback rate to 1.10 (10% faster)
      audio.playbackRate = 1.10;
      
      // Play the audio
      audio.play()
        .then(() => {
          showStatus('Playing audio...', 'info');
        })
        .catch(error => {
          showStatus('Error playing audio: ' + error.message, 'error');
          console.error('Audio playback error:', error);
        });
        
      // Clean up the object URL when done
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
      };
    })
    .catch(error => {
      showStatus('Error generating speech: ' + error.message, 'error');
      console.error('TTS error:', error);
      
      // Fallback to browser's speech synthesis
      fallbackSpeakText(text, langCode);
    });
  }
  
  // Fallback TTS using browser's speech synthesis
  function fallbackSpeakText(text, langCode) {
    if (!window.speechSynthesis) {
      showStatus('Text-to-speech is not supported in your browser', 'warning');
      return;
    }
    
    // Stop any current speech
    window.speechSynthesis.cancel();
    
    // Create a new utterance
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Set rate to 1.10 (10% faster)
    utterance.rate = 1.10;
    
    // Set language
    utterance.lang = langCode;
    
    // Start speaking
    window.speechSynthesis.speak(utterance);
    showStatus('Playing audio (browser TTS fallback)...', 'info');
  }
  
  // Check browser compatibility
  function checkBrowserCompatibility() {
    // Check for MediaRecorder API
    if (!window.MediaRecorder) {
      showStatus('Your browser does not support audio recording. Please try a modern browser like Chrome, Firefox, Edge, or Safari.', 'error', true);
      document.querySelectorAll('.record-button').forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = 0.5;
      });
      return false;
    }
    
    // Check for getUserMedia support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showStatus('Your browser does not support microphone access. Please try a modern browser.', 'error', true);
      document.querySelectorAll('.record-button').forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = 0.5;
      });
      return false;
    }
    
    return true;
  }
  
  // Error handling for microphone issues
  function handleMicrophoneError(error) {
    if (error.name === 'NotAllowedError') {
      showStatus('Microphone access denied. Please enable permissions in your browser settings.', 'error', true);
    } else if (error.name === 'NotFoundError') {
      showStatus('No microphone detected on your device.', 'warning', true);
    } else if (error.name === 'NotReadableError') {
      showStatus('Cannot access microphone. It may be in use by another app.', 'warning', true);
    } else if (error.name === 'SecurityError') {
      showStatus('Microphone access requires a secure connection (HTTPS).', 'error', true);
    } else if (error.name === 'AbortError') {
      showStatus('Microphone access was aborted. Please try again.', 'warning');
    } else {
      showStatus('Microphone access error: ' + error.message, 'warning', true);
    }
    console.error('Microphone error:', error);
  }
  
  // Get supported media types based on browser/device
  function getSupportedMediaTypes() {
    const supportedTypes = [];
    
    // Check for browser type
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isAndroid = /Android/.test(navigator.userAgent);
    const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
    
    // Check what audio formats are supported
    const mimeTypes = [
      'audio/webm',
      'audio/webm;codecs=opus',
      'audio/mp4',
      'audio/mpeg',
      'audio/ogg',
      'audio/ogg;codecs=opus',
      'audio/wav'
    ];
    
    // Test each MIME type
    mimeTypes.forEach(type => {
      if (MediaRecorder.isTypeSupported(type)) {
        supportedTypes.push(type);
      }
    });
    
    // Determine the best MIME type based on device/browser
    let bestType;
    
    if (isIOS || isSafari) {
      // iOS and Safari prefer these formats
      bestType = supportedTypes.find(t => t.includes('mp4')) ||
                 supportedTypes.find(t => t.includes('mpeg')) ||
                 supportedTypes[0];
    } else if (isAndroid) {
      // Android typically supports these well
      bestType = supportedTypes.find(t => t.includes('webm;codecs=opus')) ||
                 supportedTypes.find(t => t.includes('webm')) ||
                 supportedTypes.find(t => t.includes('ogg')) ||
                 supportedTypes[0];
    } else {
      // Desktop browsers generally support these
      bestType = supportedTypes.find(t => t.includes('webm;codecs=opus')) ||
                 supportedTypes.find(t => t.includes('webm')) ||
                 supportedTypes.find(t => t.includes('ogg')) ||
                 supportedTypes[0];
    }
    
    return { supportedTypes, bestType };
  }
  
  // Audio recording function
  async function startRecording(options = {}) {
    try {
      // Visual indication that we're requesting mic access
      showStatus('Requesting microphone access...', 'info');
      
      // Get audio constraints with echo cancellation and noise suppression
      const constraints = {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      };
      
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      
      // Get the best supported MIME type
      const { bestType } = getSupportedMediaTypes();
      
      // Configure recorder
      const recorderOptions = bestType ? { mimeType: bestType } : {};
      const mediaRecorder = new MediaRecorder(stream, recorderOptions);
      
      // Setup data array
      const audioChunks = [];
      
      // Data available listener
      mediaRecorder.addEventListener('dataavailable', event => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      });
      
      // Start recording
      mediaRecorder.start(100); // Get events more frequently for better responsiveness
      showStatus('Recording started', 'success');
      
      // Add visual feedback for recording
      const recordButton = options.recordButton || null;
      if (recordButton) {
        recordButton.classList.add('recording');
      }
      
      // Log diagnostics
      console.log("Recording started with:", {
        mimeType: mediaRecorder.mimeType || "default",
        deviceInfo: "Audio input device",
        sampleRate: stream.getAudioTracks()[0].getSettings().sampleRate || "unknown"
      });
      
      return {
        mediaRecorder,
        audioChunks,
        stream
      };
    } catch (error) {
      handleMicrophoneError(error);
      throw error; // Re-throw to let caller handle it
    }
  }
  
  // Process and send audio data
  function processAudio(audioChunks, mimeType, formData) {
    return new Promise((resolve, reject) => {
      try {
        // Check for browser type
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
        const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
        
        // Determine best file format based on MIME type and device
        let fileType, fileName;
        
        if (mimeType.includes('webm')) {
          fileType = 'audio/webm';
          fileName = 'recording.webm';
        } else if (mimeType.includes('mp4')) {
          fileType = 'audio/mp4';
          fileName = 'recording.m4a';
        } else if (mimeType.includes('ogg')) {
          fileType = 'audio/ogg';
          fileName = 'recording.ogg';
        } else if (mimeType.includes('wav')) {
          fileType = 'audio/wav';
          fileName = 'recording.wav';
        } else {
          // Default fallback - try to pick the best format for the platform
          if (isIOS || isSafari) {
            fileType = 'audio/mp4';
            fileName = 'recording.m4a';
          } else {
            fileType = 'audio/webm';
            fileName = 'recording.webm';
          }
        }
        
        // Create blob with determined type
        const audioBlob = new Blob(audioChunks, { type: fileType });
        
        // Validate blob
        if (audioBlob.size === 0) {
          reject(new Error('No audio data recorded'));
          return;
        }
        
        // Create file object
        const audioFile = new File([audioBlob], fileName, { type: fileType });
        
        // Add file to form data
        formData.append('file', audioFile);
        
        // Log diagnostic info
        console.log("Audio recording info:", {
          recordedMimeType: mimeType,
          blobType: fileType,
          fileName: fileName,
          blobSize: audioBlob.size,
          chunkCount: audioChunks.length
        });
        
        resolve(formData);
      } catch (error) {
        console.error("Error processing audio:", error);
        reject(error);
      }
    });
  }
  
  // Send form data to server with timeout and retry
  function sendToServer(formData, endpoint = '/api/transcribe', maxRetries = 1) {
    return new Promise(async (resolve, reject) => {
      let attempt = 0;
      
      while (attempt <= maxRetries) {
        try {
          // Create AbortController for timeout
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout
          
          const response = await fetch(endpoint, {
            method: 'POST',
            body: formData,
            signal: controller.signal
          });
          
          // Clear timeout
          clearTimeout(timeoutId);
          
          if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
          }
          
          const result = await response.json();
          resolve(result);
          return; // Exit the retry loop on success
          
        } catch (error) {
          attempt++;
          
          // Log the error
          console.error(`Attempt ${attempt} failed:`, error);
          
          // If it's a timeout or a network error and we have retries left
          if ((error.name === 'AbortError' || 
              (error.name === 'TypeError' && error.message.includes('Failed to fetch'))) && 
              attempt <= maxRetries) {
            console.log(`Retrying... (${attempt}/${maxRetries})`);
            await new Promise(r => setTimeout(r, 1000)); // Wait 1 second before retry
            continue;
          }
          
          // If we're out of retries or it's not a retriable error
          reject(error);
          return;
        }
      }
    });
  }
  
  // Translate text function
  async function translateText(text, targetLang) {
    try {
      const response = await fetch('/api/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          target_language: targetLang
        })
      });
      
      if (!response.ok) {
        throw new Error(`Translation failed: ${response.status}`);
      }
      
      const result = await response.json();
      return result.text;
    } catch (error) {
      console.error('Translation error:', error);
      showStatus('Translation failed: ' + error.message, 'error');
      return null;
    }
  }
  
  // ========================
  // Initialize Application
  // ========================
  
  // Check browser compatibility first
  const isBrowserCompatible = checkBrowserCompatibility();
  
  // Initialize mode toggle
  const modeToggle = document.getElementById('bilingual-mode');
  const basicMode = document.getElementById('basic-mode');
  const bilingualMode = document.getElementById('bilingual-mode-content');
  const appSubtitle = document.getElementById('app-subtitle');
  
  if (modeToggle && basicMode && bilingualMode) {
    modeToggle.addEventListener('change', () => {
      if (modeToggle.checked) {
        // Bilingual mode
        basicMode.style.display = 'none';
        bilingualMode.style.display = 'block';
        if (appSubtitle) {
          appSubtitle.textContent = 'Bilingual Conversation Tool';
        }
      } else {
        // Basic mode
        basicMode.style.display = 'block';
        bilingualMode.style.display = 'none';
        if (appSubtitle) {
          appSubtitle.textContent = 'Accurate Multilingual Speech-to-Text Transcription';
        }
      }
    });
  }
  
  // Load languages from API
  function loadLanguages() {
    return fetch('/api/languages')
      .then(response => response.json())
      .then(languages => {
        // Sort language names alphabetically
        const sortedLanguages = Object.entries(languages).sort((a, b) => 
          a[0].localeCompare(b[0])
        );
        
        return sortedLanguages;
      })
      .catch(error => {
        console.error("Error loading languages:", error);
        showStatus('Could not load language options. Please refresh the page.', 'warning', true);
        return [];
      });
  }
  
  // Helper function to populate a language dropdown
  function populateLanguageDropdown(dropdownId, languages, defaultCode) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;
    
    dropdown.innerHTML = ''; // Clear existing options
    
    // Add language options
    languages.forEach(([name, details]) => {
      const option = document.createElement('option');
      option.value = details.code;
      option.textContent = `${name} (${details.native})`;
      if (details.code === defaultCode) option.selected = true;
      dropdown.appendChild(option);
    });
  }
  
  // Initialize language dropdowns
  loadLanguages().then(languages => {
    // Populate all language dropdowns
    populateLanguageDropdown('global-language', languages, 'en');
    populateLanguageDropdown('basic-language', languages, 'en');
    populateLanguageDropdown('language-1', languages, 'en');
    populateLanguageDropdown('language-2', languages, 'es');
    
    // Set up global language dropdown listener
    const globalLanguageSelect = document.getElementById('global-language');
    if (globalLanguageSelect) {
      globalLanguageSelect.addEventListener('change', function() {
        const selectedLanguage = this.value;
        
        // Update the language in the basic mode
        const basicLanguageSelect = document.getElementById('basic-language');
        if (basicLanguageSelect) {
          basicLanguageSelect.value = selectedLanguage;
        }
        
        // Update the language in the bilingual mode for speaker 1
        const language1Select = document.getElementById('language-1');
        if (language1Select) {
          language1Select.value = selectedLanguage;
        }
        
        showStatus(`Input language changed to ${globalLanguageSelect.options[globalLanguageSelect.selectedIndex].text}`, 'info');
      });
    }
  });
  
  // ========================
  // Basic Mode Implementation
  // ========================
  
  // Basic mode file upload
  const basicUploadForm = document.getElementById('basic-upload-form');
  if (basicUploadForm) {
    basicUploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const fileInput = document.getElementById('basic-file-input');
      if (!fileInput || !fileInput.files.length) {
        showStatus('Please select a file', 'warning');
        return;
      }
      
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('language', document.getElementById('basic-language').value);
      
      // Get selected model
      const modelRadios = document.querySelectorAll('input[name="basic-model"]');
      let selectedModel = 'gpt-4o-mini-transcribe'; // Default
      modelRadios.forEach(radio => {
        if (radio.checked) {
          selectedModel = radio.value;
        }
      });
      formData.append('model', selectedModel);
      
      showStatus('Transcribing your audio...', 'info');
      
      try {
        // Get transcription
        const result = await sendToServer(formData);
        
        // Update transcript
        const transcriptEl = document.getElementById('basic-transcript');
        if (transcriptEl) {
          transcriptEl.value = result.text || "No transcript received.";
        }
        
        showStatus('Transcription complete!', 'success');
      } catch (error) {
        console.error('Upload error:', error);
        
        // User-friendly error messages
        if (error.name === 'AbortError') {
          showStatus('The request took too long to complete. Please try with a smaller file or check your connection.', 'warning');
        } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
          showStatus('Network error. Please check your internet connection and try again.', 'error');
        } else {
          showStatus(`Error: ${error.message}`, 'error');
        }
      }
    });
  }
  
  // Basic mode copy button
  const basicCopyBtn = document.getElementById('basic-copy-btn');
  if (basicCopyBtn) {
    basicCopyBtn.addEventListener('click', () => {
      const transcriptEl = document.getElementById('basic-transcript');
      if (!transcriptEl) return;
      
      const text = transcriptEl.value;
      copyTextToClipboard(text, 'Transcript copied to clipboard!');
    });
  }
  
  // Basic mode play button
  const basicPlayBtn = document.getElementById('basic-play-btn');
  if (basicPlayBtn) {
    basicPlayBtn.addEventListener('click', () => {
      const transcriptEl = document.getElementById('basic-transcript');
      if (!transcriptEl) return;
      
      const text = transcriptEl.value;
      const langSelect = document.getElementById('basic-language');
      const lang = langSelect ? langSelect.value : 'en';
      
      speakText(text, lang);
    });
  }
  
  // Basic mode recording
  const basicRecordBtn = document.getElementById('basic-record-btn');
  if (basicRecordBtn && isBrowserCompatible) {
    let recording = null;
    let isRecording = false;
    
    basicRecordBtn.addEventListener('click', async () => {
      // If not recording, start recording
      if (!isRecording) {
        try {
          const recordingStatus = document.getElementById('basic-recording-status');
          if (recordingStatus) {
            recordingStatus.textContent = 'Recording in progress...';
          }
          
          isRecording = true;
          
          // Start recording using the enhanced function with button reference
          recording = await startRecording({
            recordButton: basicRecordBtn
          });
        } catch (error) {
          // Error already handled by handleMicrophoneError
          basicRecordBtn.classList.remove('recording');
          const recordingStatus = document.getElementById('basic-recording-status');
          if (recordingStatus) {
            recordingStatus.textContent = 'Click to start recording';
          }
          isRecording = false;
        }
      } else {
        // Stop recording
        if (recording && recording.mediaRecorder && 
            recording.mediaRecorder.state !== 'inactive') {
            
          const recordingStatus = document.getElementById('basic-recording-status');
          if (recordingStatus) {
            recordingStatus.textContent = 'Processing...';
          }
          
          try {
            // Stop the media recorder
            recording.mediaRecorder.stop();
            
            // Stop all tracks in the stream
            recording.stream.getTracks().forEach(track => track.stop());
            
            // Prepare form data
            const formData = new FormData();
            
            const languageSelect = document.getElementById('basic-language');
            formData.append('language', languageSelect ? languageSelect.value : 'en');
            
            // Get selected model
            const modelRadios = document.querySelectorAll('input[name="basic-model"]');
            let selectedModel = 'gpt-4o-mini-transcribe'; // Default
            modelRadios.forEach(radio => {
              if (radio.checked) {
                selectedModel = radio.value;
              }
            });
            formData.append('model', selectedModel);
            
            // Process the recorded audio after a short delay to ensure all data is collected
            setTimeout(async () => {
              try {
                // Process audio data
                const processedFormData = await processAudio(
                  recording.audioChunks,
                  recording.mediaRecorder.mimeType,
                  formData
                );
                
                // Show transcribing status
                showStatus('Transcribing your recording...', 'info');
                
                // Send to server
                const result = await sendToServer(processedFormData);
                
                if (result.text) {
                  // Update transcript
                  const transcriptEl = document.getElementById('basic-transcript');
                  if (transcriptEl) {
                    transcriptEl.value = result.text;
                  }
                  
                  showStatus('Transcription complete!', 'success');
                } else if (result.error) {
                  console.error('Server error:', result.error);
                  showStatus(`Error: ${result.error}`, 'error', true);
                } else {
                  showStatus('Transcription failed. Please try again.', 'error');
                }
              } catch (error) {
                console.error('Processing error:', error);
                
                if (error.message === 'No audio data recorded') {
                  showStatus('No audio data recorded. Please try again and speak louder.', 'warning');
                } else if (error.name === 'AbortError') {
                  showStatus('Request timed out. Please try a shorter recording or check your connection.', 'warning');
                } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                  showStatus('Network error. Please check your internet connection.', 'error');
                } else {
                  showStatus(`Error: ${error.message}`, 'error');
                }
              }
              
              // Reset UI
              basicRecordBtn.classList.remove('recording');
              const recordingStatus = document.getElementById('basic-recording-status');
              if (recordingStatus) {
                recordingStatus.textContent = 'Click to start recording';
              }
            }, 500); // Short delay to ensure all data is collected
            
          } catch (error) {
            console.error('Error stopping recording:', error);
            showStatus('Error processing recording. Please try again.', 'error');
            basicRecordBtn.classList.remove('recording');
            const recordingStatus = document.getElementById('basic-recording-status');
            if (recordingStatus) {
              recordingStatus.textContent = 'Click to start recording';
            }
          }
        }
        
        isRecording = false;
      }
    });
  }
  
  // ========================
  // Bilingual Mode Implementation
  // ========================
  
  // Initialize speakers
  const speakers = [
    {
      id: 1,
      recordBtn: document.getElementById('record-btn-1'),
      recordingStatus: document.getElementById('recording-status-1'),
      transcriptEl: document.getElementById('transcript-1'),
      translationEl: document.getElementById('translation-1'),
      languageSelect: document.getElementById('language-1'),
      modelSelect: document.getElementById('model-1'),
      playTranscriptBtn: document.getElementById('play-transcript-1'),
      playTranslationBtn: document.getElementById('play-translation-1'),
      copyTranscriptBtn: document.getElementById('copy-transcript-1'),
      copyTranslationBtn: document.getElementById('copy-translation-1'),
      enableTTS: document.getElementById('enable-tts-1'),
      recording: null,
      isRecording: false,
      partnerId: 2
    },
    {
      id: 2,
      recordBtn: document.getElementById('record-btn-2'),
      recordingStatus: document.getElementById('recording-status-2'),
      transcriptEl: document.getElementById('transcript-2'),
      translationEl: document.getElementById('translation-2'),
      languageSelect: document.getElementById('language-2'),
      modelSelect: document.getElementById('model-2'),
      playTranscriptBtn: document.getElementById('play-transcript-2'),
      playTranslationBtn: document.getElementById('play-translation-2'),
      copyTranscriptBtn: document.getElementById('copy-transcript-2'),
      copyTranslationBtn: document.getElementById('copy-translation-2'),
      enableTTS: document.getElementById('enable-tts-2'),
      recording: null,
      isRecording: false,
      partnerId: 1
    }
  ];
  
  // Set up bilingual mode if browser is compatible
  if (isBrowserCompatible) {
    speakers.forEach(speaker => {
      // Skip if any key elements are missing
      if (!speaker.recordBtn || !speaker.transcriptEl || !speaker.languageSelect) {
        return;
      }
      
      // Record button functionality
      speaker.recordBtn.addEventListener('click', async () => {
        // If not recording, start recording
        if (!speaker.isRecording) {
          try {
            if (speaker.recordingStatus) {
              speaker.recordingStatus.textContent = 'Recording in progress...';
            }
            
            speaker.isRecording = true;
            
            // Start recording
            speaker.recording = await startRecording({
              recordButton: speaker.recordBtn
            });
          } catch (error) {
            // Error already handled by handleMicrophoneError
            speaker.recordBtn.classList.remove('recording');
            if (speaker.recordingStatus) {
              speaker.recordingStatus.textContent = 'Click to start recording';
            }
            speaker.isRecording = false;
          }
        } else {
          // Stop recording
          if (speaker.recording && speaker.recording.mediaRecorder && 
              speaker.recording.mediaRecorder.state !== 'inactive') {
              
            if (speaker.recordingStatus) {
              speaker.recordingStatus.textContent = 'Processing...';
            }
            
            try {
              // Stop the media recorder
              speaker.recording.mediaRecorder.stop();
              
              // Stop all tracks in the stream
              speaker.recording.stream.getTracks().forEach(track => track.stop());
              
              // Get the partner's language for translation
              const partnerSpeaker = speakers.find(s => s.id === speaker.partnerId);
              const partnerLang = partnerSpeaker?.languageSelect?.value || 'en';
              
              // Prepare form data
              const formData = new FormData();
              formData.append('language', speaker.languageSelect.value);
              
              // Get model value
              let modelValue = 'gpt-4o-mini-transcribe';
              if (speaker.modelSelect) {
                modelValue = speaker.modelSelect.value;
              }
              formData.append('model', modelValue);
              
              // Process the recorded audio after a short delay
              setTimeout(async () => {
                try {
                  // Process audio data
                  const processedFormData = await processAudio(
                    speaker.recording.audioChunks,
                    speaker.recording.mediaRecorder.mimeType,
                    formData
                  );
                  
                  // Show transcribing status
                  showStatus(`Transcribing Speaker ${speaker.id}'s recording...`, 'info');
                  
                  // Send to server
                  const result = await sendToServer(processedFormData);
                  
                  if (result.text) {
                    // Update transcript
                    speaker.transcriptEl.value = result.text;
                    
                    // Translate the transcript
                    showStatus('Translating...', 'info');
                    const translatedText = await translateText(result.text, partnerLang);
                    
                    if (translatedText && partnerSpeaker?.translationEl) {
                      // Update partner's translation display
                      partnerSpeaker.translationEl.value = translatedText;
                      
                      // Play TTS if enabled for the partner
                      if (partnerSpeaker.enableTTS && partnerSpeaker.enableTTS.checked) {
                        speakText(translatedText, partnerLang);
                      }
                      
                      showStatus('Transcription and translation complete!', 'success');
                    } else {
                      showStatus('Transcription complete, but translation failed.', 'warning');
                    }
                  } else if (result.error) {
                    console.error('Server error:', result.error);
                    showStatus(`Error: ${result.error}`, 'error', true);
                  } else {
                    showStatus('Transcription failed. Please try again.', 'error');
                  }
                } catch (error) {
                  console.error('Processing error:', error);
                  
                  if (error.message === 'No audio data recorded') {
                    showStatus('No audio data recorded. Please try again and speak louder.', 'warning');
                  } else if (error.name === 'AbortError') {
                    showStatus('Request timed out. Please try a shorter recording or check your connection.', 'warning');
                  } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                    showStatus('Network error. Please check your internet connection.', 'error');
                  } else {
                    showStatus(`Error: ${error.message}`, 'error');
                  }
                }
                
                // Reset UI
                speaker.recordBtn.classList.remove('recording');
                if (speaker.recordingStatus) {
                  speaker.recordingStatus.textContent = 'Click to start recording';
                }
              }, 500); // Short delay to ensure all data is collected
              
            } catch (error) {
              console.error('Error stopping recording:', error);
              showStatus('Error processing recording. Please try again.', 'error');
              speaker.recordBtn.classList.remove('recording');
              if (speaker.recordingStatus) {
                speaker.recordingStatus.textContent = 'Click to start recording';
              }
            }
          }
          
          speaker.isRecording = false;
        }
      });
      
      // Play transcript button
      if (speaker.playTranscriptBtn) {
        speaker.playTranscriptBtn.addEventListener('click', () => {
          const text = speaker.transcriptEl.value;
          if (text && text !== 'Your speech will appear here...') {
            speakText(text, speaker.languageSelect.value);
          } else {
            showStatus('No transcript to play', 'warning');
          }
        });
      }
      
      // Play translation button
      if (speaker.playTranslationBtn) {
        speaker.playTranslationBtn.addEventListener('click', () => {
          const text = speaker.translationEl.value;
          if (text && text !== 'Translation will appear here...') {
            const partnerSpeaker = speakers.find(s => s.id === speaker.partnerId);
            const lang = partnerSpeaker?.languageSelect?.value || 'en';
            speakText(text, lang);
          } else {
            showStatus('No translation to play', 'warning');
          }
        });
      }
      
      // Copy transcript button
      if (speaker.copyTranscriptBtn) {
        speaker.copyTranscriptBtn.addEventListener('click', () => {
          const text = speaker.transcriptEl.value;
          copyTextToClipboard(text, `Speaker ${speaker.id}'s transcript copied!`);
        });
      }
      
      // Copy translation button
      if (speaker.copyTranslationBtn) {
        speaker.copyTranslationBtn.addEventListener('click', () => {
          const text = speaker.translationEl.value;
          copyTextToClipboard(text, `Speaker ${speaker.id}'s translation copied!`);
        });
      }
    });
  }
  
  // File selection display
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(input => {
    input.addEventListener('change', () => {
      const fileNameDisplay = document.querySelector(`[data-for="${input.id}"]`);
      if (fileNameDisplay) {
        fileNameDisplay.textContent = input.files.length ? input.files[0].name : 'No file chosen';
      }
    });
  });
  
  // About section toggle
  const aboutToggle = document.getElementById('about-toggle');
  const aboutContent = document.getElementById('about-content');
  if (aboutToggle && aboutContent) {
    aboutToggle.addEventListener('click', () => {
      const isExpanded = aboutToggle.getAttribute('aria-expanded') === 'true';
      aboutToggle.setAttribute('aria-expanded', !isExpanded);
      aboutContent.style.display = isExpanded ? 'none' : 'block';
      const icon = aboutToggle.querySelector('i');
      if (icon) {
        icon.style.transform = isExpanded ? 'rotate(0deg)' : 'rotate(180deg)';
      }
    });
  }
});