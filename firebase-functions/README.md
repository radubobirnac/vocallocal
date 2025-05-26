# Firebase Cloud Functions for Usage Validation

This document explains the Firebase Cloud Functions for usage validation in the VocalLocal application.

## Overview

These Cloud Functions validate user requests against their available usage limits and subscription plans. They ensure that users have sufficient resources (transcription minutes, translation words, TTS minutes, AI credits) before allowing operations that consume these resources.

## Functions

### 1. `validateTranscriptionUsage`

Validates if a user has sufficient transcription minutes available.

**Parameters:**
- `userId` (string): The user ID to validate
- `minutesRequested` (number): The number of minutes requested

**Returns:**
```json
{
  "allowed": boolean,
  "remaining": number,
  "planType": string,
  "upgradeRequired": boolean,
  "error": {
    "code": string,
    "message": string,
    "details": string
  }
}
```

### 2. `validateTranslationUsage`

Validates if a user has sufficient translation words available.

**Parameters:**
- `userId` (string): The user ID to validate
- `wordsRequested` (number): The number of words requested

**Returns:** Same structure as `validateTranscriptionUsage`

### 3. `validateTTSUsage`

Validates if a user has sufficient text-to-speech minutes available.

**Parameters:**
- `userId` (string): The user ID to validate
- `minutesRequested` (number): The number of minutes requested

**Returns:** Same structure as `validateTranscriptionUsage`

### 4. `validateAICredits`

Validates if a user has sufficient AI credits available.

**Parameters:**
- `userId` (string): The user ID to validate
- `creditsRequested` (number): The number of AI credits requested

**Returns:** Same structure as `validateTranscriptionUsage`

### 5. `trackUsage`

Tracks usage for a specific service.

**Parameters:**
- `userId` (string): The user ID to track usage for
- `serviceType` (string): The type of service ('transcription', 'translation', 'tts', 'ai')
- `amount` (number): The amount to track

**Returns:**
```json
{
  "success": boolean,
  "currentPeriodUsage": number,
  "totalUsage": number,
  "error": {
    "code": string,
    "message": string,
    "details": string
  }
}
```

### 6. `deductUsage`

Deducts usage from a user's account, intelligently choosing between subscription plan allocation and pay-as-you-go balance.

**Parameters:**
- `userId` (string): The user ID to deduct usage from
- `serviceType` (string): The type of service ('transcription', 'translation', 'tts', 'ai')
- `amount` (number): The amount to deduct

**Returns:**
```json
{
  "success": boolean,
  "deducted": number,
  "fromPlan": number,
  "fromPayg": number,
  "remainingPlan": number,
  "remainingPayg": number,
  "error": {
    "code": string,
    "message": string,
    "details": string
  }
}
```

### 7. `deductTranscriptionUsage`

Deducts transcription minutes from a user's account using atomic transactions.

**Parameters:**
- `userId` (string): The user ID to deduct usage from
- `minutesUsed` (number): The number of minutes to deduct

**Returns:**
```json
{
  "success": boolean,
  "deducted": number,
  "currentPeriodUsage": number,
  "totalUsage": number,
  "serviceType": "transcription",
  "error": {
    "code": string,
    "message": string,
    "details": string
  }
}
```

### 8. `deductTranslationUsage`

Deducts translation words from a user's account using atomic transactions.

**Parameters:**
- `userId` (string): The user ID to deduct usage from
- `wordsUsed` (number): The number of words to deduct

**Returns:** Same structure as `deductTranscriptionUsage` with `serviceType: "translation"`

### 9. `deductTTSUsage`

Deducts TTS minutes from a user's account using atomic transactions.

**Parameters:**
- `userId` (string): The user ID to deduct usage from
- `minutesUsed` (number): The number of minutes to deduct

**Returns:** Same structure as `deductTranscriptionUsage` with `serviceType: "tts"`

### 10. `deductAICredits`

Deducts AI credits from a user's account using atomic transactions.

**Parameters:**
- `userId` (string): The user ID to deduct usage from
- `creditsUsed` (number): The number of credits to deduct

**Returns:** Same structure as `deductTranscriptionUsage` with `serviceType: "ai"`

## Deployment

To deploy these functions to Firebase:

1. Install the Firebase CLI:
   ```
   npm install -g firebase-tools
   ```

2. Login to Firebase:
   ```
   firebase login
   ```

3. Initialize Firebase in your project (if not already done):
   ```
   firebase init functions
   ```

4. Copy the `usage-validation-functions.js` file to your functions directory.

5. Deploy the functions:
   ```
   firebase deploy --only functions
   ```

## Client-Side Usage

### Web Client (JavaScript)

