/**
 * Firebase Cloud Functions for VocalLocal
 *
 * This file exports all the Cloud Functions for the VocalLocal application.
 */

// Import the usage validation functions
const usageValidation = require('./usage-validation-functions');
const monthlyReset = require('./monthly-reset-functions');

// Export all functions
module.exports = {
  // Usage validation functions
  validateTranscriptionUsage: usageValidation.validateTranscriptionUsage,
  validateTranslationUsage: usageValidation.validateTranslationUsage,
  validateTTSUsage: usageValidation.validateTTSUsage,
  validateAICredits: usageValidation.validateAICredits,

  // Usage tracking functions
  trackUsage: usageValidation.trackUsage,
  deductUsage: usageValidation.deductUsage,

  // Specific deduct functions
  deductTranscriptionUsage: usageValidation.deductTranscriptionUsage,
  deductTranslationUsage: usageValidation.deductTranslationUsage,
  deductTTSUsage: usageValidation.deductTTSUsage,
  deductAICredits: usageValidation.deductAICredits,

  // Monthly usage reset functions
  resetMonthlyUsage: monthlyReset.resetMonthlyUsage,
  resetMonthlyUsageHTTP: monthlyReset.resetMonthlyUsageHTTP,
  getUsageStatistics: monthlyReset.getUsageStatistics,
  checkAndResetUsage: monthlyReset.checkAndResetUsage
};
