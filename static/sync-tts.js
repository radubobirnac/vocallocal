/**
 * Synchronized Text-to-Speech System
 *
 * This module provides a completely new implementation of the TTS system
 * that ensures proper synchronization with the visible text in the UI.
 * It replaces the existing TTS functionality to fix synchronization issues
 * in bilingual mode on both mobile and desktop platforms.
 */

// Global state for the synchronized TTS system
const syncTTS = {
  // Active audio players
  players: {},

  // Counter for unique IDs
  counter: 0,

  // Debug mode
  debug: true,

  // Log messages if debug is enabled
  log: function(message) {
    if (this.debug) {
      console.log(`[SyncTTS] ${message}`);
    }
  }
};

/**
 * Get the current visible text from a DOM element
 *
 * @param {string} elementId - The ID of the DOM element
 * @returns {string|null} - The text content or null if not found
 */
function getVisibleText(elementId) {
  // Get the element
  const element = document.getElementById(elementId);

  // Check if element exists
  if (!element) {
    syncTTS.log(`Element not found: ${elementId}`);
    return null;
  }

  // Get text from textarea or input
  if (element.tagName === 'TEXTAREA' || element.tagName === 'INPUT') {
    const text = element.value;

    // Check if text is empty or placeholder
    if (!text || text.trim() === '' ||
        text === 'Your speech will appear here...' ||
        text === 'Translation will appear here...') {
      syncTTS.log(`No valid text in element: ${elementId}`);
      return null;
    }

    syncTTS.log(`Got text from ${elementId}: "${text.substring(0, 30)}${text.length > 30 ? '...' : ''}"`);
    return text;
  }

  // Get text from other elements
  const text = element.textContent;

  // Check if text is empty
  if (!text || text.trim() === '') {
    syncTTS.log(`No text content in element: ${elementId}`);
    return null;
  }

  syncTTS.log(`Got text from ${elementId}: "${text.substring(0, 30)}${text.length > 30 ? '...' : ''}"`);
  return text;
}

/**
 * Get the appropriate language code for an element
 *
 * @param {string} elementId - The ID of the element
 * @returns {string} - The language code
 */
function getLanguageForElement(elementId) {
  // For translation elements
  if (elementId.startsWith('translation-')) {
    const speakerId = elementId.split('-')[1];
    const partnerId = speakerId === '1' ? '2' : '1';
    const langSelect = document.getElementById(`language-${partnerId}`);
    return langSelect ? langSelect.value : 'en';
  }
  // For transcript elements
  else if (elementId.startsWith('transcript-')) {
    const speakerId = elementId.split('-')[1];
    const langSelect = document.getElementById(`language-${speakerId}`);
    return langSelect ? langSelect.value : 'en';
  }
  // For basic mode
  else if (elementId === 'basic-transcript') {
    const langSelect = document.getElementById('basic-language');
    return langSelect ? langSelect.value : 'en';
  }

  // Default fallback
  return 'en';
}

/**
 * Update the play/stop button states
 *
 * @param {string} elementId - The ID of the element
 * @param {string} state - The state ('playing' or 'stopped')
 */
function updateButtonState(elementId, state) {
  let playBtn, stopBtn;

  // Get the appropriate buttons based on element ID
  if (elementId === 'basic-transcript') {
    playBtn = document.getElementById('basic-play-btn');
    stopBtn = document.getElementById('basic-stop-btn');
  } else if (elementId.startsWith('transcript-')) {
    const speakerId = elementId.split('-')[1];
    playBtn = document.getElementById(`play-transcript-${speakerId}`);
    stopBtn = document.getElementById(`stop-transcript-${speakerId}`);
  } else if (elementId.startsWith('translation-')) {
    const speakerId = elementId.split('-')[1];
    playBtn = document.getElementById(`play-translation-${speakerId}`);
    stopBtn = document.getElementById(`stop-translation-${speakerId}`);
  }

  // Update button visibility
  if (playBtn && stopBtn) {
    if (state === 'playing') {
      playBtn.style.display = 'none';
      stopBtn.style.display = 'inline-flex';
      syncTTS.log(`Updated buttons for ${elementId}: showing STOP button`);
    } else {
      playBtn.style.display = 'inline-flex';
      stopBtn.style.display = 'none';
      syncTTS.log(`Updated buttons for ${elementId}: showing PLAY button`);
    }
  } else {
    syncTTS.log(`Could not find buttons for ${elementId}`);
  }
}

