// Direct TTS System - A completely new implementation to fix synchronization issues
// This bypasses the existing TTS system entirely

// Global state for the direct TTS system
const directTTSPlayers = {};
let directTTSCounter = 0;

// Function to get the current visible text directly from the DOM
function getVisibleText(elementId) {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`[DirectTTS] Element not found: ${elementId}`);
    return null;
  }

  // Get the text directly from the element
  const text = element.value || element.innerText || '';

  if (!text || text.trim() === '') {
    console.warn(`[DirectTTS] No text found in element: ${elementId}`);
    return null;
  }

  return text.trim();
}

// Function to get the language for a specific element
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

  return 'en'; // Default fallback
}

// Function to show status messages
function showDirectTTSStatus(message, type = 'info') {
  const statusEl = document.getElementById('status');
  if (!statusEl) return;

  statusEl.textContent = message;
  statusEl.className = `status status-${type}`;
  statusEl.style.display = 'block';

  setTimeout(() => {
    statusEl.style.display = 'none';
  }, 3000);
}

// Function to update button states
function updateDirectTTSButtonState(elementId, state) {
  let playBtn, stopBtn;

  // Handle different button ID patterns based on elementId
  if (elementId === 'basic-transcript') {
    // Basic mode buttons
    playBtn = document.getElementById('basic-play-btn');
    stopBtn = document.getElementById('basic-stop-btn');
  } else if (elementId.startsWith('transcript-')) {
    // Bilingual mode transcript buttons
    const speakerId = elementId.split('-')[1];
    playBtn = document.getElementById(`play-transcript-${speakerId}`);
    stopBtn = document.getElementById(`stop-transcript-${speakerId}`);
  } else if (elementId.startsWith('translation-')) {
    // Bilingual mode translation buttons
    const speakerId = elementId.split('-')[1];
    playBtn = document.getElementById(`play-translation-${speakerId}`);
    stopBtn = document.getElementById(`stop-translation-${speakerId}`);
  }

  if (!playBtn || !stopBtn) {
    console.warn(`[DirectTTS] Could not find play/stop buttons for: ${elementId}`);
    return;
  }

  if (state === 'playing') {
    playBtn.style.display = 'none';
    stopBtn.style.display = 'inline-flex';
  } else {
    playBtn.style.display = 'inline-flex';
    stopBtn.style.display = 'none';
  }
}

// Main function to speak text directly from a DOM element
function directSpeakText(elementId) {
  // Stop any currently playing TTS
  stopAllDirectTTS();

  // Get the text directly from the DOM at the moment of the call
  const text = getVisibleText(elementId);
  if (!text) {
    showDirectTTSStatus('No text to speak', 'warning');
    return;
  }

  // Get the language for this element
  const language = getLanguageForElement(elementId);

  // Generate a unique ID for this TTS request
  const ttsId = `direct-tts-${elementId}-${directTTSCounter++}`;

  // Log the exact text and language being used
  console.log(`[DirectTTS] Speaking text from ${elementId} in ${language}: "${text.substring(0, 30)}..."`);

  // Show status
  showDirectTTSStatus('Generating speech...', 'info');

  // Update button state
  updateDirectTTSButtonState(elementId, 'playing');

  // Store the element ID for this TTS request
  directTTSPlayers[ttsId] = { elementId, playing: true };

  // Make the API request to generate speech
  fetch('/api/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: text, language: language })
  })
  .then(response => {
    if (!response.ok) throw new Error(`TTS service error (${response.status})`);
    return response.blob();
  })
  .then(audioBlob => {
    // Create audio element
    const audio = new Audio(URL.createObjectURL(audioBlob));

    // Store the audio element
    directTTSPlayers[ttsId].audio = audio;
    directTTSPlayers[ttsId].blobUrl = URL.createObjectURL(audioBlob);

    // Set up event handlers
    audio.onplay = () => {
      showDirectTTSStatus('Playing speech...', 'info');
    };

    audio.onended = () => {
      updateDirectTTSButtonState(elementId, 'stopped');
      delete directTTSPlayers[ttsId];
    };

    audio.onerror = (e) => {
      console.error('[DirectTTS] Audio playback error:', e);
      showDirectTTSStatus('Error playing speech', 'error');
      updateDirectTTSButtonState(elementId, 'stopped');
      delete directTTSPlayers[ttsId];
    };

    // Play the audio
    audio.play().catch(error => {
      console.error('[DirectTTS] Error playing audio:', error);
      showDirectTTSStatus('Error playing speech: ' + error.message, 'error');
      updateDirectTTSButtonState(elementId, 'stopped');
      delete directTTSPlayers[ttsId];
    });
  })
  .catch(error => {
    console.error('[DirectTTS] Error generating speech:', error);
    showDirectTTSStatus('Error generating speech: ' + error.message, 'error');
    updateDirectTTSButtonState(elementId, 'stopped');
    delete directTTSPlayers[ttsId];

    // Try fallback if available
    tryFallbackTTS(elementId, text, language);
  });
}

// Function to stop TTS for a specific element
function stopDirectTTS(elementId) {
  // Find all TTS players for this element
  Object.keys(directTTSPlayers).forEach(ttsId => {
    if (directTTSPlayers[ttsId].elementId === elementId) {
      if (directTTSPlayers[ttsId].audio) {
        directTTSPlayers[ttsId].audio.pause();
        if (directTTSPlayers[ttsId].blobUrl) {
          URL.revokeObjectURL(directTTSPlayers[ttsId].blobUrl);
        }
      }
      delete directTTSPlayers[ttsId];
    }
  });

  // Update button state
  updateDirectTTSButtonState(elementId, 'stopped');
}

