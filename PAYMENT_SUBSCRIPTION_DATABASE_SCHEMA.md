# VocalLocal Payment & Subscription Database Schema Documentation

## Overview

VocalLocal uses a dual-database approach for payment and subscription management:
- **Firebase Realtime Database**: Stores user account data, subscription status, and usage tracking
- **Stripe**: Handles payment processing, customer management, and subscription billing

## Database Architecture

### 1. Firebase Realtime Database Structure

#### User Account Schema
```
/users/{userId}/
├── profile/
│   ├── email: string
│   ├── displayName: string
│   ├── createdAt: number (timestamp)
│   ├── lastLoginAt: number (timestamp)
│   └── status: string ("active" | "inactive")
├── subscription/
│   ├── planType: string ("free" | "basic" | "professional" | "enterprise")
│   ├── status: string ("active" | "canceled" | "expired" | "trial")
│   ├── startDate: number (timestamp in milliseconds)
│   ├── endDate: number (timestamp in milliseconds)
│   ├── renewalDate: number (timestamp in milliseconds)
│   ├── paymentMethod: string ("stripe" | "none")
│   └── billingCycle: string ("monthly" | "annual" | "quarterly")
├── usage/
│   ├── currentPeriod/
│   │   ├── transcriptionMinutes: number
│   │   ├── translationWords: number
│   │   ├── ttsMinutes: number
│   │   ├── aiCredits: number
│   │   └── resetDate: number (timestamp)
│   ├── totalUsage/
│   │   ├── transcriptionMinutes: number
│   │   ├── translationWords: number
│   │   ├── ttsMinutes: number
│   │   └── aiCredits: number
│   └── lastResetAt: number (timestamp)
└── billing/
    ├── payAsYouGo/
    │   ├── unitsRemaining/
    │   │   ├── transcriptionMinutes: number
    │   │   ├── translationWords: number
    │   │   ├── ttsMinutes: number
    │   │   └── aiCredits: number
    │   └── purchaseHistory: array
    └── stripeCustomerId: string (optional)
```

#### Subscription Plans Schema
```
/subscriptionPlans/{planId}/
├── id: string
├── name: string
├── price: number
├── transcriptionMinutes: number
├── translationWords: number
├── ttsMinutes: number
├── aiCredits: number
├── transcriptionModel: string
└── isActive: boolean
```

#### Usage History Schema
```
/usage/history/{YYYY-MM}/{userId}/
├── transcriptionMinutes: number
├── translationWords: number
├── ttsMinutes: number
├── aiCredits: number
├── resetDate: number
├── archivedAt: number
└── planType: string
```

### 2. Stripe Database Structure

#### Customer Object
```json
{
  "id": "cus_...",
  "email": "user@example.com",
  "metadata": {
    "app": "vocallocal",
    "firebase_user_id": "user@example,com"
  }
}
```

#### Subscription Object
```json
{
  "id": "sub_...",
  "customer": "cus_...",
  "status": "active",
  "metadata": {
    "user_email": "user@example.com",
    "plan_type": "basic"
  },
  "items": {
    "data": [{
      "price": {
        "id": "price_...",
        "unit_amount": 499,
        "currency": "usd"
      }
    }]
  }
}
```

#### Invoice Object
```json
{
  "id": "in_...",
  "customer": "cus_...",
  "subscription": "sub_...",
  "amount_paid": 499,
  "currency": "usd",
  "status": "paid",
  "metadata": {
    "service": "vocallocal_subscription",
    "plan_type": "basic"
  }
}
```

## Data Flow & Relationships

### 1. User Registration Flow
1. User registers → Firebase user account created with `planType: "free"`
2. User data stored in `/users/{email.replace('.', ',')}/`
3. Default usage limits applied based on free plan

### 2. Payment Flow
1. User clicks upgrade → Stripe customer created/retrieved
2. Checkout session created with plan metadata
3. Payment processed → Webhook triggers subscription update
4. Firebase subscription data updated via `UserAccountService.update_subscription()`

### 3. Subscription Status Synchronization
- **Primary Source**: Stripe (for billing and payment status)
- **Secondary Source**: Firebase (for application logic and usage tracking)
- **Sync Method**: Stripe webhooks update Firebase data

## Key Service Classes

### UserAccountService
**File**: `services/user_account_service.py`
**Purpose**: Manages Firebase user account data

**Key Methods**:
- `create_user_account()`: Creates new user with default free plan
- `update_subscription()`: Updates subscription data in Firebase
- `get_user_account()`: Retrieves user account data
- `track_usage()`: Records service usage

### PaymentService
**File**: `services/payment_service.py`
**Purpose**: Handles Stripe integration

**Key Methods**:
- `create_checkout_session()`: Creates Stripe checkout session
- `check_existing_subscription()`: Validates existing subscriptions
- `handle_webhook_event()`: Processes Stripe webhook events
- `get_customer_by_email()`: Retrieves Stripe customer

## Current Issues Identified

### 1. Subscription Checking Logic Issue
**Problem**: `check_existing_subscription()` only checks Stripe, not Firebase
**Impact**: Users may have Firebase subscription data but no Stripe subscription
**Location**: `services/payment_service.py:592-638`

### 2. Dashboard Plan Display Issue
**Problem**: Dashboard relies on Firebase data which may be out of sync
**Impact**: Users see incorrect plan status
**Location**: `routes/main.py:717-732`

### 3. Data Synchronization Gap
**Problem**: No automatic sync between Stripe and Firebase subscription status
**Impact**: Inconsistent subscription state across systems

## Recommended Fixes

1. **Enhanced Subscription Checking**: Check both Stripe AND Firebase data
2. **Improved Dashboard Logic**: Prioritize Stripe data over Firebase for active subscriptions
3. **Sync Service**: Create service to synchronize Stripe and Firebase subscription data
4. **Webhook Enhancement**: Ensure all Stripe events properly update Firebase

## Environment Variables

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_BASIC_PRICE_ID=price_...
STRIPE_PROFESSIONAL_PRICE_ID=price_...

# Firebase Configuration
FIREBASE_DATABASE_URL=https://...firebaseio.com
FIREBASE_STORAGE_BUCKET=...appspot.com
```

## Security Considerations

1. **Firebase Rules**: Restrict subscription data access to user and admins
2. **Stripe Webhooks**: Verify webhook signatures to prevent tampering
3. **User ID Mapping**: Email addresses converted to Firebase-safe keys (dots → commas)
4. **Metadata Validation**: Ensure plan types match allowed values

This documentation provides the foundation for understanding and fixing the current payment system issues.