/**
 * Show a status message
 *
 * @param {string} message - The message to show
 * @param {string} type - The message type (info, success, warning, error)
 */
function showStatus(message, type = 'info') {
  const statusEl = document.getElementById('status');
  if (!statusEl) return;

  statusEl.textContent = message;
  statusEl.className = `status status-${type}`;
  statusEl.style.display = 'block';

  setTimeout(() => {
    statusEl.style.display = 'none';
  }, 3000);
}

/**
 * Play text from a DOM element using TTS
 *
 * @param {string} elementId - The ID of the DOM element
 */
function playText(elementId) {
  // Stop any currently playing audio
  stopAllAudio();

  // Get the text directly from the DOM at the moment of the call
  const text = getVisibleText(elementId);
  if (!text) {
    showStatus('No text to speak', 'warning');
    return;
  }

  // Get the language for this element
  const language = getLanguageForElement(elementId);

  // Generate a unique ID for this TTS request
  const ttsId = `sync-tts-${syncTTS.counter++}`;

  // Show status
  showStatus('Generating speech...', 'info');

  // Update button state
  updateButtonState(elementId, 'playing');

  // Store the player info
  syncTTS.players[ttsId] = {
    elementId: elementId,
    text: text,
    language: language,
    timestamp: new Date().toISOString()
  };

  // Get the TTS model
  const ttsModelSelect = document.getElementById('tts-model-select');
  const ttsModel = ttsModelSelect ? ttsModelSelect.value : 'gemini-2.5-flash-tts';

  // Make the API request
  fetch('/api/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: text,
      language: language,
      tts_model: ttsModel
    })
  })
  .then(response => {
    if (!response.ok) throw new Error(`TTS service error (${response.status})`);
    return response.blob();
  })
  .then(audioBlob => {
    // Create audio element
    const audio = new Audio(URL.createObjectURL(audioBlob));

    // Store the audio element
    syncTTS.players[ttsId].audio = audio;
    syncTTS.players[ttsId].blobUrl = URL.createObjectURL(audioBlob);

    // Set up event handlers
    audio.onplay = () => {
      showStatus('Playing speech...', 'info');
      syncTTS.log(`Started playing audio for ${elementId}`);
    };

    audio.onended = () => {
      updateButtonState(elementId, 'stopped');
      syncTTS.log(`Finished playing audio for ${elementId}`);

      // Clean up
      if (syncTTS.players[ttsId] && syncTTS.players[ttsId].blobUrl) {
        URL.revokeObjectURL(syncTTS.players[ttsId].blobUrl);
      }
      delete syncTTS.players[ttsId];
    };

    audio.onerror = (e) => {
      syncTTS.log(`Error playing audio for ${elementId}: ${e}`);
      showStatus('Error playing speech', 'error');
      updateButtonState(elementId, 'stopped');

      // Clean up
      if (syncTTS.players[ttsId] && syncTTS.players[ttsId].blobUrl) {
        URL.revokeObjectURL(syncTTS.players[ttsId].blobUrl);
      }
      delete syncTTS.players[ttsId];
    };

    // Play the audio
    audio.play().catch(error => {
      syncTTS.log(`Error playing audio for ${elementId}: ${error.message}`);
      showStatus('Error playing speech: ' + error.message, 'error');
      updateButtonState(elementId, 'stopped');

      // Clean up
      if (syncTTS.players[ttsId] && syncTTS.players[ttsId].blobUrl) {
        URL.revokeObjectURL(syncTTS.players[ttsId].blobUrl);
      }
      delete syncTTS.players[ttsId];
    });
  })
  .catch(error => {
    syncTTS.log(`Error generating speech for ${elementId}: ${error.message}`);
    showStatus('Error generating speech: ' + error.message, 'error');
    updateButtonState(elementId, 'stopped');
    delete syncTTS.players[ttsId];

    // Try fallback if available
    tryFallbackTTS(elementId, text, language);
  });
}

/**
 * Stop audio playback for a specific element
 *
 * @param {string} elementId - The ID of the element
 */
