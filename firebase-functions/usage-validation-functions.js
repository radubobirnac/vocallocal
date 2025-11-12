/**
 * Firebase Cloud Functions for VocalLocal Usage Validation
 *
 * These functions validate user requests against their available usage limits
 * and subscription plans.
 */

const functions = require('firebase-functions');
const admin = require('firebase-admin');

// Initialize Firebase Admin SDK
admin.initializeApp();

// Reference to the database
const db = admin.database();

/**
 * Standardized response object for all validation functions
 *
 * @typedef {Object} ValidationResponse
 * @property {boolean} allowed - Whether the requested usage is allowed
 * @property {number} remaining - Remaining units after the requested usage
 * @property {string} planType - The user's current subscription plan type
 * @property {boolean} upgradeRequired - Whether the user needs to upgrade their plan
 * @property {Object} [error] - Error information if applicable
 */

/**
 * Get user subscription and usage data
 *
 * @param {string} userId - The user ID to get data for
 * @returns {Promise<Object>} - User data including subscription and usage
 * @throws {Error} - If user data cannot be retrieved
 */
async function getUserData(userId) {
  try {
    // Get user subscription data
    const userRef = db.ref(`users/${userId}`);
    const snapshot = await userRef.once('value');
    const userData = snapshot.val();

    if (!userData) {
      throw new Error('User data not found');
    }

    return userData;
  } catch (error) {
    functions.logger.error('Error getting user data:', error);
    throw error;
  }
}

/**
 * Get subscription plan details
 *
 * @param {string} planType - The plan type to get details for
 * @returns {Promise<Object>} - Subscription plan details
 * @throws {Error} - If plan data cannot be retrieved
 */
async function getSubscriptionPlan(planType) {
  try {
    const planRef = db.ref(`subscriptionPlans/${planType}`);
    const snapshot = await planRef.once('value');
    const planData = snapshot.val();

    if (!planData) {
      throw new Error(`Subscription plan '${planType}' not found`);
    }

    return planData;
  } catch (error) {
    functions.logger.error('Error getting subscription plan:', error);
    throw error;
  }
}

/**
 * Check if usage needs to be reset for a new month and reset if necessary
 *
 * This function implements automatic monthly usage reset by:
 * 1. Checking if the current month/year differs from the last reset month/year
 * 2. If different, archives the previous month's usage to history
 * 3. Resets currentPeriod usage counters to zero
 * 4. Updates the periodStartDate to the first day of the current month
 *
 * @param {string} userId - The user ID to check and reset
 * @returns {Promise<boolean>} - True if reset was performed, false otherwise
 */
async function checkAndResetMonthlyUsage(userId) {
  try {
    const userRef = db.ref(`users/${userId}`);
    const snapshot = await userRef.once('value');
    const userData = snapshot.val();

    if (!userData || !userData.usage) {
      // Initialize usage structure if it doesn't exist
      await userRef.child('usage').set({
        currentPeriod: {
          transcriptionMinutes: 0,
          translationWords: 0,
          ttsMinutes: 0,
          aiCredits: 0,
          periodStartDate: new Date().setDate(1) // First day of current month
        },
        totalUsage: {
          transcriptionMinutes: 0,
          translationWords: 0,
          ttsMinutes: 0,
          aiCredits: 0
        },
        lastResetAt: Date.now()
      });
      return true;
    }

    const currentPeriod = userData.usage.currentPeriod || {};
    const periodStartDate = currentPeriod.periodStartDate || 0;

    // Get current month/year and period start month/year
    const now = new Date();
    const currentMonth = now.getUTCMonth();
    const currentYear = now.getUTCFullYear();

    const periodStart = new Date(periodStartDate);
    const periodMonth = periodStart.getUTCMonth();
    const periodYear = periodStart.getUTCFullYear();

    // Check if we're in a new month
    const isNewMonth = (currentYear > periodYear) || (currentYear === periodYear && currentMonth > periodMonth);

    if (isNewMonth) {
      functions.logger.info(`Automatic monthly reset triggered for user ${userId}: ${periodYear}-${periodMonth + 1} -> ${currentYear}-${currentMonth + 1}`);

      // Archive previous month's usage
      const archiveMonth = `${periodYear}-${String(periodMonth + 1).padStart(2, '0')}`;
      const archiveData = {
        transcriptionMinutes: currentPeriod.transcriptionMinutes || 0,
        translationWords: currentPeriod.translationWords || 0,
        ttsMinutes: currentPeriod.ttsMinutes || 0,
        aiCredits: currentPeriod.aiCredits || 0,
        periodStartDate: periodStartDate,
        archivedAt: Date.now(),
        planType: userData.subscription?.planType || 'free'
      };

      // Calculate first day of current month
      const firstDayOfMonth = new Date(Date.UTC(currentYear, currentMonth, 1)).getTime();

      // Prepare batch updates
      const updates = {};
      updates[`usage/history/${archiveMonth}/${userId}`] = archiveData;
      updates[`users/${userId}/usage/currentPeriod`] = {
        transcriptionMinutes: 0,
        translationWords: 0,
        ttsMinutes: 0,
        aiCredits: 0,
        periodStartDate: firstDayOfMonth
      };
      updates[`users/${userId}/usage/lastResetAt`] = Date.now();

      // Execute batch update
      await db.ref().update(updates);

      functions.logger.info(`Monthly usage reset completed for user ${userId}. Archived ${archiveData.transcriptionMinutes} transcription minutes, ${archiveData.translationWords} translation words to ${archiveMonth}`);

      return true;
    }

    return false;
  } catch (error) {
    functions.logger.error(`Error checking/resetting monthly usage for user ${userId}:`, error);
    // Don't throw - allow the operation to continue even if reset fails
    return false;
  }
}

