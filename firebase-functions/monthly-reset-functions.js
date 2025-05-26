/**
 * Firebase Cloud Functions for Monthly Usage Reset
 *
 * These functions handle monthly usage reset for all users in the VocalLocal application.
 * Designed to work within Firebase's free Spark plan limitations.
 */

const functions = require('firebase-functions');
const admin = require('firebase-admin');

/**
 * Reset monthly usage for all users
 *
 * This function:
 * 1. Resets all users' currentPeriod usage counters to zero
 * 2. Archives previous month's usage data to usage/history/{YYYY-MM}/
 * 3. Updates resetDate field for each user to next month's reset date
 * 4. Uses UTC timezone for consistency
 *
 * Can be triggered manually by admin or via HTTP trigger for external cron services
 */
exports.resetMonthlyUsage = functions.https.onCall(async (data, context) => {
  try {
    // Check if user is authenticated and is admin (for manual triggers)
    if (context.auth) {
      const userId = context.auth.uid;
      const adminSnapshot = await admin.database().ref(`admins/${userId}`).once('value');
      const isAdmin = adminSnapshot.val() === true;

      if (!isAdmin) {
        return {
          success: false,
          error: 'Unauthorized',
          message: 'Only admin users can trigger monthly usage reset'
        };
      }
    }

    functions.logger.info('Starting monthly usage reset process');

    // Get current date and calculate reset dates
    const now = new Date();
    const currentMonth = now.getUTCFullYear() + '-' + String(now.getUTCMonth() + 1).padStart(2, '0');

    // Calculate next reset date (first day of next month)
    const nextMonth = new Date(now.getUTCFullYear(), now.getUTCMonth() + 1, 1);
    const nextResetTimestamp = nextMonth.getTime();

    // Get all users
    const usersSnapshot = await admin.database().ref('users').once('value');
    const users = usersSnapshot.val();

    if (!users) {
      return {
        success: true,
        message: 'No users found to reset',
        usersProcessed: 0,
        archiveMonth: currentMonth
      };
    }

    const resetResults = {
      usersProcessed: 0,
      usersSkipped: 0,
      errors: [],
      archiveMonth: currentMonth,
      totalUsageArchived: {
        transcriptionMinutes: 0,
        translationWords: 0,
        ttsMinutes: 0,
        aiCredits: 0
      }
    };

    // Process each user
    for (const [userId, userData] of Object.entries(users)) {
      try {
        const currentUsage = userData.usage?.currentPeriod || {};
        const currentResetDate = currentUsage.resetDate || 0;

        // Check if reset is needed (current time > reset date)
        if (now.getTime() <= currentResetDate && !data.forceReset) {
          resetResults.usersSkipped++;
          continue;
        }

        // Archive current usage data
        const archiveData = {
          transcriptionMinutes: currentUsage.transcriptionMinutes || 0,
          translationWords: currentUsage.translationWords || 0,
          ttsMinutes: currentUsage.ttsMinutes || 0,
          aiCredits: currentUsage.aiCredits || 0,
          resetDate: currentResetDate,
          archivedAt: now.getTime(),
          planType: userData.subscription?.planType || 'free'
        };

        // Add to total archived usage
        resetResults.totalUsageArchived.transcriptionMinutes += archiveData.transcriptionMinutes;
        resetResults.totalUsageArchived.translationWords += archiveData.translationWords;
        resetResults.totalUsageArchived.ttsMinutes += archiveData.ttsMinutes;
        resetResults.totalUsageArchived.aiCredits += archiveData.aiCredits;

        // Prepare batch updates
        const updates = {};

        // Archive the usage data
        updates[`usage/history/${currentMonth}/${userId}`] = archiveData;

        // Reset current period usage
        updates[`users/${userId}/usage/currentPeriod`] = {
          transcriptionMinutes: 0,
          translationWords: 0,
          ttsMinutes: 0,
          aiCredits: 0,
          resetDate: nextResetTimestamp
        };

        // Update last reset timestamp
        updates[`users/${userId}/usage/lastResetAt`] = now.getTime();

        // Execute batch update
        await admin.database().ref().update(updates);

        resetResults.usersProcessed++;

        functions.logger.info(`Reset usage for user ${userId}: archived ${archiveData.transcriptionMinutes} transcription minutes, ${archiveData.translationWords} translation words`);

      } catch (userError) {
        functions.logger.error(`Error resetting usage for user ${userId}:`, userError);
        resetResults.errors.push({
          userId,
          error: userError.message
        });
      }
    }

    functions.logger.info(`Monthly usage reset completed: ${resetResults.usersProcessed} users processed, ${resetResults.usersSkipped} users skipped, ${resetResults.errors.length} errors`);

    return {
      success: true,
      message: `Monthly usage reset completed successfully`,
      ...resetResults
    };

  } catch (error) {
    functions.logger.error('Error in monthly usage reset:', error);
    return {
      success: false,
      error: 'ServerError',
      message: 'An error occurred during monthly usage reset',
      details: error.message
    };
  }
});

