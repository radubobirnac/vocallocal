/**
 * Usage Deduction Utilities for VocalLocal (Firebase Free Plan Compatible)
 *
 * This module provides client-side utilities for deducting usage
 * from user accounts using direct Firebase Realtime Database operations
 * instead of Cloud Functions, making it compatible with Firebase's free plan.
 */

/**
 * Deduct transcription usage from a user's account using direct database operations
 *
 * @param {string} userId - The user ID to deduct usage from
 * @param {number} minutesUsed - The number of minutes to deduct
 * @returns {Promise<Object>} - Deduction result
 */
async function deductTranscriptionUsage(userId, minutesUsed) {
  try {
    return await deductUsageDirectly(userId, 'transcriptionMinutes', minutesUsed, 'transcription');
  } catch (error) {
    console.error('Error deducting transcription usage:', error);
    throw error;
  }
}

/**
 * Deduct translation usage from a user's account
 *
 * @param {string} userId - The user ID to deduct usage from
 * @param {number} wordsUsed - The number of words to deduct
 * @returns {Promise<Object>} - Deduction result
 */
async function deductTranslationUsage(userId, wordsUsed) {
  try {
    const deductFunction = firebase.functions().httpsCallable('deductTranslationUsage');
    const result = await deductFunction({
      userId: userId,
      wordsUsed: wordsUsed
    });

    return result.data;
  } catch (error) {
    console.error('Error deducting translation usage:', error);
    throw error;
  }
}

/**
 * Deduct TTS usage from a user's account
 *
 * @param {string} userId - The user ID to deduct usage from
 * @param {number} minutesUsed - The number of minutes to deduct
 * @returns {Promise<Object>} - Deduction result
 */
async function deductTTSUsage(userId, minutesUsed) {
  try {
    const deductFunction = firebase.functions().httpsCallable('deductTTSUsage');
    const result = await deductFunction({
      userId: userId,
      minutesUsed: minutesUsed
    });

    return result.data;
  } catch (error) {
    console.error('Error deducting TTS usage:', error);
    throw error;
  }
}

/**
 * Deduct AI credits from a user's account
 *
 * @param {string} userId - The user ID to deduct usage from
 * @param {number} creditsUsed - The number of credits to deduct
 * @returns {Promise<Object>} - Deduction result
 */
async function deductAICredits(userId, creditsUsed) {
  try {
    const deductFunction = firebase.functions().httpsCallable('deductAICredits');
    const result = await deductFunction({
      userId: userId,
      creditsUsed: creditsUsed
    });

    return result.data;
  } catch (error) {
    console.error('Error deducting AI credits:', error);
    throw error;
  }
}

/**
 * Generic deduct usage function (uses the existing deductUsage function)
 *
 * @param {string} userId - The user ID to deduct usage from
 * @param {string} serviceType - The type of service ('transcription', 'translation', 'tts', 'ai')
 * @param {number} amount - The amount to deduct
 * @returns {Promise<Object>} - Deduction result
 */
async function deductUsage(userId, serviceType, amount) {
  try {
    const deductFunction = firebase.functions().httpsCallable('deductUsage');
    const result = await deductFunction({
      userId: userId,
      serviceType: serviceType,
      amount: amount
    });

    return result.data;
  } catch (error) {
    console.error('Error deducting usage:', error);
    throw error;
  }
}

/**
 * Helper function to handle deduction results and display user feedback
 *
 * @param {Object} result - The deduction result from a Cloud Function
 * @param {string} serviceType - The type of service for user feedback
 */
function handleDeductionResult(result, serviceType) {
  if (result.success) {
    console.log(`Successfully deducted ${result.deducted} ${serviceType} usage`);
    console.log(`Current period usage: ${result.currentPeriodUsage}`);
    console.log(`Total usage: ${result.totalUsage}`);

    // You can add UI updates here, such as:
    // - Updating usage displays
    // - Showing success messages
    // - Refreshing user account information

    return true;
  } else {
    console.error(`Failed to deduct ${serviceType} usage:`, result.error);

    // Handle different error types
    switch (result.error.code) {
      case 'unauthenticated':
        alert('Please log in to continue.');
        break;
      case 'permission-denied':
        alert('You do not have permission to perform this action.');
        break;
      case 'internal-error':
        alert('An error occurred while processing your request. Please try again.');
        break;
      default:
        alert(`Error: ${result.error.message}`);
    }

    return false;
  }
}

/**
 * Example usage functions for common scenarios
 */

/**
 * Deduct usage after a successful transcription
 *
 * @param {string} userId - The user ID
 * @param {number} audioDurationMinutes - The duration of the transcribed audio
 */
async function handleTranscriptionComplete(userId, audioDurationMinutes) {
  try {
    const result = await deductTranscriptionUsage(userId, audioDurationMinutes);

    if (handleDeductionResult(result, 'transcription')) {
      // Update UI to reflect new usage
      updateUsageDisplay('transcription', result.currentPeriodUsage);
    }
  } catch (error) {
    console.error('Failed to deduct transcription usage:', error);
  }
}

/**
 * Deduct usage after a successful translation
 *
 * @param {string} userId - The user ID
 * @param {string} translatedText - The translated text to count words
 */
async function handleTranslationComplete(userId, translatedText) {
  try {
    // Count words in the translated text
    const wordCount = translatedText.trim().split(/\s+/).length;

    const result = await deductTranslationUsage(userId, wordCount);

    if (handleDeductionResult(result, 'translation')) {
      // Update UI to reflect new usage
      updateUsageDisplay('translation', result.currentPeriodUsage);
    }
  } catch (error) {
    console.error('Failed to deduct translation usage:', error);
  }
}

/**
 * Deduct usage after TTS generation
 *
 * @param {string} userId - The user ID
 * @param {number} audioLengthMinutes - The length of the generated audio
 */
async function handleTTSComplete(userId, audioLengthMinutes) {
  try {
    const result = await deductTTSUsage(userId, audioLengthMinutes);

    if (handleDeductionResult(result, 'TTS')) {
      // Update UI to reflect new usage
      updateUsageDisplay('tts', result.currentPeriodUsage);
    }
  } catch (error) {
    console.error('Failed to deduct TTS usage:', error);
  }
}

/**
 * Deduct AI credits after AI operation
 *
 * @param {string} userId - The user ID
 * @param {number} creditsUsed - The number of credits consumed
 */
async function handleAIOperationComplete(userId, creditsUsed) {
  try {
    const result = await deductAICredits(userId, creditsUsed);

    if (handleDeductionResult(result, 'AI credits')) {
      // Update UI to reflect new usage
      updateUsageDisplay('ai', result.currentPeriodUsage);
    }
  } catch (error) {
    console.error('Failed to deduct AI credits:', error);
  }
}

/**
 * Placeholder function for updating usage display in UI
 * You should implement this based on your UI structure
 *
 * @param {string} serviceType - The type of service
 * @param {number} currentUsage - The current usage amount
 */
function updateUsageDisplay(serviceType, currentUsage) {
  // Example implementation:
  const usageElement = document.getElementById(`${serviceType}-usage`);
  if (usageElement) {
    usageElement.textContent = currentUsage;
  }

  console.log(`Updated ${serviceType} usage display: ${currentUsage}`);
}

// Export functions for use in other modules
window.usageDeduction = {
  deductTranscriptionUsage,
  deductTranslationUsage,
  deductTTSUsage,
  deductAICredits,
  deductUsage,
  handleDeductionResult,
  handleTranscriptionComplete,
  handleTranslationComplete,
  handleTTSComplete,
  handleAIOperationComplete,
  updateUsageDisplay
};