function stopAudio(elementId) {
  let stopped = false;

  // Find all players for this element
  Object.keys(syncTTS.players).forEach(ttsId => {
    const player = syncTTS.players[ttsId];
    if (player.elementId === elementId) {
      if (player.audio) {
        player.audio.pause();
        if (player.blobUrl) {
          URL.revokeObjectURL(player.blobUrl);
        }
      }
      delete syncTTS.players[ttsId];
      stopped = true;
    }
  });

  if (stopped) {
    syncTTS.log(`Stopped audio for ${elementId}`);
    showStatus('Playback stopped', 'info');
  }

  // Update button state
  updateButtonState(elementId, 'stopped');
}

/**
 * Stop all audio playback
 */
function stopAllAudio() {
  Object.keys(syncTTS.players).forEach(ttsId => {
    const player = syncTTS.players[ttsId];
    if (player.audio) {
      player.audio.pause();
      if (player.blobUrl) {
        URL.revokeObjectURL(player.blobUrl);
      }
    }
    updateButtonState(player.elementId, 'stopped');
  });

  // Clear the players object
  syncTTS.players = {};
  syncTTS.log('Stopped all audio playback');
}

/**
 * Try to use browser's built-in TTS as a fallback
 *
 * @param {string} elementId - The ID of the element
 * @param {string} text - The text to speak
 * @param {string} language - The language code
 */
function tryFallbackTTS(elementId, text, language) {
  if (!window.speechSynthesis) {
    showStatus('Text-to-speech is not supported in your browser', 'warning');
    return;
  }

  // Cancel any current speech
  window.speechSynthesis.cancel();

  // Create utterance
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = language;

  // Set up event handlers
  utterance.onstart = () => {
    showStatus('Playing speech (browser fallback)...', 'info');
    updateButtonState(elementId, 'playing');
    syncTTS.log(`Started playing fallback TTS for ${elementId}`);
  };

  utterance.onend = () => {
    updateButtonState(elementId, 'stopped');
    syncTTS.log(`Finished playing fallback TTS for ${elementId}`);
  };

  utterance.onerror = (e) => {
    syncTTS.log(`Error with fallback TTS for ${elementId}: ${e}`);
    showStatus('Browser TTS error', 'error');
    updateButtonState(elementId, 'stopped');
  };

  // Speak the text
  window.speechSynthesis.speak(utterance);
}

/**
 * Override the original TTS functions
 */
function overrideOriginalTTS() {
  // Store the original functions if they exist
  if (window.originalSpeakText === undefined && window.speakText) {
    window.originalSpeakText = window.speakText;

    // Replace with our function
    window.speakText = function(sourceId, text, langCode) {
      syncTTS.log(`Intercepted original TTS call for ${sourceId}`);

      // Extract the element ID from the sourceId
      let elementId = sourceId;

      // Call our function instead
      playText(elementId);

      // Return to prevent the original function from executing
      return;
    };

    syncTTS.log('Successfully overrode original speakText function');
  }

  // Override the stop function
  if (window.originalStopSpeakText === undefined && window.stopSpeakText) {
    window.originalStopSpeakText = window.stopSpeakText;

    // Replace with our function
    window.stopSpeakText = function(sourceId) {
      syncTTS.log(`Intercepted original stop TTS call for ${sourceId}`);

      // Call our function instead
      stopAudio(sourceId);

      // Return to prevent the original function from executing
      return;
    };

    syncTTS.log('Successfully overrode original stopSpeakText function');
  }
}

/**
 * Add direct event listeners to all TTS buttons
 */
function addDirectEventListeners() {
  // Map of button IDs to their corresponding element IDs
  const buttonMappings = {
    // Basic mode
    'basic-play-btn': 'basic-transcript',
    'basic-stop-btn': 'basic-transcript',

    // Speaker 1
    'play-transcript-1': 'transcript-1',
    'stop-transcript-1': 'transcript-1',
    'play-translation-1': 'translation-1',
    'stop-translation-1': 'translation-1',

    // Speaker 2
    'play-transcript-2': 'transcript-2',
    'stop-transcript-2': 'transcript-2',
    'play-translation-2': 'translation-2',
    'stop-translation-2': 'translation-2'
  };

  // Add direct event listeners to all buttons
  Object.entries(buttonMappings).forEach(([buttonId, elementId]) => {
    const button = document.getElementById(buttonId);
    if (button) {
      // Remove any existing event listeners
      const newButton = button.cloneNode(true);
      if (button.parentNode) {
        button.parentNode.replaceChild(newButton, button);
      }

      // Add our event listener
      if (buttonId.includes('play')) {
        newButton.addEventListener('click', (e) => {
          e.stopPropagation();
          playText(elementId);
          return false;
        });
      } else if (buttonId.includes('stop')) {
        newButton.addEventListener('click', (e) => {
          e.stopPropagation();
          stopAudio(elementId);
          return false;
        });
      }
    }
  });

  syncTTS.log('Added direct event listeners to all TTS buttons');
}

