/**
 * TypeScript interfaces for VocalLocal user account data structures
 * These interfaces define the schema for user data in Firebase Realtime Database
 */

/**
 * User Profile information
 */
export interface UserProfile {
  email: string;
  displayName: string;
  createdAt: number; // Timestamp in milliseconds
  lastLoginAt: number; // Timestamp in milliseconds
  status: 'active' | 'suspended' | 'inactive';
}

/**
 * User Subscription information
 */
export interface UserSubscription {
  planType: 'free' | 'basic' | 'premium' | 'enterprise';
  status: 'active' | 'canceled' | 'expired' | 'trial';
  startDate: number; // Timestamp in milliseconds
  endDate: number; // Timestamp in milliseconds
  renewalDate: number; // Timestamp in milliseconds
  paymentMethod: string;
  billingCycle: 'monthly' | 'annual' | 'quarterly';
}

/**
 * Current Period Usage metrics
 */
export interface CurrentPeriodUsage {
  transcriptionMinutes: number;
  translationWords: number;
  ttsMinutes: number;
  aiCredits: number;
  resetDate: number; // Timestamp in milliseconds
}

/**
 * Lifetime Usage metrics
 */
export interface TotalUsage {
  transcriptionMinutes: number;
  translationWords: number;
  ttsMinutes: number;
  aiCredits: number;
}

/**
 * Units remaining for pay-as-you-go billing
 */
export interface UnitsRemaining {
  transcriptionMinutes: number;
  translationWords: number;
  ttsMinutes: number;
  aiCredits: number;
}

/**
 * Purchase history entry
 */
export interface PurchaseHistoryEntry {
  date: number; // Timestamp in milliseconds
  amount: number;
  serviceType: 'transcription' | 'translation' | 'tts' | 'ai' | 'bundle';
  unitsPurchased: number;
}

/**
 * Pay-as-you-go billing information
 */
export interface PayAsYouGoBilling {
  unitsRemaining: UnitsRemaining;
  purchaseHistory: PurchaseHistoryEntry[];
}

/**
 * Complete User Account structure
 */
export interface UserAccount {
  profile: UserProfile;
  subscription: UserSubscription;
  usage: {
    currentPeriod: CurrentPeriodUsage;
    totalUsage: TotalUsage;
  };
  billing: {
    payAsYouGo: PayAsYouGoBilling;
  };
}
