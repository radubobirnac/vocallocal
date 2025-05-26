# Firebase User Account Structure for VocalLocal

This document describes the Firebase Realtime Database structure for user accounts in the VocalLocal application.

## Overview

The user account structure is designed to store user profiles, subscription information, usage tracking, and billing details. It follows a hierarchical structure with the following main components:

1. User Profile
2. User Subscription
3. Current Period Usage
4. Lifetime Usage
5. Pay-As-You-Go Billing

## Database Structure

### 1. User Profile

**Path**: `/users/{userId}/profile`

**Fields**:
- `email` (string): User's email address
- `displayName` (string): User's display name
- `createdAt` (timestamp): Account creation date
- `lastLoginAt` (timestamp): Last login date
- `status` (string): Account status (e.g., "active", "suspended", "inactive")

### 2. User Subscription

**Path**: `/users/{userId}/subscription`

**Fields**:
- `planType` (string): Type of subscription plan (e.g., "free", "basic", "premium", "enterprise")
- `status` (string): Subscription status (e.g., "active", "canceled", "expired", "trial")
- `startDate` (timestamp): Subscription start date
- `endDate` (timestamp): Subscription end date
- `renewalDate` (timestamp): Next renewal date
- `paymentMethod` (string): Payment method used
- `billingCycle` (string): Billing frequency (e.g., "monthly", "annual", "quarterly")

### 3. Current Period Usage

**Path**: `/users/{userId}/usage/currentPeriod`

**Fields**:
- `transcriptionMinutes` (number): Minutes of audio transcribed in current period
- `translationWords` (number): Number of words translated in current period
- `ttsMinutes` (number): Minutes of text-to-speech generated in current period
- `aiCredits` (number): AI credits used in current period
- `resetDate` (timestamp): Date when usage counters will reset

### 4. Lifetime Usage

**Path**: `/users/{userId}/usage/totalUsage`

**Fields**:
- `transcriptionMinutes` (number): Total minutes of audio transcribed
- `translationWords` (number): Total number of words translated
- `ttsMinutes` (number): Total minutes of text-to-speech generated
- `aiCredits` (number): Total AI credits used

### 5. Pay-As-You-Go Billing

**Path**: `/users/{userId}/billing/payAsYouGo`

**Fields**:
- `unitsRemaining` (object): Remaining units by service type
  - `transcriptionMinutes` (number)
  - `translationWords` (number)
  - `ttsMinutes` (number)
  - `aiCredits` (number)
- `purchaseHistory` (array): List of previous purchases
  - Each entry contains: `date`, `amount`, `serviceType`, `unitsPurchased`

## Usage Examples

### Creating a New User Account

```javascript
// Client-side JavaScript
const userId = firebase.auth().currentUser.uid;
const email = firebase.auth().currentUser.email;
const displayName = firebase.auth().currentUser.displayName;

// Initialize user account
userAccountService.initializeUserAccount(userId, email, displayName)
  .then(account => {
    console.log('User account created:', account);
  })
  .catch(error => {
    console.error('Error creating user account:', error);
  });
```

### Tracking Usage

```javascript
// Client-side JavaScript
const userId = firebase.auth().currentUser.uid;

// Track 5 minutes of transcription
userAccountService.trackUsage(userId, 'transcriptionMinutes', 5)
  .then(result => {
    console.log('Usage tracked:', result);
  })
  .catch(error => {
    console.error('Error tracking usage:', error);
  });
```

### Checking Available Units

```javascript
// Client-side JavaScript
const userId = firebase.auth().currentUser.uid;

// Check if user has enough transcription minutes
userAccountService.checkSufficientUnits(userId, 'transcriptionMinutes', 10)
  .then(isAvailable => {
    if (isAvailable) {
      console.log('User has enough transcription minutes');
    } else {
      console.log('User does not have enough transcription minutes');
    }
  })
  .catch(error => {
    console.error('Error checking available units:', error);
  });
```

## Firebase Security Rules

The database is secured with rules that:

1. Allow users to read and write only their own data
2. Validate data structure and field types
3. Allow administrators to manage all user accounts
4. Prevent unauthorized access to sensitive information

See the `firebase-rules.json` file for the complete security rules configuration.

## TypeScript Interfaces

TypeScript interfaces for these data structures are available in the `static/types/user-account.d.ts` file. These interfaces provide type safety when accessing the database from TypeScript code.

## Cloud Functions

Firebase Cloud Functions are used to validate usage against available limits:

1. `validateTranscriptionMinutes`: Checks if a user has enough transcription minutes
2. `validateTranslationWords`: Checks if a user has enough translation words
3. `validateTtsMinutes`: Checks if a user has enough text-to-speech minutes
4. `validateAiCredits`: Checks if a user has enough AI credits

These functions are defined in the `firebase-functions/usage-validation.js` file.
