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

  // Global state for TTS players
  const ttsPlayers = {};

  // Function to manage button states for TTS
  function setTTSButtonState(sourceId, state) {
    let playBtn, stopBtn;

    // Handle different button ID patterns based on sourceId
    if (sourceId === 'basic-transcript') {
      // Basic mode buttons
      playBtn = document.getElementById('basic-play-btn');
      stopBtn = document.getElementById('basic-stop-btn');
    } else if (sourceId.startsWith('transcript-')) {
      // Bilingual mode transcript buttons
      const speakerId = sourceId.split('-')[1];
      playBtn = document.getElementById(`play-transcript-${speakerId}`);
      stopBtn = document.getElementById(`stop-transcript-${speakerId}`);
    } else if (sourceId.startsWith('translation-')) {
      // Bilingual mode translation buttons
      const speakerId = sourceId.split('-')[1];
      playBtn = document.getElementById(`play-translation-${speakerId}`);
      stopBtn = document.getElementById(`stop-translation-${speakerId}`);
    } else {
      // Default pattern (for backward compatibility)
      playBtn = document.getElementById(`play-${sourceId}`);
      stopBtn = document.getElementById(`stop-${sourceId}`);
    }

    if (!playBtn || !stopBtn) {
      console.warn(`Could not find play/stop buttons for sourceId: ${sourceId}`);
      return;
    }

    if (state === 'playing') {
      playBtn.style.display = 'none';
      stopBtn.style.display = 'inline-flex'; // Use inline-flex to match button class
      console.log(`TTS Button State: ${sourceId} - PLAYING - Showing stop button`);
    } else { // 'stopped', 'paused', 'ended', 'error'
      playBtn.style.display = 'inline-flex';
      stopBtn.style.display = 'none';
      console.log(`TTS Button State: ${sourceId} - ${state} - Showing play button`);
    }
  }

  // Helper function to detect mobile devices
  function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  }

  // Speak text using TTS with play/pause/resume
  function speakText(sourceId, text, langCode) {
    // For mobile devices or when sourceId refers to a DOM element, always get the latest text
    if (isMobileDevice() || sourceId.includes('-')) {
      // For translation elements, always get the current text from the DOM
      if (sourceId.startsWith('translation-')) {
        const speakerId = sourceId.split('-')[1];
        const translationEl = document.getElementById(`translation-${speakerId}`);
        if (translationEl && translationEl.value.trim() !== '') {
          text = translationEl.value;
          console.log(`Using current DOM text for TTS (translation-${speakerId}): ${text.substring(0, 30)}...`);
        }
      } else if (sourceId.startsWith('transcript-')) {
        const speakerId = sourceId.split('-')[1];
        const transcriptEl = document.getElementById(`transcript-${speakerId}`);
        if (transcriptEl && transcriptEl.value.trim() !== '') {
          text = transcriptEl.value;
          console.log(`Using current DOM text for TTS (transcript-${speakerId}): ${text.substring(0, 30)}...`);
        }
      } else if (sourceId === 'basic-transcript') {
        const transcriptEl = document.getElementById('basic-transcript');
        if (transcriptEl && transcriptEl.value.trim() !== '') {
          text = transcriptEl.value;
          console.log(`Using current DOM text for TTS (basic): ${text.substring(0, 30)}...`);
        }
      }
    }

    if (!text || text.trim() === '') {
      showStatus('No text to speak', 'warning');
      return;
    }

    // Initialize player state if it doesn't exist
    if (!ttsPlayers[sourceId]) {
      ttsPlayers[sourceId] = {
        audio: null,
        paused: false,
        blobUrl: null,
        lang: null,
        text: null,
        error: false
      };
    }

    const player = ttsPlayers[sourceId];

    // --- Resume Logic ---
    if (player.audio && player.paused && player.text === text && player.lang === langCode) {
      player.audio.play()
        .then(() => {
          player.paused = false;
          setTTSButtonState(sourceId, 'playing');
          showStatus('Resuming audio...', 'info');
        })
        .catch(error => {
          showStatus('Error resuming audio: ' + error.message, 'error');
          console.error('Audio resume error:', error);
          setTTSButtonState(sourceId, 'error');
          player.error = true;
        });
      return; // Don't fetch new audio if resuming
    }

    // --- Stop any currently playing audio for this source ---
    if (player.audio && !player.audio.paused) {
      player.audio.pause();
      player.audio.currentTime = 0; // Reset playback position
      if (player.blobUrl) {
        URL.revokeObjectURL(player.blobUrl); // Clean up old blob URL
        player.blobUrl = null;
      }
    }
    // Also stop any other playing audio to prevent overlap
    Object.keys(ttsPlayers).forEach(id => {
        if (id !== sourceId && ttsPlayers[id].audio && !ttsPlayers[id].audio.paused) {
            ttsPlayers[id].audio.pause();
            ttsPlayers[id].paused = true; // Mark as paused
            setTTSButtonState(id, 'paused');
        }
    });


    player.text = text;
    player.lang = langCode;
    player.paused = false;
    player.error = false;

    // --- Play from existing blob if available ---
    if (player.blobUrl) {
      try {
        player.audio = new Audio(player.blobUrl);
        player.audio.playbackRate = 1.10;

        player.audio.onplay = () => {
          setTTSButtonState(sourceId, 'playing');
          showStatus('Playing audio...', 'info');
        };
        player.audio.onpause = () => {
          // Only set to paused if not at the end
          if (!player.audio.ended) {
            player.paused = true;
            setTTSButtonState(sourceId, 'paused');
          }
        };
        player.audio.onended = () => {
          player.paused = false;
          setTTSButtonState(sourceId, 'ended');
          // Don't revoke URL here, allow replaying
        };
        player.audio.onerror = (e) => {
          showStatus('Error playing audio', 'error');
          console.error('Audio playback error:', e);
          setTTSButtonState(sourceId, 'error');
          player.error = true;
          if (player.blobUrl) URL.revokeObjectURL(player.blobUrl); // Clean up on error
          player.blobUrl = null;
        };

        player.audio.play().catch(error => {
          showStatus('Error playing audio: ' + error.message, 'error');
          console.error('Audio playback error:', error);
          setTTSButtonState(sourceId, 'error');
          player.error = true;
          if (player.blobUrl) URL.revokeObjectURL(player.blobUrl);
          player.blobUrl = null;
        });
      } catch (e) {
          showStatus('Error creating audio player', 'error');
          console.error('Audio element creation error:', e);
          setTTSButtonState(sourceId, 'error');
          player.error = true;
          if (player.blobUrl) URL.revokeObjectURL(player.blobUrl);
          player.blobUrl = null;
      }
      return;
    }

    // Get the selected TTS model
    const ttsModelSelect = document.getElementById('tts-model-select');
    const ttsModel = ttsModelSelect ? ttsModelSelect.value : 'gemini'; // Default to Gemini if not found

    // --- Fetch new audio blob ---
    showStatus(`Generating audio using ${ttsModel === 'gemini' ? 'Gemini' : 'OpenAI'} TTS...`, 'info');
    setTTSButtonState(sourceId, 'loading'); // Indicate loading state visually if needed

    fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        language: langCode,
        tts_model: ttsModel
      })
    })
    .then(response => {
      if (!response.ok) throw new Error(`TTS service error (${response.status})`);
      return response.blob();
    })
    .then(audioBlob => {
      player.blobUrl = URL.createObjectURL(audioBlob);
      player.audio = new Audio(player.blobUrl);
      player.audio.playbackRate = 1.10;

      player.audio.onplay = () => {
        setTTSButtonState(sourceId, 'playing');
        showStatus('Playing audio...', 'info');
      };
      player.audio.onpause = () => {
        if (!player.audio.ended) {
          player.paused = true;
          setTTSButtonState(sourceId, 'paused');
        }
      };
      player.audio.onended = () => {
        player.paused = false;
        setTTSButtonState(sourceId, 'ended');
        // Don't revoke URL here, allow replaying
      };
      player.audio.onerror = (e) => {
        showStatus('Error playing generated audio', 'error');
        console.error('Audio playback error:', e);
        setTTSButtonState(sourceId, 'error');
        player.error = true;
        if (player.blobUrl) URL.revokeObjectURL(player.blobUrl);
        player.blobUrl = null;
      };

      player.audio.play().catch(error => {
        showStatus('Error playing audio: ' + error.message, 'error');
        console.error('Audio playback error:', error);
        setTTSButtonState(sourceId, 'error');
        player.error = true;
        if (player.blobUrl) URL.revokeObjectURL(player.blobUrl);
        player.blobUrl = null;
      });
    })
    .catch(error => {
      showStatus('Error generating speech: ' + error.message, 'error');
      console.error('TTS error:', error);
      setTTSButtonState(sourceId, 'error');
      player.error = true;
      // Consider fallbackSpeakText here if desired, but it won't have pause/resume
      // fallbackSpeakText(sourceId, text, langCode);
    });
  }

  // Function to stop (pause) TTS playback
  function stopSpeakText(sourceId) {
    if (ttsPlayers[sourceId] && ttsPlayers[sourceId].audio && !ttsPlayers[sourceId].audio.paused) {
      ttsPlayers[sourceId].audio.pause();
      // State update (paused=true, button state) handled by onpause listener
      showStatus('Playback stopped.', 'info');
    }
  }

  // Fallback TTS using browser's speech synthesis (No pause/resume implemented here)
  function fallbackSpeakText(sourceId, text, langCode) {
      // Note: Implementing reliable pause/resume with SpeechSynthesis is tricky
      // and varies across browsers. Sticking to basic playback for fallback.
      if (!window.speechSynthesis) {
          showStatus('Text-to-speech is not supported in your browser', 'warning');
          setTTSButtonState(sourceId, 'error');
          return;
      }

      // Stop any current speech globally
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.10;
      utterance.lang = langCode;

      utterance.onstart = () => {
          setTTSButtonState(sourceId, 'playing');
          showStatus('Playing audio (browser TTS fallback)...', 'info');
      };
      utterance.onend = () => {
          setTTSButtonState(sourceId, 'ended');
      };
      utterance.onerror = (event) => {
          showStatus('Browser TTS error: ' + event.error, 'error');
          console.error('SpeechSynthesis error:', event);
          setTTSButtonState(sourceId, 'error');
      };

      window.speechSynthesis.speak(utterance);
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

  // Get the current translation model
  function getTranslationModel() {
    // Get the selected value from the dropdown
    const translationModelSelect = document.getElementById('translation-model-select');
    if (translationModelSelect) {
      return translationModelSelect.value;
    } else {
      return 'gemini'; // Default to Gemini if dropdown not found
    }
  }

  // Save translation model preference
  function saveTranslationModelPreference(model) {
    try {
      localStorage.setItem('vocal-local-translation-model', model);
    } catch (e) {
      console.warn('LocalStorage is not available. Translation model preference will not be saved.');
    }
  }

  // Load translation model preference
  function loadTranslationModelPreference() {
    try {
      return localStorage.getItem('vocal-local-translation-model') || 'gemini'; // Default to Gemini
    } catch (e) {
      console.warn('LocalStorage is not available. Defaulting to Gemini.');
      return 'gemini';
    }
  }

  // Translate text function
  async function translateText(text, targetLang) {
    try {
      // Get the current translation model
      const translationModel = getTranslationModel();

      // Log which model is being used
      console.log(`Translating with ${translationModel} model`);

      const response = await fetch('/api/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          target_language: targetLang,
          translation_model: translationModel
        })
      });

      if (!response.ok) {
        throw new Error(`Translation failed: ${response.status}`);
      }

      const result = await response.json();

      // Log performance metrics
      if (result.performance) {
        console.log(`Translation performance: ${result.performance.time_seconds}s, ${result.performance.characters_per_second} chars/s`);
      }

      // Show a message if fallback was used
      if (result.fallback_used) {
        showStatus(`Translation completed using ${result.model_used} as fallback`, 'info');
      }

      return result.text;
    } catch (error) {
      console.error('Translation error:', error);
      showStatus('Translation failed: ' + error.message, 'error');
      return null;
    }
  }

