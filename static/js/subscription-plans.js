/**
 * Subscription Plans Utilities for VocalLocal
 *
 * This module provides client-side utilities for working with subscription plans
 * in the Firebase Realtime Database.
 */

/**
 * Get all subscription plans
 *
 * @param {boolean} includeInactive - Whether to include inactive plans
 * @returns {Promise<Object>} - Dictionary of subscription plans
 */
async function getAllSubscriptionPlans(includeInactive = false) {
  const snapshot = await firebase.database().ref('subscriptionPlans').once('value');
  const plans = snapshot.val() || {};

  if (!includeInactive) {
    // Filter out inactive plans
    const activePlans = {};
    Object.keys(plans).forEach(planId => {
      if (plans[planId].isActive) {
        activePlans[planId] = plans[planId];
      }
    });
    return activePlans;
  }

  return plans;
}

/**
 * Get a specific subscription plan
 *
 * @param {string} planId - The ID of the plan to get
 * @returns {Promise<Object>} - The subscription plan data or null if not found
 */
async function getSubscriptionPlan(planId) {
  const snapshot = await firebase.database().ref(`subscriptionPlans/${planId}`).once('value');
  return snapshot.val();
}

/**
 * Get all service plans (excluding pay-as-you-go add-ons)
 *
 * @returns {Promise<Object>} - Dictionary of service plans
 */
async function getServicePlans() {
  const allPlans = await getAllSubscriptionPlans();
  const servicePlans = {};

  Object.keys(allPlans).forEach(planId => {
    const plan = allPlans[planId];
    // Check if it's a service plan (has transcriptionMinutes)
    if ('transcriptionMinutes' in plan && !('credits' in plan)) {
      servicePlans[planId] = plan;
    }
  });

  return servicePlans;
}

/**
 * Get all pay-as-you-go add-on plans
 *
 * @param {string} compatibleWithPlan - Filter add-ons compatible with this plan ID
 * @returns {Promise<Object>} - Dictionary of pay-as-you-go plans
 */
async function getPayAsYouGoPlans(compatibleWithPlan = null) {
  const allPlans = await getAllSubscriptionPlans();
  const paygPlans = {};

  Object.keys(allPlans).forEach(planId => {
    const plan = allPlans[planId];
    // Check if it's a pay-as-you-go plan (has credits)
    if ('credits' in plan) {
      // If filtering by compatibility, check if this plan is compatible
      if (compatibleWithPlan) {
        if (plan.compatiblePlans && plan.compatiblePlans[compatibleWithPlan] === true) {
          paygPlans[planId] = plan;
        }
      } else {
        paygPlans[planId] = plan;
      }
    }
  });

  return paygPlans;
}

/**
 * Calculate the total price of a subscription
 *
 * @param {string} planId - The ID of the base plan
 * @param {Array<string>} addOnIds - Array of add-on plan IDs
 * @returns {Promise<number>} - The total price
 */
async function calculateSubscriptionPrice(planId, addOnIds = []) {
  let totalPrice = 0;

  // Get the base plan
  const basePlan = await getSubscriptionPlan(planId);
  if (basePlan) {
    totalPrice += basePlan.price;
  }

  // Add the price of each add-on
  for (const addOnId of addOnIds) {
    const addOn = await getSubscriptionPlan(addOnId);
    if (addOn) {
      totalPrice += addOn.price;
    }
  }

  return totalPrice;
}

/**
 * Format a price as a string with currency symbol
 *
 * @param {number} price - The price to format
 * @param {string} currency - The currency code (default: USD)
 * @returns {string} - Formatted price string
 */
function formatPrice(price, currency = 'USD') {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency
  }).format(price);
}

/**
 * Get the features of a subscription plan as an array of strings
 *
 * @param {Object} plan - The subscription plan object
 * @returns {Array<string>} - Array of feature strings
 */
function getPlanFeatures(plan) {
  const features = [];

  if (plan.transcriptionMinutes > 0) {
    features.push(`${plan.transcriptionMinutes} mins AI transcription (${plan.transcriptionModel} model)`);
  }

  if (plan.translationWords > 0) {
    features.push(`${plan.translationWords.toLocaleString()} words translation`);
  }

  if (plan.ttsMinutes > 0) {
    features.push(`${plan.ttsMinutes} mins text-to-speech`);
  }

  if (plan.aiCredits > 0) {
    features.push(`${plan.aiCredits} AI credits`);
  }

  if (plan.credits > 0) {
    features.push(`${plan.credits} additional credits`);
  }

  return features;
}

// Export functions for use in other modules
window.subscriptionPlansService = {
  getAllSubscriptionPlans,
  getSubscriptionPlan,
  getServicePlans,
  getPayAsYouGoPlans,
  calculateSubscriptionPrice,
  formatPrice,
  getPlanFeatures
};
