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
    // Check if our background-supporting function exists
    if (window.sendToServerWithBackgroundSupport) {
      return window.sendToServerWithBackgroundSupport(formData, null, endpoint);
    } else {
      // Fall back to the original function
      return originalSendToServer(formData, endpoint, maxRetries);
    }
  };
  
  console.log('Background processing support enabled');
});