// ========================
  // Editable Transcript Functions
  // ========================

  // Store original transcription when received from API
  function updateTranscript(elementId, text) {
    const transcriptEl = document.getElementById(elementId);
    if (!transcriptEl) return;

    transcriptEl.value = text;
    transcriptEl.dataset.originalText = text; // Store original for undo

    console.log(`Updated transcript ${elementId} with ${text.length} characters`);
  }

  // Function to handle translate edited text button clicks
  function setupTranslateEditedButtons() {
    // Basic mode translate button
    const basicTranslateBtn = document.getElementById('basic-translate-btn');
    if (basicTranslateBtn) {
      basicTranslateBtn.addEventListener('click', async () => {
        const transcriptEl = document.getElementById('basic-transcript');
        if (!transcriptEl || !transcriptEl.value.trim()) {
          showStatus('Please enter some text to translate', 'warning');
          return;
        }

        // Get target language from global language selector
        const targetLang = document.getElementById('global-language').value;

        // Show translating status
        showStatus('Translating edited text...', 'info');

        try {
          const translatedText = await translateText(transcriptEl.value, targetLang);
          if (translatedText) {
            // Update translation textarea
            const translationEl = document.getElementById('basic-translation');
            if (translationEl) {
              translationEl.value = translatedText;
            }
            showStatus('Translation complete!', 'success');
          }
        } catch (error) {
          console.error('Translation error:', error);
          showStatus('Translation failed. Please try again.', 'error');
        }
      });
    }

    // Bilingual mode translate buttons
    const translateEdited1 = document.getElementById('translate-edited-1');
    const translateEdited2 = document.getElementById('translate-edited-2');

    if (translateEdited1) {
      translateEdited1.addEventListener('click', async () => {
        const transcriptEl = document.getElementById('transcript-1');
        if (!transcriptEl || !transcriptEl.value.trim()) {
          showStatus('Please enter some text to translate', 'warning');
          return;
        }

        // Get partner's language for translation
        const partnerLang = document.getElementById('language-2').value;

        // Show translating status
        showStatus('Translating edited text...', 'info');

        try {
          const translatedText = await translateText(transcriptEl.value, partnerLang);
          if (translatedText) {
            // Update partner's translation display
            const translationEl = document.getElementById('translation-2');
            if (translationEl) {
              translationEl.value = translatedText;
            }

            // Play TTS if enabled for the partner
            const enableTTS = document.getElementById('enable-tts-2');
            if (enableTTS && enableTTS.checked) {
              speakText(translatedText, partnerLang);
            }

            showStatus('Translation complete!', 'success');
          }
        } catch (error) {
          console.error('Translation error:', error);
          showStatus('Translation failed. Please try again.', 'error');
        }
      });
    }

    if (translateEdited2) {
      translateEdited2.addEventListener('click', async () => {
        const transcriptEl = document.getElementById('transcript-2');
        if (!transcriptEl || !transcriptEl.value.trim()) {
          showStatus('Please enter some text to translate', 'warning');
          return;
        }

        // Get partner's language for translation
        const partnerLang = document.getElementById('language-1').value;

        // Show translating status
        showStatus('Translating edited text...', 'info');

        try {
          const translatedText = await translateText(transcriptEl.value, partnerLang);
          if (translatedText) {
            // Update partner's translation display
            const translationEl = document.getElementById('translation-1');
            if (translationEl) {
              translationEl.value = translatedText;
            }

            // Play TTS if enabled for the partner
            const enableTTS = document.getElementById('enable-tts-1');
            if (enableTTS && enableTTS.checked) {
              speakText(translatedText, partnerLang);
            }

            showStatus('Translation complete!', 'success');
          }
        } catch (error) {
          console.error('Translation error:', error);
          showStatus('Translation failed. Please try again.', 'error');
        }
      });
    }
  }

  // Function to handle undo edits button clicks
  function setupUndoButtons() {
    // Basic mode undo button
    const basicUndoBtn = document.getElementById('basic-undo-btn');
    if (basicUndoBtn) {
      basicUndoBtn.addEventListener('click', () => {
        const transcriptEl = document.getElementById('basic-transcript');
        if (!transcriptEl) return;

        const originalText = transcriptEl.dataset.originalText || '';

        if (originalText) {
          transcriptEl.value = originalText;
          showStatus('Reverted to original transcription', 'info');
        } else {
          showStatus('No original transcription to revert to', 'warning');
        }
      });
    }

    // Bilingual mode undo buttons
    const undoEdits1 = document.getElementById('undo-edits-1');
    const undoEdits2 = document.getElementById('undo-edits-2');

    if (undoEdits1) {
      undoEdits1.addEventListener('click', () => {
        const transcriptEl = document.getElementById('transcript-1');
        if (!transcriptEl) return;

        const originalText = transcriptEl.dataset.originalText || '';

        if (originalText) {
          transcriptEl.value = originalText;
          showStatus('Reverted to original transcription', 'info');
        } else {
          showStatus('No original transcription to revert to', 'warning');
        }
      });
    }

    if (undoEdits2) {
      undoEdits2.addEventListener('click', () => {
        const transcriptEl = document.getElementById('transcript-2');
        if (!transcriptEl) return;

        const originalText = transcriptEl.dataset.originalText || '';

        if (originalText) {
          transcriptEl.value = originalText;
          showStatus('Reverted to original transcription', 'info');
        } else {
          showStatus('No original transcription to revert to', 'warning');
        }
      });
    }
  }

