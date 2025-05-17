/**
 * File size warning utility for VocalLocal
 * This script adds enhanced warnings for large file uploads
 */

// Function to show file size warnings
function showFileSizeWarnings(fileSizeMB, isOpenAIModel, showStatus) {
  // Clear any existing warnings
  const statusEl = document.getElementById('status');
  if (statusEl && statusEl.classList.contains('status-warning')) {
    statusEl.style.display = 'none';
  }

  // Show warnings based on file size and selected model
  if (isOpenAIModel && fileSizeMB > 25) {
    showStatus(`Warning: File size (${fileSizeMB.toFixed(2)} MB) exceeds OpenAI's 25MB limit. Will automatically switch to Gemini.`, 'warning', true);
    return true;
  }

  // Only show warnings for very large files
  if (fileSizeMB > 150) {
    showStatus(`Warning: Very large file (${fileSizeMB.toFixed(2)} MB). Processing may take longer.`, 'warning', true);
    return true;
  }

  if (fileSizeMB > 100) {
    showStatus(`Warning: Large file (${fileSizeMB.toFixed(2)} MB). Processing may take longer.`, 'warning');
    return true;
  }

  return false;
}

// Function to confirm large file uploads
function confirmLargeFileUpload(fileSizeMB) {
  // Only confirm for extremely large files (>200MB)
  if (fileSizeMB > 200) {
    return confirm(`This file is ${fileSizeMB.toFixed(2)} MB, which exceeds Gemini's 200MB limit. The transcription may take longer or be less reliable. Do you want to continue anyway?`);
  }

  return true;
}

// Apply the enhanced warnings to all file inputs
document.addEventListener('DOMContentLoaded', () => {
  // Override the existing file change handlers with our enhanced version
  const fileInputs = document.querySelectorAll('input[type="file"]');

  fileInputs.forEach(input => {
    // Store the original change handler
    const originalChangeHandler = input.onchange;

    // Add our enhanced handler
    input.addEventListener('change', (event) => {
      if (input.files.length) {
        const file = input.files[0];
        const fileSizeMB = file.size / (1024 * 1024);

        // Get the transcription model
        const selectedModel = window.getTranscriptionModel ? window.getTranscriptionModel() : 'gemini';
        const isOpenAIModel = selectedModel.startsWith('gpt-') || selectedModel.startsWith('whisper-');

        // Show enhanced warnings for large files
        showFileSizeWarnings(fileSizeMB, isOpenAIModel, window.showStatus);

        // Only confirm for extremely large files
        if (fileSizeMB > 200) {
          if (!confirmLargeFileUpload(fileSizeMB)) {
            // User chose to cancel
            input.value = ''; // Clear the file input
            window.showStatus('File upload cancelled. Please select a smaller file.', 'info');
            event.preventDefault();
            event.stopPropagation();
            return false;
          }
        }
      }
    }, true); // Use capturing to run before other handlers
  });
});
