document.addEventListener('DOMContentLoaded', () => {
  // ========================
  // CRITICAL: ENSURE RECORD BUTTON VISIBILITY FIRST
  // ========================
  function ensureRecordButtonVisibility() {
    const recordBtn = document.getElementById('basic-record-btn');
    if (recordBtn) {
      // Force visibility with maximum specificity - circular button
      recordBtn.style.setProperty('display', 'flex', 'important');
      recordBtn.style.setProperty('visibility', 'visible', 'important');
      recordBtn.style.setProperty('opacity', '1', 'important');
      recordBtn.style.setProperty('position', 'relative', 'important');
      recordBtn.style.setProperty('z-index', '100', 'important');

      // Ensure icon is present and visible (icon-only circular button)
      let icon = recordBtn.querySelector('i');

      if (!icon) {
        recordBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        icon = recordBtn.querySelector('i');
      }

      // Force icon visibility with comprehensive styling
      if (icon) {
        icon.style.setProperty('display', 'inline-block', 'important');
        icon.style.setProperty('visibility', 'visible', 'important');
        icon.style.setProperty('opacity', '1', 'important');
        icon.style.setProperty('color', 'white', 'important');
        icon.style.setProperty('font-size', '20px', 'important');
        icon.style.setProperty('font-family', '"Font Awesome 6 Free", "Font Awesome 5 Free", FontAwesome', 'important');
        icon.style.setProperty('font-weight', '900', 'important');
        icon.style.setProperty('font-style', 'normal', 'important');
        icon.style.setProperty('line-height', '1', 'important');
        icon.style.setProperty('text-align', 'center', 'important');
        icon.style.setProperty('position', 'relative', 'important');
        icon.style.setProperty('z-index', '1000', 'important');
      }

      console.log('✅ Record button visibility ensured');
    } else {
      console.error('❌ Record button not found in DOM');
    }
  }

  // Ensure record button is visible immediately
  ensureRecordButtonVisibility();

  // Also ensure it stays visible with periodic checks
  setInterval(ensureRecordButtonVisibility, 1000);

  // ========================
  // DOM ELEMENT VERIFICATION TEST
  // ========================
  console.log('🔍 DOM VERIFICATION: Checking all TTS button elements...');

  const transcriptPlayBtn = document.getElementById('basic-play-btn');
  const transcriptStopBtn = document.getElementById('basic-stop-btn');
  const interpretationPlayBtn = document.getElementById('basic-play-interpretation-btn');
  const interpretationStopBtn = document.getElementById('basic-stop-interpretation-btn');
  const interpretationTextarea = document.getElementById('basic-interpretation');
  const transcriptTextarea = document.getElementById('basic-transcript');
  const languageSelect = document.getElementById('basic-language');

  console.log('🔍 DOM VERIFICATION Results:', {
    transcriptPlayBtn: !!transcriptPlayBtn,
    transcriptStopBtn: !!transcriptStopBtn,
    interpretationPlayBtn: !!interpretationPlayBtn,
    interpretationStopBtn: !!interpretationStopBtn,
    interpretationTextarea: !!interpretationTextarea,
    transcriptTextarea: !!transcriptTextarea,
    languageSelect: !!languageSelect
  });

  if (!interpretationPlayBtn) {
    console.error('❌ DOM VERIFICATION: Interpretation play button NOT FOUND in DOM!');
  } else {
    console.log('✅ DOM VERIFICATION: Interpretation play button found in DOM');
  }

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
      plan: data.user_plan,
      hasPremiumAccess: data.has_premium_access,
      restrictions: data.restrictions
    };

    // Show role and plan-based status message
    if (data.user_role === 'super_user') {
      showStatus('Super User access: All models available', 'success');
    } else if (data.user_role === 'admin') {
      showStatus('Admin access: Full system access', 'success');
    } else if (data.user_role === 'normal_user') {
      // Check plan type for appropriate messaging
      if (data.user_plan === 'professional') {
        showStatus('Professional plan active: Full access to all models', 'success');
      } else if (data.user_plan === 'basic') {
        showStatus('Basic plan active: Access to premium models included', 'success');
      } else {
        // Free plan users
        showStatus('Free models available. Upgrade for premium models.', 'info');
      }
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
    'transcription': ['gemini-2.5-flash-preview', 'gpt-4o-mini-transcribe', 'gpt-4o-transcribe', 'gemini-2.5-flash-preview-05-20'],
    'translation': ['gemini-2.5-flash-preview', 'gpt-4.1-mini']
  };

  // Store current selection
  const currentValue = selectElement.value;

  // Clear existing options
  selectElement.innerHTML = '';

  // Filter models to only include authorized ones and remove duplicates
  const filteredModels = models.filter(model => {
    if (modelType === 'transcription') {
      return authorizedModels.transcription.includes(model.value);
    } else if (modelType === 'translation') {
      return authorizedModels.translation.includes(model.value);
    }
    return true; // Allow other model types (TTS, interpretation) to pass through
  });

  // Remove duplicates based on model value
  const uniqueModels = filteredModels.filter((model, index, self) =>
    index === self.findIndex(m => m.value === model.value)
  );

  // Add unique authorized models only
  uniqueModels.forEach(model => {
    const option = document.createElement('option');
    option.value = model.value;
    option.textContent = model.label;

    // Add title attribute for additional context
    if (model.free) {
      option.title = `${model.label} - Free Access`;
    } else {
      option.title = `${model.label} - Premium Access`;
    }

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

  console.log(`Updated ${modelType} model dropdown with ${uniqueModels.length} unique authorized models (filtered from ${models.length} total, removed ${filteredModels.length - uniqueModels.length} duplicates)`);
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

  // Global state for TTS audio objects (for pause/resume functionality)
  const ttsAudioObjects = {};

  // Debug function to check TTS state
  window.debugTTSState = function(sourceId) {
    const audioObj = ttsAudioObjects[sourceId];
    const player = ttsPlayers[sourceId];

    console.log('🔍 TTS Debug State for', sourceId, ':', {
      hasAudioObject: !!audioObj,
      audioState: audioObj ? {
        paused: audioObj.paused,
        ended: audioObj.ended,
        currentTime: audioObj.currentTime,
        duration: audioObj.duration,
        readyState: audioObj.readyState
      } : null,
      hasPlayer: !!player,
      playerUrl: player ? player.url : null
    });

    return { audioObj, player };
  };

  // Function to manage button states for TTS
  function setTTSButtonState(sourceId, state) {
    console.log('🔘 TTS Debug: setTTSButtonState called with:', { sourceId, state });
    let playBtn, stopBtn;

    // Handle different button ID patterns based on sourceId
    if (sourceId === 'basic-transcript') {
      // Basic mode transcript buttons
      playBtn = document.getElementById('basic-play-btn');
      stopBtn = document.getElementById('basic-stop-btn');
      console.log('🔘 TTS Debug: Basic transcript buttons found:', { playBtn: !!playBtn, stopBtn: !!stopBtn });
    } else if (sourceId === 'basic-interpretation') {
      // Basic mode interpretation buttons
      playBtn = document.getElementById('basic-play-interpretation-btn');
      stopBtn = document.getElementById('basic-stop-interpretation-btn');
      console.log('🔘 TTS Debug: Basic interpretation buttons found:', { playBtn: !!playBtn, stopBtn: !!stopBtn });
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
    } else if (sourceId === 'bilingual-original-text') {
      // New bilingual mode original text buttons
      playBtn = document.getElementById('play-original');
      stopBtn = document.getElementById('stop-original');
      console.log('🔘 TTS Debug: Bilingual original buttons found:', { playBtn: !!playBtn, stopBtn: !!stopBtn });
    } else if (sourceId === 'bilingual-translation-text') {
      // New bilingual mode translation text buttons
      playBtn = document.getElementById('play-translation');
      stopBtn = document.getElementById('stop-translation');
      console.log('🔘 TTS Debug: Bilingual translation buttons found:', { playBtn: !!playBtn, stopBtn: !!stopBtn });
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
      // Show pause icon when playing
      const playIcon = playBtn.querySelector('i');
      if (playIcon) {
        playIcon.className = 'fas fa-pause';
      }
      playBtn.style.display = 'inline-flex';
      stopBtn.style.display = 'inline-flex';
      playBtn.setAttribute('title', 'Pause audio');
      console.log(`TTS Button State: ${sourceId} - PLAYING - Showing pause button`);

      // Dispatch TTS started event
      document.dispatchEvent(new CustomEvent('tts-started', {
        detail: { sourceId: sourceId }
      }));
    } else if (state === 'paused') {
      // Show play icon when paused
      const playIcon = playBtn.querySelector('i');
      if (playIcon) {
        playIcon.className = 'fas fa-play';
      }
      playBtn.style.display = 'inline-flex';
      stopBtn.style.display = 'inline-flex';
      playBtn.setAttribute('title', 'Resume audio');
      console.log(`TTS Button State: ${sourceId} - PAUSED - Showing play button for resume`);

      // Dispatch TTS paused event
      document.dispatchEvent(new CustomEvent('tts-paused', {
        detail: { sourceId: sourceId }
      }));
    } else { // 'stopped', 'ended', 'error', 'ready'
      // Show play icon when stopped
      const playIcon = playBtn.querySelector('i');
      if (playIcon) {
        playIcon.className = 'fas fa-play';
      }
      playBtn.style.display = 'inline-flex';
      stopBtn.style.display = 'none';
      playBtn.setAttribute('title', 'Play audio');
      console.log(`TTS Button State: ${sourceId} - ${state} - Showing play button`);

      // Dispatch appropriate TTS event
      const eventType = state === 'ended' ? 'tts-ended' : 'tts-stopped';
      document.dispatchEvent(new CustomEvent(eventType, {
        detail: { sourceId: sourceId }
      }));
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
    console.log('🛑 TTS Debug: stopAllAudio called');

    let stoppedCount = 0;

    // Stop all TTS players
    Object.keys(ttsPlayers).forEach(sourceId => {
      if (ttsPlayers[sourceId] && ttsPlayers[sourceId].audio) {
        console.log('🛑 TTS Debug: Stopping audio for sourceId:', sourceId);
        const player = ttsPlayers[sourceId];

        // Stop the audio completely
        player.audio.pause();
        player.audio.currentTime = 0;

        // Clean up the URL to free memory
        if (player.url) {
          URL.revokeObjectURL(player.url);
        }

        // Update button state for this sourceId
        setTTSButtonState(sourceId, 'ready');

        // Clean up the player reference
        delete ttsPlayers[sourceId];
        stoppedCount++;
      }
    });

    // Stop global currentAudio as fallback
    if (currentAudio) {
      console.log('🛑 TTS Debug: Stopping global currentAudio');
      currentAudio.pause();
      currentAudio.currentTime = 0;
      currentAudio = null;
      stoppedCount++;
    }

    console.log(`🛑 TTS Debug: All audio stopped (${stoppedCount} streams)`);
    showStatus(`All audio playback stopped (${stoppedCount} streams)`, 'info');
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

  // Function to pause TTS playback
  function pauseSpeakText(sourceId) {
    console.log('⏸️ TTS Debug: pauseSpeakText called for sourceId:', sourceId);

    const audioObj = ttsAudioObjects[sourceId];
    if (audioObj && !audioObj.paused) {
      audioObj.pause();
      setTTSButtonState(sourceId, 'paused');
      showStatus('Audio paused', 'info');
      console.log('✅ TTS Debug: Audio paused successfully');
    } else {
      console.log('⚠️ TTS Debug: No active audio to pause for sourceId:', sourceId);
    }
  }

  // Function to resume TTS playback
  function resumeSpeakText(sourceId) {
    console.log('▶️ TTS Debug: resumeSpeakText called for sourceId:', sourceId);

    const audioObj = ttsAudioObjects[sourceId];
    if (audioObj && audioObj.paused) {
      audioObj.play()
        .then(() => {
          setTTSButtonState(sourceId, 'playing');
          showStatus('Audio resumed', 'info');
          console.log('✅ TTS Debug: Audio resumed successfully');
        })
        .catch(error => {
          console.error('❌ TTS Debug: Error resuming audio:', error);
          showStatus('Error resuming audio: ' + error.message, 'danger');
        });
    } else {
      console.log('⚠️ TTS Debug: No paused audio to resume for sourceId:', sourceId);
    }
  }

  // Speak text using TTS with play/pause/resume
  function speakText(sourceId, text, langCode) {
    console.log('🎵 TTS Debug: speakText called with:', {
      sourceId: sourceId,
      textLength: text ? text.length : 0,
      textPreview: text ? text.substring(0, 50) + '...' : 'EMPTY',
      langCode: langCode,
      isMobile: isMobileDevice()
    });

    // Check if there's a paused audio for this sourceId that can be resumed
    const existingAudio = ttsAudioObjects[sourceId];
    if (existingAudio && existingAudio.paused && !existingAudio.ended) {
      console.log('🔄 TTS Debug: Found paused audio, resuming instead of creating new');
      resumeSpeakText(sourceId);
      return;
    }

    // Always get the latest text from DOM for certain sourceIds
    if (isMobileDevice() || sourceId.includes('-') || sourceId === 'basic-transcript' || sourceId === 'basic-interpretation') {
      console.log('🔍 TTS Debug: Getting text from DOM for sourceId:', sourceId);

      // For translation elements, always get the current text from the DOM
      if (sourceId.startsWith('translation-')) {
        const speakerId = sourceId.split('-')[1];
        const translationEl = document.getElementById(`translation-${speakerId}`);
        if (translationEl && translationEl.value.trim() !== '') {
          text = translationEl.value;
          console.log(`🔍 TTS Debug: Retrieved text from translation-${speakerId}:`, text.substring(0, 30) + '...');
        }
      } else if (sourceId.startsWith('transcript-')) {
        const speakerId = sourceId.split('-')[1];
        const transcriptEl = document.getElementById(`transcript-${speakerId}`);
        if (transcriptEl && transcriptEl.value.trim() !== '') {
          text = transcriptEl.value;
          console.log(`🔍 TTS Debug: Retrieved text from transcript-${speakerId}:`, text.substring(0, 30) + '...');
        }
      } else if (sourceId === 'basic-transcript') {
        const transcriptEl = document.getElementById('basic-transcript');
        if (transcriptEl && transcriptEl.value.trim() !== '') {
          text = transcriptEl.value;
          console.log('🔍 TTS Debug: Retrieved text from basic-transcript:', text.substring(0, 30) + '...');
        }
      } else if (sourceId === 'basic-interpretation') {
        console.log('🔍 TTS Debug: Handling basic-interpretation case');
        const interpretationEl = document.getElementById('basic-interpretation');
        console.log('🔍 TTS Debug: Interpretation element found:', !!interpretationEl);

        if (interpretationEl) {
          console.log('🔍 TTS Debug: Interpretation element value length:', interpretationEl.value.length);
          console.log('🔍 TTS Debug: Interpretation element value preview:', interpretationEl.value.substring(0, 50) + '...');

          if (interpretationEl.value.trim() !== '') {
            text = interpretationEl.value;
            console.log('✅ TTS Debug: Successfully retrieved interpretation text:', text.substring(0, 30) + '...');
          } else {
            console.warn('⚠️ TTS Debug: Interpretation textarea is empty');
          }
        } else {
          console.error('❌ TTS Debug: Interpretation textarea not found in DOM');
        }
      } else if (sourceId === 'bilingual-original-text') {
        console.log('🔍 TTS Debug: Handling bilingual-original-text case');
        const originalEl = document.getElementById('bilingual-original-text');
        if (originalEl && originalEl.value.trim() !== '') {
          text = originalEl.value;
          console.log('✅ TTS Debug: Successfully retrieved bilingual original text:', text.substring(0, 30) + '...');
        }
      } else if (sourceId === 'bilingual-translation-text') {
        console.log('🔍 TTS Debug: Handling bilingual-translation-text case');
        const translationEl = document.getElementById('bilingual-translation-text');
        if (translationEl && translationEl.value.trim() !== '') {
          text = translationEl.value;
          console.log('✅ TTS Debug: Successfully retrieved bilingual translation text:', text.substring(0, 30) + '...');
        }
      }
    }

    if (!text || text.trim() === '') {
      console.error('❌ TTS Debug: No text to speak');
      showStatus('No text to speak', 'warning');
      return;
    }

    console.log('✅ TTS Debug: Text validation passed, proceeding with TTS');

    // Stop any currently playing audio
    stopAllAudio();

    // Get the selected TTS model
    const ttsModelSelect = document.getElementById('tts-model-select');
    const ttsModel = ttsModelSelect ? ttsModelSelect.value : 'auto'; // Default to auto if not found
    console.log('🔍 TTS Debug: Selected TTS model:', ttsModel);

    // Validate TTS access first
    console.log('🔍 TTS Debug: Checking TTS access control...');
    if (window.ttsAccessControl && window.ttsAccessControl.hasLoadedUserInfo) {
      console.log('🔍 TTS Debug: TTS access control found, validating access...');
      const accessValidation = window.ttsAccessControl.validateTTSAccess();
      console.log('🔍 TTS Debug: Access validation result:', accessValidation);

      if (!accessValidation.allowed) {
        console.warn('⚠️ TTS Debug: TTS access denied, showing upgrade modal');
        window.ttsAccessControl.showTTSUpgradeModal();
        setTTSButtonState(sourceId, 'error');
        return;
      }
      console.log('✅ TTS Debug: TTS access granted');
    } else {
      console.log('🔍 TTS Debug: TTS access control not available or not loaded');
    }

    // Validate model access if model access control is available
    console.log('🔍 TTS Debug: Checking model access control...');
    if (window.modelAccessControl && window.modelAccessControl.hasLoadedUserRole) {
      console.log('🔍 TTS Debug: Model access control found, checking model access...');
      const canAccess = window.modelAccessControl.canAccessModel(ttsModel);
      console.log('🔍 TTS Debug: Can access model:', canAccess);

      if (!canAccess) {
        console.warn('⚠️ TTS Debug: Model access denied, showing upgrade prompt');
        window.modelAccessControl.showUpgradePrompt(ttsModel);
        setTTSButtonState(sourceId, 'error');
        return;
      }
      console.log('✅ TTS Debug: Model access granted');
    } else {
      console.log('🔍 TTS Debug: Model access control not available or not loaded');
    }

    // Show loading status
    console.log('🔍 TTS Debug: Setting loading state and making API request...');
    showStatus(`Generating audio using ${ttsModel} TTS...`, 'info');
    setTTSButtonState(sourceId, 'loading');

    const apiPayload = {
      text: text,
      language: langCode,
      tts_model: ttsModel
    };
    console.log('🔍 TTS Debug: API payload:', apiPayload);

    // Make API request
    fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(apiPayload)
    })
    .then(response => {
      console.log('🔍 TTS Debug: API response received:', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      });

      if (!response.ok) {
        throw new Error(`TTS service error (${response.status}): ${response.statusText}`);
      }
      return response.blob();
    })
    .then(audioBlob => {
      console.log('🔍 TTS Debug: Audio blob received:', {
        size: audioBlob.size,
        type: audioBlob.type
      });

      // Create URL for the audio blob
      const audioUrl = URL.createObjectURL(audioBlob);
      console.log('🔍 TTS Debug: Audio URL created:', audioUrl);

      // Create and play the audio
      const audio = new Audio(audioUrl);
      console.log('🔍 TTS Debug: Audio object created');

      // Store the audio element both globally and per-source
      currentAudio = audio;
      ttsPlayers[sourceId] = { audio: audio, url: audioUrl };
      ttsAudioObjects[sourceId] = audio; // Store for pause/resume functionality
      console.log('🔍 TTS Debug: Audio stored in ttsPlayers and ttsAudioObjects for sourceId:', sourceId);

      // Set playback rate to 1.10 (10% faster)
      audio.playbackRate = 1.10;
      console.log('🔍 TTS Debug: Playback rate set to 1.10');

      // Add event listeners for proper button state management
      audio.onplay = () => {
        console.log('🎵 TTS Debug: Audio onplay event fired');
        setTTSButtonState(sourceId, 'playing');
        showStatus('Playing audio...', 'info');
      };

      audio.onpause = () => {
        console.log('⏸️ TTS Debug: Audio onpause event fired');
        setTTSButtonState(sourceId, 'paused');
        showStatus('Playback paused.', 'info');
      };

      audio.onended = () => {
        console.log('🏁 TTS Debug: Audio onended event fired');
        setTTSButtonState(sourceId, 'stopped');
        URL.revokeObjectURL(audioUrl);
        currentAudio = null;
        delete ttsPlayers[sourceId];
        delete ttsAudioObjects[sourceId]; // Clean up pause/resume audio object
        showStatus('Playback completed.', 'info');
      };

      audio.onerror = (event) => {
        console.error('❌ TTS Debug: Audio onerror event fired:', event);
        setTTSButtonState(sourceId, 'error');
        showStatus('Audio playback error', 'danger');
        URL.revokeObjectURL(audioUrl);
        currentAudio = null;
        delete ttsPlayers[sourceId];
        delete ttsAudioObjects[sourceId]; // Clean up pause/resume audio object
      };

      // Play the audio
      console.log('🎵 TTS Debug: Attempting to play audio...');
      audio.play()
        .then(() => {
          console.log('✅ TTS Debug: Audio play() promise resolved successfully');
        })
        .catch(error => {
          console.error('❌ TTS Debug: Audio play() promise rejected:', error);
          showStatus('Error playing audio: ' + error.message, 'danger');
          fallbackSpeakText(sourceId, text, langCode);
        });
    })
    .catch(error => {
      console.error('❌ TTS Debug: API request failed:', error);
      showStatus('Error generating speech: ' + error.message, 'danger');

      // Fallback to browser's speech synthesis
      console.log('🔄 TTS Debug: Attempting fallback to browser TTS');
      fallbackSpeakText(sourceId, text, langCode);
    })
    .finally(() => {
      console.log('🔍 TTS Debug: Finally block executed, setting button state to ready');
      setTTSButtonState(sourceId, 'ready');
    });
  }

  // Function to completely stop TTS playback (not pause)
  function stopSpeakText(sourceId) {
    console.log('⏹️ TTS Debug: stopSpeakText called for sourceId:', sourceId);

    // Try to stop the specific audio for this sourceId
    if (ttsPlayers[sourceId] && ttsPlayers[sourceId].audio) {
      console.log('⏹️ TTS Debug: Stopping audio for sourceId:', sourceId);
      const player = ttsPlayers[sourceId];

      // Stop the audio completely
      player.audio.pause();
      player.audio.currentTime = 0;

      // Clean up the URL to free memory
      if (player.url) {
        URL.revokeObjectURL(player.url);
      }

      // Update button state immediately
      setTTSButtonState(sourceId, 'stopped');

      // Clean up the player reference
      delete ttsPlayers[sourceId];
      delete ttsAudioObjects[sourceId]; // Clean up pause/resume audio object

      // Clear global currentAudio if it matches this audio
      if (currentAudio === player.audio) {
        currentAudio = null;
      }

      showStatus('Playback stopped.', 'info');
      console.log('⏹️ TTS Debug: Audio stopped and cleaned up for sourceId:', sourceId);
      return;
    }

    // Fallback: stop global currentAudio if it exists
    if (currentAudio && !currentAudio.paused) {
      console.log('⏹️ TTS Debug: Stopping global currentAudio as fallback');
      currentAudio.pause();
      currentAudio.currentTime = 0;
      currentAudio = null;
      setTTSButtonState(sourceId, 'ready');
      showStatus('Playback stopped.', 'info');
    } else {
      console.log('⏹️ TTS Debug: No active audio found for sourceId:', sourceId);
      // Still update button state in case UI is out of sync
      setTTSButtonState(sourceId, 'ready');
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
      // Don't disable the button - let it show an error when clicked instead
      console.warn('MediaRecorder API not supported, but keeping record button visible');
      return false;
    }

    // Check for getUserMedia support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showStatus('Your browser does not support microphone access. Please try a modern browser.', 'error', true);
      // Don't disable the button - let it show an error when clicked instead
      console.warn('getUserMedia not supported, but keeping record button visible');
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
  let MAX_RECORDING_DURATION = 20 * 60; // 20 minutes in seconds
  let WARNING_THRESHOLD = 19 * 60; // 19 minutes in seconds

  // Simple recording variables
  let currentMediaRecorder = null;
  let currentStream = null;

  // Function to reset recording state between sessions
  function resetRecordingState() {
    // Clear timers
    if (recordingTimer) {
      clearInterval(recordingTimer);
      recordingTimer = null;
    }

    // Reset timing variables
    recordingStartTime = null;
    recordingDuration = 0;

    // Clean up stream
    if (currentStream) {
      currentStream.getTracks().forEach(track => track.stop());
      currentStream = null;
    }

    // Reset recorder
    currentMediaRecorder = null;

    // Reset duration limits to defaults
    MAX_RECORDING_DURATION = 20 * 60; // 20 minutes
    WARNING_THRESHOLD = 19 * 60; // 19 minutes

    console.log('Recording state reset for new session');
  }

  // Format seconds as MM:SS
  function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
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

  // Audio recording function - simplified without chunking
  async function startRecording(options = {}) {
    try {
      // Reset recording state for clean session
      resetRecordingState();

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

      // Store stream reference
      currentStream = stream;

      // Get the best supported MIME type
      const { bestType } = getSupportedMediaTypes();

      // Configure recorder for single-session recording
      const recorderOptions = bestType ? { mimeType: bestType } : {};
      const mediaRecorder = new MediaRecorder(stream, recorderOptions);

      // Setup data array for recording
      const audioChunks = [];

      // Data available listener
      mediaRecorder.addEventListener('dataavailable', event => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      });

      // Start recording
      mediaRecorder.start(100); // Get events more frequently for better responsiveness

      // Store as current recorder
      currentMediaRecorder = mediaRecorder;
      showStatus('Recording started', 'success');

      // Add visual feedback for recording
      const recordButton = options.recordButton || null;
      if (recordButton) {
        recordButton.classList.add('recording');
        // Update button text to "Stop Recording"
        const textSpan = recordButton.querySelector('.record-button-text');
        if (textSpan) {
          textSpan.textContent = 'Stop Recording';
        }
      }

      // Start recording timer
      recordingStartTime = new Date();
      if (recordingTimer) clearInterval(recordingTimer);
      recordingTimer = setInterval(() => updateRecordingTimer(), 1000);

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

      console.log('sendToServer called with:', {
        endpoint,
        maxRetries,
        formDataEntries: Array.from(formData.entries()).map(([key, value]) => [
          key,
          value instanceof File ? `File(${value.name}, ${value.size} bytes, ${value.type})` : value
        ])
      });

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

  // Smart file size detection and routing
  function processAudioWithSmartRouting(audioChunks, mimeType, formData) {
    return new Promise(async (resolve, reject) => {
      try {
        // First process the audio to get the file
        const processedFormData = await processAudio(audioChunks, mimeType, formData);
        const file = processedFormData.get('file');

        if (!file) {
          reject(new Error('No audio file created'));
          return;
        }

        // Check file size (25MB threshold)
        const fileSizeMB = file.size / (1024 * 1024);
        const CHUNKING_THRESHOLD_MB = 25;

        console.log(`Audio file size: ${fileSizeMB.toFixed(2)} MB`);

        if (fileSizeMB <= CHUNKING_THRESHOLD_MB) {
          // Small file - use direct transcription
          console.log(`File size (${fileSizeMB.toFixed(2)} MB) is under ${CHUNKING_THRESHOLD_MB}MB threshold. Using direct transcription.`);
          showStatus(`Processing ${fileSizeMB.toFixed(1)}MB recording...`, 'info');

          // Send directly to transcription endpoint
          const result = await sendToServer(processedFormData, '/api/transcribe');
          resolve(result);
        } else {
          // Large file - backend will handle chunking automatically
          console.log(`File size (${fileSizeMB.toFixed(2)} MB) exceeds ${CHUNKING_THRESHOLD_MB}MB threshold. Backend will handle chunking.`);
          showStatus(`Processing large ${fileSizeMB.toFixed(1)}MB recording with smart chunking...`, 'info');

          // Send to transcription endpoint - backend will detect size and chunk if needed
          const result = await sendToServer(processedFormData, '/api/transcribe');
          resolve(result);
        }
      } catch (error) {
        console.error('Error in smart audio routing:', error);
        reject(error);
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
      return 'gemini-2.5-flash-preview'; // Default to Gemini 2.5 Flash Preview if dropdown not found
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
      const savedModel = localStorage.getItem('vocal-local-interpretation-model');
      
      // Handle legacy model names for backward compatibility
      if (savedModel === 'gemini-2.0-flash-lite') {
        return 'gemini-2.5-flash-preview';
      }
      
      return savedModel || 'gemini-2.5-flash-preview'; // Default to Gemini 2.5 Flash Preview
    } catch (e) {
      console.warn('LocalStorage is not available. Defaulting to Gemini 2.5 Flash Preview.');
      return 'gemini-2.5-flash-preview';
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
        return 'gemini-2.5-flash-preview';
      } else if (savedModel === 'openai') {
        return 'gemini-2.5-flash-preview';
      } else if (savedModel === 'gemini-2.0-flash-lite') {
        return 'gemini-2.5-flash-preview';
      } else if (savedModel === 'gemini-2.5-flash') {
        return 'gemini-2.5-flash-preview-05-20';
      }

      return savedModel || 'gemini-2.5-flash-preview'; // Default to Gemini 2.5 Flash Preview
    } catch (e) {
      console.warn('LocalStorage is not available. Defaulting to Gemini 2.5 Flash Preview.');
      return 'gemini-2.5-flash-preview';
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

            // TTS functionality removed - translations will not be read aloud automatically

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

            // TTS functionality removed - translations will not be read aloud automatically

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
  const htmlElement = document.documentElement; // Get the <html> element

  // Function to apply the selected theme
  function applyTheme(theme) {
    // Apply the theme class to the <html> element
    htmlElement.setAttribute('data-theme', theme);

    // Update the toggle button icon based on current theme
    const icon = themeToggleButton.querySelector('i');
    if (theme === 'light') {
      // Show moon icon when in light mode (clicking will switch to dark)
      icon.className = 'fas fa-moon';
    } else {
      // Show sun icon when in dark mode (clicking will switch to light)
      icon.className = 'fas fa-sun';
    }

    // Save the user's theme preference
    try {
      localStorage.setItem('vocal-local-theme', theme);
    } catch (e) {
      console.warn('LocalStorage is not available. Theme preference will not be saved.');
    }

    console.log(`Applied theme: ${theme}`);
  }

  // Function to load the saved theme or default to light
  function loadTheme() {
    let savedTheme = 'light'; // Default to light
    try {
      savedTheme = localStorage.getItem('vocal-local-theme') || 'light';
    } catch (e) {
      console.warn('LocalStorage is not available. Defaulting to light theme.');
    }
    applyTheme(savedTheme);
  }

  // Function to toggle between light and dark themes
  function toggleTheme() {
    const currentTheme = htmlElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);
  }

  // Event listener for the theme toggle button
  // Only add if mobile navigation system is not present to avoid conflicts
  if (themeToggleButton && !window.mobileNav) {
    themeToggleButton.addEventListener('click', (event) => {
      event.stopPropagation();
      toggleTheme();
    });
  }

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
    // Store languages globally for bilingual conversation mode
    window.languages = Object.entries(languages).map(([name, details]) => ({
      name: name,
      native: details.native,
      code: details.code
    }));

    // Get saved language preferences from cookies
    const sourceLanguage = window.languagePreferences ?
      window.languagePreferences.loadLanguagePreference('source', 'en') : 'en';
    const targetLanguage = window.languagePreferences ?
      window.languagePreferences.loadLanguagePreference('target', 'es') : 'es';

    // Populate all language dropdowns with saved preferences
    populateLanguageDropdown('global-language', languages, sourceLanguage);
    populateLanguageDropdown('basic-language', languages, sourceLanguage);
    populateLanguageDropdown('language-1', languages, sourceLanguage);
    populateLanguageDropdown('language-2', languages, targetLanguage);

    // Populate new bilingual conversation dropdowns
    populateLanguageDropdown('bilingual-from-language', languages, sourceLanguage);
    populateLanguageDropdown('bilingual-to-language', languages, targetLanguage);

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

        // Update the new bilingual conversation mode "from" language
        const bilingualFromSelect = document.getElementById('bilingual-from-language');
        if (bilingualFromSelect) {
          bilingualFromSelect.value = selectedLanguage;
          // Trigger the update of language displays if bilingual conversation is active
          if (window.bilingualConversation) {
            window.bilingualConversation.updateLanguageDisplays();
          }
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
      const sourceId = 'basic-transcript';
      const transcriptEl = document.getElementById('basic-transcript');
      if (!transcriptEl) return;

      // Check if there's currently playing audio that should be paused
      const currentAudioObj = ttsAudioObjects[sourceId];
      if (currentAudioObj && !currentAudioObj.paused && !currentAudioObj.ended) {
        // Audio is currently playing, so pause it
        pauseSpeakText(sourceId);
        return;
      }

      // Check if there's paused audio that should be resumed
      if (currentAudioObj && currentAudioObj.paused && !currentAudioObj.ended) {
        // Audio is paused, so resume it
        resumeSpeakText(sourceId);
        return;
      }

      // No audio or audio ended, start new playback
      const text = transcriptEl.value;
      const langSelect = document.getElementById('basic-language');
      const lang = langSelect ? langSelect.value : 'en';

      // For mobile devices, add a small delay to ensure the DOM is fully updated
      if (isMobileDevice()) {
        setTimeout(() => {
          // Get the text again to ensure it's the most current
          const currentText = transcriptEl.value;
          speakText(sourceId, currentText, lang);
        }, 50);
      } else {
        speakText(sourceId, text, lang);
      }
    });
  }
  if (basicStopBtn) {
    basicStopBtn.addEventListener('click', () => {
      stopSpeakText('basic-transcript'); // Use consistent sourceId format
    });
  }

  // Duplicate test event listener removed to prevent multiple voices


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

            // Clean up stream
            if (currentStream) {
              currentStream.getTracks().forEach(track => track.stop());
              currentStream = null;
            }

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
                // Process audio data with smart routing
                const result = await processAudioWithSmartRouting(
                  recording.audioChunks,
                  recording.mediaRecorder.mimeType,
                  formData
                );

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

              // Reset UI and recording state
              basicRecordBtn.classList.remove('recording');
              // Reset button text to "Start Recording"
              const textSpan = basicRecordBtn.querySelector('.record-button-text');
              if (textSpan) {
                textSpan.textContent = 'Start Recording';
              }
              const recordingStatus = document.getElementById('basic-recording-status');
              if (recordingStatus) {
                recordingStatus.textContent = 'Click to start recording';
              }
              resetRecordingState();
            }, 500); // Short delay to ensure all data is collected

          } catch (error) {
            console.error('Error stopping recording:', error);
            console.error('Error details:', {
              name: error.name,
              message: error.message,
              stack: error.stack,
              recording: recording,
              audioChunks: recording?.audioChunks?.length || 'undefined',
              mediaRecorder: recording?.mediaRecorder?.state || 'undefined'
            });
            showStatus(`Error processing recording: ${error.message}. Please try again.`, 'error');
            basicRecordBtn.classList.remove('recording');
            const recordingStatus = document.getElementById('basic-recording-status');
            if (recordingStatus) {
              recordingStatus.textContent = 'Click to start recording';
            }
            resetRecordingState();
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

              // Clean up stream
              if (currentStream) {
                currentStream.getTracks().forEach(track => track.stop());
                currentStream = null;
              }

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
                  // Process audio data with smart routing
                  const result = await processAudioWithSmartRouting(
                    speaker.recording.audioChunks,
                    speaker.recording.mediaRecorder.mimeType,
                    formData
                  );

                  if (result.text) {
                    // Update transcript
                    updateTranscript(`transcript-${speaker.id}`, result.text);

                    // Translate the transcript
                    showStatus('Translating...', 'info');
                    const translatedText = await translateText(result.text, partnerLang);

                    if (translatedText && partnerSpeaker?.translationEl) {
                      // Update partner's translation display
                      partnerSpeaker.translationEl.value = translatedText;

                      // TTS functionality removed - translations will not be read aloud automatically

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

                // Reset UI and recording state
                speaker.recordBtn.classList.remove('recording');
                if (speaker.recordingStatus) {
                  speaker.recordingStatus.textContent = 'Click to start recording';
                }
                resetRecordingState();
              }, 500); // Short delay to ensure all data is collected

            } catch (error) {
              console.error('Error stopping recording:', error);
              console.error('Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack,
                speakerId: speaker.id,
                recording: speaker.recording,
                audioChunks: speaker.recording?.audioChunks?.length || 'undefined',
                mediaRecorder: speaker.recording?.mediaRecorder?.state || 'undefined'
              });
              showStatus(`Error processing recording: ${error.message}. Please try again.`, 'error');
              speaker.recordBtn.classList.remove('recording');
              if (speaker.recordingStatus) {
                speaker.recordingStatus.textContent = 'Click to start recording';
              }
              resetRecordingState();
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
        } else if (status.status === 'not_found') {
          // Job not found - this can happen if the job hasn't been stored yet
          // Continue polling for a few attempts before giving up
          if (attempts <= 5) {
            console.log(`Job ${jobId} not found yet, continuing to poll (attempt ${attempts})`);
            showStatus('Starting background processing...', 'info', true);
            return false; // Continue polling
          } else {
            console.error(`Job ${jobId} not found after ${attempts} attempts`);
            showStatus('Background job not found. Please try again.', 'error');
            return true; // Stop polling
          }
        } else {
          console.warn(`Unknown status for job ${jobId}:`, status);
          showStatus(`Transcription status: ${status.status}`, 'warning');
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
    // Set default to first TTS model (all are now premium)
    ttsModelSelect.value = 'gemini-2.5-flash-tts';

    // Note: TTS model selection access control is handled by plan-access-control.js
    // This handler only manages localStorage and status display for successful selections
    ttsModelSelect.addEventListener('change', function() {
      const selectedModel = this.value;

      // Save the selection (plan-access-control.js will handle access validation)
      localStorage.setItem('tts-model', selectedModel);

      // Get the display name from the selected option
      const selectedOption = this.options[this.selectedIndex];
      const displayName = selectedOption ? selectedOption.textContent : selectedModel;
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

  // ========================
  // Basic mode interpretation play/stop buttons (matching transcription pattern)
  // ========================
  console.log('🔍 TTS Debug: Looking for interpretation buttons...');
  const basicPlayInterpretationBtn = document.getElementById('basic-play-interpretation-btn');
  const basicStopInterpretationBtn = document.getElementById('basic-stop-interpretation-btn');

  console.log('🔍 TTS Debug: Interpretation buttons found:', {
    play: !!basicPlayInterpretationBtn,
    stop: !!basicStopInterpretationBtn,
    playElement: basicPlayInterpretationBtn,
    stopElement: basicStopInterpretationBtn
  });

  // Test if we can find the working transcription button for comparison
  const workingTranscriptBtn = document.getElementById('basic-play-btn');
  console.log('🔍 TTS Debug: Working transcript button found:', !!workingTranscriptBtn);

  if (basicPlayInterpretationBtn) {
    console.log('✅ TTS Debug: Attaching event listener to interpretation play button');

    basicPlayInterpretationBtn.addEventListener('click', () => {
      console.log('🎵 TTS Debug: Interpretation play button clicked!');

      const sourceId = 'basic-interpretation';
      const interpretationEl = document.getElementById('basic-interpretation');
      if (!interpretationEl) {
        console.error('❌ TTS Debug: Interpretation textarea not found!');
        return;
      }

      // Check if there's currently playing audio that should be paused
      const currentAudioObj = ttsAudioObjects[sourceId];
      if (currentAudioObj && !currentAudioObj.paused && !currentAudioObj.ended) {
        // Audio is currently playing, so pause it
        pauseSpeakText(sourceId);
        return;
      }

      // Check if there's paused audio that should be resumed
      if (currentAudioObj && currentAudioObj.paused && !currentAudioObj.ended) {
        // Audio is paused, so resume it
        resumeSpeakText(sourceId);
        return;
      }

      // No audio or audio ended, start new playback
      const text = interpretationEl.value;
      console.log('🔍 TTS Debug: Text length:', text.length, 'Preview:', text.substring(0, 30) + '...');

      const langSelect = document.getElementById('basic-language');
      const lang = langSelect ? langSelect.value : 'en';

      // For mobile devices, add a small delay to ensure the DOM is fully updated
      if (isMobileDevice()) {
        setTimeout(() => {
          // Get the text again to ensure it's the most current
          const currentText = interpretationEl.value;
          speakText(sourceId, currentText, lang);
        }, 50);
      } else {
        speakText(sourceId, text, lang);
      }
    });

    // Debug code removed - no automatic test text or button clicking
  } else {
    console.error('❌ TTS Debug: Interpretation play button NOT FOUND!');
  }

  if (basicStopInterpretationBtn) {
    basicStopInterpretationBtn.addEventListener('click', () => {
      console.log('⏹️ TTS Debug: Interpretation stop button clicked!');
      stopSpeakText('basic-interpretation'); // Use consistent sourceId format
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

  // ========================
  // Bilingual mode TTS buttons
  // ========================
  console.log('🔍 TTS Debug: Setting up bilingual mode TTS buttons...');

  // Original text play/stop buttons
  const bilingualPlayOriginalBtn = document.getElementById('play-original');
  const bilingualStopOriginalBtn = document.getElementById('stop-original');

  if (bilingualPlayOriginalBtn) {
    console.log('✅ TTS Debug: Found bilingual play-original button');
    bilingualPlayOriginalBtn.addEventListener('click', () => {
      console.log('🎵 TTS Debug: Bilingual play-original button clicked');
      const textArea = document.getElementById('bilingual-original-text');
      if (!textArea) {
        console.error('❌ TTS Debug: bilingual-original-text textarea not found');
        return;
      }

      const text = textArea.value;
      if (!text || text.trim() === '') {
        showStatus('No original text to play', 'warning');
        return;
      }

      // Get language from the from-language selector
      const fromLangSelect = document.getElementById('bilingual-from-language');
      const langCode = fromLangSelect ? fromLangSelect.value : 'en';

      console.log('🎵 TTS Debug: Playing bilingual original text:', text.substring(0, 30) + '...');
      speakText('bilingual-original-text', text, langCode);
    });
  } else {
    console.warn('⚠️ TTS Debug: play-original button not found');
  }

  if (bilingualStopOriginalBtn) {
    bilingualStopOriginalBtn.addEventListener('click', () => {
      console.log('⏹️ TTS Debug: Bilingual stop-original button clicked');
      stopSpeakText('bilingual-original-text');
    });
  }

  // Translation text play/stop buttons
  const bilingualPlayTranslationBtn = document.getElementById('play-translation');
  const bilingualStopTranslationBtn = document.getElementById('stop-translation');

  if (bilingualPlayTranslationBtn) {
    console.log('✅ TTS Debug: Found bilingual play-translation button');
    bilingualPlayTranslationBtn.addEventListener('click', () => {
      console.log('🎵 TTS Debug: Bilingual play-translation button clicked');
      const textArea = document.getElementById('bilingual-translation-text');
      if (!textArea) {
        console.error('❌ TTS Debug: bilingual-translation-text textarea not found');
        return;
      }

      const text = textArea.value;
      if (!text || text.trim() === '') {
        showStatus('No translation text to play', 'warning');
        return;
      }

      // Get language from the to-language selector
      const toLangSelect = document.getElementById('bilingual-to-language');
      const langCode = toLangSelect ? toLangSelect.value : 'es';

      console.log('🎵 TTS Debug: Playing bilingual translation text:', text.substring(0, 30) + '...');
      speakText('bilingual-translation-text', text, langCode);
    });
  } else {
    console.warn('⚠️ TTS Debug: play-translation button not found');
  }

  if (bilingualStopTranslationBtn) {
    bilingualStopTranslationBtn.addEventListener('click', () => {
      console.log('⏹️ TTS Debug: Bilingual stop-translation button clicked');
      stopSpeakText('bilingual-translation-text');
    });
  }

  // Expose functions globally for bilingual conversation mode
  window.startRecording = startRecording;
  window.processAudioWithSmartRouting = processAudioWithSmartRouting;
  window.showStatus = showStatus;
  window.getTranscriptionModel = getTranscriptionModel;
  window.speakText = speakText;
  window.stopSpeakText = stopSpeakText;
});
