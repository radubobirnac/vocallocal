/**
 * Client-side usage validation for VocalLocal
 *
 * This module provides functions to validate and track usage without Cloud Functions.
 */

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDQpgqsQIYXvZUPCIWpIFG-wHGAZ1_7MKs",
  authDomain: "vocal-local-e1e70.firebaseapp.com",
  databaseURL: "https://vocal-local-e1e70-default-rtdb.firebaseio.com",
  projectId: "vocal-local-e1e70",
  storageBucket: "vocal-local-e1e70.appspot.com",
  messagingSenderId: "1082430804880",
  appId: "1:1082430804880:web:9a3e6a3b6fd3e3a6a6a6a6"
};

// Initialize Firebase if not already initialized
if (typeof firebase !== 'undefined' && !firebase.apps.length) {
  firebase.initializeApp(firebaseConfig);
}

/**
 * Validate if a user has sufficient transcription minutes available
 *
 * @param {string} userId - The user ID to validate
 * @param {number} minutesRequested - The number of minutes requested
 * @returns {Promise<Object>} - Validation response
 */
async function validateTranscriptionUsage(userId, minutesRequested) {
  try {
    console.log(`Validating transcription usage for user ${userId}: ${minutesRequested} minutes requested`);

    // Get user data
    const userRef = firebase.database().ref(`users/${userId}`);
    const userSnapshot = await userRef.once('value');
    const userData = userSnapshot.val();

    if (!userData) {
      console.error(`User data not found for user ${userId}`);
      return {
        allowed: false,
        remaining: 0,
        planType: 'none',
        upgradeRequired: true,
        error: {
          code: 'not-found',
          message: 'User data not found'
        }
      };
    }

    // Check user role first - admins and super users have unlimited access
    const userRole = userData.role || 'normal_user';
    if (userRole === 'admin' || userRole === 'super_user') {
      console.log(`Unlimited transcription access for ${userRole} role`);
      return {
        allowed: true,
        remaining: 999999, // Unlimited
        planType: 'unlimited',
        upgradeRequired: false,
        role: userRole
      };
    }

    // Get subscription plan
    const subscription = userData.subscription || {};
    const planType = subscription.status === 'active' ? subscription.planType : 'free';

    // Get plan details
    const planRef = firebase.database().ref(`subscriptionPlans/${planType}`);
    const planSnapshot = await planRef.once('value');
    const planData = planSnapshot.val();

    if (!planData) {
      console.error(`Subscription plan '${planType}' not found`);
      return {
        allowed: false,
        remaining: 0,
        planType: planType,
        upgradeRequired: true,
        error: {
          code: 'plan-not-found',
          message: 'Subscription plan not found'
        }
      };
    }

    // Get current usage
    const currentUsage = userData.usage?.currentPeriod?.transcriptionMinutes || 0;

    // Get pay-as-you-go balance
    const paygBalance = userData.billing?.payAsYouGo?.unitsRemaining?.transcriptionMinutes || 0;

    // Calculate available minutes from subscription plan
    const planLimit = planData.transcriptionMinutes || 0;
    const remainingPlanMinutes = Math.max(0, planLimit - currentUsage);

    // Total available minutes (subscription + pay-as-you-go)
    const totalAvailableMinutes = remainingPlanMinutes + paygBalance;

    // Check if user has enough minutes
    const allowed = totalAvailableMinutes >= minutesRequested;
    const remaining = Math.max(0, totalAvailableMinutes - minutesRequested);
    const upgradeRequired = !allowed && remainingPlanMinutes < minutesRequested;

    console.log(`Transcription validation result for user ${userId}: allowed=${allowed}, remaining=${remaining}, planType=${planType}, upgradeRequired=${upgradeRequired}`);

    return {
      allowed,
      remaining,
      planType,
      upgradeRequired
    };
  } catch (error) {
    console.error(`Error validating transcription usage for user ${userId}:`, error);

    return {
      allowed: false,
      remaining: 0,
      planType: 'unknown',
      upgradeRequired: false,
      error: {
        code: 'internal-error',
        message: 'An error occurred while validating usage',
        details: error.message
      }
    };
  }
}

/**
 * Validate if a user has sufficient translation words available
 *
 * @param {string} userId - The user ID to validate
 * @param {number} wordsRequested - The number of words requested
 * @returns {Promise<Object>} - Validation response
 */
