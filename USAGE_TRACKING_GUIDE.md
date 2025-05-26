# VocalLocal Usage Tracking Guide

This guide explains the Firebase Cloud Functions for usage tracking in the VocalLocal application, specifically designed to work with Firebase's free plan.

## Overview

The VocalLocal application includes comprehensive usage tracking functions that:

- ✅ **Work with Firebase Free Plan** - Uses Realtime Database, not Firestore
- ✅ **Atomic Transactions** - Ensures data consistency using Firebase transactions
- ✅ **Error Handling** - Comprehensive error handling and logging
- ✅ **Real-time Updates** - Updates both currentPeriod and totalUsage counters
- ✅ **Authentication** - Secure access control with admin permissions
- ✅ **Type-specific Functions** - Dedicated functions for each service type

## Available Functions

### 1. Specific Deduct Functions

#### `deductTranscriptionUsage(userId, minutesUsed)`
- **Purpose**: Deduct transcription minutes from user account
- **Parameters**: 
  - `userId` (string): User ID to deduct from
  - `minutesUsed` (number): Minutes to deduct
- **Updates**: currentPeriod.transcriptionMinutes, totalUsage.transcriptionMinutes

#### `deductTranslationUsage(userId, wordsUsed)`
- **Purpose**: Deduct translation words from user account
- **Parameters**: 
  - `userId` (string): User ID to deduct from
  - `wordsUsed` (number): Words to deduct
- **Updates**: currentPeriod.translationWords, totalUsage.translationWords

#### `deductTTSUsage(userId, minutesUsed)`
- **Purpose**: Deduct TTS minutes from user account
- **Parameters**: 
  - `userId` (string): User ID to deduct from
  - `minutesUsed` (number): Minutes to deduct
- **Updates**: currentPeriod.ttsMinutes, totalUsage.ttsMinutes

#### `deductAICredits(userId, creditsUsed)`
- **Purpose**: Deduct AI credits from user account
- **Parameters**: 
  - `userId` (string): User ID to deduct from
  - `creditsUsed` (number): Credits to deduct
- **Updates**: currentPeriod.aiCredits, totalUsage.aiCredits

### 2. Generic Functions

#### `deductUsage(userId, serviceType, amount)`
- **Purpose**: Generic deduction function with intelligent plan/payg handling
- **Parameters**: 
  - `userId` (string): User ID to deduct from
  - `serviceType` (string): 'transcription', 'translation', 'tts', 'ai'
  - `amount` (number): Amount to deduct

#### `trackUsage(userId, serviceType, amount)`
- **Purpose**: Track usage without plan/payg logic
- **Parameters**: Same as deductUsage

## Key Features

### Atomic Transactions
All functions use Firebase transactions to ensure data consistency:

```javascript
return await userRef.transaction((userData) => {
  if (!userData) {
    return userData; // Abort if user doesn't exist
  }
  
  // Update usage counters atomically
  userData.usage.currentPeriod.transcriptionMinutes = currentUsage + minutesUsed;
  userData.usage.totalUsage.transcriptionMinutes = totalUsage + minutesUsed;
  userData.lastActivityAt = Date.now();
  
  return userData;
});
```

### Error Handling
Comprehensive error handling with specific error codes:

- `unauthenticated` - User not logged in
- `permission-denied` - Insufficient permissions
- `internal-error` - Server-side errors
- `invalid-argument` - Invalid parameters

### Real-time Database Updates
Updates both usage counters simultaneously:

- **currentPeriod**: Usage for current billing period
- **totalUsage**: Lifetime usage totals
- **lastActivityAt**: Timestamp of last activity

## Usage Examples

### Client-Side JavaScript

```javascript
// Include the usage deduction utility
<script src="/static/js/usage-deduction.js"></script>

// Deduct transcription usage after successful transcription
async function afterTranscription(userId, audioDurationMinutes) {
  try {
    const result = await usageDeduction.deductTranscriptionUsage(userId, audioDurationMinutes);
    
    if (result.success) {
      console.log(`Deducted ${result.deducted} minutes`);
      console.log(`Current usage: ${result.currentPeriodUsage}`);
      // Update UI
      updateUsageDisplay('transcription', result.currentPeriodUsage);
    } else {
      console.error('Deduction failed:', result.error);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

// Deduct translation usage after successful translation
async function afterTranslation(userId, translatedText) {
  const wordCount = translatedText.trim().split(/\s+/).length;
  
  const result = await usageDeduction.deductTranslationUsage(userId, wordCount);
  usageDeduction.handleDeductionResult(result, 'translation');
}
```