```javascript
// Initialize Firebase
const app = firebase.initializeApp(firebaseConfig);
const functions = firebase.functions();

// Validate transcription usage
async function validateTranscription(userId, minutes) {
  try {
    const validateTranscriptionUsage = firebase.functions().httpsCallable('validateTranscriptionUsage');
    const result = await validateTranscriptionUsage({
      userId: userId,
      minutesRequested: minutes
    });

    return result.data;
  } catch (error) {
    console.error('Error validating transcription usage:', error);
    throw error;
  }
}

// Track usage
async function trackTranscriptionUsage(userId, minutes) {
  try {
    const trackUsage = firebase.functions().httpsCallable('trackUsage');
    const result = await trackUsage({
      userId: userId,
      serviceType: 'transcription',
      amount: minutes
    });

    return result.data;
  } catch (error) {
    console.error('Error tracking usage:', error);
    throw error;
  }
}

// Deduct usage
async function deductTranscriptionUsage(userId, minutes) {
  try {
    const deductUsage = firebase.functions().httpsCallable('deductUsage');
    const result = await deductUsage({
      userId: userId,
      serviceType: 'transcription',
      amount: minutes
    });

    return result.data;
  } catch (error) {
    console.error('Error deducting usage:', error);
    throw error;
  }
}
```

### Python Client

```python
import firebase_admin
from firebase_admin import credentials, functions

# Initialize Firebase Admin SDK
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Validate transcription usage
def validate_transcription(user_id, minutes):
    try:
        validate_function = functions.https_fn.call('validateTranscriptionUsage', {
            'userId': user_id,
            'minutesRequested': minutes
        })
        return validate_function
    except Exception as e:
        print(f"Error validating transcription usage: {e}")
        raise e

# Track usage
def track_transcription_usage(user_id, minutes):
    try:
        track_function = functions.https_fn.call('trackUsage', {
            'userId': user_id,
            'serviceType': 'transcription',
            'amount': minutes
        })
        return track_function
    except Exception as e:
        print(f"Error tracking usage: {e}")
        raise e
```

## Security Considerations

1. **Authentication**: All functions require authentication. Users can only validate and track their own usage unless they are admins.

2. **Admin Access**: Admin users can validate, track, and deduct usage for any user.

3. **Error Handling**: All functions include proper error handling and return standardized error responses.

4. **Logging**: All functions include logging for debugging and monitoring.

5. **Data Validation**: All functions validate input data before processing.

## Monthly Usage Reset Functions

### 11. `resetMonthlyUsage`

Resets monthly usage for all users and archives previous month's data.

**Parameters:**
- `forceReset` (boolean, optional): Force reset even if reset date hasn't passed

**Returns:**
```json
{
  "success": boolean,
  "message": string,
  "usersProcessed": number,
  "usersSkipped": number,
  "errors": [{"userId": string, "error": string}],
  "archiveMonth": string,
  "totalUsageArchived": {
    "transcriptionMinutes": number,
    "translationWords": number,
    "ttsMinutes": number,
    "aiCredits": number
  }
}
```

### 12. `resetMonthlyUsageHTTP`

HTTP trigger for external cron services to trigger monthly reset.

**HTTP Method:** POST
**Headers:**
- `x-reset-token`: Secret token for authentication

**Body:**
```json
{
  "token": string,        // Alternative to header
  "forceReset": boolean   // Optional
}
```

### 13. `getUsageStatistics`

Returns current usage statistics across all users (admin only).

**Returns:**
```json
{
  "success": boolean,
  "statistics": {
    "totalUsers": number,
    "currentPeriodUsage": {
      "transcriptionMinutes": number,
      "translationWords": number,
      "ttsMinutes": number,
      "aiCredits": number
    },
    "usersNeedingReset": number,
    "planDistribution": {
      "free": number,
      "basic": number,
      "professional": number
    },
    "nextResetDate": number
  }
}
```

### 14. `checkAndResetUsage`

Checks if users need usage reset and optionally triggers it.

**Returns:**
```json
{
  "success": boolean,
  "resetTriggered": boolean,
  "usersNeedingReset": number,
  "resetResult": object,     // If reset was triggered
  "userReset": boolean,      // If individual user reset
  "archivedUsage": object    // Archived usage data
}
```

## Database Structure

These functions work with the following database structure:

```
/users/{userId}/
  subscription/
    planType: string
    status: string

  usage/
    currentPeriod/
      transcriptionMinutes: number
      translationWords: number
      ttsMinutes: number
      aiCredits: number
      resetDate: number

    totalUsage/
      transcriptionMinutes: number
      translationWords: number
      ttsMinutes: number
      aiCredits: number

    lastResetAt: number

  billing/
    payAsYouGo/
      unitsRemaining/
        transcriptionMinutes: number
        translationWords: number
        ttsMinutes: number
        aiCredits: number

/usage/history/{YYYY-MM}/{userId}/
  transcriptionMinutes: number
  translationWords: number
  ttsMinutes: number
  aiCredits: number
  resetDate: number
  archivedAt: number
  planType: string

/subscriptionPlans/{planId}/
  transcriptionMinutes: number
  translationWords: number
  ttsMinutes: number
  aiCredits: number

/admins/{userId}: boolean
```

## Testing

You can test these functions using the Firebase Emulator Suite:

1. Install the Firebase Emulator Suite:
   ```
   firebase setup:emulators:functions
   ```

2. Start the emulators:
   ```
   firebase emulators:start
   ```

3. Use the Firebase Console Functions tab to test the functions with sample data.