async function validateTranslationUsage(userId, wordsRequested) {
  try {
    console.log(`Validating translation usage for user ${userId}: ${wordsRequested} words requested`);

    // Get user data
    const userRef = firebase.database().ref(`users/${userId}`);
    const userSnapshot = await userRef.once('value');
    const userData = userSnapshot.val();

    if (!userData) {
      console.error(`User data not found for user ${userId}`);
      return {
        allowed: false,
        remaining: 0,
        planType: 'none',
        upgradeRequired: true,
        error: {
          code: 'not-found',
          message: 'User data not found'
        }
      };
    }

    // Check user role first - admins and super users have unlimited access
    const userRole = userData.role || 'normal_user';
    if (userRole === 'admin' || userRole === 'super_user') {
      console.log(`Unlimited translation access for ${userRole} role`);
      return {
        allowed: true,
        remaining: 999999, // Unlimited
        planType: 'unlimited',
        upgradeRequired: false,
        role: userRole
      };
    }

    // Get subscription plan
    const subscription = userData.subscription || {};
    const planType = subscription.status === 'active' ? subscription.planType : 'free';

    // Get plan details
    const planRef = firebase.database().ref(`subscriptionPlans/${planType}`);
    const planSnapshot = await planRef.once('value');
    const planData = planSnapshot.val();

    if (!planData) {
      console.error(`Subscription plan '${planType}' not found`);
      return {
        allowed: false,
        remaining: 0,
        planType: planType,
        upgradeRequired: true,
        error: {
          code: 'plan-not-found',
          message: 'Subscription plan not found'
        }
      };
    }

    // Get current usage
    const currentUsage = userData.usage?.currentPeriod?.translationWords || 0;

    // Get pay-as-you-go balance
    const paygBalance = userData.billing?.payAsYouGo?.unitsRemaining?.translationWords || 0;

    // Calculate available words from subscription plan
    const planLimit = planData.translationWords || 0;
    const remainingPlanWords = Math.max(0, planLimit - currentUsage);

    // Total available words (subscription + pay-as-you-go)
    const totalAvailableWords = remainingPlanWords + paygBalance;

    // Check if user has enough words
    const allowed = totalAvailableWords >= wordsRequested;
    const remaining = Math.max(0, totalAvailableWords - wordsRequested);
    const upgradeRequired = !allowed && remainingPlanWords < wordsRequested;

    console.log(`Translation validation result for user ${userId}: allowed=${allowed}, remaining=${remaining}, planType=${planType}, upgradeRequired=${upgradeRequired}`);

    return {
      allowed,
      remaining,
      planType,
      upgradeRequired
    };
  } catch (error) {
    console.error(`Error validating translation usage for user ${userId}:`, error);

    return {
      allowed: false,
      remaining: 0,
      planType: 'unknown',
      upgradeRequired: false,
      error: {
        code: 'internal-error',
        message: 'An error occurred while validating usage',
        details: error.message
      }
    };
  }
}

/**
 * Track usage for a specific service
 *
 * @param {string} userId - The user ID to track usage for
 * @param {string} serviceType - The type of service (transcription, translation, tts, ai)
 * @param {number} amount - The amount to track
 * @returns {Promise<Object>} - Updated usage data
 */
async function trackUsage(userId, serviceType, amount) {
  try {
    console.log(`Tracking usage for user ${userId}: ${amount} ${serviceType}`);

    // Map service type to database field
    const serviceTypeMap = {
      'transcription': 'transcriptionMinutes',
      'translation': 'translationWords',
      'tts': 'ttsMinutes',
      'ai': 'aiCredits'
    };

    const dbField = serviceTypeMap[serviceType];
    if (!dbField) {
      console.error(`Invalid service type: ${serviceType}`);
      return {
        success: false,
        error: {
          code: 'invalid-argument',
          message: `Invalid service type: ${serviceType}`
        }
      };
    }

    // Get current usage
    const userRef = firebase.database().ref(`users/${userId}`);
    const snapshot = await userRef.once('value');
    const userData = snapshot.val();

    if (!userData) {
      console.error(`User data not found for user ${userId}`);
      return {
        success: false,
        error: {
          code: 'not-found',
          message: 'User data not found'
        }
      };
    }

    // Get current usage values
    const currentPeriodUsage = userData.usage?.currentPeriod?.[dbField] || 0;
    const totalUsage = userData.usage?.totalUsage?.[dbField] || 0;

    // Calculate new usage values
    const newCurrentPeriodUsage = currentPeriodUsage + amount;
    const newTotalUsage = totalUsage + amount;

    // Update usage in database
    const updates = {};
    updates[`users/${userId}/usage/currentPeriod/${dbField}`] = newCurrentPeriodUsage;
    updates[`users/${userId}/usage/totalUsage/${dbField}`] = newTotalUsage;

    await firebase.database().ref().update(updates);

    console.log(`Usage tracked for user ${userId}: ${amount} ${serviceType}, new total: ${newCurrentPeriodUsage}`);

    return {
      success: true,
      currentPeriodUsage: newCurrentPeriodUsage,
      totalUsage: newTotalUsage
    };
  } catch (error) {
    console.error(`Error tracking usage for user ${userId}:`, error);

    return {
      success: false,
      error: {
        code: 'internal-error',
        message: 'An error occurred while tracking usage',
        details: error.message
      }
    };
  }
}

// Export functions for use in other modules
window.usageValidation = {
  validateTranscriptionUsage,
  validateTranslationUsage,
  trackUsage
};
