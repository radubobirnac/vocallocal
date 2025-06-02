document.addEventListener('DOMContentLoaded', () => {
  // ========================
  // Utility Functions
  // ========================

// Function to load user-specific available models
async function loadUserAvailableModels() {
  try {
    const response = await fetch('/api/user/available-models');
    if (!response.ok) {
      console.warn('Failed to load user available models, using defaults');
      return;
    }

    const data = await response.json();
    console.log('User available models:', data);

    // Update transcription model dropdown
    const transcriptionModelSelect = document.getElementById('global-transcription-model');
    if (transcriptionModelSelect && data.transcription_models) {
      updateModelDropdown(transcriptionModelSelect, data.transcription_models, 'transcription');
    }

    // Update translation model dropdown
    const translationModelSelect = document.getElementById('translation-model-select');
    if (translationModelSelect && data.translation_models) {
      updateModelDropdown(translationModelSelect, data.translation_models, 'translation');
    }

    // Store user role info for later use
    window.userRoleInfo = {
      role: data.user_role,
      hasPremiumAccess: data.has_premium_access,
      restrictions: data.restrictions
    };

    // Show role-based status message
    if (data.user_role === 'super_user') {
      showStatus('Super User access: All models available', 'success');
    } else if (data.user_role === 'admin') {
      showStatus('Admin access: Full system access', 'success');
    } else if (data.user_role === 'normal_user') {
      showStatus('Free models available. Upgrade for premium models.', 'info');
    }

  } catch (error) {
    console.error('Error loading user available models:', error);
  }
}

// Function to update model dropdown with available models
function updateModelDropdown(selectElement, models, modelType) {
  if (!selectElement || !models) return;

  // Define authorized models for validation
  const authorizedModels = {
    'transcription': ['gemini-2.0-flash-lite', 'gpt-4o-mini-transcribe', 'gpt-4o-transcribe', 'gemini-2.5-flash-preview-04-17'],
    'translation': ['gemini-2.0-flash-lite', 'gemini-2.5-flash', 'gpt-4.1-mini']
  };

  // Store current selection
  const currentValue = selectElement.value;

  // Clear existing options
  selectElement.innerHTML = '';

  // Filter models to only include authorized ones
  const filteredModels = models.filter(model => {
    if (modelType === 'transcription') {
      return authorizedModels.transcription.includes(model.value);
    } else if (modelType === 'translation') {
      return authorizedModels.translation.includes(model.value);
    }
    return true; // Allow other model types (TTS, interpretation) to pass through
  });

  // Add authorized models only
  filteredModels.forEach(model => {
    const option = document.createElement('option');
    option.value = model.value;
    option.textContent = model.label;

    // Disable locked models
    if (model.locked) {
      option.disabled = true;
      option.style.color = '#999';
    }

    selectElement.appendChild(option);
  });

  // Try to restore previous selection, or use first available model
  if (selectElement.querySelector(`option[value="${currentValue}"]`) &&
      !selectElement.querySelector(`option[value="${currentValue}"]`).disabled) {
    selectElement.value = currentValue;
  } else {
    // Select first non-disabled option
    const firstAvailable = selectElement.querySelector('option:not([disabled])');
    if (firstAvailable) {
      selectElement.value = firstAvailable.value;
    }
  }

  // Add event listener for locked model selection
  selectElement.addEventListener('change', function() {
    const selectedOption = this.options[this.selectedIndex];
    if (selectedOption && selectedOption.disabled) {
      // Prevent selection of locked models
      showStatus('This model requires a premium subscription or role upgrade', 'warning');
      // Revert to first available option
      const firstAvailable = this.querySelector('option:not([disabled])');
      if (firstAvailable) {
        this.value = firstAvailable.value;
      }
    }
  });

  console.log(`Updated ${modelType} model dropdown with ${filteredModels.length} authorized models (filtered from ${models.length} total)`);
}

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

  // Global variable to track the current audio element
  let currentAudio = null;

  // Function to stop all audio playback
  function stopAllAudio() {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      currentAudio = null;
      showStatus('Audio playback stopped', 'info');
    }
  }

  // Add a function to create a stop button
  function addStopButton() {
    // Check if stop button already exists
    if (document.getElementById('stop-audio-btn')) {
      return;
    }

    // Find the container where the TTS controls are
    const controlsContainer = document.querySelector('.controls-container') ||
                             document.querySelector('.action-buttons') ||
                             document.querySelector('.toolbar');

    if (controlsContainer) {
      // Create stop button
      const stopButton = document.createElement('button');
      stopButton.id = 'stop-audio-btn';
      stopButton.className = 'btn btn-danger btn-sm';
      stopButton.innerHTML = '<i class="fas fa-stop"></i> Stop Audio';
      stopButton.onclick = stopAllAudio;

      // Add to container
      controlsContainer.appendChild(stopButton);
    }
  }

  // Add keyboard shortcut for stopping audio
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      stopAllAudio();
    }
  });

  // Initialize when the document is ready
  document.addEventListener('DOMContentLoaded', function() {
    // Add the stop button
    addStopButton();

    // Other initialization code...
  });

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

    // Stop any currently playing audio
    stopAllAudio();

    // Get the selected TTS model
    const ttsModelSelect = document.getElementById('tts-model-select');
    const ttsModel = ttsModelSelect ? ttsModelSelect.value : 'auto'; // Default to auto if not found

    // Validate model access if model access control is available
    if (window.modelAccessControl && window.modelAccessControl.hasLoadedUserRole) {
      if (!window.modelAccessControl.canAccessModel(ttsModel)) {
        window.modelAccessControl.showUpgradePrompt(ttsModel);
        setTTSButtonState(sourceId, 'error');
        return;
      }
    }

    // Show loading status
    showStatus(`Generating audio using ${ttsModel} TTS...`, 'info');
    setTTSButtonState(sourceId, 'loading');

    // Make API request
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
      if (!response.ok) {
        throw new Error(`TTS service error (${response.status})`);
      }
      return response.blob();
    })
    .then(audioBlob => {
      // Create URL for the audio blob
      const audioUrl = URL.createObjectURL(audioBlob);

      // Create and play the audio
      const audio = new Audio(audioUrl);

      // Store the audio element globally so we can stop it later
      currentAudio = audio;

      // Set playback rate to 1.10 (10% faster)
      audio.playbackRate = 1.10;

      // Play the audio
      audio.play()
        .then(() => {
          showStatus('Playing audio...', 'info');
        })
        .catch(error => {
          showStatus('Error playing audio: ' + error.message, 'danger');
          console.error('Audio playback error:', error);
          fallbackSpeakText(text, langCode);
        });

      // Clean up when done
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        currentAudio = null;
      };
    })
    .catch(error => {
      showStatus('Error generating speech: ' + error.message, 'danger');
      console.error('TTS error:', error);

      // Fallback to browser's speech synthesis
      fallbackSpeakText(text, langCode);
    })
    .finally(() => {
      setTTSButtonState(sourceId, 'ready');
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

  // Global variables for recording timer
  let recordingTimer = null;
  let recordingStartTime = null;
  let recordingDuration = 0;
  const MAX_RECORDING_DURATION = 20 * 60; // 20 minutes in seconds
  const WARNING_THRESHOLD = 19 * 60; // 19 minutes in seconds

  // Progressive transcription variables
  let progressiveTimer = null;
  let currentChunkData = [];
  let chunkCounter = 0;
  let lastChunkTime = null;
  const CHUNK_INTERVAL = 65000; // 65 seconds for flexible timing
  const OVERLAP_PERCENTAGE = 0.10; // 10% overlap to prevent word loss

  // Overlapping chunk management
  let allAudioChunks = [];
  let lastProcessedIndex = 0;
  let currentMediaRecorder = null;
  let currentStream = null;

  // Format seconds as MM:SS
  function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  // Progressive transcription functions
  function startProgressiveTranscription(elementId = 'basic-transcript') {
    console.log('Starting progressive transcription for element:', elementId);
    chunkCounter = 0;
    currentChunkData = [];
    lastChunkTime = Date.now();

    // Clear any existing timer
    if (progressiveTimer) {
      clearInterval(progressiveTimer);
    }

    // Start the chunk processing timer - this will restart MediaRecorder for each chunk
    progressiveTimer = setInterval(() => {
      processCurrentChunkWithRestart(elementId);
    }, CHUNK_INTERVAL);
  }

  function stopProgressiveTranscription() {
    console.log('Stopping progressive transcription');
    if (progressiveTimer) {
      clearInterval(progressiveTimer);
      progressiveTimer = null;
    }

    // Stop chunk recording if active
    if (isChunkRecording && currentMediaRecorder) {
      stopChunkRecording();
    }

    // Process any remaining chunk data
    if (currentChunkData.length > 0) {
      processCurrentChunk();
    }
  }

  async function stopProgressiveTranscriptionWithFinalChunk() {
    console.log('Stopping progressive transcription with final chunk processing');

    // Stop the timer first
    if (progressiveTimer) {
      clearInterval(progressiveTimer);
      progressiveTimer = null;
    }

    // Process the final chunk if we have active chunk recording
    if (isChunkRecording && currentMediaRecorder) {
      try {
        console.log('Processing final chunk before stopping');
        const finalChunkBlob = await stopChunkRecording();

        if (finalChunkBlob && finalChunkBlob.size > 1000) {
          // Validate the final WebM chunk before sending
          const isValid = await isValidWebMChunk(finalChunkBlob);

          if (isValid) {
            console.log(`✅ Final chunk is valid WebM, proceeding with transcription`);

            // Show processing status for final chunk
            showChunkProcessing(chunkCounter);

            // Send final chunk for transcription
            const elementId = 'basic-transcript'; // Default element
            const result = await sendChunkForTranscription(finalChunkBlob, chunkCounter, elementId);

            if (result && result.text) {
              // Append result to transcript
              appendChunkResult(result.text, chunkCounter, elementId);
              showChunkComplete(chunkCounter);
            }
          } else {
            console.log(`❌ Final chunk is invalid WebM, skipping transcription`);
          }
        }
      } catch (error) {
        console.error('Error processing final chunk:', error);
      }
    }

    // Clean up stream
    if (currentStream) {
      currentStream.getTracks().forEach(track => track.stop());
      currentStream = null;
    }

    // Reset chunk recording state
    isChunkRecording = false;
    currentMediaRecorder = null;
  }

  // New function to handle overlapping chunk processing
  async function processCurrentChunkWithRestart(elementId = 'basic-transcript') {
    if (!currentMediaRecorder || currentMediaRecorder.state !== 'recording') {
      console.log('No active recording for chunk processing');
      return;
    }

    console.log(`Processing overlapping chunk ${chunkCounter + 1}...`);

    try {
      // Calculate overlap (10% overlap to prevent word loss during chunking)
      const overlapChunks = Math.max(0, Math.floor(allAudioChunks.length * OVERLAP_PERCENTAGE));
      const startIndex = Math.max(0, lastProcessedIndex - overlapChunks);

      // Create chunk from overlapping audio data
      const chunkData = allAudioChunks.slice(startIndex);
      const chunkBlob = new Blob(chunkData, { type: 'audio/webm' });

      console.log(`📦 Chunk ${chunkCounter + 1}: ${chunkBlob.size} bytes (${Math.round(OVERLAP_PERCENTAGE * 100)}% overlap: ${overlapChunks} pieces, total: ${chunkData.length} pieces)`);

      if (chunkBlob && chunkBlob.size > 1000) { // Ensure chunk has meaningful data
        // Validate the WebM chunk before sending
        const isValid = await isValidWebMChunk(chunkBlob);

        if (isValid) {
          console.log(`✅ Chunk ${chunkCounter + 1} is valid WebM, proceeding with transcription`);

          // Show processing status
          showChunkProcessing(chunkCounter);

          // Send chunk for transcription with overlap info
          const result = await sendChunkForTranscription(chunkBlob, chunkCounter, elementId, {
            hasOverlap: overlapChunks > 0,
            overlapSeconds: Math.floor(overlapChunks * 0.1), // Estimate overlap time
            overlapPercentage: Math.round(OVERLAP_PERCENTAGE * 100)
          });

          if (result && result.text) {
            // Append result to transcript
            appendChunkResult(result.text, chunkCounter, elementId);
            showChunkComplete(chunkCounter);
          }

          chunkCounter++;
        } else {
          console.log(`❌ Chunk ${chunkCounter + 1} is invalid WebM, skipping transcription`);
          showStatus(`Chunk ${chunkCounter + 1} invalid, skipping`, 'warning');
        }
      } else {
        console.log('Chunk too small or empty, skipping transcription');
      }

      // Update the last processed index
      lastProcessedIndex = allAudioChunks.length;

    } catch (error) {
      console.error('Error processing overlapping chunk:', error);
      showStatus(`Error processing chunk ${chunkCounter + 1}: ${error.message}`, 'error');
    }
  }

  // Helper function to validate WebM chunks
  function isValidWebMChunk(blob) {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = function(e) {
        const arrayBuffer = e.target.result;
        const uint8Array = new Uint8Array(arrayBuffer);

        // Check for WebM signature (EBML header)
        // WebM files start with 0x1A, 0x45, 0xDF, 0xA3 (EBML signature)
        if (uint8Array.length >= 4) {
          const hasEBMLHeader = uint8Array[0] === 0x1A &&
                               uint8Array[1] === 0x45 &&
                               uint8Array[2] === 0xDF &&
                               uint8Array[3] === 0xA3;

          console.log(`WebM validation: size=${blob.size}, hasEBMLHeader=${hasEBMLHeader}`);
          resolve(hasEBMLHeader);
        } else {
          console.log(`WebM validation: size=${blob.size}, too small`);
          resolve(false);
        }
      };
      reader.onerror = () => resolve(false);
      reader.readAsArrayBuffer(blob.slice(0, 32)); // Read first 32 bytes for header check
    });
  }

  // Helper functions for chunk recording management
  async function startChunkRecording() {
    if (!currentStream) {
      throw new Error('No active stream available for chunk recording');
    }

    console.log('Starting new chunk recording');

    // Get the best supported MIME type
    const { bestType } = getSupportedMediaTypes();

    // Create new MediaRecorder for this chunk
    const recorderOptions = bestType ? { mimeType: bestType } : {};
    currentMediaRecorder = new MediaRecorder(currentStream, recorderOptions);

    // Setup data collection for this chunk
    currentChunkData = [];

    // Data available listener
    currentMediaRecorder.addEventListener('dataavailable', event => {
      if (event.data.size > 0) {
        currentChunkData.push(event.data);
      }
    });

    // Start recording this chunk
    currentMediaRecorder.start();
    isChunkRecording = true;

    console.log('Chunk recording started with MIME type:', bestType || 'default');
  }

  async function stopChunkRecording() {
    return new Promise((resolve, reject) => {
      if (!currentMediaRecorder || !isChunkRecording) {
        resolve(null);
        return;
      }

      console.log('Stopping chunk recording');

      // Set up the stop handler
      currentMediaRecorder.addEventListener('stop', () => {
        console.log(`Chunk recording stopped, collected ${currentChunkData.length} data pieces`);

        // Create blob from collected data
        const chunkBlob = new Blob(currentChunkData, { type: currentMediaRecorder.mimeType || 'audio/webm' });
        console.log(`Created chunk blob: ${chunkBlob.size} bytes, type: ${chunkBlob.type}`);

        isChunkRecording = false;
        resolve(chunkBlob);
      });

      // Set up error handler
      currentMediaRecorder.addEventListener('error', (event) => {
        console.error('MediaRecorder error during stop:', event.error);
        isChunkRecording = false;
        reject(event.error);
      });

      // Stop the recorder
      currentMediaRecorder.stop();
    });
  }

  async function processCurrentChunk(elementId = 'basic-transcript') {
    if (currentChunkData.length === 0) {
      console.log('No chunk data to process');
      return;
    }

    console.log(`Processing chunk ${chunkCounter + 1} with ${currentChunkData.length} audio pieces`);

    try {
      // Create blob from current chunk data
      const chunkBlob = new Blob(currentChunkData, { type: 'audio/webm' });

      // Show processing status
      showChunkProcessing(chunkCounter);

      // Send chunk for transcription
      const result = await sendChunkForTranscription(chunkBlob, chunkCounter, elementId);

      if (result && result.text) {
        // Append result to transcript
        appendChunkResult(result.text, chunkCounter, elementId);
        showChunkComplete(chunkCounter);
      }

      chunkCounter++;

      // Keep last portion for overlap (approximate)
      const overlapSize = Math.max(1, Math.floor(currentChunkData.length * 0.1)); // Keep ~10%
      currentChunkData = currentChunkData.slice(-overlapSize);

    } catch (error) {
      console.error('Error processing chunk:', error);
      showStatus(`Error processing chunk ${chunkCounter + 1}: ${error.message}`, 'error');
    }
  }

  async function sendChunkForTranscription(chunkBlob, chunkNumber, elementId, overlapInfo = {}) {
    console.log(`Sending chunk ${chunkNumber + 1} for transcription`);

    const formData = new FormData();
    formData.append('audio', chunkBlob, `chunk_${chunkNumber}.webm`);
    formData.append('language', document.getElementById('language-select')?.value || 'en');
    formData.append('model', document.getElementById('model-select')?.value || 'gemini-2.0-flash-lite');
    formData.append('chunk_number', chunkNumber.toString());
    formData.append('element_id', elementId);

    // Add overlap metadata
    if (overlapInfo.hasOverlap) {
      formData.append('has_overlap', 'true');
      formData.append('overlap_seconds', overlapInfo.overlapSeconds.toString());
      formData.append('overlap_percentage', overlapInfo.overlapPercentage.toString());
    }

    try {
      const response = await fetch('/api/transcribe_chunk', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const result = await response.json();
      console.log(`Chunk ${chunkNumber + 1} transcription result:`, result);
      return result;

    } catch (error) {
      console.error(`Error transcribing chunk ${chunkNumber + 1}:`, error);
      throw error;
    }
  }

  function appendChunkResult(text, chunkNumber, elementId) {
    console.log(`Appending chunk ${chunkNumber + 1} result to ${elementId}`);

    const transcriptEl = document.getElementById(elementId);
    if (!transcriptEl) {
      console.error(`Element ${elementId} not found`);
      return;
    }

    const currentText = transcriptEl.value;
    const timestamp = Math.floor((chunkNumber * 65) / 60); // Approximate minutes

    // Simple deduplication - remove common ending/beginning words
    let cleanText = text;
    if (currentText && chunkNumber > 0) {
      cleanText = simpleDeduplication(text, currentText);
    }

    // Append with timestamp
    const newText = currentText +
      (currentText ? '\n\n' : '') +
      `[${timestamp}m${Math.floor((chunkNumber * 65) % 60)}s] ${cleanText}`;

    transcriptEl.value = newText;

    // Auto-scroll to bottom
    transcriptEl.scrollTop = transcriptEl.scrollHeight;

    // Trigger change event for any listeners
    const event = new Event('change');
    transcriptEl.dispatchEvent(event);
  }

  function simpleDeduplication(newText, previousText) {
    if (!previousText || !newText) return newText;

    // Get last 10 words from previous text
    const prevWords = previousText.trim().split(/\s+/).slice(-10);
    const newWords = newText.trim().split(/\s+/);

    // Find overlap and remove from new text
    for (let i = 1; i <= Math.min(prevWords.length, newWords.length); i++) {
      const prevEnd = prevWords.slice(-i).join(' ').toLowerCase();
      const newStart = newWords.slice(0, i).join(' ').toLowerCase();

      if (prevEnd === newStart) {
        return newWords.slice(i).join(' ');
      }
    }

    return newText;
  }

  function showChunkProcessing(chunkNumber) {
    showStatus(`Processing chunk ${chunkNumber + 1}...`, 'info');
  }

  function showChunkComplete(chunkNumber) {
    showStatus(`Chunk ${chunkNumber + 1} transcribed. Recording continues...`, 'success');

    // Clear status after 2 seconds
    setTimeout(() => {
      if (recordingStartTime) { // Only if still recording
        showStatus('Recording in progress...', 'info');
      }
    }, 2000);
  }

  // Update recording timer display
  function updateRecordingTimer(elementId = 'recording-timer') {
    if (!recordingStartTime) return;

    const now = new Date();
    const elapsedSeconds = (now - recordingStartTime) / 1000;
    recordingDuration = elapsedSeconds;

    // Only show warning when approaching max duration
    if (elapsedSeconds >= WARNING_THRESHOLD && elapsedSeconds < MAX_RECORDING_DURATION) {
      // Show continue button if not already visible
      const continueButton = document.getElementById('continue-recording');
      if (continueButton && continueButton.style.display !== 'inline-block') {
        continueButton.style.display = 'inline-block';
      }
    }

    // Auto-stop recording if max duration reached
    if (elapsedSeconds >= MAX_RECORDING_DURATION) {
      // Find the active recording button and trigger a click to stop recording
      const activeRecordButton = document.querySelector('.record-button.recording');
      if (activeRecordButton) {
        activeRecordButton.click();
      }
    }
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

      // Store stream for chunk recording
      currentStream = stream;

      // Get the best supported MIME type
      const { bestType } = getSupportedMediaTypes();

      // Configure recorder for main recording (full recording)
      const recorderOptions = bestType ? { mimeType: bestType } : {};
      const mediaRecorder = new MediaRecorder(stream, recorderOptions);

      // Setup data array for main recording
      const audioChunks = [];

      // Data available listener for main recording
      mediaRecorder.addEventListener('dataavailable', event => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
          // Also add to overlapping chunks array
          allAudioChunks.push(event.data);
        }
      });

      // Start main recording
      mediaRecorder.start(100); // Get events more frequently for better responsiveness

      // Store as current recorder for chunk processing
      currentMediaRecorder = mediaRecorder;
      showStatus('Recording started', 'success');

      // Add visual feedback for recording
      const recordButton = options.recordButton || null;
      if (recordButton) {
        recordButton.classList.add('recording');
      }

      // Start recording timer
      recordingStartTime = new Date();
      if (recordingTimer) clearInterval(recordingTimer);
      recordingTimer = setInterval(() => updateRecordingTimer(), 1000);

      // Start progressive transcription
      const elementId = options.elementId || 'basic-transcript';

      // Reset chunk tracking for overlapping approach
      allAudioChunks = [];
      lastProcessedIndex = 0;

      startProgressiveTranscription(elementId);

      // Create continue button if needed
      let continueButton = document.getElementById('continue-recording');
      if (!continueButton) {
        // Create continue button
        continueButton = document.createElement('button');
        continueButton.id = 'continue-recording';
        continueButton.className = 'continue-recording-btn';
        continueButton.textContent = 'Continue Recording';
        continueButton.style.display = 'none';
        continueButton.onclick = function() {
          // Reset the recording start time to extend duration
          recordingStartTime = new Date();
          // Add 10 more minutes to the max duration
          MAX_RECORDING_DURATION += 10 * 60; // Add 10 more minutes
          WARNING_THRESHOLD = MAX_RECORDING_DURATION - 60; // 1 minute before the new limit
          this.style.display = 'none';
        };

        // Add button to the page
        const recordingContainer = recordButton.parentElement;
        recordingContainer.appendChild(continueButton);
      } else {
        // Hide continue button
        continueButton.style.display = 'none';
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

      // Check model access permissions before making API call
      if (window.modelAccessControl && window.modelAccessControl.hasLoadedUserRole) {
        const model = formData.get('model');
        if (model && !window.modelAccessControl.canAccessModel(model)) {
          window.modelAccessControl.showUpgradePrompt(model);
          reject(new Error(`Access denied: ${model} requires premium access`));
          return;
        }
      }

      // Check if this is a WebM recording from browser
      const file = formData.get('file');
      const isWebmRecording = file && file.type === 'audio/webm';

      // For WebM recordings, we'll use a longer timeout and more retries
      // This helps prevent timeouts with browser recordings
      if (isWebmRecording) {
        console.log("Detected WebM recording from browser, using extended timeout and retries");
        maxRetries = 2; // Increase retries for WebM recordings
      }

      while (attempt <= maxRetries) {
        try {
          // Create AbortController for timeout
          const controller = new AbortController();

          // Use a longer timeout for WebM recordings
          const timeoutDuration = isWebmRecording ? 120000 : 60000; // 120 seconds for WebM, 60 seconds for others
          const timeoutId = setTimeout(() => controller.abort(), timeoutDuration);

          console.log(`Sending request to ${endpoint} (attempt ${attempt + 1}/${maxRetries + 1}, timeout: ${timeoutDuration/1000}s)`);

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

          // Check if this is a background processing job
          if (result.status === 'processing' && result.job_id) {
            console.log(`Server is processing the request in background (job ID: ${result.job_id})`);

            // For WebM recordings, we'll automatically use the background processing handler
            if (isWebmRecording) {
              // Determine which transcript element to update
              let elementId = 'basic-transcript';

              // Start polling for status
              pollTranscriptionStatus(result.job_id, elementId);

              // Return a placeholder result
              resolve({
                text: "Processing recording in background...",
                processing: true,
                job_id: result.job_id
              });
              return;
            }
          }

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

  // Make the showStatus function available globally
  window.showStatus = showStatus;

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

  // Get the current interpretation model
  function getInterpretationModel() {
    // Get the selected value from the dropdown
    const interpretationModelSelect = document.getElementById('interpretation-model-select');
    if (interpretationModelSelect) {
      return interpretationModelSelect.value;
    } else {
      return 'gemini-2.0-flash-lite'; // Default to Gemini 2.0 Flash Lite if dropdown not found
    }
  }

  // Save interpretation model preference
  function saveInterpretationModelPreference(model) {
    try {
      localStorage.setItem('vocal-local-interpretation-model', model);
    } catch (e) {
      console.warn('LocalStorage is not available. Interpretation model preference will not be saved.');
    }
  }

  // Load interpretation model preference
  function loadInterpretationModelPreference() {
    try {
      return localStorage.getItem('vocal-local-interpretation-model') || 'gemini-2.0-flash-lite'; // Default to Gemini 2.0 Flash Lite
    } catch (e) {
      console.warn('LocalStorage is not available. Defaulting to Gemini 2.0 Flash Lite.');
      return 'gemini-2.0-flash-lite';
    }
  }

  // Function to interpret text using AI
  async function interpretText(text, tone) {
    if (!text || text.trim() === '') {
      showStatus('No text to interpret', 'warning');
      return null;
    }

    try {
      // Get the current interpretation model
      const interpretationModel = getInterpretationModel();

      // Validate model access if model access control is available
      if (window.modelAccessControl && window.modelAccessControl.hasLoadedUserRole) {
        if (!window.modelAccessControl.canAccessModel(interpretationModel)) {
          window.modelAccessControl.showUpgradePrompt(interpretationModel);
          return null;
        }
      }

      // Log which model is being used
      console.log(`Interpreting with ${interpretationModel} model`);

      showStatus(`Generating AI interpretation using ${interpretationModel.includes('2.5') ? 'Gemini 2.5 Flash' : 'Gemini 2.0 Flash Lite'}...`, 'info');

      const response = await fetch('/api/interpret', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: text,
          tone: tone,
          interpretation_model: interpretationModel
        })
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const result = await response.json();

      if (result.interpretation) {
        // Show a message if fallback was used
        if (result.fallback_used) {
          showStatus(`Interpretation completed using ${result.model_used} as fallback`, 'info');
        } else {
          showStatus('Interpretation complete!', 'success');
        }
        return result.interpretation;
      } else if (result.error) {
        throw new Error(result.error);
      } else {
        throw new Error('No interpretation received');
      }
    } catch (error) {
      console.error('Interpretation error:', error);
      showStatus(`Interpretation failed: ${error.message}`, 'error');
      return null;
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
      const savedModel = localStorage.getItem('vocal-local-translation-model');

      // Handle old model names for backward compatibility
      if (savedModel === 'gemini') {
        return 'gemini-2.0-flash-lite';
      } else if (savedModel === 'openai') {
        return 'gemini-2.5-flash';
      }

      return savedModel || 'gemini-2.0-flash-lite'; // Default to Gemini 2.0 Flash Lite
    } catch (e) {
      console.warn('LocalStorage is not available. Defaulting to Gemini 2.0 Flash Lite.');
      return 'gemini-2.0-flash-lite';
    }
  }

  // Translate text function
  async function translateText(text, targetLang) {
    try {
      // Get the current translation model
      const translationModel = getTranslationModel();

      // Validate model access if model access control is available
      if (window.modelAccessControl && window.modelAccessControl.hasLoadedUserRole) {
        if (!window.modelAccessControl.canAccessModel(translationModel)) {
          window.modelAccessControl.showUpgradePrompt(translationModel);
          return null;
        }
      }

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
    console.log(`updateTranscript called with elementId: ${elementId}, text length: ${text ? text.length : 0}`);

    const transcriptEl = document.getElementById(elementId);
    if (!transcriptEl) {
      console.error(`❌ Element with ID '${elementId}' not found!`);
      return;
    }

    console.log(`✅ Found element ${elementId}:`, transcriptEl);

    // Update the element value
    transcriptEl.value = text;
    transcriptEl.dataset.originalText = text; // Store original for undo

    console.log(`✅ Updated transcript ${elementId} with ${text.length} characters`);
    console.log(`Text preview: "${text.substring(0, 100)}${text.length > 100 ? '...' : ''}"`);

    // Trigger change event for any listeners
    const event = new Event('change');
    transcriptEl.dispatchEvent(event);
    console.log(`✅ Triggered change event for ${elementId}`);

    // If this is the basic transcript, also update the interpretation
    if (elementId === 'basic-transcript') {
      console.log('🔄 Updating interpretation for basic transcript');
      updateInterpretation(text);
    }
  }

  // Make updateTranscript globally available for other scripts
  window.updateTranscript = updateTranscript;

  // Update interpretation based on transcript text
  async function updateInterpretation(text) {
    const interpretationEl = document.getElementById('basic-interpretation');
    if (!interpretationEl) return;

    // Check if interpretation is enabled
    const isEnabled = loadInterpretationEnabledPreference();

    // If interpretation is disabled, don't process anything
    if (!isEnabled) {
      return;
    }

    // Only interpret if there's text to interpret
    if (!text || text.trim() === '') {
      interpretationEl.value = '';
      return;
    }

    // Get the selected tone
    const toneSelect = document.getElementById('interpretation-tone-select');
    const tone = toneSelect ? toneSelect.value : 'professional';

    // Generate interpretation
    const interpretation = await interpretText(text, tone);

    if (interpretation) {
      interpretationEl.value = interpretation;
    }
  }

  // Function to toggle the visibility of the interpretation section and settings
  function toggleInterpretationSection(isEnabled) {
    // Toggle the interpretation section in the main UI
    const interpretationSection = document.querySelector('.interpretation-section');
    if (interpretationSection) {
      interpretationSection.style.display = isEnabled ? 'block' : 'none';
    }

    // Toggle all interpretation-related settings in the settings panel
    const interpretationSettings = document.querySelectorAll('.interpretation-setting');
    interpretationSettings.forEach(setting => {
      setting.style.display = isEnabled ? 'block' : 'none';
    });
  }

  // Function to handle translate edited text button clicks
  function setupTranslateEditedButtons() {
    // Basic mode translate button removed as per UI requirements

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
      icon.className = 'fas fa-lightbulb'; // Changed to lightbulb
    } else if (theme === 'dark') {
      icon.className = 'fas fa-moon';
    } else { // system
      icon.className = 'fas fa-circle-half-stroke'; // Changed to circle-half-stroke
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

  // Initialize interpretation settings visibility based on saved preference
  const isInterpretationEnabled = loadInterpretationEnabledPreference();
  toggleInterpretationSection(isInterpretationEnabled);

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
      return 'gemini-2.0-flash-lite'; // Default to Gemini 2.0 Flash Lite if dropdown not found
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
      return localStorage.getItem('vocal-local-transcription-model') || 'gemini-2.0-flash-lite'; // Default to Gemini 2.0 Flash Lite
    } catch (e) {
      console.warn('LocalStorage is not available. Defaulting to Gemini 2.0 Flash Lite.');
      return 'gemini-2.0-flash-lite';
    }
  }

  // Save interpretation tone preference
  function saveInterpretationTonePreference(tone) {
    try {
      localStorage.setItem('vocal-local-interpretation-tone', tone);
    } catch (e) {
      console.warn('LocalStorage is not available. Interpretation tone preference will not be saved.');
    }
  }

  // Load interpretation tone preference
  function loadInterpretationTonePreference() {
    try {
      return localStorage.getItem('vocal-local-interpretation-tone') || 'professional'; // Default to professional
    } catch (e) {
      console.warn('LocalStorage is not available. Defaulting to professional tone.');
      return 'professional';
    }
  }

  // Save interpretation enabled preference
  function saveInterpretationEnabledPreference(enabled) {
    try {
      localStorage.setItem('vocal-local-interpretation-enabled', enabled ? 'true' : 'false');
    } catch (e) {
      console.warn('LocalStorage is not available. Interpretation enabled preference will not be saved.');
    }
  }

  // Load interpretation enabled preference
  function loadInterpretationEnabledPreference() {
    try {
      const savedPreference = localStorage.getItem('vocal-local-interpretation-enabled');
      // If no preference is saved, default to enabled (true)
      return savedPreference === null ? true : savedPreference === 'true';
    } catch (e) {
      console.warn('LocalStorage is not available. Defaulting to interpretation enabled.');
      return true;
    }
  }

  // Initialize transcription model dropdown
  const globalTranscriptionModel = document.getElementById('global-transcription-model');
  if (globalTranscriptionModel) {
    // Load saved preference
    const savedModel = loadTranscriptionModelPreference();

    // Check if the saved model is Gemini 2.5 Pro Preview which has been removed
    if (savedModel === 'gemini-2.5-pro-preview-03-25') {
      // Reset to default model (Gemini 2.0 Flash Lite)
      saveTranscriptionModelPreference('gemini');
      globalTranscriptionModel.value = 'gemini';
      showStatus('Your previously selected transcription model is no longer available. Defaulting to Gemini 2.0 Flash Lite.', 'info');
    } else {
      // Set the saved model if it's still available
      try {
        globalTranscriptionModel.value = savedModel;
      } catch (e) {
        // If there's an error (e.g., option doesn't exist), default to Gemini
        globalTranscriptionModel.value = 'gemini';
      }
    }

    // Update the upload model display
    updateUploadModelDisplay(globalTranscriptionModel);

    // Add event listener
    globalTranscriptionModel.addEventListener('change', () => {
      const model = globalTranscriptionModel.value;
      saveTranscriptionModelPreference(model);

      // Get the model display name
      const selectedOption = globalTranscriptionModel.options[globalTranscriptionModel.selectedIndex];
      const modelDisplayName = selectedOption ? selectedOption.textContent : model;

      // Update the upload model display
      updateUploadModelDisplay(globalTranscriptionModel);

      showStatus(`Transcription model changed to ${modelDisplayName}`, 'info');
    });
  }

  // Function to update the upload model display
  function updateUploadModelDisplay(modelSelect) {
    const uploadModelDisplay = document.getElementById('upload-model-display');
    if (uploadModelDisplay && modelSelect) {
      const selectedOption = modelSelect.options[modelSelect.selectedIndex];
      const modelDisplayName = selectedOption ? selectedOption.textContent : modelSelect.value;
      uploadModelDisplay.textContent = modelDisplayName;
    }
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

  // Load user-specific available models
  loadUserAvailableModels();

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

  // Basic mode file upload is now handled by file input change event
  // No form submission needed as we removed the form

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

            // Stop and clear recording timer
            if (recordingTimer) {
              clearInterval(recordingTimer);
              recordingTimer = null;
            }

            // Stop progressive transcription and process final chunk
            await stopProgressiveTranscriptionWithFinalChunk();

            // No timer display in main app

            // Hide continue button
            const continueButton = document.getElementById('continue-recording');
            if (continueButton && continueButton.parentNode) {
              continueButton.style.display = 'none';
              continueButton.parentNode.removeChild(continueButton);
            }

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
            const elementId = speaker.number === 1 ? 'transcript-1' : 'transcript-2';
            speaker.recording = await startRecording({
              recordButton: speaker.recordBtn,
              elementId: elementId
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

              // Stop and clear recording timer
              if (recordingTimer) {
                clearInterval(recordingTimer);
                recordingTimer = null;
              }

              // Stop progressive transcription and process final chunk
              await stopProgressiveTranscriptionWithFinalChunk();

              // No timer display in main app

              // Hide continue button
              const continueButton = document.getElementById('continue-recording');
              if (continueButton && continueButton.parentNode) {
                continueButton.style.display = 'none';
                continueButton.parentNode.removeChild(continueButton);
              }

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

  // File selection display and auto-transcription
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(input => {
    input.addEventListener('change', () => {
      // Basic mode file upload
      if (input.id === 'basic-file-input' && input.files.length) {
        const file = input.files[0];
        const fileSizeMB = file.size / (1024 * 1024);
        const fileName = file.name;

        // Check file size and show appropriate warnings based on selected model
        const selectedModel = getTranscriptionModel();

        // Validate model access if plan access control is available
        if (window.planAccessControl) {
          const validation = window.planAccessControl.validateModelAccess(selectedModel, 'transcription');
          if (!validation.allowed) {
            showStatus(validation.error.message, 'error');
            input.value = ''; // Clear the file input
            return;
          }
        }

        const isOpenAIModel = selectedModel.startsWith('gpt-') || selectedModel.startsWith('whisper-');

        // Show file info
        showStatus(`Selected file: ${fileName} (${fileSizeMB.toFixed(2)} MB)`, 'info');

        // Show warnings based on file size and selected model
        if (isOpenAIModel && fileSizeMB > 25) {
          showStatus(`Warning: File size (${fileSizeMB.toFixed(2)} MB) exceeds OpenAI's 25MB limit. Will automatically switch to Gemini.`, 'warning', true);
        } else if (fileSizeMB > 150) {
          showStatus(`Warning: Very large file (${fileSizeMB.toFixed(2)} MB). Consider splitting into smaller segments for better reliability.`, 'warning', true);
        } else if (fileSizeMB > 100) {
          showStatus(`Warning: Large file (${fileSizeMB.toFixed(2)} MB). Processing may take longer.`, 'warning');
        }

        // For extremely large files, show a more prominent warning
        if (fileSizeMB > 200) {
          if (!confirm(`This file is ${fileSizeMB.toFixed(2)} MB, which exceeds Gemini's 200MB limit. The transcription will likely fail. Do you want to continue anyway?`)) {
            // User chose to cancel
            input.value = ''; // Clear the file input
            showStatus('File upload cancelled. Please select a smaller file.', 'info');
            return;
          }
        }

        // Auto-start transcription when a file is selected
        // Create FormData object
        const formData = new FormData();
        formData.append('file', file);
        formData.append('language', document.getElementById('basic-language').value);
        formData.append('model', selectedModel);
        formData.append('speaker', 'basic');

        // Show status message
        showStatus('Transcribing your audio...', 'info');

        // Use the upload progress indicator
        if (window.sendToServerWithProgress) {
          // Store a reference to the upload button for state updates
          const uploadBtn = document.getElementById('basic-upload-btn');
          const uploadProgressInstance = uploadBtn._progressInstance;

          sendToServerWithProgress(formData, 'basic-upload-btn')
            .then(result => {
              // Check if this is a background processing job
              if (result.processing && result.job_id) {
                // Already handled by pollTranscriptionStatus
                showStatus('Processing large file in background...', 'info', true);
              } else {
                // Update transcript
                updateTranscript('basic-transcript', result.text || "No transcript received.");
                showStatus('Transcription complete!', 'success');
              }
            })
            .catch(error => {
              console.error('Upload error:', error);

              // User-friendly error messages
              if (error.name === 'AbortError' || error.message === 'Upload cancelled') {
                showStatus('Upload cancelled.', 'warning');
              } else if (error.name === 'AbortError') {
                showStatus('The request took too long to complete. Please try with a smaller file or check your connection.', 'warning');
              } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                showStatus('Network error. Please check your internet connection and try again.', 'error');
              } else {
                showStatus(`Error: ${error.message}`, 'error');
              }
            });
        } else {
          // Fallback to original method if progress indicator not available
          sendToServer(formData)
            .then(result => {
              // Update transcript
              updateTranscript('basic-transcript', result.text || "No transcript received.");
              showStatus('Transcription complete!', 'success');
            })
            .catch(error => {
              console.error('Upload error:', error);

              // User-friendly error messages
              if (error.name === 'AbortError') {
                showStatus('The request took too long to complete. Please try with a smaller file or check your connection.', 'warning');
              } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                showStatus('Network error. Please check your internet connection and try again.', 'error');
              } else {
                showStatus(`Error: ${error.message}`, 'error');
              }
            });
        }
      }
      // Bilingual mode file upload for Speaker 1
      else if (input.id === 'file-input-1' && input.files.length) {
        const file = input.files[0];
        const fileSizeMB = file.size / (1024 * 1024);
        const fileName = file.name;

        // Check file size and show appropriate warnings based on selected model
        const selectedModel = getTranscriptionModel();

        // Validate model access if plan access control is available
        if (window.planAccessControl) {
          const validation = window.planAccessControl.validateModelAccess(selectedModel, 'transcription');
          if (!validation.allowed) {
            showStatus(validation.error.message, 'error');
            input.value = ''; // Clear the file input
            return;
          }
        }

        const isOpenAIModel = selectedModel.startsWith('gpt-') || selectedModel.startsWith('whisper-');

        // Show file info
        showStatus(`Selected file for Speaker 1: ${fileName} (${fileSizeMB.toFixed(2)} MB)`, 'info');

        // Show warnings based on file size and selected model
        if (isOpenAIModel && fileSizeMB > 25) {
          showStatus(`Warning: File size (${fileSizeMB.toFixed(2)} MB) exceeds OpenAI's 25MB limit. Will automatically switch to Gemini.`, 'warning', true);
        } else if (fileSizeMB > 150) {
          showStatus(`Warning: Very large file (${fileSizeMB.toFixed(2)} MB). Consider splitting into smaller segments for better reliability.`, 'warning', true);
        } else if (fileSizeMB > 100) {
          showStatus(`Warning: Large file (${fileSizeMB.toFixed(2)} MB). Processing may take longer.`, 'warning');
        }

        // For extremely large files, show a more prominent warning
        if (fileSizeMB > 200) {
          if (!confirm(`This file is ${fileSizeMB.toFixed(2)} MB, which exceeds Gemini's 200MB limit. The transcription will likely fail. Do you want to continue anyway?`)) {
            // User chose to cancel
            input.value = ''; // Clear the file input
            showStatus('File upload cancelled. Please select a smaller file.', 'info');
            return;
          }
        }

        // Create FormData object
        const formData = new FormData();
        formData.append('file', file);
        formData.append('language', document.getElementById('language-1').value);
        formData.append('model', selectedModel);
        formData.append('speaker', '1');

        // Show status message
        showStatus('Transcribing Speaker 1 audio...', 'info');

        // Use the upload progress indicator
        if (window.sendToServerWithProgress) {
          // Store a reference to the upload button for state updates
          const uploadBtn = document.getElementById('upload-btn-1');

          sendToServerWithProgress(formData, 'upload-btn-1')
            .then(result => {
              // Update transcript
              updateTranscript('transcript-1', result.text || "No transcript received.");

              // Wait a moment to ensure the transcript is visible before removing the spinner
              setTimeout(() => {
                // Signal completion to the progress indicator
                if (uploadBtn && uploadBtn._progressInstance && uploadBtn._progressInstance.updateState) {
                  uploadBtn._progressInstance.updateState('completed');
                }
              }, 500);

              showStatus('Speaker 1 transcription complete!', 'success');
            })
            .catch(error => {
              console.error('Upload error:', error);

              if (error.message === 'Upload cancelled') {
                showStatus('Upload cancelled.', 'warning');
              } else {
                showStatus(`Error: ${error.message}`, 'error');
              }
            });
        } else {
          // Fallback to original method if progress indicator not available
          sendToServer(formData)
            .then(result => {
              // Update transcript
              updateTranscript('transcript-1', result.text || "No transcript received.");
              showStatus('Speaker 1 transcription complete!', 'success');
            })
            .catch(error => {
              console.error('Upload error:', error);
              showStatus(`Error: ${error.message}`, 'error');
            });
        }
      }
      // Bilingual mode file upload for Speaker 2
      else if (input.id === 'file-input-2' && input.files.length) {
        const file = input.files[0];
        const fileSizeMB = file.size / (1024 * 1024);
        const fileName = file.name;

        // Check file size and show appropriate warnings based on selected model
        const selectedModel = getTranscriptionModel();

        // Validate model access if plan access control is available
        if (window.planAccessControl) {
          const validation = window.planAccessControl.validateModelAccess(selectedModel, 'transcription');
          if (!validation.allowed) {
            showStatus(validation.error.message, 'error');
            input.value = ''; // Clear the file input
            return;
          }
        }

        const isOpenAIModel = selectedModel.startsWith('gpt-') || selectedModel.startsWith('whisper-');

        // Show file info
        showStatus(`Selected file for Speaker 2: ${fileName} (${fileSizeMB.toFixed(2)} MB)`, 'info');

        // Show warnings based on file size and selected model
        if (isOpenAIModel && fileSizeMB > 25) {
          showStatus(`Warning: File size (${fileSizeMB.toFixed(2)} MB) exceeds OpenAI's 25MB limit. Will automatically switch to Gemini.`, 'warning', true);
        } else if (fileSizeMB > 150) {
          showStatus(`Warning: Very large file (${fileSizeMB.toFixed(2)} MB). Consider splitting into smaller segments for better reliability.`, 'warning', true);
        } else if (fileSizeMB > 100) {
          showStatus(`Warning: Large file (${fileSizeMB.toFixed(2)} MB). Processing may take longer.`, 'warning');
        }

        // For extremely large files, show a more prominent warning
        if (fileSizeMB > 200) {
          if (!confirm(`This file is ${fileSizeMB.toFixed(2)} MB, which exceeds Gemini's 200MB limit. The transcription will likely fail. Do you want to continue anyway?`)) {
            // User chose to cancel
            input.value = ''; // Clear the file input
            showStatus('File upload cancelled. Please select a smaller file.', 'info');
            return;
          }
        }

        // Create FormData object
        const formData = new FormData();
        formData.append('file', file);
        formData.append('language', document.getElementById('language-2').value);
        formData.append('model', selectedModel);
        formData.append('speaker', '2');

        // Show status message
        showStatus('Transcribing Speaker 2 audio...', 'info');

        // Use the upload progress indicator
        if (window.sendToServerWithProgress) {
          // Store a reference to the upload button for state updates
          const uploadBtn = document.getElementById('upload-btn-2');

          sendToServerWithProgress(formData, 'upload-btn-2')
            .then(result => {
              // Update transcript
              updateTranscript('transcript-2', result.text || "No transcript received.");

              // Wait a moment to ensure the transcript is visible before removing the spinner
              setTimeout(() => {
                // Signal completion to the progress indicator
                if (uploadBtn && uploadBtn._progressInstance && uploadBtn._progressInstance.updateState) {
                  uploadBtn._progressInstance.updateState('completed');
                }
              }, 500);

              showStatus('Speaker 2 transcription complete!', 'success');
            })
            .catch(error => {
              console.error('Upload error:', error);

              if (error.message === 'Upload cancelled') {
                showStatus('Upload cancelled.', 'warning');
              } else {
                showStatus(`Error: ${error.message}`, 'error');
              }
            });
        } else {
          // Fallback to original method if progress indicator not available
          sendToServer(formData)
            .then(result => {
              // Update transcript
              updateTranscript('transcript-2', result.text || "No transcript received.");
              showStatus('Speaker 2 transcription complete!', 'success');
            })
            .catch(error => {
              console.error('Upload error:', error);
              showStatus(`Error: ${error.message}`, 'error');
            });
        }
      }
    });
  });

  // Function to poll for transcription job status
  async function pollTranscriptionStatus(jobId, elementId) {
    console.log(`🔄 Starting polling for job ${jobId}, target element: ${elementId}`);

    const maxAttempts = 60; // 5 minutes (5s intervals)
    let attempts = 0;

    showStatus('Processing large file in background...', 'info', true);

    const checkStatus = async () => {
      try {
        console.log(`📡 Checking status for job ${jobId}, attempt ${attempts + 1}/${maxAttempts}`);

        const response = await fetch(`/api/transcription_status/${jobId}`);
        const status = await response.json();

        console.log(`📋 Received status for job ${jobId}:`, status);

        if (status.status === 'completed' && status.result) {
          // Extract the text from the result - handle both string and object formats
          let transcriptionText;

          if (typeof status.result === 'string') {
            // Direct string result (used by background processing)
            transcriptionText = status.result;
          } else if (status.result.text) {
            // Object with text property (used by regular processing)
            transcriptionText = status.result.text;
          } else {
            // Fallback for unexpected formats
            transcriptionText = status.result.toString() || "Transcription completed but no text was returned.";
          }

          console.log('Transcription result format:', typeof status.result, 'Text length:', transcriptionText.length);

          // Update transcript using the proper updateTranscript function
          // This ensures all related functionality (original text storage, interpretation updates) works correctly
          updateTranscript(elementId, transcriptionText);

          console.log(`Successfully updated transcript element ${elementId} with ${transcriptionText.length} characters`);

          showStatus('Transcription complete!', 'success');
          return true;
        } else if (status.status === 'failed') {
          showStatus(`Transcription failed: ${status.error}`, 'error', true);
          return true;
        } else if (status.status === 'processing') {
          // Continue polling
          showStatus(`Processing large file... ${status.progress || ''}`, 'info', true);
          return false;
        } else {
          showStatus('Transcription status unknown', 'warning');
          return true;
        }
      } catch (error) {
        console.error('Error checking transcription status:', error);
        showStatus('Error checking transcription status', 'error');
        return true; // Stop polling on error
      }
    };

    // Start polling
    const poll = async () => {
      attempts++;
      const done = await checkStatus();

      if (!done && attempts < maxAttempts) {
        setTimeout(poll, 5000); // Check every 5 seconds
      } else if (!done) {
        showStatus('Transcription timed out. Please check back later.', 'warning', true);
      }
    };

    poll();
  }

  // Update the sendToServer function to handle background processing
  async function sendToServerWithBackgroundSupport(formData, uploadButtonId, endpoint = '/api/transcribe') {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const result = await response.json();

      // Check if this is a background processing job
      if (result.status === 'processing' && result.job_id) {
        // Determine which transcript element to update based on formData
        let elementId = 'basic-transcript';

        // For conversation mode, check if this is speaker 1 or 2
        const speaker = formData.get('speaker');
        if (speaker === '1') {
          elementId = 'transcript-1';
        } else if (speaker === '2') {
          elementId = 'transcript-2';
        }

        // Start polling for status
        pollTranscriptionStatus(result.job_id, elementId);

        // Return a placeholder result
        return {
          text: "Processing large file in background...",
          processing: true,
          job_id: result.job_id
        };
      }

      // Regular result
      return result;
    } catch (error) {
      console.error('Error sending to server:', error);
      throw error;
    }
  }

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
    // Always hide settings by default on all devices
    function updateSettingsPanelVisibility() {
      // Hide settings by default on all devices
      settingsPanel.style.display = 'none';
      settingsToggle.classList.remove('active');
    }

    // Initial setup
    updateSettingsPanelVisibility();

    // Toggle settings panel when button is clicked
    settingsToggle.addEventListener('click', () => {
      const isVisible = settingsPanel.style.display === 'block';
      settingsPanel.style.display = isVisible ? 'none' : 'block';
      settingsToggle.classList.toggle('active');
    });

    // No need to update on window resize since we always hide settings by default
  }

  // Initialize editable transcript functionality
  setupTranslateEditedButtons();
  setupUndoButtons();

  // Initialize TTS model selector
  const ttsModelSelect = document.getElementById('tts-model-select');
  if (ttsModelSelect) {
    // Set default to free model
    ttsModelSelect.value = 'gemini-2.5-flash-tts';

    // Save selection to localStorage when changed
    ttsModelSelect.addEventListener('change', function() {
      localStorage.setItem('tts-model', this.value);

      // Get the display name from the selected option
      const selectedOption = this.options[this.selectedIndex];
      const displayName = selectedOption ? selectedOption.textContent : this.value;
      showStatus(`TTS model set to ${displayName}`, 'success');
    });

    // Load saved selection from localStorage if available
    const savedTtsModel = localStorage.getItem('tts-model');
    if (savedTtsModel) {
      ttsModelSelect.value = savedTtsModel;
    }
  }

  // Initialize interpretation model selector
  const interpretationModelSelect = document.getElementById('interpretation-model-select');
  if (interpretationModelSelect) {
    // Load saved preference
    const savedModel = loadInterpretationModelPreference();
    interpretationModelSelect.value = savedModel;

    // Add event listener
    interpretationModelSelect.addEventListener('change', () => {
      const model = interpretationModelSelect.value;
      saveInterpretationModelPreference(model);

      // Get the model display name
      const selectedOption = interpretationModelSelect.options[interpretationModelSelect.selectedIndex];
      const modelDisplayName = selectedOption ? selectedOption.textContent : model;

      showStatus(`Interpretation model changed to ${modelDisplayName}`, 'info');

      // If interpretation is enabled and there's text in the transcript, update the interpretation
      const isEnabled = loadInterpretationEnabledPreference();
      if (isEnabled) {
        const transcriptEl = document.getElementById('basic-transcript');
        if (transcriptEl && transcriptEl.value.trim() !== '') {
          updateInterpretation(transcriptEl.value);
        }
      }
    });
  }

  // Initialize interpretation tone selector
  const interpretationToneSelect = document.getElementById('interpretation-tone-select');
  if (interpretationToneSelect) {
    // Load saved preference
    const savedTone = loadInterpretationTonePreference();
    interpretationToneSelect.value = savedTone;

    // Add event listener
    interpretationToneSelect.addEventListener('change', () => {
      const tone = interpretationToneSelect.value;
      saveInterpretationTonePreference(tone);

      // Get the tone display name
      const selectedOption = interpretationToneSelect.options[interpretationToneSelect.selectedIndex];
      const toneDisplayName = selectedOption ? selectedOption.textContent : tone;

      showStatus(`Interpretation tone changed to ${toneDisplayName}`, 'info');

      // If interpretation is enabled and there's text in the transcript, update the interpretation
      const isEnabled = loadInterpretationEnabledPreference();
      if (isEnabled) {
        const transcriptEl = document.getElementById('basic-transcript');
        if (transcriptEl && transcriptEl.value.trim() !== '') {
          updateInterpretation(transcriptEl.value);
        }
      }
    });
  }

  // Initialize interpretation toggle
  const enableInterpretationToggle = document.getElementById('enable-interpretation');
  if (enableInterpretationToggle) {
    // Load saved preference
    const isEnabled = loadInterpretationEnabledPreference();
    enableInterpretationToggle.checked = isEnabled;

    // Set initial visibility of interpretation section and settings
    toggleInterpretationSection(isEnabled);

    // Add event listener
    enableInterpretationToggle.addEventListener('change', () => {
      const isEnabled = enableInterpretationToggle.checked;
      saveInterpretationEnabledPreference(isEnabled);

      // Toggle visibility of interpretation section and settings
      toggleInterpretationSection(isEnabled);

      // Show status message
      showStatus(`AI Interpretation ${isEnabled ? 'enabled' : 'disabled'}`, 'info');

      // If enabled and there's text in the transcript, update the interpretation
      if (isEnabled) {
        const transcriptEl = document.getElementById('basic-transcript');
        if (transcriptEl && transcriptEl.value.trim() !== '') {
          updateInterpretation(transcriptEl.value);
        }
      }
    });
  }

  // Basic mode interpretation button
  const basicInterpretBtn = document.getElementById('basic-interpret-btn');
  if (basicInterpretBtn) {
    basicInterpretBtn.addEventListener('click', async () => {
      // Check if interpretation is enabled
      const isEnabled = loadInterpretationEnabledPreference();
      if (!isEnabled) {
        showStatus('AI Interpretation is disabled. Enable it in settings to use this feature.', 'warning');
        return;
      }

      const transcriptEl = document.getElementById('basic-transcript');
      const interpretationEl = document.getElementById('basic-interpretation');

      if (!transcriptEl || !interpretationEl) return;

      const text = transcriptEl.value;
      if (!text || text.trim() === '') {
        showStatus('No text to interpret', 'warning');
        return;
      }

      // Get the selected tone
      const toneSelect = document.getElementById('interpretation-tone-select');
      const tone = toneSelect ? toneSelect.value : 'professional';

      // Generate interpretation
      const interpretation = await interpretText(text, tone);

      if (interpretation) {
        interpretationEl.value = interpretation;
      }
    });
  }

  // Basic mode interpretation play/stop buttons
  const basicPlayInterpretationBtn = document.getElementById('basic-play-interpretation-btn');
  const basicStopInterpretationBtn = document.getElementById('basic-stop-interpretation-btn');

  if (basicPlayInterpretationBtn) {
    basicPlayInterpretationBtn.addEventListener('click', () => {
      const interpretationEl = document.getElementById('basic-interpretation');
      if (!interpretationEl) return;

      const text = interpretationEl.value;
      const langSelect = document.getElementById('basic-language');
      const lang = langSelect ? langSelect.value : 'en';

      if (isMobileDevice()) {
        setTimeout(() => {
          const currentText = interpretationEl.value;
          speakText('basic-interpretation', currentText, lang);
        }, 50);
      } else {
        speakText('basic-interpretation', text, lang);
      }
    });
  }

  if (basicStopInterpretationBtn) {
    basicStopInterpretationBtn.addEventListener('click', () => {
      stopSpeakText('basic-interpretation');
    });
  }

  // Basic mode copy interpretation button
  const basicCopyInterpretationBtn = document.getElementById('basic-copy-interpretation-btn');
  if (basicCopyInterpretationBtn) {
    basicCopyInterpretationBtn.addEventListener('click', () => {
      const interpretationEl = document.getElementById('basic-interpretation');
      if (!interpretationEl) return;

      const text = interpretationEl.value;
      copyTextToClipboard(text, 'Interpretation copied to clipboard!');
    });
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