/**
 * Validate if a user has sufficient transcription minutes available
 *
 * @param {Object} data - The request data
 * @param {string} data.userId - The user ID to validate
 * @param {number} data.minutesRequested - The number of minutes requested
 * @returns {Promise<ValidationResponse>} - Validation response
 */
exports.validateTranscriptionUsage = functions.https.onCall(async (data, context) => {
  // Ensure user is authenticated
  if (!context.auth) {
    return {
      allowed: false,
      remaining: 0,
      planType: 'none',
      upgradeRequired: true,
      error: {
        code: 'unauthenticated',
        message: 'User must be authenticated to validate usage'
      }
    };
  }

  // Ensure the authenticated user is requesting their own data
  if (context.auth.uid !== data.userId) {
    return {
      allowed: false,
      remaining: 0,
      planType: 'none',
      upgradeRequired: false,
      error: {
        code: 'permission-denied',
        message: 'Users can only validate their own usage'
      }
    };
  }

  const userId = data.userId;
  const minutesRequested = data.minutesRequested || 0;

  try {
    functions.logger.info(`Validating transcription usage for user ${userId}: ${minutesRequested} minutes requested`);

    // Check and reset monthly usage if needed (automatic monthly reset)
    await checkAndResetMonthlyUsage(userId);

    // Get user data (after potential reset)
    const userData = await getUserData(userId);

    // Check user role first - admins and super users have unlimited access
    const userRole = userData.role || 'normal_user';
    if (userRole === 'admin' || userRole === 'super_user') {
      functions.logger.info(`Unlimited transcription access for ${userRole} role`);
      return {
        allowed: true,
        remaining: 999999, // Unlimited
        planType: 'unlimited',
        upgradeRequired: false,
        role: userRole
      };
    }

    const subscription = userData.subscription || {};
    const planType = subscription.status === 'active' ? subscription.planType : 'free';

    // Get subscription plan details
    const planData = await getSubscriptionPlan(planType);

    // Get current usage (only from current month due to automatic reset above)
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

    functions.logger.info(`Transcription validation result for user ${userId}: allowed=${allowed}, remaining=${remaining}, planType=${planType}, upgradeRequired=${upgradeRequired}`);

    return {
      allowed,
      remaining,
      planType,
      upgradeRequired
    };
  } catch (error) {
    functions.logger.error(`Error validating transcription usage for user ${userId}:`, error);

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
});

/**
 * Validate if a user has sufficient translation words available
 *
 * @param {Object} data - The request data
 * @param {string} data.userId - The user ID to validate
 * @param {number} data.wordsRequested - The number of words requested
 * @returns {Promise<ValidationResponse>} - Validation response
 */
exports.validateTranslationUsage = functions.https.onCall(async (data, context) => {
  // Ensure user is authenticated
  if (!context.auth) {
    return {
      allowed: false,
      remaining: 0,
      planType: 'none',
      upgradeRequired: true,
      error: {
        code: 'unauthenticated',
        message: 'User must be authenticated to validate usage'
      }
    };
  }

  // Ensure the authenticated user is requesting their own data
  if (context.auth.uid !== data.userId) {
    return {
      allowed: false,
      remaining: 0,
      planType: 'none',
      upgradeRequired: false,
      error: {
        code: 'permission-denied',
        message: 'Users can only validate their own usage'
      }
    };
  }

  const userId = data.userId;
  const wordsRequested = data.wordsRequested || 0;

  try {
    functions.logger.info(`Validating translation usage for user ${userId}: ${wordsRequested} words requested`);

    // Check and reset monthly usage if needed (automatic monthly reset)
    await checkAndResetMonthlyUsage(userId);

    // Get user data (after potential reset)
    const userData = await getUserData(userId);

    // Check user role first - admins and super users have unlimited access
    const userRole = userData.role || 'normal_user';
    if (userRole === 'admin' || userRole === 'super_user') {
      functions.logger.info(`Unlimited translation access for ${userRole} role`);
      return {
        allowed: true,
        remaining: 999999, // Unlimited
        planType: 'unlimited',
        upgradeRequired: false,
        role: userRole
      };
    }

    const subscription = userData.subscription || {};
    const planType = subscription.status === 'active' ? subscription.planType : 'free';

    // Get subscription plan details
    const planData = await getSubscriptionPlan(planType);

    // Get current usage (only from current month due to automatic reset above)
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

    functions.logger.info(`Translation validation result for user ${userId}: allowed=${allowed}, remaining=${remaining}, planType=${planType}, upgradeRequired=${upgradeRequired}`);

    return {
      allowed,
      remaining,
      planType,
      upgradeRequired
    };
  } catch (error) {
    functions.logger.error(`Error validating translation usage for user ${userId}:`, error);

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
});

/**
 * Validate if a user has sufficient text-to-speech minutes available
 *
 * @param {Object} data - The request data
 * @param {string} data.userId - The user ID to validate
 * @param {number} data.minutesRequested - The number of minutes requested
 * @returns {Promise<ValidationResponse>} - Validation response
 */
exports.validateTTSUsage = functions.https.onCall(async (data, context) => {
  // Ensure user is authenticated
  if (!context.auth) {
    return {
      allowed: false,
      remaining: 0,
      planType: 'none',
      upgradeRequired: true,
      error: {
        code: 'unauthenticated',
        message: 'User must be authenticated to validate usage'
      }
    };
  }

  // Ensure the authenticated user is requesting their own data
  if (context.auth.uid !== data.userId) {
    return {
      allowed: false,
      remaining: 0,
      planType: 'none',
      upgradeRequired: false,
      error: {
        code: 'permission-denied',
        message: 'Users can only validate their own usage'
      }
    };
  }

  const userId = data.userId;
  const minutesRequested = data.minutesRequested || 0;

  try {
    functions.logger.info(`Validating TTS usage for user ${userId}: ${minutesRequested} minutes requested`);

    // Check and reset monthly usage if needed (automatic monthly reset)
    await checkAndResetMonthlyUsage(userId);

    // Get user data (after potential reset)
    const userData = await getUserData(userId);

    // Check user role first - admins and super users have unlimited access
    const userRole = userData.role || 'normal_user';
    if (userRole === 'admin' || userRole === 'super_user') {
      functions.logger.info(`Unlimited TTS access for ${userRole} role`);
      return {
        allowed: true,
        remaining: 999999, // Unlimited
        planType: 'unlimited',
        upgradeRequired: false,
        role: userRole
      };
    }

    const subscription = userData.subscription || {};
    const planType = subscription.status === 'active' ? subscription.planType : 'free';

    // Free users have no TTS access
    if (planType === 'free') {
      functions.logger.info(`TTS access denied for free user ${userId}`);
      return {
        allowed: false,
        remaining: 0,
        planType: 'free',
        upgradeRequired: true,
        error: {
          code: 'tts_not_available_free',
          message: 'Text-to-Speech is not available on the Free Plan. Upgrade to Basic or Professional plan to access TTS features.'
        }
      };
    }

    // Get subscription plan details
    const planData = await getSubscriptionPlan(planType);

    // Get current usage (only from current month due to automatic reset above)
    const currentUsage = userData.usage?.currentPeriod?.ttsMinutes || 0;

    // Get pay-as-you-go balance
    const paygBalance = userData.billing?.payAsYouGo?.unitsRemaining?.ttsMinutes || 0;

    // Calculate available minutes from subscription plan
    const planLimit = planData.ttsMinutes || 0;
    const remainingPlanMinutes = Math.max(0, planLimit - currentUsage);

    // Total available minutes (subscription + pay-as-you-go)
    const totalAvailableMinutes = remainingPlanMinutes + paygBalance;

    // Check if user has enough minutes
    const allowed = totalAvailableMinutes >= minutesRequested;
    const remaining = Math.max(0, totalAvailableMinutes - minutesRequested);
    const upgradeRequired = !allowed && remainingPlanMinutes < minutesRequested;

    functions.logger.info(`TTS validation result for user ${userId}: allowed=${allowed}, remaining=${remaining}, planType=${planType}, upgradeRequired=${upgradeRequired}`);

    return {
      allowed,
      remaining,
      planType,
      upgradeRequired
    };
  } catch (error) {
    functions.logger.error(`Error validating TTS usage for user ${userId}:`, error);

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
});

/**
 * Validate if a user has sufficient AI credits available
 *
 * @param {Object} data - The request data
 * @param {string} data.userId - The user ID to validate
 * @param {number} data.creditsRequested - The number of AI credits requested
 * @returns {Promise<ValidationResponse>} - Validation response
 */
exports.validateAICredits = functions.https.onCall(async (data, context) => {
  // Ensure user is authenticated
  if (!context.auth) {
    return {
      allowed: false,
      remaining: 0,
      planType: 'none',
      upgradeRequired: true,
      error: {
        code: 'unauthenticated',
        message: 'User must be authenticated to validate usage'
      }
    };
  }

  // Ensure the authenticated user is requesting their own data
  if (context.auth.uid !== data.userId) {
    return {
      allowed: false,
      remaining: 0,
      planType: 'none',
      upgradeRequired: false,
      error: {
        code: 'permission-denied',
        message: 'Users can only validate their own usage'
      }
    };
  }

  const userId = data.userId;
  const creditsRequested = data.creditsRequested || 0;

  try {
    functions.logger.info(`Validating AI credits usage for user ${userId}: ${creditsRequested} credits requested`);

    // Get user data
    const userData = await getUserData(userId);
    const subscription = userData.subscription || {};
    const planType = subscription.status === 'active' ? subscription.planType : 'free';

    // Get subscription plan details
    const planData = await getSubscriptionPlan(planType);

    // Get current usage
    const currentUsage = userData.usage?.currentPeriod?.aiCredits || 0;

    // Get pay-as-you-go balance
    const paygBalance = userData.billing?.payAsYouGo?.unitsRemaining?.aiCredits || 0;

    // Calculate available credits from subscription plan
    const planLimit = planData.aiCredits || 0;
    const remainingPlanCredits = Math.max(0, planLimit - currentUsage);

    // Total available credits (subscription + pay-as-you-go)
    const totalAvailableCredits = remainingPlanCredits + paygBalance;

    // Check if user has enough credits
    const allowed = totalAvailableCredits >= creditsRequested;
    const remaining = Math.max(0, totalAvailableCredits - creditsRequested);
    const upgradeRequired = !allowed && remainingPlanCredits < creditsRequested;

    functions.logger.info(`AI credits validation result for user ${userId}: allowed=${allowed}, remaining=${remaining}, planType=${planType}, upgradeRequired=${upgradeRequired}`);

    return {
      allowed,
      remaining,
      planType,
      upgradeRequired
    };
  } catch (error) {
    functions.logger.error(`Error validating AI credits usage for user ${userId}:`, error);

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
});

/**
 * Check if a user is an admin
 *
 * @param {string} userId - The user ID to check
 * @returns {Promise<boolean>} - Whether the user is an admin
 */
async function isAdminUser(userId) {
  try {
    const adminRef = db.ref(`admins/${userId}`);
    const snapshot = await adminRef.once('value');
    return snapshot.exists() && snapshot.val() === true;
  } catch (error) {
    functions.logger.error(`Error checking admin status for user ${userId}:`, error);
    return false;
  }
}

/**
 * Track usage for a specific service
 *
 * @param {Object} data - The request data
 * @param {string} data.userId - The user ID to track usage for
 * @param {string} data.serviceType - The type of service (transcription, translation, tts, ai)
 * @param {number} data.amount - The amount to track
 * @returns {Promise<Object>} - Updated usage data
 */
exports.trackUsage = functions.https.onCall(async (data, context) => {
  // Ensure user is authenticated
  if (!context.auth) {
    return {
      success: false,
      error: {
        code: 'unauthenticated',
        message: 'User must be authenticated to track usage'
      }
    };
  }

  // Only allow admin users or the user themselves to track usage
  const isAdmin = await isAdminUser(context.auth.uid);
  if (!isAdmin && context.auth.uid !== data.userId) {
    return {
      success: false,
      error: {
        code: 'permission-denied',
        message: 'Only admin users can track usage for other users'
      }
    };
  }

  const userId = data.userId;
  const serviceType = data.serviceType;
  const amount = data.amount || 0;

  // Map service type to database field
  const serviceTypeMap = {
    'transcription': 'transcriptionMinutes',
    'translation': 'translationWords',
    'tts': 'ttsMinutes',
    'ai': 'aiCredits'
  };

  const dbField = serviceTypeMap[serviceType];
  if (!dbField) {
    return {
      success: false,
      error: {
        code: 'invalid-argument',
        message: `Invalid service type: ${serviceType}`
      }
    };
  }

  try {
    functions.logger.info(`Tracking usage for user ${userId}: ${amount} ${serviceType}`);

    // Get current usage
    const userRef = db.ref(`users/${userId}`);
    const snapshot = await userRef.once('value');
    const userData = snapshot.val();

    if (!userData) {
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

    await db.ref().update(updates);

    functions.logger.info(`Usage tracked for user ${userId}: ${amount} ${serviceType}, new total: ${newCurrentPeriodUsage}`);

    return {
      success: true,
      currentPeriodUsage: newCurrentPeriodUsage,
      totalUsage: newTotalUsage
    };
  } catch (error) {
    functions.logger.error(`Error tracking usage for user ${userId}:`, error);

    return {
      success: false,
      error: {
        code: 'internal-error',
        message: 'An error occurred while tracking usage',
        details: error.message
      }
    };
  }
});

/**
 * Deduct usage from a user's account
 *
 * @param {Object} data - The request data
 * @param {string} data.userId - The user ID to deduct usage from
 * @param {string} data.serviceType - The type of service (transcription, translation, tts, ai)
 * @param {number} data.amount - The amount to deduct
 * @returns {Promise<Object>} - Updated usage data
 */
exports.deductUsage = functions.https.onCall(async (data, context) => {
  // Ensure user is authenticated
  if (!context.auth) {
    return {
      success: false,
      error: {
        code: 'unauthenticated',
        message: 'User must be authenticated to deduct usage'
      }
    };
  }

  // Only allow admin users or the user themselves to deduct usage
  const isAdmin = await isAdminUser(context.auth.uid);
  if (!isAdmin && context.auth.uid !== data.userId) {
    return {
      success: false,
      error: {
        code: 'permission-denied',
        message: 'Only admin users can deduct usage for other users'
      }
    };
  }

  const userId = data.userId;
  const serviceType = data.serviceType;
  const amount = data.amount || 0;

  // Map service type to database field
  const serviceTypeMap = {
    'transcription': 'transcriptionMinutes',
    'translation': 'translationWords',
    'tts': 'ttsMinutes',
    'ai': 'aiCredits'
  };

  const dbField = serviceTypeMap[serviceType];
  if (!dbField) {
    return {
      success: false,
      error: {
        code: 'invalid-argument',
        message: `Invalid service type: ${serviceType}`
      }
    };
  }

  try {
    functions.logger.info(`Deducting usage for user ${userId}: ${amount} ${serviceType}`);

    // Get user data
    const userData = await getUserData(userId);
    const subscription = userData.subscription || {};
    const planType = subscription.status === 'active' ? subscription.planType : 'free';

    // Get subscription plan details
    const planData = await getSubscriptionPlan(planType);

    // Get current usage
    const currentUsage = userData.usage?.currentPeriod?.[dbField] || 0;

    // Get pay-as-you-go balance
    const paygBalance = userData.billing?.payAsYouGo?.unitsRemaining?.[dbField] || 0;

    // Calculate available units from subscription plan
    const planLimit = planData[dbField] || 0;
    const remainingPlanUnits = Math.max(0, planLimit - currentUsage);

    // Determine how much to deduct from each source
    let planDeduction = 0;
    let paygDeduction = 0;

    if (remainingPlanUnits >= amount) {
      // Deduct entirely from plan
      planDeduction = amount;
    } else {
      // Deduct what we can from plan
      planDeduction = remainingPlanUnits;

      // Deduct the rest from pay-as-you-go
      paygDeduction = amount - remainingPlanUnits;

      // Ensure we don't deduct more than available
      paygDeduction = Math.min(paygDeduction, paygBalance);
    }

    // Update usage in database
    const updates = {};

    // Update current period usage (for plan deduction)
    if (planDeduction > 0) {
      const newCurrentUsage = currentUsage + planDeduction;
      updates[`users/${userId}/usage/currentPeriod/${dbField}`] = newCurrentUsage;
    }

    // Update pay-as-you-go balance (for payg deduction)
    if (paygDeduction > 0) {
      const newPaygBalance = paygBalance - paygDeduction;
      updates[`users/${userId}/billing/payAsYouGo/unitsRemaining/${dbField}`] = newPaygBalance;
    }

    // Update total usage (for both deductions)
    const totalUsage = userData.usage?.totalUsage?.[dbField] || 0;
    const totalDeduction = planDeduction + paygDeduction;
    const newTotalUsage = totalUsage + totalDeduction;
    updates[`users/${userId}/usage/totalUsage/${dbField}`] = newTotalUsage;

    // Apply updates
    await db.ref().update(updates);

    functions.logger.info(`Usage deducted for user ${userId}: ${totalDeduction} ${serviceType} (plan: ${planDeduction}, payg: ${paygDeduction})`);

    return {
      success: true,
      deducted: totalDeduction,
      fromPlan: planDeduction,
      fromPayg: paygDeduction,
      remainingPlan: remainingPlanUnits - planDeduction,
      remainingPayg: paygBalance - paygDeduction
    };
  } catch (error) {
    functions.logger.error(`Error deducting usage for user ${userId}:`, error);

    return {
      success: false,
      error: {
        code: 'internal-error',
        message: 'An error occurred while deducting usage',
        details: error.message
      }
    };
  }
});

/**
 * Deduct transcription usage from a user's account
 *
 * @param {Object} data - The request data
 * @param {string} data.userId - The user ID to deduct usage from
 * @param {number} data.minutesUsed - The number of minutes to deduct
 * @returns {Promise<Object>} - Updated usage data
 */
exports.deductTranscriptionUsage = functions.https.onCall(async (data, context) => {
  // Ensure user is authenticated
  if (!context.auth) {
    return {
      success: false,
      error: {
        code: 'unauthenticated',
        message: 'User must be authenticated to deduct transcription usage'
      }
    };
  }

  // Only allow admin users or the user themselves to deduct usage
  const isAdmin = await isAdminUser(context.auth.uid);
  if (!isAdmin && context.auth.uid !== data.userId) {
    return {
      success: false,
      error: {
        code: 'permission-denied',
        message: 'Only admin users can deduct usage for other users'
      }
    };
  }

  const userId = data.userId;
  const minutesUsed = data.minutesUsed || 0;

  try {
    functions.logger.info(`Deducting transcription usage for user ${userId}: ${minutesUsed} minutes`);

    // Check and reset monthly usage if needed (automatic monthly reset)
    await checkAndResetMonthlyUsage(userId);

    // Use atomic transaction for consistency
    const userRef = db.ref(`users/${userId}`);

    return await userRef.transaction((userData) => {
      if (!userData) {
        return userData; // Abort transaction if user doesn't exist
      }

      // Initialize usage structure if it doesn't exist
      if (!userData.usage) {
        const firstDayOfMonth = new Date(Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth(), 1)).getTime();
        userData.usage = {
          currentPeriod: {
            transcriptionMinutes: 0,
            translationWords: 0,
            ttsMinutes: 0,
            aiCredits: 0,
            periodStartDate: firstDayOfMonth
          },
          totalUsage: { transcriptionMinutes: 0, translationWords: 0, ttsMinutes: 0, aiCredits: 0 }
        };
      }

      // Get current values
      const currentUsage = userData.usage.currentPeriod.transcriptionMinutes || 0;
      const totalUsage = userData.usage.totalUsage.transcriptionMinutes || 0;

      // Update usage counters (only current month due to automatic reset above)
      userData.usage.currentPeriod.transcriptionMinutes = currentUsage + minutesUsed;
      userData.usage.totalUsage.transcriptionMinutes = totalUsage + minutesUsed;

      // Update last activity timestamp
      userData.lastActivityAt = Date.now();

      return userData;
    }).then((result) => {
      if (result.committed) {
        const newData = result.snapshot.val();
        const newCurrentUsage = newData.usage.currentPeriod.transcriptionMinutes;
        const newTotalUsage = newData.usage.totalUsage.transcriptionMinutes;

        functions.logger.info(`Transcription usage deducted for user ${userId}: ${minutesUsed} minutes, new current: ${newCurrentUsage}, new total: ${newTotalUsage}`);

        return {
          success: true,
          deducted: minutesUsed,
          currentPeriodUsage: newCurrentUsage,
          totalUsage: newTotalUsage,
          serviceType: 'transcription'
        };
      } else {
        throw new Error('Transaction failed - user data may not exist');
      }
    });

  } catch (error) {
    functions.logger.error(`Error deducting transcription usage: ${error.message}`);

    return {
      success: false,
      error: {
        code: 'internal-error',
        message: 'An error occurred while deducting transcription usage',
        details: error.message
      }
    };
  }
});

/**
 * Deduct translation usage from a user's account
 *
 * @param {Object} data - The request data
 * @param {string} data.userId - The user ID to deduct usage from
 * @param {number} data.wordsUsed - The number of words to deduct
 * @returns {Promise<Object>} - Updated usage data
 */
exports.deductTranslationUsage = functions.https.onCall(async (data, context) => {
  // Ensure user is authenticated
  if (!context.auth) {
    return {
      success: false,
      error: {
        code: 'unauthenticated',
        message: 'User must be authenticated to deduct translation usage'
      }
    };
  }

  // Only allow admin users or the user themselves to deduct usage
  const isAdmin = await isAdminUser(context.auth.uid);
  if (!isAdmin && context.auth.uid !== data.userId) {
    return {
      success: false,
      error: {
        code: 'permission-denied',
        message: 'Only admin users can deduct usage for other users'
      }
    };
  }

  const userId = data.userId;
  const wordsUsed = data.wordsUsed || 0;

  try {
    functions.logger.info(`Deducting translation usage for user ${userId}: ${wordsUsed} words`);

    // Check and reset monthly usage if needed (automatic monthly reset)
    await checkAndResetMonthlyUsage(userId);

    // Use atomic transaction for consistency
    const userRef = db.ref(`users/${userId}`);

    return await userRef.transaction((userData) => {
      if (!userData) {
        return userData; // Abort transaction if user doesn't exist
      }

      // Initialize usage structure if it doesn't exist
      if (!userData.usage) {
        const firstDayOfMonth = new Date(Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth(), 1)).getTime();
        userData.usage = {
          currentPeriod: {
            transcriptionMinutes: 0,
            translationWords: 0,
            ttsMinutes: 0,
            aiCredits: 0,
            periodStartDate: firstDayOfMonth
          },
          totalUsage: { transcriptionMinutes: 0, translationWords: 0, ttsMinutes: 0, aiCredits: 0 }
        };
      }

      // Get current values
      const currentUsage = userData.usage.currentPeriod.translationWords || 0;
      const totalUsage = userData.usage.totalUsage.translationWords || 0;

      // Update usage counters (only current month due to automatic reset above)
      userData.usage.currentPeriod.translationWords = currentUsage + wordsUsed;
      userData.usage.totalUsage.translationWords = totalUsage + wordsUsed;

      // Update last activity timestamp
      userData.lastActivityAt = Date.now();

      return userData;
    }).then((result) => {
      if (result.committed) {
        const newData = result.snapshot.val();
        const newCurrentUsage = newData.usage.currentPeriod.translationWords;
        const newTotalUsage = newData.usage.totalUsage.translationWords;

        functions.logger.info(`Translation usage deducted for user ${userId}: ${wordsUsed} words, new current: ${newCurrentUsage}, new total: ${newTotalUsage}`);

        return {
          success: true,
          deducted: wordsUsed,
          currentPeriodUsage: newCurrentUsage,
          totalUsage: newTotalUsage,
          serviceType: 'translation'
        };
      } else {
        throw new Error('Transaction failed - user data may not exist');
      }
    });

  } catch (error) {
    functions.logger.error(`Error deducting translation usage: ${error.message}`);

    return {
      success: false,
      error: {
        code: 'internal-error',
        message: 'An error occurred while deducting translation usage',
        details: error.message
      }
    };
  }
});

/**
 * Deduct TTS usage from a user's account
 *
 * @param {Object} data - The request data
 * @param {string} data.userId - The user ID to deduct usage from
 * @param {number} data.minutesUsed - The number of minutes to deduct
 * @returns {Promise<Object>} - Updated usage data
 */
exports.deductTTSUsage = functions.https.onCall(async (data, context) => {
  // Ensure user is authenticated
  if (!context.auth) {
    return {
      success: false,
      error: {
        code: 'unauthenticated',
        message: 'User must be authenticated to deduct TTS usage'
      }
    };
  }

  // Only allow admin users or the user themselves to deduct usage
  const isAdmin = await isAdminUser(context.auth.uid);
  if (!isAdmin && context.auth.uid !== data.userId) {
    return {
      success: false,
      error: {
        code: 'permission-denied',
        message: 'Only admin users can deduct usage for other users'
      }
    };
  }

  const userId = data.userId;
  const minutesUsed = data.minutesUsed || 0;

  try {
    functions.logger.info(`Deducting TTS usage for user ${userId}: ${minutesUsed} minutes`);

    // Check and reset monthly usage if needed (automatic monthly reset)
    await checkAndResetMonthlyUsage(userId);

    // Use atomic transaction for consistency
    const userRef = db.ref(`users/${userId}`);

    return await userRef.transaction((userData) => {
      if (!userData) {
        return userData; // Abort transaction if user doesn't exist
      }

      // Initialize usage structure if it doesn't exist
      if (!userData.usage) {
        const firstDayOfMonth = new Date(Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth(), 1)).getTime();
        userData.usage = {
          currentPeriod: {
            transcriptionMinutes: 0,
            translationWords: 0,
            ttsMinutes: 0,
            aiCredits: 0,
            periodStartDate: firstDayOfMonth
          },
          totalUsage: { transcriptionMinutes: 0, translationWords: 0, ttsMinutes: 0, aiCredits: 0 }
        };
      }

      // Get current values
      const currentUsage = userData.usage.currentPeriod.ttsMinutes || 0;
      const totalUsage = userData.usage.totalUsage.ttsMinutes || 0;

      // Update usage counters (only current month due to automatic reset above)
      userData.usage.currentPeriod.ttsMinutes = currentUsage + minutesUsed;
      userData.usage.totalUsage.ttsMinutes = totalUsage + minutesUsed;

      // Update last activity timestamp
      userData.lastActivityAt = Date.now();

      return userData;
    }).then((result) => {
      if (result.committed) {
        const newData = result.snapshot.val();
        const newCurrentUsage = newData.usage.currentPeriod.ttsMinutes;
        const newTotalUsage = newData.usage.totalUsage.ttsMinutes;

        functions.logger.info(`TTS usage deducted for user ${userId}: ${minutesUsed} minutes, new current: ${newCurrentUsage}, new total: ${newTotalUsage}`);

        return {
          success: true,
          deducted: minutesUsed,
          currentPeriodUsage: newCurrentUsage,
          totalUsage: newTotalUsage,
          serviceType: 'tts'
        };
      } else {
        throw new Error('Transaction failed - user data may not exist');
      }
    });

  } catch (error) {
    functions.logger.error(`Error deducting TTS usage: ${error.message}`);

    return {
      success: false,
      error: {
        code: 'internal-error',
        message: 'An error occurred while deducting TTS usage',
        details: error.message
      }
    };
  }
});

/**
 * Deduct AI credits from a user's account
 *
 * @param {Object} data - The request data
 * @param {string} data.userId - The user ID to deduct usage from
 * @param {number} data.creditsUsed - The number of credits to deduct
 * @returns {Promise<Object>} - Updated usage data
 */
exports.deductAICredits = functions.https.onCall(async (data, context) => {
  // Ensure user is authenticated
  if (!context.auth) {
    return {
      success: false,
      error: {
        code: 'unauthenticated',
        message: 'User must be authenticated to deduct AI credits'
      }
    };
  }

  // Only allow admin users or the user themselves to deduct usage
  const isAdmin = await isAdminUser(context.auth.uid);
  if (!isAdmin && context.auth.uid !== data.userId) {
    return {
      success: false,
      error: {
        code: 'permission-denied',
        message: 'Only admin users can deduct usage for other users'
      }
    };
  }

  const userId = data.userId;
  const creditsUsed = data.creditsUsed || 0;

  try {
    functions.logger.info(`Deducting AI credits for user ${userId}: ${creditsUsed} credits`);

    // Check and reset monthly usage if needed (automatic monthly reset)
    await checkAndResetMonthlyUsage(userId);

    // Use atomic transaction for consistency
    const userRef = db.ref(`users/${userId}`);

    return await userRef.transaction((userData) => {
      if (!userData) {
        return userData; // Abort transaction if user doesn't exist
      }

      // Initialize usage structure if it doesn't exist
      if (!userData.usage) {
        const firstDayOfMonth = new Date(Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth(), 1)).getTime();
        userData.usage = {
          currentPeriod: {
            transcriptionMinutes: 0,
            translationWords: 0,
            ttsMinutes: 0,
            aiCredits: 0,
            periodStartDate: firstDayOfMonth
          },
          totalUsage: { transcriptionMinutes: 0, translationWords: 0, ttsMinutes: 0, aiCredits: 0 }
        };
      }

      // Get current values
      const currentUsage = userData.usage.currentPeriod.aiCredits || 0;
      const totalUsage = userData.usage.totalUsage.aiCredits || 0;

      // Update usage counters (only current month due to automatic reset above)
      userData.usage.currentPeriod.aiCredits = currentUsage + creditsUsed;
      userData.usage.totalUsage.aiCredits = totalUsage + creditsUsed;

      // Update last activity timestamp
      userData.lastActivityAt = Date.now();

      return userData;
    }).then((result) => {
      if (result.committed) {
        const newData = result.snapshot.val();
        const newCurrentUsage = newData.usage.currentPeriod.aiCredits;
        const newTotalUsage = newData.usage.totalUsage.aiCredits;

        functions.logger.info(`AI credits deducted for user ${userId}: ${creditsUsed} credits, new current: ${newCurrentUsage}, new total: ${newTotalUsage}`);

        return {
          success: true,
          deducted: creditsUsed,
          currentPeriodUsage: newCurrentUsage,
          totalUsage: newTotalUsage,
          serviceType: 'ai'
        };
      } else {
        throw new Error('Transaction failed - user data may not exist');
      }
    });

  } catch (error) {
    functions.logger.error(`Error deducting AI credits: ${error.message}`);

    return {
      success: false,
      error: {
        code: 'internal-error',
        message: 'An error occurred while deducting AI credits',
        details: error.message
      }
    };
  }
});