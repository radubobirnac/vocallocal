/**
 * Example usage of the usage validation functions
 *
 * This file demonstrates how to use the client-side usage validation
 * functions to check if a user has sufficient resources before
 * performing operations.
 */

// Example: Check if user has enough transcription minutes
async function checkTranscriptionAvailability(minutes) {
  try {
    // Get the current user ID
    const userId = getCurrentUserId();
    if (!userId) {
      console.error('User not logged in');
      return false;
    }

    // Validate transcription usage
    const result = await window.usageValidation.validateTranscriptionUsage(userId, minutes);

    if (result.allowed) {
      console.log(`You have ${result.remaining} minutes remaining.`);
      return true;
    } else {
      console.log(`Not enough minutes available. You need to upgrade your plan.`);

      // Show upgrade message if needed (but not for admin/super users)
      if (result.upgradeRequired && result.role !== 'admin' && result.role !== 'super_user') {
        showUpgradeMessage(result.planType, 'transcription');
      }

      return false;
    }
  } catch (error) {
    console.error('Error validating transcription usage:', error);
    return false;
  }
}

// Example: Check if user has enough translation words
async function checkTranslationAvailability(words) {
  try {
    // Get the current user ID
    const userId = getCurrentUserId();
    if (!userId) {
      console.error('User not logged in');
      return false;
    }

    // Validate translation usage
    const result = await window.usageValidation.validateTranslationUsage(userId, words);

    if (result.allowed) {
      console.log(`You have ${result.remaining} words remaining.`);
      return true;
    } else {
      console.log(`Not enough words available. You need to upgrade your plan.`);

      // Show upgrade message if needed (but not for admin/super users)
      if (result.upgradeRequired && result.role !== 'admin' && result.role !== 'super_user') {
        showUpgradeMessage(result.planType, 'translation');
      }

      return false;
    }
  } catch (error) {
    console.error('Error validating translation usage:', error);
    return false;
  }
}

// Example: Track usage after successful operation
async function recordTranscriptionUsage(minutes) {
  try {
    // Get the current user ID
    const userId = getCurrentUserId();
    if (!userId) {
      console.error('User not logged in');
      return;
    }

    // Track usage
    const result = await window.usageValidation.trackUsage(userId, 'transcription', minutes);

    if (result.success) {
      console.log(`Recorded ${minutes} minutes of transcription usage.`);
      console.log(`Current period usage: ${result.currentPeriodUsage} minutes`);
      console.log(`Total usage: ${result.totalUsage} minutes`);
    } else {
      console.error('Error tracking usage:', result.error);
    }
  } catch (error) {
    console.error('Error tracking usage:', error);
  }
}

// Helper function to get the current user ID
function getCurrentUserId() {
  // Check if Firebase Auth is available
  if (typeof firebase !== 'undefined' && firebase.auth && firebase.auth().currentUser) {
    return firebase.auth().currentUser.uid;
  }

  // Fallback: Try to get user ID from the page
  // This assumes there's a hidden input with the user ID
  const userIdElement = document.getElementById('current-user-id');
  if (userIdElement) {
    return userIdElement.value;
  }

  return null;
}

// Helper function to show upgrade message
function showUpgradeMessage(currentPlan, resourceType) {
  // Create or get upgrade message container
  let messageContainer = document.getElementById('upgrade-message');
  if (!messageContainer) {
    messageContainer = document.createElement('div');
    messageContainer.id = 'upgrade-message';
    messageContainer.className = 'upgrade-message';
    document.body.appendChild(messageContainer);
  }

  // Set message content
  let resourceName = '';
  let upgradeLink = '';

  switch (resourceType) {
    case 'transcription':
      resourceName = 'transcription minutes';
      break;
    case 'translation':
      resourceName = 'translation words';
      break;
    case 'tts':
      resourceName = 'text-to-speech minutes';
      break;
    case 'ai':
      resourceName = 'AI credits';
      break;
    default:
      resourceName = 'resources';
  }

  // Create upgrade link based on current plan
  switch (currentPlan) {
    case 'free':
      upgradeLink = '/subscription/basic';
      break;
    case 'basic':
      upgradeLink = '/subscription/professional';
      break;
    default:
      upgradeLink = '/subscription/plans';
  }

  // Set message HTML
  messageContainer.innerHTML = `
    <div class="upgrade-message-content">
      <h3>Upgrade Your Plan</h3>
      <p>You've reached your ${resourceName} limit on the ${currentPlan} plan.</p>
      <p>Upgrade to get more ${resourceName} and additional features.</p>
      <div class="upgrade-actions">
        <a href="${upgradeLink}" class="button button-primary">Upgrade Now</a>
        <button class="button button-outline close-upgrade-message">Dismiss</button>
      </div>
    </div>
  `;

  // Show the message
  messageContainer.style.display = 'flex';

  // Add event listener to close button
  const closeButton = messageContainer.querySelector('.close-upgrade-message');
  if (closeButton) {
    closeButton.addEventListener('click', function() {
      messageContainer.style.display = 'none';
    });
  }
}

// Example usage in a transcription function
async function transcribeAudio(audioBlob, durationMinutes) {
  // First check if user has enough minutes
  const hasEnoughMinutes = await checkTranscriptionAvailability(durationMinutes);

  if (!hasEnoughMinutes) {
    // Show error message or upgrade prompt
    console.log('Not enough transcription minutes available');
    return;
  }

  // Proceed with transcription
  console.log('Transcribing audio...');

  // After successful transcription, record the usage
  await recordTranscriptionUsage(durationMinutes);
}

// Export functions for use in other modules
window.usageExample = {
  checkTranscriptionAvailability,
  checkTranslationAvailability,
  recordTranscriptionUsage,
  transcribeAudio
};