// Function to stop all TTS
function stopAllDirectTTS() {
  Object.keys(directTTSPlayers).forEach(ttsId => {
    const player = directTTSPlayers[ttsId];
    if (player.audio) {
      player.audio.pause();
      if (player.blobUrl) {
        URL.revokeObjectURL(player.blobUrl);
      }
    }
    updateDirectTTSButtonState(player.elementId, 'stopped');
    delete directTTSPlayers[ttsId];
  });
}

// Fallback TTS using browser's speech synthesis
function tryFallbackTTS(elementId, text, language) {
  if (!window.speechSynthesis) {
    showDirectTTSStatus('Text-to-speech is not supported in your browser', 'warning');
    return;
  }

  // Cancel any current speech
  window.speechSynthesis.cancel();

  // Create utterance
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = language;

  // Set up event handlers
  utterance.onstart = () => {
    showDirectTTSStatus('Playing speech (browser fallback)...', 'info');
    updateDirectTTSButtonState(elementId, 'playing');
  };

  utterance.onend = () => {
    updateDirectTTSButtonState(elementId, 'stopped');
  };

  utterance.onerror = (e) => {
    console.error('[DirectTTS] Browser TTS error:', e);
    showDirectTTSStatus('Browser TTS error', 'error');
    updateDirectTTSButtonState(elementId, 'stopped');
  };

  // Speak the text
  window.speechSynthesis.speak(utterance);
}

// Override the original speakText function to prevent double TTS
function overrideOriginalTTS() {
  // Store the original function for reference if needed
  if (window.originalSpeakText === undefined && window.speakText) {
    window.originalSpeakText = window.speakText;

    // Replace the original function with our interceptor
    window.speakText = function(sourceId, text, langCode) {
      console.log(`[DirectTTS] Intercepted original TTS call for ${sourceId}`);

      // Extract the element ID from the sourceId
      let elementId = sourceId;

      // Call our direct TTS function instead
      directSpeakText(elementId);

      // Return to prevent the original function from executing
      return;
    };

    console.log('[DirectTTS] Successfully overrode original TTS function');
  }

  // Also override the stop function
  if (window.originalStopSpeakText === undefined && window.stopSpeakText) {
    window.originalStopSpeakText = window.stopSpeakText;

    // Replace the original function with our interceptor
    window.stopSpeakText = function(sourceId) {
      console.log(`[DirectTTS] Intercepted original stop TTS call for ${sourceId}`);

      // Call our direct stop function instead
      stopDirectTTS(sourceId);

      // Return to prevent the original function from executing
      return;
    };

    console.log('[DirectTTS] Successfully overrode original stop TTS function');
  }
}

// Initialize the direct TTS system
function initializeDirectTTS() {
  console.log('[DirectTTS] Initializing direct TTS system...');

  // Override the original TTS functions to prevent double playback
  overrideOriginalTTS();

  // We don't need to add our own event listeners since we're intercepting the original ones
  // This prevents double event handlers and ensures the button states are managed correctly

  // Add a safety check to ensure all buttons work correctly
  ensureAllButtonsWork();

  // Add event listener for mode toggle to stop all TTS
  const modeToggle = document.getElementById('bilingual-mode');
  if (modeToggle) {
    modeToggle.addEventListener('change', () => {
      stopAllDirectTTS();
    });
  }

  // Add event listeners for language changes
  const languageSelects = [
    'global-language',
    'basic-language',
    'language-1',
    'language-2'
  ];

  languageSelects.forEach(id => {
    const select = document.getElementById(id);
    if (select) {
      select.addEventListener('change', () => {
        stopAllDirectTTS();
      });
    }
  });

  console.log('[DirectTTS] Direct TTS system initialized');
}

// Function to ensure all TTS buttons work correctly
function ensureAllButtonsWork() {
  // This function adds direct event listeners as a fallback
  // in case the function override approach doesn't work for some reason

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
      // Remove any existing event listeners (not perfect but helps)
      const newButton = button.cloneNode(true);
      button.parentNode.replaceChild(newButton, button);

      // Add our event listener
      if (buttonId.includes('play')) {
        newButton.addEventListener('click', (e) => {
          // Stop event propagation to prevent double triggering
          e.stopPropagation();

          // Call our direct TTS function
          directSpeakText(elementId);

          // Return false to prevent default behavior
          return false;
        });
      } else if (buttonId.includes('stop')) {
        newButton.addEventListener('click', (e) => {
          // Stop event propagation to prevent double triggering
          e.stopPropagation();

          // Call our direct stop function
          stopDirectTTS(elementId);

          // Return false to prevent default behavior
          return false;
        });
      }
    }
  });

  console.log('[DirectTTS] Added direct event listeners to all TTS buttons');
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Wait longer to ensure all other scripts have fully loaded and initialized
  // This is critical to ensure we override the original functions after they're defined
  setTimeout(initializeDirectTTS, 1000);

  // Add a second initialization attempt as a fallback
  setTimeout(() => {
    // Check if our override was successful
    if (window.originalSpeakText === undefined && window.speakText) {
      console.log('[DirectTTS] First initialization may have failed, trying again...');
      initializeDirectTTS();
    }
  }, 2000);
});

// Also initialize on window load as a fallback
window.addEventListener('load', () => {
  // Check if our override was successful
  if (window.originalSpeakText === undefined && window.speakText) {
    console.log('[DirectTTS] Initializing on window load...');
    initializeDirectTTS();
  }
});

// Export functions for global use
window.directSpeakText = directSpeakText;
window.stopDirectTTS = stopDirectTTS;
window.stopAllDirectTTS = stopAllDirectTTS;

// Log that our script has loaded
console.log('[DirectTTS] Direct TTS script loaded');
