/**
 * Circular Upload Progress Indicator
 *
 * This module replaces the paperclip icon with a circular progress indicator
 * during file uploads, with cancel functionality on hover.
 */

/**
 * Format bytes to a human-readable format
 * @param {number} bytes - The number of bytes
 * @param {number} decimals - The number of decimal places
 * @returns {string} - The formatted string
 */
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

document.addEventListener('DOMContentLoaded', () => {
  // Configuration
  const config = {
    color: 'hsl(var(--primary))', // Use the site's primary color (purple)
    trailColor: 'hsl(var(--muted))',
    svgStyle: {
      display: 'block',
      width: '100%',
    },
    text: {
      style: {
        color: 'hsl(var(--primary))',
        position: 'absolute',
        left: '50%',
        top: '50%',
        padding: 0,
        margin: 0,
        transform: 'translate(-50%, -50%)'
      }
    },
    // Skip progress indicator for files smaller than 1MB
    fileSizeThreshold: 1024 * 1024,
    // States for the progress indicator
    states: {
      UPLOADING: 'uploading',
      PROCESSING: 'processing',
      COMPLETED: 'completed',
      CANCELLED: 'cancelled',
      ERROR: 'error'
    }
  };

  // Store active uploads and their controllers
  const activeUploads = new Map();

  /**
   * Create a circular progress indicator to replace the paperclip icon
   * @param {HTMLElement} uploadButton - The upload button element
   * @returns {Object} - The progress bar instance
   */
  function createProgressIndicator(uploadButton) {
    // Create container for the progress bar
    const container = document.createElement('div');
    container.className = 'upload-progress-container';
    container.style.position = 'relative';

    // Save the original button content
    const originalContent = uploadButton.innerHTML;

    // Clear the button content and append the container
    uploadButton.innerHTML = '';
    uploadButton.appendChild(container);

    // Create a simple spinner container
    const spinnerContainer = document.createElement('div');
    spinnerContainer.className = 'spinner-container';
    spinnerContainer.style.width = '100%';
    spinnerContainer.style.height = '100%';
    spinnerContainer.style.position = 'relative';
    spinnerContainer.style.borderRadius = '50%';
    spinnerContainer.style.backgroundColor = config.trailColor;
    container.appendChild(spinnerContainer);

    // Create the spinner element
    const spinnerElement = document.createElement('div');
    spinnerElement.className = 'spinner-element';
    spinnerElement.style.width = '80%';
    spinnerElement.style.height = '80%';
    spinnerElement.style.borderRadius = '50%';
    spinnerElement.style.border = `2px solid ${config.trailColor}`;
    spinnerElement.style.borderTopColor = config.color;
    spinnerElement.style.position = 'absolute';
    spinnerElement.style.top = '10%';
    spinnerElement.style.left = '10%';
    spinnerContainer.appendChild(spinnerElement);

    // Add the spinner animation - slow rotation (3 seconds per rotation)
    if (!document.getElementById('spinner-keyframes')) {
      const style = document.createElement('style');
      style.id = 'spinner-keyframes';
      style.textContent = `
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .spinner-element {
          animation: spin 3s linear infinite;
        }
      `;
      document.head.appendChild(style);
    }

    // Create a simple progress object
    const progressBar = {
      // Dummy animate method (we're not using it, but keeping for compatibility)
      animate: (progress) => {
        // Do nothing - we're just using the spinner
      },
      spinnerElement: spinnerElement,
      spinnerContainer: spinnerContainer
    };

    // Store the current state
    let currentState = config.states.UPLOADING;

    // Add hover effect for cancel functionality
    uploadButton.addEventListener('mouseenter', () => {
      if (activeUploads.has(uploadButton.id) && currentState === config.states.UPLOADING) {
        // Show cancel icon on hover only during upload (not during processing)
        const cancelIcon = document.createElement('i');
        cancelIcon.className = 'fas fa-times';
        cancelIcon.style.position = 'absolute';
        cancelIcon.style.left = '50%';
        cancelIcon.style.top = '50%';
        cancelIcon.style.transform = 'translate(-50%, -50%)';
        cancelIcon.style.color = 'hsl(var(--destructive))';
        cancelIcon.style.fontSize = '10px';
        cancelIcon.style.zIndex = '10';

        container.appendChild(cancelIcon);
        uploadButton.dataset.cancelVisible = 'true';
      }
    });

    uploadButton.addEventListener('mouseleave', () => {
      if (uploadButton.dataset.cancelVisible === 'true') {
        // Remove cancel icon when not hovering
        const cancelIcon = container.querySelector('.fa-times');
        if (cancelIcon) {
          cancelIcon.remove();
        }
        uploadButton.dataset.cancelVisible = 'false';
      }
    });

    // Add click handler for cancel functionality
    uploadButton.addEventListener('click', (event) => {
      if (activeUploads.has(uploadButton.id) && currentState === config.states.UPLOADING) {
        event.preventDefault();
        event.stopPropagation();

        // Cancel the upload
        const controller = activeUploads.get(uploadButton.id);
        controller.abort();

        // Reset the button
        resetUploadButton(uploadButton, originalContent);

        // Show status message
        if (window.showStatus) {
          window.showStatus('Upload cancelled', 'warning');
        }
      }
    });

    // Function to update the state
    const updateState = (newState) => {
      currentState = newState;

      // Update the visual appearance based on state
      if (newState === config.states.PROCESSING) {
        // Continue showing the spinner during processing
        // No visual change needed - spinner keeps spinning
      } else if (newState === config.states.UPLOADING) {
        // No visual change needed - spinner keeps spinning
      } else if (newState === config.states.COMPLETED) {
        // Reset the button after a short delay to show completion
        setTimeout(() => {
          resetUploadButton(uploadButton, originalContent);
        }, 500);
      } else if (newState === config.states.ERROR || newState === config.states.CANCELLED) {
        // Reset immediately
        resetUploadButton(uploadButton, originalContent);
      }
    };

    // Create the progress instance object
    const progressInstance = {
      progressBar,
      originalContent,
      updateState
    };

    // Store a reference to the progress instance on the button element
    uploadButton._progressInstance = progressInstance;

    return progressInstance;
  }

  /**
   * Reset the upload button to its original state
   * @param {HTMLElement} uploadButton - The upload button element
   * @param {string} originalContent - The original HTML content of the button
   */
  function resetUploadButton(uploadButton, originalContent) {
    uploadButton.innerHTML = originalContent;
    activeUploads.delete(uploadButton.id);
    uploadButton.style.pointerEvents = 'auto';

    // Clean up the progress instance reference
    if (uploadButton._progressInstance) {
      delete uploadButton._progressInstance;
    }
  }

  /**
   * Enhanced sendToServer function with progress tracking
   * @param {FormData} formData - The form data to send
   * @param {string} uploadButtonId - The ID of the upload button
   * @param {string} endpoint - The API endpoint
   * @param {number} maxRetries - Maximum number of retries
   * @returns {Promise} - Promise that resolves with the server response
   */
  function sendToServerWithProgress(formData, uploadButtonId, endpoint = '/api/transcribe', maxRetries = 1) {
    return new Promise(async (resolve, reject) => {
      const uploadButton = document.getElementById(uploadButtonId);
      if (!uploadButton) {
        reject(new Error(`Upload button with ID ${uploadButtonId} not found`));
        return;
      }

      // Get the file from the form data
      const file = formData.get('file');

      // Log file information
      if (file) {
        console.log(`File: ${file.name}, Size: ${formatBytes(file.size)}, Type: ${file.type}`);
      }

      // Skip progress indicator for small files
      if (file && file.size < config.fileSizeThreshold) {
        // Use the original sendToServer function for small files
        if (window.sendToServer) {
          try {
            const result = await window.sendToServer(formData, endpoint, maxRetries);
            resolve(result);
          } catch (error) {
            reject(error);
          }
          return;
        }
      }

      // Create progress indicator (now always a spinner)
      const { progressBar, originalContent, updateState } = createProgressIndicator(uploadButton);

      // Create AbortController for timeout and cancellation
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000); // 120 second timeout for larger files

      // Store the controller for potential cancellation
      activeUploads.set(uploadButtonId, controller);

      // Disable normal click behavior while uploading
      uploadButton.style.pointerEvents = 'auto';

      let attempt = 0;

      while (attempt <= maxRetries) {
        try {
          // Create XHR to track progress
          const xhr = new XMLHttpRequest();

          // Set up the request
          xhr.open('POST', endpoint, true);

          // Set up progress tracking with actual file size consideration
          xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
              // Calculate progress based on actual bytes uploaded
              const progress = event.loaded / event.total;

              // Log progress for debugging
              console.log(`Upload progress: ${Math.round(progress * 100)}% (${formatBytes(event.loaded)} / ${formatBytes(event.total)})`);

              // Update the progress indicator
              progressBar.animate(progress);
            }
          };

          // Create a promise to handle the XHR
          const xhrPromise = new Promise((xhrResolve, xhrReject) => {
            xhr.onload = () => {
              if (xhr.status >= 200 && xhr.status < 300) {
                try {
                  const result = JSON.parse(xhr.responseText);

                  // Switch to processing state after upload completes
                  updateState(config.states.PROCESSING);

                  xhrResolve(result);
                } catch (error) {
                  xhrReject(new Error('Invalid JSON response'));
                }
              } else {
                xhrReject(new Error(`Server error: ${xhr.status}`));
              }
            };

            xhr.onerror = () => {
              xhrReject(new Error('Network error'));
            };

            xhr.ontimeout = () => {
              xhrReject(new Error('Request timed out'));
            };

            // Handle abort
            xhr.onabort = () => {
              xhrReject(new Error('Upload cancelled'));
            };
          });

          // Link the abort controller to the XHR
          controller.signal.addEventListener('abort', () => {
            xhr.abort();
          });

          // Send the request
          xhr.send(formData);

          // Wait for the XHR to complete
          const result = await xhrPromise;

          // Clear timeout
          clearTimeout(timeoutId);

          // Keep the progress indicator in processing state
          // The actual completion will be handled by the callback in script.js

          resolve(result);
          return; // Exit the retry loop on success
        } catch (error) {
          attempt++;

          // Log the error
          console.error(`Attempt ${attempt} failed:`, error);

          // If it's a cancellation, don't retry
          if (error.message === 'Upload cancelled') {
            updateState(config.states.CANCELLED);
            reject(error);
            return;
          }

          // If it's a timeout or a network error and we have retries left
          if ((error.name === 'AbortError' ||
              error.message === 'Network error' ||
              error.message === 'Request timed out') &&
              attempt <= maxRetries) {
            console.log(`Retrying... (${attempt}/${maxRetries})`);
            await new Promise(r => setTimeout(r, 1000)); // Wait 1 second before retry
            continue;
          }

          // If we're out of retries or it's not a retriable error
          updateState(config.states.ERROR);
          reject(error);
          return;
        }
      }
    });
  }

  // Expose the function globally
  window.sendToServerWithProgress = sendToServerWithProgress;
});