/**
 * HTTP trigger for external cron services
 *
 * This allows external free cron services to trigger the monthly reset
 * Includes basic security through a secret token
 */
exports.resetMonthlyUsageHTTP = functions.https.onRequest(async (req, res) => {
  // Only allow POST requests
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  try {
    // Basic security check - require a secret token
    const providedToken = req.headers['x-reset-token'] || req.body.token;
    const expectedToken = functions.config().reset?.token || 'vocallocal-reset-2024';

    if (providedToken !== expectedToken) {
      res.status(401).json({ error: 'Invalid or missing reset token' });
      return;
    }

    // Call the main reset function
    const result = await exports.resetMonthlyUsage.run({ forceReset: req.body.forceReset || false }, { auth: null });

    res.status(200).json(result);

  } catch (error) {
    functions.logger.error('Error in HTTP reset trigger:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: error.message
    });
  }
});

/**
 * Get usage statistics for admin dashboard
 *
 * Returns current usage statistics across all users
 */
exports.getUsageStatistics = functions.https.onCall(async (data, context) => {
  try {
    // Check if user is authenticated and is admin
    if (!context.auth) {
      return {
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required'
      };
    }

    const userId = context.auth.uid;
    const adminSnapshot = await admin.database().ref(`admins/${userId}`).once('value');
    const isAdmin = adminSnapshot.val() === true;

    if (!isAdmin) {
      return {
        success: false,
        error: 'Unauthorized',
        message: 'Admin access required'
      };
    }

    // Get all users
    const usersSnapshot = await admin.database().ref('users').once('value');
    const users = usersSnapshot.val();

    if (!users) {
      return {
        success: true,
        statistics: {
          totalUsers: 0,
          currentPeriodUsage: { transcriptionMinutes: 0, translationWords: 0, ttsMinutes: 0, aiCredits: 0 },
          usersNeedingReset: 0,
          nextResetDate: null
        }
      };
    }

    const stats = {
      totalUsers: 0,
      currentPeriodUsage: {
        transcriptionMinutes: 0,
        translationWords: 0,
        ttsMinutes: 0,
        aiCredits: 0
      },
      usersNeedingReset: 0,
      planDistribution: { free: 0, basic: 0, professional: 0 },
      nextResetDate: null
    };

    const now = new Date().getTime();
    let earliestResetDate = null;

    // Process each user
    for (const [userId, userData] of Object.entries(users)) {
      stats.totalUsers++;

      const currentUsage = userData.usage?.currentPeriod || {};
      const resetDate = currentUsage.resetDate || 0;
      const planType = userData.subscription?.planType || 'free';

      // Add to usage totals
      stats.currentPeriodUsage.transcriptionMinutes += currentUsage.transcriptionMinutes || 0;
      stats.currentPeriodUsage.translationWords += currentUsage.translationWords || 0;
      stats.currentPeriodUsage.ttsMinutes += currentUsage.ttsMinutes || 0;
      stats.currentPeriodUsage.aiCredits += currentUsage.aiCredits || 0;

      // Count plan distribution
      if (stats.planDistribution.hasOwnProperty(planType)) {
        stats.planDistribution[planType]++;
      }

      // Check if user needs reset
      if (now > resetDate) {
        stats.usersNeedingReset++;
      }

      // Track earliest reset date
      if (resetDate > now && (earliestResetDate === null || resetDate < earliestResetDate)) {
        earliestResetDate = resetDate;
      }
    }

    stats.nextResetDate = earliestResetDate;

    return {
      success: true,
      statistics: stats
    };

  } catch (error) {
    functions.logger.error('Error getting usage statistics:', error);
    return {
      success: false,
      error: 'ServerError',
      message: 'An error occurred while getting usage statistics',
      details: error.message
    };
  }
});

