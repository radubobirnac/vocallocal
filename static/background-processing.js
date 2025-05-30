/**
 * Background processing integration for VocalLocal
 * This script adds support for background processing of large files
 */

// Wait for the page to load
document.addEventListener('DOMContentLoaded', function() {
  // Store the original sendToServer function
  const originalSendToServer = window.sendToServer;

  // Replace it with our enhanced version that supports background processing
  window.sendToServer = async function(formData, endpoint = '/api/transcribe', maxRetries = 1) {
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
      if (result && result.status === 'processing' && result.job_id) {
        console.log('Background processing detected, job ID:', result.job_id);

        // Determine which transcript element to update
        let elementId = 'basic-transcript';
        const mode = document.querySelector('input[name="mode"]:checked').value;

        if (mode === 'conversation') {
          // For conversation mode, check which speaker
          const speaker = formData.get('speaker');
          if (speaker === '1') {
            elementId = 'transcript-1';
          } else if (speaker === '2') {
            elementId = 'transcript-2';
          }
        }

        // Show processing message in the transcript area
        const transcriptElement = document.getElementById(elementId);
        if (transcriptElement) {
          transcriptElement.value = "Processing large file in background...";
        }

        // Start polling for job status
        startBackgroundJobPolling(result.job_id, elementId);

        // Return a placeholder result
        return {
          text: "Processing large file in background...",
          processing: true,
          job_id: result.job_id
        };
      }

      // For regular processing, return the result directly
      return result;
    } catch (error) {
      console.error('Error in sendToServer:', error);
      throw error;
    }
  };

  // Add a function to poll for background job status
  window.startBackgroundJobPolling = function(jobId, elementId) {
    console.log(`Starting polling for job ${jobId}, updating element ${elementId}`);

    const maxAttempts = 60; // 5 minutes (5s intervals)
    let attempts = 0;

    const statusElement = document.getElementById('status');
    if (statusElement) {
      statusElement.textContent = 'Processing large file in background...';
      statusElement.className = 'info';
    }

    function checkStatus() {
      console.log(`Checking status for job ${jobId}, attempt ${attempts + 1}`);

      fetch(`/api/transcription_status/${jobId}`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
          }
          return response.json();
        })
        .then(status => {
          console.log(`Job ${jobId} status:`, status);

          if (status.status === 'completed' && status.result) {
            // Get the transcript element
            const transcriptElement = document.getElementById(elementId);
            if (!transcriptElement) {
              console.error(`Element not found: ${elementId}`);
              return;
            }

            // Extract the text from the result
            let transcriptionText;

            if (typeof status.result === 'string') {
              transcriptionText = status.result;
            } else if (status.result && typeof status.result.text === 'string') {
              transcriptionText = status.result.text;
            } else if (status.result && typeof status.result === 'object') {
              // Try to stringify the object for debugging
              console.log('Result object:', status.result);
              // Use any text property we can find
              if (status.result.transcription) {
                transcriptionText = status.result.transcription;
              } else if (status.result.result) {
                transcriptionText = status.result.result;
              } else {
                // Last resort - use the whole object as a string
                transcriptionText = JSON.stringify(status.result);
              }
            } else {
              transcriptionText = "Transcription completed but format was unexpected.";
              console.warn("Unexpected result format:", status.result);
            }

            // Update the transcript using the proper updateTranscript function
            console.log(`Updating ${elementId} with transcription (${transcriptionText.length} chars)`);

            // Use updateTranscript function if available, otherwise fall back to direct manipulation
            if (typeof window.updateTranscript === 'function') {
              console.log('Using updateTranscript function');
              window.updateTranscript(elementId, transcriptionText);
            } else {
              console.log('updateTranscript function not available, using direct DOM manipulation');
              transcriptElement.value = transcriptionText;

              // Trigger change event
              const event = new Event('change');
              transcriptElement.dispatchEvent(event);
            }

            // Update status
            if (statusElement) {
              statusElement.textContent = 'Transcription complete!';
              statusElement.className = 'success';
            }

            // Enable any disabled buttons
            const uploadButtons = document.querySelectorAll('.upload-btn');
            uploadButtons.forEach(btn => {
              btn.disabled = false;
            });
          } else if (status.status === 'failed') {
            console.error(`Job ${jobId} failed:`, status.error);

            // Update status
            if (statusElement) {
              statusElement.textContent = `Transcription failed: ${status.error}`;
              statusElement.className = 'error';
            }

            // Enable any disabled buttons
            const uploadButtons = document.querySelectorAll('.upload-btn');
            uploadButtons.forEach(btn => {
              btn.disabled = false;
            });
          } else if (status.status === 'processing') {
            // Continue polling
            console.log(`Job ${jobId} still processing, progress: ${status.progress || 'unknown'}`);

            // Update status
            if (statusElement) {
              statusElement.textContent = `Processing large file... ${status.progress || ''}`;
              statusElement.className = 'info';
            }

            // Schedule next check
            attempts++;
            if (attempts < maxAttempts) {
              setTimeout(checkStatus, 5000);
            } else {
              console.warn(`Job ${jobId} polling timed out after ${maxAttempts} attempts`);

              // Update status
              if (statusElement) {
                statusElement.textContent = 'Transcription timed out. Please check back later.';
                statusElement.className = 'warning';
              }

              // Enable any disabled buttons
              const uploadButtons = document.querySelectorAll('.upload-btn');
              uploadButtons.forEach(btn => {
                btn.disabled = false;
              });
            }
          } else {
            console.warn(`Job ${jobId} has unknown status:`, status);

            // Update status
            if (statusElement) {
              statusElement.textContent = 'Transcription status unknown';
              statusElement.className = 'warning';
            }

            // Enable any disabled buttons
            const uploadButtons = document.querySelectorAll('.upload-btn');
            uploadButtons.forEach(btn => {
              btn.disabled = false;
            });
          }
        })
        .catch(error => {
          console.error(`Error checking status for job ${jobId}:`, error);

          // Update status
          if (statusElement) {
            statusElement.textContent = 'Error checking transcription status';
            statusElement.className = 'error';
          }

          // Schedule next check if we haven't reached the limit
          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(checkStatus, 5000);
          } else {
            console.warn(`Job ${jobId} polling timed out after ${maxAttempts} attempts`);

            // Enable any disabled buttons
            const uploadButtons = document.querySelectorAll('.upload-btn');
            uploadButtons.forEach(btn => {
              btn.disabled = false;
            });
          }
        });
    }

    // Start checking status
    checkStatus();
  };

  console.log('Background processing support enabled');
});
