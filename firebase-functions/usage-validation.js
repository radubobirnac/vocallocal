/**
 * Firebase Cloud Functions for VocalLocal Usage Validation
 * 
 * These functions validate user requests against their available usage limits
 * and subscription plans.
 */

const functions = require('firebase-functions');
const admin = require('firebase-admin');
admin.initializeApp();

/**
 * Validate transcription minutes
 * 
 * Checks if a user has enough transcription minutes available
 * based on their subscription plan and pay-as-you-go balance.
 */
exports.validateTranscriptionMinutes = functions.https.onCall(async (data, context) => {
  // Ensure user is authenticated
  if (!context.auth) {
    return {
      success: false,
      error: 'Unauthorized',
      message: 'You must be logged in to use this feature.'
    };
  }

  const userId = context.auth.uid;
  const requestedMinutes = data.minutes || 0;

  try {
    // Get user account data
    const userSnapshot = await admin.database().ref(`users/${userId}`).once('value');
    const userData = userSnapshot.val();

    if (!userData) {
      return {
        success: false,
        error: 'UserNotFound',
        message: 'User account not found.'
      };
    }

    // Get subscription plan
    const subscription = userData.subscription || {};
    const planType = subscription.planType || 'free';
    const subscriptionStatus = subscription.status || 'inactive';

    // Get current usage
    const currentUsage = userData.usage?.currentPeriod?.transcriptionMinutes || 0;

    // Get available pay-as-you-go minutes
    const payAsYouGoMinutes = userData.billing?.payAsYouGo?.unitsRemaining?.transcriptionMinutes || 0;

    // Define plan limits
    const planLimits = {
      free: 10,
      basic: 280,
      premium: 800,
      enterprise: 2000
    };

    // Check if subscription is active
    const isSubscriptionActive = subscriptionStatus === 'active' || subscriptionStatus === 'trial';
    
    // Calculate available minutes from subscription
    const planLimit = isSubscriptionActive ? (planLimits[planType] || 0) : 0;
    const remainingPlanMinutes = Math.max(0, planLimit - currentUsage);

    // Total available minutes (subscription + pay-as-you-go)
    const totalAvailableMinutes = remainingPlanMinutes + payAsYouGoMinutes;

    // Check if user has enough minutes
    if (totalAvailableMinutes >= requestedMinutes) {
      return {
        success: true,
        availableMinutes: totalAvailableMinutes,
        planMinutes: remainingPlanMinutes,
        payAsYouGoMinutes: payAsYouGoMinutes
      };
    } else {
      return {
        success: false,
        error: 'InsufficientMinutes',
        message: `You don't have enough transcription minutes. Available: ${totalAvailableMinutes}, Requested: ${requestedMinutes}`,
        availableMinutes: totalAvailableMinutes,
        planMinutes: remainingPlanMinutes,
        payAsYouGoMinutes: payAsYouGoMinutes
      };
    }
  } catch (error) {
    console.error('Error validating transcription minutes:', error);
    return {
      success: false,
      error: 'ServerError',
      message: 'An error occurred while validating your transcription minutes.'
    };
  }
});

/**
 * Validate translation words
 * 
 * Checks if a user has enough translation words available
 * based on their subscription plan and pay-as-you-go balance.
 */
exports.validateTranslationWords = functions.https.onCall(async (data, context) => {
  // Ensure user is authenticated
  if (!context.auth) {
    return {
      success: false,
      error: 'Unauthorized',
      message: 'You must be logged in to use this feature.'
    };
  }

  const userId = context.auth.uid;
  const requestedWords = data.words || 0;

  try {
    // Get user account data
    const userSnapshot = await admin.database().ref(`users/${userId}`).once('value');
    const userData = userSnapshot.val();

    if (!userData) {
      return {
        success: false,
        error: 'UserNotFound',
        message: 'User account not found.'
      };
    }

    // Get subscription plan
    const subscription = userData.subscription || {};
    const planType = subscription.planType || 'free';
    const subscriptionStatus = subscription.status || 'inactive';

    // Get current usage
    const currentUsage = userData.usage?.currentPeriod?.translationWords || 0;

    // Get available pay-as-you-go words
    const payAsYouGoWords = userData.billing?.payAsYouGo?.unitsRemaining?.translationWords || 0;

    // Define plan limits
    const planLimits = {
      free: 1000,
      basic: 50000,
      premium: 200000,
      enterprise: 500000
    };

    // Check if subscription is active
    const isSubscriptionActive = subscriptionStatus === 'active' || subscriptionStatus === 'trial';
    
    // Calculate available words from subscription
    const planLimit = isSubscriptionActive ? (planLimits[planType] || 0) : 0;
    const remainingPlanWords = Math.max(0, planLimit - currentUsage);

    // Total available words (subscription + pay-as-you-go)
    const totalAvailableWords = remainingPlanWords + payAsYouGoWords;

    // Check if user has enough words
    if (totalAvailableWords >= requestedWords) {
      return {
        success: true,
        availableWords: totalAvailableWords,
        planWords: remainingPlanWords,
        payAsYouGoWords: payAsYouGoWords
      };
    } else {
      return {
        success: false,
        error: 'InsufficientWords',
        message: `You don't have enough translation words. Available: ${totalAvailableWords}, Requested: ${requestedWords}`,
        availableWords: totalAvailableWords,
        planWords: remainingPlanWords,
        payAsYouGoWords: payAsYouGoWords
      };
    }
  } catch (error) {
    console.error('Error validating translation words:', error);
    return {
      success: false,
      error: 'ServerError',
      message: 'An error occurred while validating your translation words.'
    };
  }
});
