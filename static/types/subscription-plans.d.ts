/**
 * TypeScript interfaces for VocalLocal subscription plans
 * These interfaces define the schema for subscription plans in Firebase Realtime Database
 */

/**
 * Base subscription plan interface
 */
export interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  isActive: boolean;
}

/**
 * Service plan with usage limits
 */
export interface ServicePlan extends SubscriptionPlan {
  transcriptionMinutes: number;
  translationWords: number;
  ttsMinutes: number;
  aiCredits: number;
  transcriptionModel: string;
}

/**
 * Pay-as-you-go add-on plan
 */
export interface PayAsYouGoPlan extends SubscriptionPlan {
  credits: number;
  requiresSubscription: boolean;
  compatiblePlans: { [key: string]: boolean };
}

/**
 * Free plan
 */
export interface FreePlan extends ServicePlan {
  id: 'free';
}

/**
 * Basic plan
 */
export interface BasicPlan extends ServicePlan {
  id: 'basic';
}

/**
 * Professional plan
 */
export interface ProfessionalPlan extends ServicePlan {
  id: 'professional';
}

/**
 * Union type for all subscription plans
 */
export type AnySubscriptionPlan = FreePlan | BasicPlan | ProfessionalPlan | PayAsYouGoPlan;

/**
 * Map of all subscription plans
 */
export interface SubscriptionPlansMap {
  [planId: string]: AnySubscriptionPlan;
}