/**
 * Add event listeners for mode and language changes
 */
function addModeAndLanguageListeners() {
  // Mode toggle
  const modeToggle = document.getElementById('bilingual-mode');
  if (modeToggle) {
    modeToggle.addEventListener('change', () => {
      stopAllAudio();
      syncTTS.log('Stopped all audio due to mode change');
    });
  }

  // Language selectors
  const languageSelectors = [
    'global-language',
    'basic-language',
    'language-1',
    'language-2'
  ];

  languageSelectors.forEach(id => {
    const select = document.getElementById(id);
    if (select) {
      select.addEventListener('change', () => {
        stopAllAudio();
        syncTTS.log(`Stopped all audio due to language change in ${id}`);
      });
    }
  });
}

/**
 * Add event listeners for automatic TTS after translation
 */
function addAutoTTSListeners() {
  // Find the enable TTS checkboxes
  const enableTTS1 = document.getElementById('enable-tts-1');
  const enableTTS2 = document.getElementById('enable-tts-2');

  // Monitor changes to translation elements
  const translation1 = document.getElementById('translation-1');
  const translation2 = document.getElementById('translation-2');

  if (translation1) {
    // Use MutationObserver to detect changes to the translation
    const observer1 = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' ||
            (mutation.type === 'characterData' && mutation.target === translation1)) {
          // Check if auto TTS is enabled
          if (enableTTS2 && enableTTS2.checked) {
            syncTTS.log('Detected change to translation-1, triggering auto TTS');
            // Use setTimeout to ensure the DOM is fully updated
            setTimeout(() => {
              playText('translation-1');
            }, 250);
          }
        }
      });
    });

    // Start observing
    observer1.observe(translation1, {
      attributes: true,
      characterData: true,
      subtree: true,
      childList: true
    });
  }

  if (translation2) {
    // Use MutationObserver to detect changes to the translation
    const observer2 = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' ||
            (mutation.type === 'characterData' && mutation.target === translation2)) {
          // Check if auto TTS is enabled
          if (enableTTS1 && enableTTS1.checked) {
            syncTTS.log('Detected change to translation-2, triggering auto TTS');
            // Use setTimeout to ensure the DOM is fully updated
            setTimeout(() => {
              playText('translation-2');
            }, 250);
          }
        }
      });
    });

    // Start observing
    observer2.observe(translation2, {
      attributes: true,
      characterData: true,
      subtree: true,
      childList: true
    });
  }
}

/**
 * Initialize the synchronized TTS system
 */
function initializeSyncTTS() {
  syncTTS.log('Initializing synchronized TTS system...');

  // Override the original TTS functions
  overrideOriginalTTS();

  // Add direct event listeners to all TTS buttons
  addDirectEventListeners();

  // Add event listeners for mode and language changes
  addModeAndLanguageListeners();

  // Add event listeners for automatic TTS after translation
  addAutoTTSListeners();

  // Add a global error handler for TTS-related errors
  window.addEventListener('error', function(event) {
    if (event.message && event.message.includes('TTS')) {
      syncTTS.log(`Caught TTS-related error: ${event.message}`);
      // Try to recover
      stopAllAudio();
      // Prevent the error from showing in the console
      event.preventDefault();
    }
  });

  syncTTS.log('Synchronized TTS system initialized successfully');

  // TTS system activated silently without notification
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Wait for the original script to load first
  setTimeout(initializeSyncTTS, 1000);
});

// Also initialize on window load as a fallback
window.addEventListener('load', () => {
  // Check if already initialized
  if (window.originalSpeakText === undefined && window.speakText) {
    syncTTS.log('Initializing on window load...');
    initializeSyncTTS();
  }
});

// Export functions for global use
window.syncTTS = {
  play: playText,
  stop: stopAudio,
  stopAll: stopAllAudio
};

// Log that our script has loaded
syncTTS.log('Synchronized TTS script loaded');
