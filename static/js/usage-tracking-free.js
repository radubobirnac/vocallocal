/**
 * Usage Tracking for VocalLocal (Firebase Free Plan Compatible)
 *
 * This module provides client-side utilities for tracking usage
 * using direct Firebase Realtime Database operations without Cloud Functions.
 */

/**
 * Encode user ID to be Firebase path-safe
 * Firebase paths cannot contain: . $ # [ ] /
 */
function encodeUserId(userId) {
  if (!userId) return userId;

  let encoded = userId.replace(/\./g, ',');  // Replace dots with commas
  encoded = encoded.replace(/@/g, '_at_');  // Replace @ with _at_
  encoded = encoded.replace(/#/g, '_hash_');  // Replace # with _hash_
  encoded = encoded.replace(/\$/g, '_dollar_');  // Replace $ with _dollar_
  encoded = encoded.replace(/\[/g, '_lbracket_');  // Replace [ with _lbracket_
  encoded = encoded.replace(/\]/g, '_rbracket_');  // Replace ] with _rbracket_
  encoded = encoded.replace(/\//g, '_slash_');  // Replace / with _slash_

  return encoded;
}

/**
 * Decode Firebase path-safe user ID back to original format
 */
function decodeUserId(encodedUserId) {
  if (!encodedUserId) return encodedUserId;

  let decoded = encodedUserId.replace(/,/g, '.');  // Replace commas back to dots
  decoded = decoded.replace(/_at_/g, '@');  // Replace _at_ back to @
  decoded = decoded.replace(/_hash_/g, '#');  // Replace _hash_ back to #
  decoded = decoded.replace(/_dollar_/g, '$');  // Replace _dollar_ back to $
  decoded = decoded.replace(/_lbracket_/g, '[');  // Replace _lbracket_ back to [
  decoded = decoded.replace(/_rbracket_/g, ']');  // Replace _rbracket_ back to ]
  decoded = decoded.replace(/_slash_/g, '/');  // Replace _slash_ back to /

  return decoded;
}

/**
 * Deduct usage directly from Firebase Realtime Database using transactions
 *
 * @param {string} userId - The user ID to deduct usage from
 * @param {string} serviceType - The type of service (transcriptionMinutes, translationWords, etc.)
 * @param {number} amount - The amount to deduct
 * @param {string} serviceName - Human-readable service name
 * @returns {Promise<Object>} - Deduction result
 */
async function deductUsageDirectly(userId, serviceType, amount, serviceName) {
  try {
    console.log(`Deducting ${serviceName} usage for user ${userId}: ${amount}`);

    // Encode user ID for Firebase path safety
    const encodedUserId = encodeUserId(userId);
    console.log(`Encoded user ID: ${userId} -> ${encodedUserId}`);

    const userRef = firebase.database().ref(`users/${encodedUserId}`);

    return new Promise((resolve, reject) => {
      userRef.transaction((currentData) => {
        if (!currentData) {
          // Initialize user data if it doesn't exist
          currentData = {
            usage: {
              currentPeriod: {
                transcriptionMinutes: 0,
                translationWords: 0,
                ttsMinutes: 0,
                aiCredits: 0
              },
              totalUsage: {
                transcriptionMinutes: 0,
                translationWords: 0,
                ttsMinutes: 0,
                aiCredits: 0
              }
            },
            lastActivityAt: Date.now()
          };
        }

        // Ensure usage structure exists
        if (!currentData.usage) {
          currentData.usage = {
            currentPeriod: {
              transcriptionMinutes: 0,
              translationWords: 0,
              ttsMinutes: 0,
              aiCredits: 0
            },
            totalUsage: {
              transcriptionMinutes: 0,
              translationWords: 0,
              ttsMinutes: 0,
              aiCredits: 0
            }
          };
        }

        if (!currentData.usage.currentPeriod) {
          currentData.usage.currentPeriod = {
            transcriptionMinutes: 0,
            translationWords: 0,
            ttsMinutes: 0,
            aiCredits: 0
          };
        }

        if (!currentData.usage.totalUsage) {
          currentData.usage.totalUsage = {
            transcriptionMinutes: 0,
            translationWords: 0,
            ttsMinutes: 0,
            aiCredits: 0
          };
        }

        // Get current values
        const currentPeriodUsage = currentData.usage.currentPeriod[serviceType] || 0;
        const totalUsage = currentData.usage.totalUsage[serviceType] || 0;

        // Update usage counters
        currentData.usage.currentPeriod[serviceType] = currentPeriodUsage + amount;
        currentData.usage.totalUsage[serviceType] = totalUsage + amount;

        // Update last activity timestamp
        currentData.lastActivityAt = Date.now();

        return currentData;
      }, (error, committed, snapshot) => {
        if (error) {
          console.error(`Error deducting ${serviceName} usage:`, error);
          reject({
            success: false,
            error: {
              code: 'transaction-error',
              message: `Failed to deduct ${serviceName} usage`,
              details: error.message
            }
          });
        } else if (committed) {
          const newData = snapshot.val();
          const newCurrentUsage = newData.usage.currentPeriod[serviceType];
          const newTotalUsage = newData.usage.totalUsage[serviceType];

          console.log(`${serviceName} usage deducted for user ${userId}: ${amount}, new current: ${newCurrentUsage}, new total: ${newTotalUsage}`);

          resolve({
            success: true,
            deducted: amount,
            currentPeriodUsage: newCurrentUsage,
            totalUsage: newTotalUsage,
            serviceType: serviceName.toLowerCase().replace(' ', '_')
          });
        } else {
          reject({
            success: false,
            error: {
              code: 'transaction-aborted',
              message: 'Transaction was aborted',
              details: 'The transaction was aborted, possibly due to a conflict'
            }
          });
        }
      });
    });

  } catch (error) {
    console.error(`Error in deductUsageDirectly for ${serviceName}:`, error);
    throw {
      success: false,
      error: {
        code: 'internal-error',
        message: `An error occurred while deducting ${serviceName} usage`,
        details: error.message
      }
    };
  }
}

/**
 * Deduct transcription usage from a user's account
 *
 * @param {string} userId - The user ID to deduct usage from
 * @param {number} minutesUsed - The number of minutes to deduct
 * @returns {Promise<Object>} - Deduction result
 */
async function deductTranscriptionUsage(userId, minutesUsed) {
  return await deductUsageDirectly(userId, 'transcriptionMinutes', minutesUsed, 'transcription');
}

/**
 * Deduct translation usage from a user's account
 *
 * @param {string} userId - The user ID to deduct usage from
 * @param {number} wordsUsed - The number of words to deduct
 * @returns {Promise<Object>} - Deduction result
 */
async function deductTranslationUsage(userId, wordsUsed) {
  return await deductUsageDirectly(userId, 'translationWords', wordsUsed, 'translation');
}

/**
 * Deduct TTS usage from a user's account
 *
 * @param {string} userId - The user ID to deduct usage from
 * @param {number} minutesUsed - The number of minutes to deduct
 * @returns {Promise<Object>} - Deduction result
 */
async function deductTTSUsage(userId, minutesUsed) {
  return await deductUsageDirectly(userId, 'ttsMinutes', minutesUsed, 'TTS');
}

/**
 * Deduct AI credits from a user's account
 *
 * @param {string} userId - The user ID to deduct usage from
 * @param {number} creditsUsed - The number of credits to deduct
 * @returns {Promise<Object>} - Deduction result
 */
async function deductAICredits(userId, creditsUsed) {
  return await deductUsageDirectly(userId, 'aiCredits', creditsUsed, 'AI credits');
}

/**
 * Get current usage data for a user
 *
 * @param {string} userId - The user ID
 * @returns {Promise<Object>} - User usage data
 */
async function getUserUsage(userId) {
  try {
    // Encode user ID for Firebase path safety
    const encodedUserId = encodeUserId(userId);
    console.log(`Getting usage for encoded user ID: ${userId} -> ${encodedUserId}`);

    const snapshot = await firebase.database().ref(`users/${encodedUserId}/usage`).once('value');
    const usage = snapshot.val();

    if (!usage) {
      return {
        currentPeriod: {
          transcriptionMinutes: 0,
          translationWords: 0,
          ttsMinutes: 0,
          aiCredits: 0
        },
        totalUsage: {
          transcriptionMinutes: 0,
          translationWords: 0,
          ttsMinutes: 0,
          aiCredits: 0
        }
      };
    }

    return usage;
  } catch (error) {
    console.error('Error getting user usage:', error);
    throw error;
  }
}

/**
 * Helper function to handle deduction results and display user feedback
 *
 * @param {Object} result - The deduction result
 * @param {string} serviceType - The type of service for user feedback
 */
function handleDeductionResult(result, serviceType) {
  if (result.success) {
    console.log(`Successfully deducted ${result.deducted} ${serviceType} usage`);
    console.log(`Current period usage: ${result.currentPeriodUsage}`);
    console.log(`Total usage: ${result.totalUsage}`);

    // Update UI if elements exist
    updateUsageDisplay(serviceType, result.currentPeriodUsage);

    return true;
  } else {
    console.error(`Failed to deduct ${serviceType} usage:`, result.error);

    // Handle different error types
    switch (result.error.code) {
      case 'transaction-error':
        alert('An error occurred while updating your usage. Please try again.');
        break;
      case 'transaction-aborted':
        alert('Usage update was interrupted. Please try again.');
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
 * Update usage display in UI
 *
 * @param {string} serviceType - The type of service
 * @param {number} currentUsage - The current usage amount
 */
function updateUsageDisplay(serviceType, currentUsage) {
  const usageElement = document.getElementById(`${serviceType}-usage`);
  if (usageElement) {
    usageElement.textContent = currentUsage;
  }

  console.log(`Updated ${serviceType} usage display: ${currentUsage}`);
}

/**
 * Example usage functions for common scenarios
 */

/**
 * Handle transcription completion
 *
 * @param {string} userId - The user ID
 * @param {number} audioDurationMinutes - The duration of the transcribed audio
 */
async function handleTranscriptionComplete(userId, audioDurationMinutes) {
  try {
    const result = await deductTranscriptionUsage(userId, audioDurationMinutes);
    handleDeductionResult(result, 'transcription');
  } catch (error) {
    console.error('Failed to deduct transcription usage:', error);
  }
}

/**
 * Handle translation completion
 *
 * @param {string} userId - The user ID
 * @param {string} translatedText - The translated text to count words
 */
async function handleTranslationComplete(userId, translatedText) {
  try {
    const wordCount = translatedText.trim().split(/\s+/).length;
    const result = await deductTranslationUsage(userId, wordCount);
    handleDeductionResult(result, 'translation');
  } catch (error) {
    console.error('Failed to deduct translation usage:', error);
  }
}

// Export functions for use in other modules
window.usageTrackingFree = {
  deductTranscriptionUsage,
  deductTranslationUsage,
  deductTTSUsage,
  deductAICredits,
  getUserUsage,
  handleDeductionResult,
  handleTranscriptionComplete,
  handleTranslationComplete,
  updateUsageDisplay,
  encodeUserId,
  decodeUserId
};