/**
 * Check if users need usage reset (client-side helper)
 *
 * This function can be called by the client application to check
 * if any users need their usage reset and trigger it automatically
 */
exports.checkAndResetUsage = functions.https.onCall(async (data, context) => {
  try {
    // This function can be called by authenticated users to check their own reset status
    // or by admins to check all users
    if (!context.auth) {
      return {
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required'
      };
    }

    const userId = context.auth.uid;
    const adminSnapshot = await admin.database().ref(`admins/${userId}`).once('value');
    const isAdmin = adminSnapshot.val() === true;

    const now = new Date().getTime();
    let usersToReset = [];

    if (isAdmin) {
      // Admin can check all users
      const usersSnapshot = await admin.database().ref('users').once('value');
      const users = usersSnapshot.val();

      if (users) {
        for (const [uid, userData] of Object.entries(users)) {
          const resetDate = userData.usage?.currentPeriod?.resetDate || 0;
          if (now > resetDate) {
            usersToReset.push(uid);
          }
        }
      }
    } else {
      // Regular user can only check their own status
      const userSnapshot = await admin.database().ref(`users/${userId}`).once('value');
      const userData = userSnapshot.val();

      if (userData) {
        const resetDate = userData.usage?.currentPeriod?.resetDate || 0;
        if (now > resetDate) {
          usersToReset.push(userId);
        }
      }
    }

    // If users need reset and this is an admin or single user check, trigger reset
    if (usersToReset.length > 0 && (isAdmin || usersToReset.includes(userId))) {
      if (isAdmin) {
        // Admin can trigger full reset
        const resetResult = await exports.resetMonthlyUsage.run({ forceReset: false }, context);
        return {
          success: true,
          resetTriggered: true,
          usersNeedingReset: usersToReset.length,
          resetResult: resetResult
        };
      } else {
        // Individual user reset (simplified version)
        const userSnapshot = await admin.database().ref(`users/${userId}`).once('value');
        const userData = userSnapshot.val();
        const currentUsage = userData.usage?.currentPeriod || {};

        // Calculate next reset date
        const nextMonth = new Date(now);
        nextMonth.setUTCMonth(nextMonth.getUTCMonth() + 1);
        nextMonth.setUTCDate(1);
        nextMonth.setUTCHours(0, 0, 0, 0);
        const nextResetTimestamp = nextMonth.getTime();

        // Archive and reset user's usage
        const currentMonth = new Date().getUTCFullYear() + '-' + String(new Date().getUTCMonth() + 1).padStart(2, '0');
        const archiveData = {
          transcriptionMinutes: currentUsage.transcriptionMinutes || 0,
          translationWords: currentUsage.translationWords || 0,
          ttsMinutes: currentUsage.ttsMinutes || 0,
          aiCredits: currentUsage.aiCredits || 0,
          resetDate: currentUsage.resetDate || 0,
          archivedAt: now,
          planType: userData.subscription?.planType || 'free'
        };

        const updates = {};
        updates[`usage/history/${currentMonth}/${userId}`] = archiveData;
        updates[`users/${userId}/usage/currentPeriod`] = {
          transcriptionMinutes: 0,
          translationWords: 0,
          ttsMinutes: 0,
          aiCredits: 0,
          resetDate: nextResetTimestamp
        };
        updates[`users/${userId}/usage/lastResetAt`] = now;

        await admin.database().ref().update(updates);

        return {
          success: true,
          resetTriggered: true,
          userReset: true,
          archivedUsage: archiveData
        };
      }
    }

    return {
      success: true,
      resetTriggered: false,
      usersNeedingReset: usersToReset.length,
      message: usersToReset.length > 0 ? 'Users need reset but not triggered' : 'No users need reset'
    };

  } catch (error) {
    functions.logger.error('Error in check and reset usage:', error);
    return {
      success: false,
      error: 'ServerError',
      message: 'An error occurred while checking usage reset status',
      details: error.message
    };
  }
});
