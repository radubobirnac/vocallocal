/**
 * User Account Management Utilities for VocalLocal
 * 
 * This module provides client-side utilities for working with user account data
 * in the Firebase Realtime Database.
 */

/**
 * Initialize a new user account with default values
 * 
 * @param {string} userId - Firebase user ID
 * @param {string} email - User's email address
 * @param {string} displayName - User's display name
 * @returns {Promise<Object>} - The created user account data
 */
async function initializeUserAccount(userId, email, displayName) {
  const currentTime = Date.now(); // Current time in milliseconds
  
  // Calculate reset date (first day of next month)
  const today = new Date();
  const firstOfNextMonth = new Date(today.getFullYear(), today.getMonth() + 1, 1);
  const resetTimestamp = firstOfNextMonth.getTime();
  
  // Calculate subscription end date (30 days from now for free trial)
  const endDate = new Date();
  endDate.setDate(endDate.getDate() + 30);
  const endTimestamp = endDate.getTime();
  
  // Create user account structure
  const userAccount = {
    profile: {
      email: email,
      displayName: displayName,
      createdAt: currentTime,
      lastLoginAt: currentTime,
      status: "active"
    },
    subscription: {
      planType: "free",
      status: "trial",
      startDate: currentTime,
      endDate: endTimestamp,
      renewalDate: endTimestamp,
      paymentMethod: "none",
      billingCycle: "monthly"
    },
    usage: {
      currentPeriod: {
        transcriptionMinutes: 0,
        translationWords: 0,
        ttsMinutes: 0,
        aiCredits: 0,
        resetDate: resetTimestamp
      },
      totalUsage: {
        transcriptionMinutes: 0,
        translationWords: 0,
        ttsMinutes: 0,
        aiCredits: 0
      }
    },
    billing: {
      payAsYouGo: {
        unitsRemaining: {
          transcriptionMinutes: 10,  // Free trial minutes
          translationWords: 1000,    // Free trial words
          ttsMinutes: 5,            // Free trial TTS minutes
          aiCredits: 5              // Free trial AI credits
        },
        purchaseHistory: []
      }
    }
  };
  
  // Save to Firebase
  await firebase.database().ref(`users/${userId}`).set(userAccount);
  
  return userAccount;
}

/**
 * Get a user's account data
 * 
 * @param {string} userId - Firebase user ID
 * @returns {Promise<Object>} - User account data
 */
async function getUserAccount(userId) {
  const snapshot = await firebase.database().ref(`users/${userId}`).once('value');
  return snapshot.val();
}

/**
 * Update user's last login timestamp
 * 
 * @param {string} userId - Firebase user ID
 * @returns {Promise<void>}
 */
async function updateLastLogin(userId) {
  const currentTime = Date.now();
  await firebase.database().ref(`users/${userId}/profile/lastLoginAt`).set(currentTime);
}

/**
 * Update user's subscription information
 * 
 * @param {string} userId - Firebase user ID
 * @param {string} planType - Subscription plan type ('free', 'basic', 'premium', 'enterprise')
 * @param {string} status - Subscription status ('active', 'canceled', 'expired', 'trial')
 * @param {string} billingCycle - Billing frequency ('monthly', 'annual', 'quarterly')
 * @param {string} [paymentMethod] - Payment method used
 * @returns {Promise<Object>} - Updated subscription data
 */
async function updateSubscription(userId, planType, status, billingCycle, paymentMethod) {
  const currentTime = Date.now();
  
  // Calculate end date based on billing cycle
  let days = 30;
  if (billingCycle === "quarterly") {
    days = 90;
  } else if (billingCycle === "annual") {
    days = 365;
  }
  
  const endDate = new Date();
  endDate.setDate(endDate.getDate() + days);
  const endTimestamp = endDate.getTime();
  
  const subscriptionData = {
    planType: planType,
    status: status,
    startDate: currentTime,
    endDate: endTimestamp,
    renewalDate: endTimestamp,
    billingCycle: billingCycle
  };
  
  if (paymentMethod) {
    subscriptionData.paymentMethod = paymentMethod;
  }
  
  // Update in Firebase
  await firebase.database().ref(`users/${userId}/subscription`).update(subscriptionData);
  
  return subscriptionData;
}

/**
 * Track usage of a service and update both current period and total usage
 * 
 * @param {string} userId - Firebase user ID
 * @param {string} serviceType - Type of service ('transcriptionMinutes', 'translationWords', 'ttsMinutes', 'aiCredits')
 * @param {number} amount - Amount to add to usage
 * @returns {Promise<Object>} - Updated usage data
 */
async function trackUsage(userId, serviceType, amount) {
  // Get current usage
  const currentUsageSnapshot = await firebase.database().ref(`users/${userId}/usage/currentPeriod/${serviceType}`).once('value');
  const totalUsageSnapshot = await firebase.database().ref(`users/${userId}/usage/totalUsage/${serviceType}`).once('value');
  
  const currentUsage = currentUsageSnapshot.val() || 0;
  const totalUsage = totalUsageSnapshot.val() || 0;
  
  // Update usage
  const newCurrentUsage = currentUsage + amount;
  const newTotalUsage = totalUsage + amount;
  
  // Save to Firebase
  await firebase.database().ref(`users/${userId}/usage/currentPeriod/${serviceType}`).set(newCurrentUsage);
  await firebase.database().ref(`users/${userId}/usage/totalUsage/${serviceType}`).set(newTotalUsage);
  
  // Check if we need to reset current period usage
  const resetDateSnapshot = await firebase.database().ref(`users/${userId}/usage/currentPeriod/resetDate`).once('value');
  const resetDate = resetDateSnapshot.val();
  const currentTime = Date.now();
  
  if (resetDate && currentTime > resetDate) {
    // Calculate new reset date (first day of next month)
    const today = new Date();
    const firstOfNextMonth = new Date(today.getFullYear(), today.getMonth() + 1, 1);
    const newResetTimestamp = firstOfNextMonth.getTime();
    
    // Reset all current period usage
    await firebase.database().ref(`users/${userId}/usage/currentPeriod`).update({
      transcriptionMinutes: 0,
      translationWords: 0,
      ttsMinutes: 0,
      aiCredits: 0,
      resetDate: newResetTimestamp
    });
  }
  
  return {
    currentUsage: newCurrentUsage,
    totalUsage: newTotalUsage
  };
}

/**
 * Check if user has sufficient units for a service
 * 
 * @param {string} userId - Firebase user ID
 * @param {string} serviceType - Type of service ('transcriptionMinutes', 'translationWords', 'ttsMinutes', 'aiCredits')
 * @param {number} requiredAmount - Amount required for the operation
 * @returns {Promise<boolean>} - True if user has sufficient units
 */
async function checkSufficientUnits(userId, serviceType, requiredAmount) {
  const unitsSnapshot = await firebase.database().ref(`users/${userId}/billing/payAsYouGo/unitsRemaining/${serviceType}`).once('value');
  const availableUnits = unitsSnapshot.val() || 0;
  
  return availableUnits >= requiredAmount;
}

// Export functions for use in other modules
window.userAccountService = {
  initializeUserAccount,
  getUserAccount,
  updateLastLogin,
  updateSubscription,
  trackUsage,
  checkSufficientUnits
};
