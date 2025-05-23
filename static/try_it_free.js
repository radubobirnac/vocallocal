// Try It Free page specific JavaScript

document.addEventListener('DOMContentLoaded', function() {
  // DOM Elements
  const recordButton = document.getElementById('record-button');
  const basicRecordingTimer = document.getElementById('basic-recording-timer');
  const globalRecordingTimer = document.getElementById('global-recording-timer');
  const speaker2Timer = document.getElementById('speaker2-timer');
  const audioUpload = document.getElementById('audio-upload');
  const progressContainer = document.getElementById('progress-container');
  const progressBar = document.getElementById('progress-bar');
  const progressText = document.getElementById('progress-text');
  const transcriptionText = document.getElementById('transcription-text');
  const copyButton = document.getElementById('copy-button');
  const languageSelect = document.getElementById('language-select');

  // Settings Elements
  const settingsToggle = document.getElementById('settings-toggle');
  const settingsPanel = document.getElementById('settings-panel');
  const transcriptionModelSelect = document.getElementById('transcription-model-select');
  const translationModelSelect = document.getElementById('translation-model-select');
  const ttsModelSelect = document.getElementById('tts-model-select');
  const premiumModelsToggle = document.getElementById('premium-models-toggle');

  // Bilingual Mode Elements
  const bilingualModeToggle = document.getElementById('bilingual-mode');
  const basicMode = document.getElementById('basic-mode');
  const bilingualMode = document.getElementById('bilingual-mode-content');

  // Speaker 1 Elements
  const recordButton1 = document.getElementById('record-button-1');
  const audioUpload1 = document.getElementById('audio-upload-1');
  const transcriptionText1 = document.getElementById('transcription-text-1');
  const copyButton1 = document.getElementById('copy-button-1');
  const language1Select = document.getElementById('language-1');
  const translateButton1 = document.getElementById('translate-button-1');
  const translationText1 = document.getElementById('translation-text-1');
  const copyTranslation1 = document.getElementById('copy-translation-1');

  // Speaker 2 Elements
  const recordButton2 = document.getElementById('record-button-2');
  const audioUpload2 = document.getElementById('audio-upload-2');
  const transcriptionText2 = document.getElementById('transcription-text-2');
  const copyButton2 = document.getElementById('copy-button-2');
  const language2Select = document.getElementById('language-2');
  const translateButton2 = document.getElementById('translate-button-2');
  const translationText2 = document.getElementById('translation-text-2');
  const copyTranslation2 = document.getElementById('copy-translation-2');

  // Bilingual Progress Elements
  const bilingualProgressContainer = document.getElementById('bilingual-progress-container');
  const bilingualProgressBar = document.getElementById('bilingual-progress-bar');
  const bilingualProgressText = document.getElementById('bilingual-progress-text');

  // Constants
  const MAX_RECORDING_DURATION = 180; // 3 minutes in seconds
  const CHUNK_INTERVAL = 60; // Process every 60 seconds
  const SAMPLE_RATE = 44100;
  const CHANNELS = 1;

  // Variables
  let mediaRecorder = null;
  let audioChunks = [];
  let recordingStartTime = 0;
  let recordingInterval = null;
  let isRecording = false;
  let circleProgress = null;
  let lastChunkTime = 0;
  let partialTranscriptions = {}; // Store partial transcriptions by speaker

  // Initialize circular progress indicator
  function initializeCircularProgress() {
    if (window.ProgressBar) {
      circleProgress = new ProgressBar.Circle(progressBar, {
        strokeWidth: 6,
        easing: 'easeInOut',
        duration: 1400,
        color: getComputedStyle(document.documentElement).getPropertyValue('--primary').trim(),
        trailColor: getComputedStyle(document.documentElement).getPropertyValue('--secondary').trim(),
        trailWidth: 1,
        svgStyle: null
      });
    }
  }

  // Format time in MM:SS format
  function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  // Update recording timer
  function updateTimer(speakerNum = null) {
    const currentTime = Date.now();
    const elapsedTime = (currentTime - recordingStartTime) / 1000;
    const formattedTime = formatTime(elapsedTime);

    // Update timers based on mode
    if (bilingualModeToggle && bilingualModeToggle.checked) {
      // Bilingual mode - update the appropriate timer
      if (speakerNum === 1 && globalRecordingTimer) {
        globalRecordingTimer.textContent = formattedTime;
      } else if (speakerNum === 2 && speaker2Timer) {
        speaker2Timer.textContent = formattedTime;
      }
    } else {
      // Basic mode - update the basic timer
      if (basicRecordingTimer) {
        basicRecordingTimer.textContent = formattedTime;
      }
    }

    // Update progress if circular progress is available
    if (circleProgress) {
      const progress = Math.min(elapsedTime / MAX_RECORDING_DURATION, 1);
      circleProgress.animate(progress);
    }

    // Check if it's time to process a chunk (every CHUNK_INTERVAL seconds)
    if (isRecording && elapsedTime >= CHUNK_INTERVAL && elapsedTime - lastChunkTime >= CHUNK_INTERVAL) {
      processPartialRecording(speakerNum);
      lastChunkTime = elapsedTime;
    }

    // Auto-stop recording if max duration reached
    if (elapsedTime >= MAX_RECORDING_DURATION) {
      stopRecording(speakerNum);
    }
  }

  // Process partial recording
  function processPartialRecording(speakerNum = null) {
    // Create a copy of the current audio chunks
    const currentChunks = [...audioChunks];

    // Create a blob from the current chunks
    const audioBlob = new Blob(currentChunks, { type: 'audio/webm' });

    // Show a "processing" indicator
    showPartialProcessingIndicator(speakerNum);

    // Process this chunk
    processPartialAudio(audioBlob, speakerNum);
  }

  // Show partial processing indicator
  function showPartialProcessingIndicator(speakerNum = null) {
    let transcriptionTextToUse;

    if (speakerNum === 1) {
      transcriptionTextToUse = transcriptionText1;
    } else if (speakerNum === 2) {
      transcriptionTextToUse = transcriptionText2;
    } else {
      transcriptionTextToUse = transcriptionText;
    }

    // Add a processing indicator to the transcription area
    if (transcriptionTextToUse) {
      // Only add the indicator if there's no content yet
      if (!partialTranscriptions[speakerNum] || partialTranscriptions[speakerNum].length === 0) {
        transcriptionTextToUse.innerHTML = '<p class="transcribing-indicator">Transcribing... Please wait.</p>';
      } else {
        // If we already have partial transcriptions, append the indicator
        const currentContent = transcriptionTextToUse.innerHTML;
        if (!currentContent.includes('transcribing-indicator')) {
          transcriptionTextToUse.innerHTML = currentContent + '<p class="transcribing-indicator">Transcribing more... Please wait.</p>';
        }
      }
    }
  }

  // Process partial audio
  function processPartialAudio(audioBlob, speakerNum = null) {
    // Create FormData for API request
    const formData = new FormData();
    formData.append('file', audioBlob, 'partial_recording.webm');

    // Determine which language to use
    let selectedLanguage;
    if (speakerNum === 1 && language1Select) {
      selectedLanguage = language1Select.value;
    } else if (speakerNum === 2 && language2Select) {
      selectedLanguage = language2Select.value;
    } else if (languageSelect) {
      selectedLanguage = languageSelect.value;
    } else {
      selectedLanguage = 'en'; // Default to English
    }

    formData.append('language', selectedLanguage);

    // Get selected transcription model or use default
    const selectedModel = transcriptionModelSelect ?
      transcriptionModelSelect.value :
      localStorage.getItem('free-trial-transcription-model') || 'gemini-2.0-flash-lite';

    formData.append('model', selectedModel);

    // Add a flag to indicate this is a partial transcription
    formData.append('is_partial', 'true');

    // Send to API
    fetch('/api/transcribe', {
      method: 'POST',
      body: formData
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.error) {
        throw new Error(data.error);
      }

      // Display partial transcription
      displayPartialTranscription(data.text || data, speakerNum);
    })
    .catch(error => {
      console.error('Error transcribing partial audio:', error);
      // Handle error but don't disrupt recording
    });
  }

  // Process the final chunk of audio
  function processFinalChunk(audioBlob, speakerNum = null) {
    // Create FormData for API request
    const formData = new FormData();
    formData.append('file', audioBlob, 'final_chunk.webm');

    // Determine which language to use
    let selectedLanguage;
    if (speakerNum === 1 && language1Select) {
      selectedLanguage = language1Select.value;
    } else if (speakerNum === 2 && language2Select) {
      selectedLanguage = language2Select.value;
    } else if (languageSelect) {
      selectedLanguage = languageSelect.value;
    } else {
      selectedLanguage = 'en'; // Default to English
    }

    formData.append('language', selectedLanguage);

    // Get selected transcription model or use default
    const selectedModel = transcriptionModelSelect ?
      transcriptionModelSelect.value :
      localStorage.getItem('free-trial-transcription-model') || 'gemini-2.0-flash-lite';

    formData.append('model', selectedModel);

    // Add a flag to indicate this is the final chunk
    formData.append('is_final_chunk', 'true');

    // Determine which progress container to use
    let progressContainerToUse, progressTextToUse, progressBarToUse;

    if (speakerNum === 1 || speakerNum === 2) {
      // Bilingual mode - use shared progress container
      progressContainerToUse = bilingualProgressContainer;
      progressTextToUse = bilingualProgressText;
      progressBarToUse = bilingualProgressBar;
    } else {
      // Basic mode
      progressContainerToUse = progressContainer;
      progressTextToUse = progressText;
      progressBarToUse = progressBar;
    }

    // Show progress container
    if (progressContainerToUse) {
      progressContainerToUse.style.display = 'block';
      progressTextToUse.textContent = 'Processing final audio segment...';
    }

    // Send to API
    fetch('/api/transcribe', {
      method: 'POST',
      body: formData
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.error) {
        throw new Error(data.error);
      }

      // Add this final chunk to the partial transcriptions
      if (!partialTranscriptions[speakerNum]) {
        partialTranscriptions[speakerNum] = [];
      }

      partialTranscriptions[speakerNum].push(data.text || data);

      // Display the complete transcription
      displayCompleteTranscription(speakerNum);

      // Hide progress container
      if (progressContainerToUse) {
        progressContainerToUse.style.display = 'none';
      }
    })
    .catch(error => {
      console.error('Error transcribing final chunk:', error);

      // Hide progress container
      if (progressContainerToUse) {
        progressContainerToUse.style.display = 'none';
      }

      // Show error message
      if (progressTextToUse) {
        progressTextToUse.textContent = `Error: ${error.message}`;
      }
    });
  }

  // Display the complete transcription from all chunks
  function displayCompleteTranscription(speakerNum = null) {
    // Determine which transcription element to update
    let transcriptionTextToUse, copyButtonToUse, translateButtonToUse;

    if (speakerNum === 1) {
      transcriptionTextToUse = transcriptionText1;
      copyButtonToUse = copyButton1;
      translateButtonToUse = translateButton1;
    } else if (speakerNum === 2) {
      transcriptionTextToUse = transcriptionText2;
      copyButtonToUse = copyButton2;
      translateButtonToUse = translateButton2;
    } else {
      transcriptionTextToUse = transcriptionText;
      copyButtonToUse = copyButton;
      translateButtonToUse = null; // No translation in basic mode
    }

    // Combine all partial transcriptions
    const combinedText = partialTranscriptions[speakerNum].join(' ');

    // Update transcription text
    if (transcriptionTextToUse) {
      transcriptionTextToUse.innerHTML = `<p>${combinedText}</p>`;
    }

    // Enable copy button
    if (copyButtonToUse) {
      copyButtonToUse.disabled = false;
    }

    // Enable translate button in bilingual mode
    if (translateButtonToUse) {
      translateButtonToUse.disabled = false;
    }

    // Automatically translate in bilingual mode
    if (bilingualModeToggle && bilingualModeToggle.checked && (speakerNum === 1 || speakerNum === 2)) {
      // Short delay to allow UI to update first
      setTimeout(() => {
        // Get target language based on speaker
        const targetLang = speakerNum === 1 ?
          (language2Select ? language2Select.value : 'es') :
          (language1Select ? language1Select.value : 'en');

        // Translate the text
        translateText(combinedText, targetLang, speakerNum);
      }, 500);
    }
  }

  // Display partial transcription
  function displayPartialTranscription(text, speakerNum = null) {
    // Determine which transcription element to update
    let transcriptionTextToUse;

    if (speakerNum === 1) {
      transcriptionTextToUse = transcriptionText1;
    } else if (speakerNum === 2) {
      transcriptionTextToUse = transcriptionText2;
    } else {
      transcriptionTextToUse = transcriptionText;
    }

    // Initialize the array for this speaker if it doesn't exist
    if (!partialTranscriptions[speakerNum]) {
      partialTranscriptions[speakerNum] = [];
    }

    // Store this partial transcription
    partialTranscriptions[speakerNum].push(text);

    // Display all partial transcriptions
    if (transcriptionTextToUse) {
      const combinedText = partialTranscriptions[speakerNum].join(' ');
      transcriptionTextToUse.innerHTML = `<p>${combinedText}</p>`;

      // Enable copy button
      let copyButtonToUse;
      if (speakerNum === 1) {
        copyButtonToUse = copyButton1;
      } else if (speakerNum === 2) {
        copyButtonToUse = copyButton2;
      } else {
        copyButtonToUse = copyButton;
      }

      if (copyButtonToUse) {
        copyButtonToUse.disabled = false;
      }
    }
  }

  // Start recording
  async function startRecording(speakerNum = null) {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }});

      // Create media recorder
      mediaRecorder = new MediaRecorder(stream);

      // Set up event handlers
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        // Check if we have partial transcriptions already
        if (partialTranscriptions[speakerNum] && partialTranscriptions[speakerNum].length > 0) {
          // Only process the final chunk that hasn't been transcribed yet
          // This is the audio recorded since the last chunk was processed
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

          // Process the final chunk
          processFinalChunk(audioBlob, speakerNum);
        } else {
          // No partial transcriptions yet, process the entire recording
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
          processAudio(audioBlob, speakerNum);
        }

        // Stop all tracks in the stream
        stream.getTracks().forEach(track => track.stop());
      };

      // Start recording
      audioChunks = [];
      mediaRecorder.start(100);
      isRecording = true;
      lastChunkTime = 0;

      // Reset partial transcriptions for this speaker
      if (partialTranscriptions[speakerNum]) {
        partialTranscriptions[speakerNum] = [];
      }

      // Update UI based on mode
      if (speakerNum === 1) {
        // Speaker 1
        recordButton1.classList.add('recording');
        recordButton1.innerHTML = '<i class="fas fa-stop"></i><span>Stop</span>';


        // Disable Speaker 2 recording
        if (recordButton2) {
          recordButton2.disabled = true;
        }
      } else if (speakerNum === 2) {
        // Speaker 2
        recordButton2.classList.add('recording');
        recordButton2.innerHTML = '<i class="fas fa-stop"></i><span>Stop</span>';


        // Disable Speaker 1 recording
        if (recordButton1) {
          recordButton1.disabled = true;
        }
      } else {
        // Basic mode
        recordButton.classList.add('recording');

        recordButton.innerHTML = '<i class="fas fa-stop"></i><span>Stop</span>';


      }

      // Start timer
      recordingStartTime = Date.now();
      recordingInterval = setInterval(() => updateTimer(speakerNum), 100);

      // Initialize progress indicator
      initializeCircularProgress();

    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Could not access microphone. Please ensure you have granted permission.');
    }
  }

  // Stop recording
  function stopRecording(speakerNum = null) {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      isRecording = false;

      // Update UI based on mode
      if (speakerNum === 1) {
        // Speaker 1
        recordButton1.classList.remove('recording');

        recordButton1.innerHTML = '<i class="fas fa-microphone"></i><span>Rec</span>';


        // Re-enable Speaker 2 recording
        if (recordButton2) {
          recordButton2.disabled = false;
        }
      } else if (speakerNum === 2) {
        // Speaker 2
        recordButton2.classList.remove('recording');

        recordButton2.innerHTML = '<i class="fas fa-microphone"></i><span>Rec</span>';


        // Re-enable Speaker 1 recording
        if (recordButton1) {
          recordButton1.disabled = false;
        }
      } else {
        // Basic mode
        recordButton.classList.remove('recording');
        recordButton.innerHTML = '<i class="fas fa-microphone"></i><span>Rec</span>';

      }

      // Stop timer
      clearInterval(recordingInterval);

      // Reset all timers to 00:00 when not recording
      if (bilingualModeToggle && bilingualModeToggle.checked) {
        // Reset bilingual mode timers
        if (globalRecordingTimer) {
          globalRecordingTimer.textContent = "00:00";
        }
        if (speaker2Timer) {
          speaker2Timer.textContent = "00:00";
        }
      } else {
        // Reset basic mode timer
        if (basicRecordingTimer) {
          basicRecordingTimer.textContent = "00:00";
        }
      }
    }
  }

  // Process audio (either recorded or uploaded)
  function processAudio(audioBlob, speakerNum = null) {
    // Determine which progress container to use
    let progressContainerToUse, progressTextToUse, progressBarToUse;

    if (speakerNum === 1 || speakerNum === 2) {
      // Bilingual mode - use shared progress container
      progressContainerToUse = bilingualProgressContainer;
      progressTextToUse = bilingualProgressText;
      progressBarToUse = bilingualProgressBar;
    } else {
      // Basic mode
      progressContainerToUse = progressContainer;
      progressTextToUse = progressText;
      progressBarToUse = progressBar;
    }

    // Show progress container
    if (progressContainerToUse) {
      progressContainerToUse.style.display = 'block';
      progressTextToUse.textContent = 'Processing audio...';
    }

    if (circleProgress) {
      circleProgress.animate(0.1); // Start progress animation
    }

    // Create FormData for API request
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');

    // Determine which language to use
    let selectedLanguage;
    if (speakerNum === 1 && language1Select) {
      selectedLanguage = language1Select.value;
    } else if (speakerNum === 2 && language2Select) {
      selectedLanguage = language2Select.value;
    } else if (languageSelect) {
      selectedLanguage = languageSelect.value;
    } else {
      selectedLanguage = 'en'; // Default to English
    }

    formData.append('language', selectedLanguage);

    // Get selected transcription model or use default
    const selectedModel = transcriptionModelSelect ?
      transcriptionModelSelect.value :
      localStorage.getItem('free-trial-transcription-model') || 'gemini-2.0-flash-lite';

    formData.append('model', selectedModel);

    // Send to API
    fetch('/api/transcribe', {
      method: 'POST',
      body: formData
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.error) {
        throw new Error(data.error);
      }

      // Check if it's a background job
      if (data.status === 'processing' && data.job_id) {
        // Poll for job status
        pollJobStatus(data.job_id, speakerNum);
      } else {
        // Display transcription result
        displayTranscription(data.text || data, speakerNum);
      }
    })
    .catch(error => {
      console.error('Error transcribing audio:', error);

      // Check if this is a daily limit exceeded error
      if (error.response && error.response.status === 429) {
        // Show a more user-friendly message with sign-up prompt
        if (progressTextToUse) {
          progressTextToUse.textContent = `You've reached the daily 3-minute free trial limit. Sign up for unlimited access!`;
        }

        // Highlight the sign-up button
        const signUpButton = document.querySelector('.try-it-cta .button-primary');
        if (signUpButton) {
          signUpButton.classList.add('pulse-animation');
          setTimeout(() => {
            signUpButton.classList.remove('pulse-animation');
          }, 5000);
        }
      } else {
        // Regular error handling
        if (progressTextToUse) {
          progressTextToUse.textContent = `Error: ${error.message || 'Failed to transcribe audio'}`;
        }
      }

      if (circleProgress) {
        circleProgress.animate(0);
      }
    });
  }

  // Poll for job status
  function pollJobStatus(jobId, speakerNum = null) {
    // Determine which progress elements to use
    let progressTextToUse;

    if (speakerNum === 1 || speakerNum === 2) {
      progressTextToUse = bilingualProgressText;
    } else {
      progressTextToUse = progressText;
    }

    const pollInterval = setInterval(() => {
      fetch(`/api/transcription_status/${jobId}`)
        .then(response => response.json())
        .then(data => {
          if (data.status === 'completed') {
            clearInterval(pollInterval);
            displayTranscription(data.result.text || data.result, speakerNum);
          } else if (data.status === 'error') {
            clearInterval(pollInterval);
            throw new Error(data.error || 'Transcription failed');
          } else {
            // Update progress
            if (progressTextToUse) {
              progressTextToUse.textContent = 'Processing audio... Please wait.';
            }
            if (circleProgress) {
              circleProgress.animate(0.5); // Show progress
            }
          }
        })
        .catch(error => {
          clearInterval(pollInterval);
          console.error('Error checking job status:', error);
          if (progressTextToUse) {
            progressTextToUse.textContent = `Error: ${error.message}`;
          }
          if (circleProgress) {
            circleProgress.animate(0);
          }
        });
    }, 2000); // Check every 2 seconds
  }

  // Display transcription result
  function displayTranscription(text, speakerNum = null) {
    // Determine which elements to update
    let progressContainerToUse, transcriptionTextToUse, copyButtonToUse, translateButtonToUse;

    if (speakerNum === 1) {
      progressContainerToUse = bilingualProgressContainer;
      transcriptionTextToUse = transcriptionText1;
      copyButtonToUse = copyButton1;
      translateButtonToUse = translateButton1;
    } else if (speakerNum === 2) {
      progressContainerToUse = bilingualProgressContainer;
      transcriptionTextToUse = transcriptionText2;
      copyButtonToUse = copyButton2;
      translateButtonToUse = translateButton2;
    } else {
      progressContainerToUse = progressContainer;
      transcriptionTextToUse = transcriptionText;
      copyButtonToUse = copyButton;
      translateButtonToUse = null; // No translation in basic mode
    }

    // Hide progress container
    if (progressContainerToUse) {
      progressContainerToUse.style.display = 'none';
    }

    // Update transcription text
    if (transcriptionTextToUse) {
      transcriptionTextToUse.innerHTML = `<p>${text}</p>`;
    }

    // Enable copy button
    if (copyButtonToUse) {
      copyButtonToUse.disabled = false;
    }

    // Enable translate button in bilingual mode
    if (translateButtonToUse) {
      translateButtonToUse.disabled = false;
    }

    // Automatically translate in bilingual mode
    if (bilingualModeToggle && bilingualModeToggle.checked && (speakerNum === 1 || speakerNum === 2)) {
      // Short delay to allow UI to update first
      setTimeout(() => {
        // Get target language based on speaker
        const targetLang = speakerNum === 1 ?
          (language2Select ? language2Select.value : 'es') :
          (language1Select ? language1Select.value : 'en');

        // Translate the text
        translateText(text, targetLang, speakerNum);
      }, 500);
    }
  }

  // Translate text function
  async function translateText(text, targetLang, speakerNum) {
    try {
      // Get the selected translation model
      const selectedModel = translationModelSelect ?
        translationModelSelect.value :
        localStorage.getItem('free-trial-translation-model') || 'gemini-2.0-flash-lite';

      // Show progress
      bilingualProgressContainer.style.display = 'block';
      bilingualProgressText.textContent = 'Translating...';

      // Send translation request
      const response = await fetch('/api/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          target_language: targetLang,
          translation_model: selectedModel
        })
      });

      if (!response.ok) {
        throw new Error(`Translation failed: ${response.status}`);
      }

      const result = await response.json();

      // Hide progress
      bilingualProgressContainer.style.display = 'none';

      // Display translation
      displayTranslation(result.text, speakerNum);

      return result.text;
    } catch (error) {
      console.error('Translation error:', error);
      bilingualProgressText.textContent = `Translation error: ${error.message}`;

      // Check if this is a daily limit exceeded error
      if (error.response && error.response.status === 429) {
        bilingualProgressText.textContent = `You've reached the daily 3-minute free trial limit. Sign up for unlimited access!`;

        // Highlight the sign-up button
        const signUpButton = document.querySelector('.try-it-cta .button-primary');
        if (signUpButton) {
          signUpButton.classList.add('pulse-animation');
          setTimeout(() => {
            signUpButton.classList.remove('pulse-animation');
          }, 5000);
        }
      }

      return null;
    }
  }

  // Display translation result
  function displayTranslation(text, speakerNum) {
    let translationTextToUse, copyTranslationButtonToUse;

    if (speakerNum === 1) {
      translationTextToUse = translationText1;
      copyTranslationButtonToUse = copyTranslation1;
    } else if (speakerNum === 2) {
      translationTextToUse = translationText2;
      copyTranslationButtonToUse = copyTranslation2;
    } else {
      return; // No translation in basic mode
    }

    // Update translation text
    if (translationTextToUse) {
      translationTextToUse.innerHTML = `<p>${text}</p>`;
    }

    // Enable copy button
    if (copyTranslationButtonToUse) {
      copyTranslationButtonToUse.disabled = false;
    }
  }

  // Handle file upload
  function handleFileUpload(event, speakerNum = null) {
    const file = event.target.files[0];
    if (!file) return;

    // Check file type
    const fileType = file.type;
    if (!fileType.startsWith('audio/')) {
      alert('Please upload an audio file.');
      return;
    }

    // Check file size (max 25MB for free trial)
    const maxSize = 25 * 1024 * 1024; // 25MB in bytes
    if (file.size > maxSize) {
      alert('File size exceeds the 25MB limit for the free trial.');
      return;
    }

    // Process the file
    processAudio(file, speakerNum);
  }

  // Copy transcription to clipboard
  function copyTranscription(speakerNum = null) {
    let text, buttonToUpdate;

    if (speakerNum === 1 && transcriptionText1) {
      text = transcriptionText1.textContent;
      buttonToUpdate = copyButton1;
    } else if (speakerNum === 2 && transcriptionText2) {
      text = transcriptionText2.textContent;
      buttonToUpdate = copyButton2;
    } else if (transcriptionText) {
      text = transcriptionText.textContent;
      buttonToUpdate = copyButton;
    } else {
      return; // No text to copy
    }

    navigator.clipboard.writeText(text)
      .then(() => {
        // Show success feedback
        if (buttonToUpdate) {
          const originalText = buttonToUpdate.innerHTML;
          buttonToUpdate.innerHTML = '<i class="fas fa-check"></i><span>Copied!</span>';

          // Reset after 2 seconds
          setTimeout(() => {
            buttonToUpdate.innerHTML = originalText;
          }, 2000);
        }
      })
      .catch(err => {
        console.error('Failed to copy text:', err);
        alert('Failed to copy text to clipboard.');
      });
  }

  // Event Listeners
  recordButton.addEventListener('click', () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  });

  audioUpload.addEventListener('change', handleFileUpload);

  copyButton.addEventListener('click', copyTranscription);

  // Initialize bilingual mode toggle
  if (bilingualModeToggle && basicMode && bilingualMode) {
    // Load saved preference
    const savedBilingualMode = localStorage.getItem('free-trial-bilingual-mode') === 'true';
    bilingualModeToggle.checked = savedBilingualMode;

    // Set initial state
    if (savedBilingualMode) {
      basicMode.style.display = 'none';
      bilingualMode.style.display = 'block';
    } else {
      basicMode.style.display = 'block';
      bilingualMode.style.display = 'none';
    }

    // Add event listener for toggle
    bilingualModeToggle.addEventListener('change', () => {
      const isEnabled = bilingualModeToggle.checked;

      // Save preference
      localStorage.setItem('free-trial-bilingual-mode', isEnabled);

      // Toggle visibility
      if (isEnabled) {
        // Bilingual mode
        basicMode.style.display = 'none';
        bilingualMode.style.display = 'block';

        // Sync language from basic mode to speaker 1
        if (languageSelect && language1Select) {
          language1Select.value = languageSelect.value;
        }
      } else {
        // Basic mode
        basicMode.style.display = 'block';
        bilingualMode.style.display = 'none';
      }

      // Stop any ongoing recordings
      if (isRecording) {
        stopRecording();
      }
    });

    // Add event listeners for speaker 1 controls
    if (recordButton1) {
      recordButton1.addEventListener('click', () => {
        if (isRecording) {
          stopRecording(1);
        } else {
          startRecording(1);
        }
      });
    }

    if (audioUpload1) {
      audioUpload1.addEventListener('change', (event) => {
        handleFileUpload(event, 1);
      });
    }

    if (copyButton1) {
      copyButton1.addEventListener('click', () => {
        copyTranscription(1);
      });
    }

    // Add translation event listeners for speaker 1
    if (translateButton1) {
      translateButton1.addEventListener('click', async () => {
        // Get the text to translate
        const text = transcriptionText1.textContent.trim();
        if (!text || text === 'Speaker 1 transcription will appear here...') {
          return;
        }

        // Get the target language (speaker 2's language)
        const targetLang = language2Select ? language2Select.value : 'en';

        // Translate the text
        await translateText(text, targetLang, 1);
      });
    }

    if (copyTranslation1) {
      copyTranslation1.addEventListener('click', () => {
        const text = translationText1.textContent;
        if (text && text !== 'Translation will appear here...') {
          navigator.clipboard.writeText(text)
            .then(() => {
              // Show success feedback
              const originalText = copyTranslation1.innerHTML;
              copyTranslation1.innerHTML = '<i class="fas fa-check"></i>';

              // Reset after 2 seconds
              setTimeout(() => {
                copyTranslation1.innerHTML = originalText;
              }, 2000);
            })
            .catch(err => {
              console.error('Failed to copy text:', err);
              alert('Failed to copy text to clipboard.');
            });
        }
      });
    }

    // Add event listeners for speaker 2 controls
    if (recordButton2) {
      recordButton2.addEventListener('click', () => {
        if (isRecording) {
          stopRecording(2);
        } else {
          startRecording(2);
        }
      });
    }

    if (audioUpload2) {
      audioUpload2.addEventListener('change', (event) => {
        handleFileUpload(event, 2);
      });
    }

    if (copyButton2) {
      copyButton2.addEventListener('click', () => {
        copyTranscription(2);
      });
    }

    // Add translation event listeners for speaker 2
    if (translateButton2) {
      translateButton2.addEventListener('click', async () => {
        // Get the text to translate
        const text = transcriptionText2.textContent.trim();
        if (!text || text === 'Speaker 2 transcription will appear here...') {
          return;
        }

        // Get the target language (speaker 1's language)
        const targetLang = language1Select ? language1Select.value : 'en';

        // Translate the text
        await translateText(text, targetLang, 2);
      });
    }

    if (copyTranslation2) {
      copyTranslation2.addEventListener('click', () => {
        const text = translationText2.textContent;
        if (text && text !== 'Translation will appear here...') {
          navigator.clipboard.writeText(text)
            .then(() => {
              // Show success feedback
              const originalText = copyTranslation2.innerHTML;
              copyTranslation2.innerHTML = '<i class="fas fa-check"></i>';

              // Reset after 2 seconds
              setTimeout(() => {
                copyTranslation2.innerHTML = originalText;
              }, 2000);
            })
            .catch(err => {
              console.error('Failed to copy text:', err);
              alert('Failed to copy text to clipboard.');
            });
        }
      });
    }
  }

  // Function to toggle premium models
  function togglePremiumModels(showPremium = true) {
    const modelSelects = [transcriptionModelSelect, translationModelSelect, ttsModelSelect];

    modelSelects.forEach(select => {
      if (!select) return;

      // Get current value to preserve selection if possible
      const currentValue = select.value;

      // Process each option
      Array.from(select.options).forEach(option => {
        const isPremium = option.getAttribute('data-free-tier') !== 'true';

        if (isPremium) {
          if (!showPremium) {
            // Disable premium options
            option.disabled = true;
            option.classList.add('premium-disabled');
          } else {
            // Enable premium options
            option.disabled = false;
            option.classList.remove('premium-disabled');
          }
        }
      });

      // If current selection is now disabled, switch to default free tier option
      if (!showPremium && Array.from(select.options).find(opt => opt.value === currentValue)?.disabled) {
        // Find first free tier option
        const freeTierOption = Array.from(select.options).find(opt => opt.getAttribute('data-free-tier') === 'true');
        if (freeTierOption) {
          select.value = freeTierOption.value;

          // Update localStorage
          const storageKey = select.id === 'transcription-model-select' ? 'free-trial-transcription-model' :
                            select.id === 'translation-model-select' ? 'free-trial-translation-model' :
                            'free-trial-tts-model';

          localStorage.setItem(storageKey, freeTierOption.value);
        }
      }
    });
  }

  // Initialize settings panel functionality
  if (settingsToggle && settingsPanel) {
    // Toggle settings panel when button is clicked
    settingsToggle.addEventListener('click', (event) => {
      event.stopPropagation();
      const isVisible = settingsPanel.style.display === 'block';
      settingsPanel.style.display = isVisible ? 'none' : 'block';
      settingsToggle.classList.toggle('active');
    });

    // Close settings panel when clicking outside
    document.addEventListener('click', (event) => {
      if (!settingsToggle.contains(event.target) && !settingsPanel.contains(event.target)) {
        settingsPanel.style.display = 'none';
        settingsToggle.classList.remove('active');
      }
    });

    // Initialize model selectors with saved preferences or defaults
    if (transcriptionModelSelect) {
      // Set default to Gemini 2.0 Flash Lite
      const savedTranscriptionModel = localStorage.getItem('free-trial-transcription-model') || 'gemini-2.0-flash-lite';
      transcriptionModelSelect.value = savedTranscriptionModel;

      // Save selection to localStorage when changed
      transcriptionModelSelect.addEventListener('change', function() {
        localStorage.setItem('free-trial-transcription-model', this.value);
      });
    }

    if (translationModelSelect) {
      // Set default to Gemini 2.0 Flash Lite
      const savedTranslationModel = localStorage.getItem('free-trial-translation-model') || 'gemini-2.0-flash-lite';
      translationModelSelect.value = savedTranslationModel;

      // Save selection to localStorage when changed
      translationModelSelect.addEventListener('change', function() {
        localStorage.setItem('free-trial-translation-model', this.value);
      });
    }

    if (ttsModelSelect) {
      // Set default to Gemini 2.5 Flash TTS
      const savedTtsModel = localStorage.getItem('free-trial-tts-model') || 'gemini-2.5-flash-tts';
      ttsModelSelect.value = savedTtsModel;

      // Save selection to localStorage when changed
      ttsModelSelect.addEventListener('change', function() {
        localStorage.setItem('free-trial-tts-model', this.value);
      });
    }

    // Initialize premium models toggle
    if (premiumModelsToggle) {
      // Load saved preference (default to showing all models)
      const showPremiumModels = localStorage.getItem('free-trial-show-premium-models') !== 'false';
      premiumModelsToggle.checked = showPremiumModels;

      // Apply initial state
      togglePremiumModels(showPremiumModels);

      // Add event listener for toggle
      premiumModelsToggle.addEventListener('change', function() {
        const showPremium = this.checked;
        localStorage.setItem('free-trial-show-premium-models', showPremium);
        togglePremiumModels(showPremium);
      });
    }
  }

  // Initialize theme toggle functionality
  const themeToggleBtn = document.getElementById('theme-toggle-btn');
  const themeOptionsDropdown = document.getElementById('theme-options');
  const themeOptions = document.querySelectorAll('.theme-option');

  if (themeToggleBtn && themeOptionsDropdown) {
    // Toggle dropdown when clicking the button
    themeToggleBtn.addEventListener('click', (event) => {
      event.stopPropagation();
      const isShown = themeOptionsDropdown.classList.toggle('show');
      themeOptionsDropdown.style.display = isShown ? 'block' : 'none';
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (event) => {
      if (!themeToggleBtn.contains(event.target) && !themeOptionsDropdown.contains(event.target)) {
        themeOptionsDropdown.classList.remove('show');
        themeOptionsDropdown.style.display = 'none';
      }
    });

    // Handle theme selection
    themeOptions.forEach(option => {
      option.addEventListener('click', () => {
        const theme = option.getAttribute('data-theme');
        applyTheme(theme);

        // Save theme preference
        try {
          localStorage.setItem('vocal-local-theme', theme);
        } catch (e) {
          console.warn('LocalStorage is not available.');
        }

        // Close dropdown
        themeOptionsDropdown.classList.remove('show');
        themeOptionsDropdown.style.display = 'none';
      });
    });

    // Load saved theme
    loadTheme();
  }

  // Function to apply the selected theme
  function applyTheme(theme) {
    let effectiveTheme = theme;

    // Determine the actual theme if 'system' is selected
    if (theme === 'system') {
      effectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    // Apply the theme class to the <html> element
    document.documentElement.setAttribute('data-theme', effectiveTheme);

    // Update the toggle button icon
    if (themeToggleBtn) {
      const icon = themeToggleBtn.querySelector('i');
      if (icon) {
        if (theme === 'light') {
          icon.className = 'fas fa-lightbulb';
        } else if (theme === 'dark') {
          icon.className = 'fas fa-moon';
        } else { // system
          icon.className = 'fas fa-circle-half-stroke';
        }
      }
    }
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
});