### Server-Side Python

```python
import firebase_admin
from firebase_admin import functions

# Call Cloud Function from Python
def deduct_transcription_usage(user_id, minutes_used):
    try:
        deduct_function = functions.https_fn.call('deductTranscriptionUsage', {
            'userId': user_id,
            'minutesUsed': minutes_used
        })
        return deduct_function
    except Exception as e:
        print(f"Error deducting usage: {e}")
        raise e
```

### Direct Firebase Function Call

```javascript
// Direct Firebase function call
const deductFunction = firebase.functions().httpsCallable('deductTranscriptionUsage');

const result = await deductFunction({
  userId: 'user123',
  minutesUsed: 5.5
});

if (result.data.success) {
  console.log('Usage deducted successfully');
} else {
  console.error('Error:', result.data.error);
}
```

## Database Structure

The functions update the following Firebase Realtime Database structure:

```
/users/{userId}/
  usage/
    currentPeriod/
      transcriptionMinutes: number
      translationWords: number
      ttsMinutes: number
      aiCredits: number
      resetDate: timestamp
    totalUsage/
      transcriptionMinutes: number
      translationWords: number
      ttsMinutes: number
      aiCredits: number
  lastActivityAt: timestamp
```

## Security

- **Authentication Required**: All functions require user authentication
- **Permission Control**: Users can only deduct their own usage (admins can deduct for any user)
- **Admin Override**: Admin users can deduct usage for any user
- **Firebase Security Rules**: Database protected by comprehensive security rules

## Firebase Free Plan Compatibility

These functions are specifically designed for Firebase's free plan:

- **Uses Realtime Database**: Not Firestore (which has limited free tier)
- **Efficient Operations**: Minimal database reads/writes
- **No External Dependencies**: Uses only Firebase core services
- **Optimized Transactions**: Single transaction per operation

## Deployment

1. **Deploy Functions**:
   ```bash
   cd firebase-functions
   firebase deploy --only functions
   ```

2. **Verify Deployment**:
   - Check Firebase Console > Functions
   - Should see all 10 functions listed

3. **Test Functions**:
   ```javascript
   // Test in browser console
   const result = await firebase.functions()
     .httpsCallable('deductTranscriptionUsage')({
       userId: 'test-user',
       minutesUsed: 1
     });
   console.log(result.data);
   ```

## Integration Points

### After Transcription
```javascript
// In your transcription completion handler
if (transcriptionSuccessful) {
  await usageDeduction.handleTranscriptionComplete(userId, audioDuration);
}
```

### After Translation
```javascript
// In your translation completion handler
if (translationSuccessful) {
  await usageDeduction.handleTranslationComplete(userId, translatedText);
}
```

### After TTS Generation
```javascript
// In your TTS completion handler
if (ttsSuccessful) {
  await usageDeduction.handleTTSComplete(userId, audioLength);
}
```

### After AI Operations
```javascript
// In your AI operation completion handler
if (aiOperationSuccessful) {
  await usageDeduction.handleAIOperationComplete(userId, creditsUsed);
}
```

## Monitoring and Logging

All functions include comprehensive logging:

- **Info Logs**: Successful operations with details
- **Error Logs**: Failed operations with error details
- **Performance Logs**: Transaction timing and results

View logs in Firebase Console > Functions > Logs.

## Files Involved

- `firebase-functions/usage-validation-functions.js` - Main function implementations
- `firebase-functions/index.js` - Function exports
- `static/js/usage-deduction.js` - Client-side utilities
- `firebase-security-rules.json` - Database security rules
- `firebase-functions/README.md` - Detailed function documentation
- `firebase-functions/SETUP-GUIDE.md` - Deployment instructions