// ========================
  // Theme Switcher Logic
  // ========================
  const themeToggleButton = document.getElementById('theme-toggle-btn');
  const themeOptionsContainer = document.getElementById('theme-options');
  const themeOptionButtons = document.querySelectorAll('.theme-option');
  const htmlElement = document.documentElement; // Get the <html> element

  // Function to apply the selected theme
  function applyTheme(theme) {
    let effectiveTheme = theme;

    // Determine the actual theme if 'system' is selected
    if (theme === 'system') {
      effectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    // Apply the theme class to the <html> element
    htmlElement.setAttribute('data-theme', effectiveTheme);

    // Update the toggle button icon
    const icon = themeToggleButton.querySelector('i');
    if (theme === 'light') {
      icon.className = 'fas fa-sun';
    } else if (theme === 'dark') {
      icon.className = 'fas fa-moon';
    } else { // system
      icon.className = 'fas fa-desktop';
    }

    // Update active state in dropdown
    themeOptionButtons.forEach(btn => {
      if (btn.getAttribute('data-theme') === theme) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // Save the user's *chosen* theme preference (light, dark, or system)
    try {
      localStorage.setItem('vocal-local-theme', theme);
    } catch (e) {
      console.warn('LocalStorage is not available. Theme preference will not be saved.');
    }

    console.log(`Applied theme: ${effectiveTheme} (User choice: ${theme})`);
  }

  // Function to load the saved theme or default to system
  function loadTheme() {
    let savedTheme = 'system'; // Default to system
    try {
      savedTheme = localStorage.getItem('vocal-local-theme') || 'system';
    } catch (e) {
      console.warn('LocalStorage is not available. Defaulting to system theme.');
    }
    applyTheme(savedTheme);
  }

  // Event listener for the theme toggle button
  if (themeToggleButton && themeOptionsContainer) {
    themeToggleButton.addEventListener('click', (event) => {
      event.stopPropagation(); // Prevent click from immediately closing dropdown
      const isShown = themeOptionsContainer.classList.toggle('show');
      themeOptionsContainer.style.display = isShown ? 'block' : 'none';
    });
  }

  // Event listeners for theme option buttons
  themeOptionButtons.forEach(button => {
    button.addEventListener('click', () => {
      const selectedTheme = button.getAttribute('data-theme');
      applyTheme(selectedTheme);
      themeOptionsContainer.classList.remove('show'); // Hide dropdown after selection
      themeOptionsContainer.style.display = 'none';
    });
  });

  // Listener to close dropdown when clicking outside
  document.addEventListener('click', (event) => {
    if (themeOptionsContainer && themeOptionsContainer.classList.contains('show') && !themeToggleButton.contains(event.target) && !themeOptionsContainer.contains(event.target)) {
      themeOptionsContainer.classList.remove('show');
      themeOptionsContainer.style.display = 'none';
    }
  });

  // Listener for changes in system color scheme preference
  const systemColorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');

  try {
      systemColorSchemeQuery.addEventListener('change', () => {
          let currentPreference = 'system';
          try {
              currentPreference = localStorage.getItem('vocal-local-theme') || 'system';
          } catch (e) { /* Ignore localStorage error here */ }

          // Only re-apply if the user's choice is 'system'
          if (currentPreference === 'system') {
              applyTheme('system');
          }
      });
  } catch (e) {
      // Fallback for older browsers that use addListener
      try {
          systemColorSchemeQuery.addListener(() => {
              let currentPreference = 'system';
              try {
                  currentPreference = localStorage.getItem('vocal-local-theme') || 'system';
              } catch (e) { /* Ignore localStorage error here */ }

              if (currentPreference === 'system') {
                  applyTheme('system');
              }
          });
      } catch (err) {
          console.error("Error adding listener for system color scheme changes:", err);
      }
  }

  // Load the theme when the DOM is ready
  loadTheme();
  // ========================
  // Initialize Application
  // ========================

  // Check browser compatibility first
  const isBrowserCompatible = checkBrowserCompatibility();

  // Initialize translation model dropdown
  const translationModelSelect = document.getElementById('translation-model-select');
  if (translationModelSelect) {
    // Load saved preference
    const savedModel = loadTranslationModelPreference();
    translationModelSelect.value = savedModel;

    // Add event listener
    translationModelSelect.addEventListener('change', () => {
      const model = translationModelSelect.value;
      saveTranslationModelPreference(model);

      // Get the model display name
      const selectedOption = translationModelSelect.options[translationModelSelect.selectedIndex];
      const modelDisplayName = selectedOption ? selectedOption.textContent : model;

      showStatus(`Translation model changed to ${modelDisplayName}`, 'info');
    });
  }

  // Get the current transcription model
  function getTranscriptionModel() {
    // Get the selected value from the dropdown
    const transcriptionModelSelect = document.getElementById('global-transcription-model');
    if (transcriptionModelSelect) {
      return transcriptionModelSelect.value;
    } else {
      return 'gemini'; // Default to Gemini if dropdown not found
    }
  }

  // Save transcription model preference
  function saveTranscriptionModelPreference(model) {
    try {
      localStorage.setItem('vocal-local-transcription-model', model);
    } catch (e) {
      console.warn('LocalStorage is not available. Transcription model preference will not be saved.');
    }
  }

  // Load transcription model preference
  function loadTranscriptionModelPreference() {
    try {
      return localStorage.getItem('vocal-local-transcription-model') || 'gemini'; // Default to Gemini
    } catch (e) {
      console.warn('LocalStorage is not available. Defaulting to Gemini.');
      return 'gemini';
    }
  }

  // Initialize transcription model dropdown
  const globalTranscriptionModel = document.getElementById('global-transcription-model');
  if (globalTranscriptionModel) {
    // Load saved preference
    const savedModel = loadTranscriptionModelPreference();
    globalTranscriptionModel.value = savedModel;

    // Add event listener
    globalTranscriptionModel.addEventListener('change', () => {
      const model = globalTranscriptionModel.value;
      saveTranscriptionModelPreference(model);

      // Get the model display name
      const selectedOption = globalTranscriptionModel.options[globalTranscriptionModel.selectedIndex];
      const modelDisplayName = selectedOption ? selectedOption.textContent : model;

      showStatus(`Transcription model changed to ${modelDisplayName}`, 'info');
    });
  }

  // Initialize mode toggle
  const modeToggle = document.getElementById('bilingual-mode');
  const basicMode = document.getElementById('basic-mode');
  const bilingualMode = document.getElementById('bilingual-mode-content');
  const appSubtitle = document.getElementById('app-subtitle');
  const translationModelContainer = document.getElementById('translation-model-container');

  if (modeToggle && basicMode && bilingualMode) {
    modeToggle.addEventListener('change', () => {
      if (modeToggle.checked) {
        // Bilingual mode
        basicMode.style.display = 'none';
        bilingualMode.style.display = 'block';

        // Show translation model dropdown
        if (translationModelContainer) {
          translationModelContainer.style.display = 'flex';
        }

        if (appSubtitle) {
          appSubtitle.textContent = 'Bilingual Conversation Tool';
        }
      } else {
        // Basic mode
        basicMode.style.display = 'block';
        bilingualMode.style.display = 'none';

        // Hide translation model dropdown
        if (translationModelContainer) {
          translationModelContainer.style.display = 'none';
        }

        if (appSubtitle) {
          appSubtitle.textContent = 'Accurate Multilingual Speech-to-Text Transcription';
        }
      }
    });

    // Set initial state
    if (modeToggle.checked) {
      // If bilingual mode is initially active
      basicMode.style.display = 'none';
      bilingualMode.style.display = 'block';

      if (translationModelContainer) {
        translationModelContainer.style.display = 'flex';
      }

      if (appSubtitle) {
        appSubtitle.textContent = 'Bilingual Conversation Tool';
      }
    } else {
      // If basic mode is initially active
      if (translationModelContainer) {
        translationModelContainer.style.display = 'none';
      }
    }
  } else {
    console.warn("Some UI elements are missing");
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

      // Get selected model from global transcription model
      let selectedModel = getTranscriptionModel();
      formData.append('model', selectedModel);

      showStatus('Transcribing your audio...', 'info');

      try {
        // Get transcription
        const result = await sendToServer(formData);

        // Update transcript
        updateTranscript('basic-transcript', result.text || "No transcript received.");

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

  // Basic mode play/stop buttons
  const basicPlayBtn = document.getElementById('basic-play-btn');
  const basicStopBtn = document.getElementById('basic-stop-btn');

  if (basicPlayBtn) {
    basicPlayBtn.addEventListener('click', () => {
      const transcriptEl = document.getElementById('basic-transcript');
      if (!transcriptEl) return;
      const text = transcriptEl.value;
      const langSelect = document.getElementById('basic-language');
      const lang = langSelect ? langSelect.value : 'en';

      // For mobile devices, add a small delay to ensure the DOM is fully updated
      if (isMobileDevice()) {
        setTimeout(() => {
          // Get the text again to ensure it's the most current
          const currentText = transcriptEl.value;
          speakText('basic-transcript', currentText, lang);
        }, 50);
      } else {
        speakText('basic-transcript', text, lang); // Use consistent sourceId format
      }
    });
  }
  if (basicStopBtn) {
    basicStopBtn.addEventListener('click', () => {
      stopSpeakText('basic-transcript'); // Use consistent sourceId format
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

            // Get selected model from global transcription model
            let selectedModel = getTranscriptionModel();
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
                  updateTranscript('basic-transcript', result.text);

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
      playTranscriptBtn: document.getElementById('play-transcript-1'),
      stopTranscriptBtn: document.getElementById('stop-transcript-1'),
      playTranslationBtn: document.getElementById('play-translation-1'),
      stopTranslationBtn: document.getElementById('stop-translation-1'),
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
      playTranscriptBtn: document.getElementById('play-transcript-2'),
      stopTranscriptBtn: document.getElementById('stop-transcript-2'),
      playTranslationBtn: document.getElementById('play-translation-2'),
      stopTranslationBtn: document.getElementById('stop-translation-2'),
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

              // Get model value from global transcription model
              let modelValue = getTranscriptionModel();
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
                    updateTranscript(`transcript-${speaker.id}`, result.text);

                    // Translate the transcript
                    showStatus('Translating...', 'info');
                    const translatedText = await translateText(result.text, partnerLang);

                    if (translatedText && partnerSpeaker?.translationEl) {
                      // Update partner's translation display
                      partnerSpeaker.translationEl.value = translatedText;

                      // Play TTS if enabled for the partner
                      if (partnerSpeaker.enableTTS && partnerSpeaker.enableTTS.checked) {
                        // Use the correct sourceId format for the translation
                        const sourceId = `translation-${partnerSpeaker.id}`;

                        // Small delay to ensure the DOM is updated with the latest translation
                        setTimeout(() => {
                          // Get the text directly from the DOM element to ensure it's current
                          const currentTranslationText = partnerSpeaker.translationEl.value;
                          speakText(sourceId, currentTranslationText, partnerLang);
                        }, 100);
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

      // Play/Stop transcript buttons
      if (speaker.playTranscriptBtn) {
        speaker.playTranscriptBtn.addEventListener('click', () => {
          // Always get the current text from the DOM element
          const text = speaker.transcriptEl.value;
          const sourceId = `transcript-${speaker.id}`;
          if (text && text !== 'Your speech will appear here...') {
            // For mobile devices, add a small delay to ensure the DOM is fully updated
            if (isMobileDevice()) {
              setTimeout(() => {
                // Get the text again to ensure it's the most current
                const currentText = speaker.transcriptEl.value;
                speakText(sourceId, currentText, speaker.languageSelect.value);
              }, 50);
            } else {
              speakText(sourceId, text, speaker.languageSelect.value);
            }
          } else {
            showStatus('No transcript to play', 'warning');
          }
        });
      }
      if (speaker.stopTranscriptBtn) {
          speaker.stopTranscriptBtn.addEventListener('click', () => {
              const sourceId = `transcript-${speaker.id}`;
              stopSpeakText(sourceId);
          });
      }


      // Play/Stop translation buttons
      if (speaker.playTranslationBtn) {
        speaker.playTranslationBtn.addEventListener('click', () => {
          // Always get the current text from the DOM element
          const text = speaker.translationEl.value;
          const sourceId = `translation-${speaker.id}`;
          if (text && text !== 'Translation will appear here...') {
            const partnerSpeaker = speakers.find(s => s.id === speaker.partnerId);
            const lang = partnerSpeaker?.languageSelect?.value || 'en';

            // For mobile devices, add a small delay to ensure the DOM is fully updated
            if (isMobileDevice()) {
              setTimeout(() => {
                // Get the text again to ensure it's the most current
                const currentText = speaker.translationEl.value;
                speakText(sourceId, currentText, lang);
              }, 50);
            } else {
              speakText(sourceId, text, lang);
            }
          } else {
            showStatus('No translation to play', 'warning');
          }
        });
      }
      if (speaker.stopTranslationBtn) {
          speaker.stopTranslationBtn.addEventListener('click', () => {
              const sourceId = `translation-${speaker.id}`;
              stopSpeakText(sourceId);
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

  // Settings panel toggle
  const settingsToggle = document.getElementById('settings-toggle');
  const settingsPanel = document.getElementById('settings-panel');

  if (settingsToggle && settingsPanel) {
    // Check if we should show settings by default on desktop
    function updateSettingsPanelVisibility() {
      if (window.innerWidth >= 768) {
        // On desktop, show settings by default
        settingsPanel.style.display = 'block';
        settingsToggle.classList.add('active');
      } else {
        // On mobile, hide settings by default
        settingsPanel.style.display = 'none';
        settingsToggle.classList.remove('active');
      }
    }

    // Initial setup
    updateSettingsPanelVisibility();

    // Toggle settings panel when button is clicked
    settingsToggle.addEventListener('click', () => {
      const isVisible = settingsPanel.style.display === 'block';
      settingsPanel.style.display = isVisible ? 'none' : 'block';
      settingsToggle.classList.toggle('active');
    });

    // Update on window resize
    window.addEventListener('resize', updateSettingsPanelVisibility);
  }

  // Initialize editable transcript functionality
  setupTranslateEditedButtons();
  setupUndoButtons();

  // Initialize TTS model selector
  const ttsModelSelect = document.getElementById('tts-model-select');
  if (ttsModelSelect) {
    // Set default to Gemini
    ttsModelSelect.value = 'gemini';

    // Save selection to localStorage when changed
    ttsModelSelect.addEventListener('change', function() {
      localStorage.setItem('tts-model', this.value);
      showStatus(`TTS model set to ${this.value === 'gemini' ? 'Gemini 2.0 Flash Lite' : 'OpenAI'}`, 'success');
    });

    // Load saved selection from localStorage if available
    const savedTtsModel = localStorage.getItem('tts-model');
    if (savedTtsModel) {
      ttsModelSelect.value = savedTtsModel;
    }
  }

  // Add auto-scroll on focus for mobile
  document.querySelectorAll('.form-textarea').forEach(textarea => {
    textarea.addEventListener('focus', function() {
      // On mobile, scroll the textarea into view when focused
      if (window.innerWidth < 768) {
        setTimeout(() => {
          this.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300); // Short delay to account for keyboard appearance
      }
    });
  });
});