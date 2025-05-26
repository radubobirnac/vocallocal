# Firebase Setup Guide for VocalLocal (Free Spark Plan)

This guide provides step-by-step instructions for setting up Firebase for the VocalLocal application using the free Spark plan, without upgrading to the Blaze plan or enabling Cloud Functions.

## 1. Firebase Console Setup

### 1.1. Create or Access Your Firebase Project

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Sign in with your Google account
3. Select your existing "vocal-local-e1e70" project or create a new project

### 1.2. Set Up Realtime Database

1. In the Firebase Console, click on "Build" in the left sidebar
2. Select "Realtime Database"
3. Click "Create Database" if you haven't already
4. Choose a location (preferably close to your users)
5. Start in test mode, we'll update the security rules later

### 1.3. Update Security Rules

1. In the Realtime Database section, click on the "Rules" tab
2. Copy the content from your `firebase-security-rules.json` file
3. Paste it into the rules editor
4. Click "Publish" to make the rules active

### 1.4. Set Up Authentication

1. In the left sidebar, click on "Build" > "Authentication"
2. Click "Get Started" if you haven't already
3. Enable the sign-in methods you want to use (Email/Password, Google, etc.)
4. Set up your authorized domains if needed

### 1.5. Create Admin Users (Optional)

1. In the Authentication section, find a user you want to make an admin
2. Copy their UID (User ID)
3. Go to the Realtime Database, navigate to the "Data" tab
4. Manually create an "admins" node
5. Add the user's UID as a child with the value `true`
6. Example: `/admins/YOUR_ADMIN_USER_UID: true`

## 2. Initialize Subscription Plans

### 2.1. Run the Initialization Script

1. Make sure your Firebase configuration is set up in your `.env` file:
   ```
   FIREBASE_DATABASE_URL=https://vocal-local-e1e70-default-rtdb.firebaseio.com
   FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
   ```

2. Run the initialization script:
   ```bash
   cd git_vocal_local/vocallocal
   python initialize_subscription_plans.py
   ```

3. This will create the default subscription plans in your Firebase Realtime Database.

## 3. Client-Side Implementation

Since you're using the free Spark plan, you'll need to implement the validation logic directly in your client-side code. Here's how to do it:

### 3.1. Create a Client-Side Validation Service

Create a new file `static/js/usage-validation.js` with the following content:

```javascript
/**
 * Client-side usage validation for VocalLocal
 * 
 * This module provides functions to validate and track usage without Cloud Functions.
 */

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDQpgqsQIYXvZUPCIWpIFG-wHGAZ1_7MKs",
  authDomain: "vocal-local-e1e70.firebaseapp.com",
  databaseURL: "https://vocal-local-e1e70-default-rtdb.firebaseio.com",
  projectId: "vocal-local-e1e70",
  storageBucket: "vocal-local-e1e70.appspot.com",
  messagingSenderId: "1082430804880",
  appId: "1:1082430804880:web:9a3e6a3b6fd3e3a6a6a6a6"
};

// Initialize Firebase if not already initialized
if (!firebase.apps.length) {
  firebase.initializeApp(firebaseConfig);
}

/**
 * Validate if a user has sufficient transcription minutes available
 * 
 * @param {string} userId - The user ID to validate
 * @param {number} minutesRequested - The number of minutes requested
 * @returns {Promise<Object>} - Validation response
 */
async function validateTranscriptionUsage(userId, minutesRequested) {
  try {
    // Get user data
    const userRef = firebase.database().ref(`users/${userId}`);
    const userSnapshot = await userRef.once('value');
    const userData = userSnapshot.val();
    
    if (!userData) {
      return {
        allowed: false,
        remaining: 0,
        planType: 'none',
        upgradeRequired: true,
        error: {
          code: 'not-found',
          message: 'User data not found'
        }
      };
    }
    
    // Get subscription plan
    const subscription = userData.subscription || {};
    const planType = subscription.status === 'active' ? subscription.planType : 'free';
    
    // Get plan details
    const planRef = firebase.database().ref(`subscriptionPlans/${planType}`);
    const planSnapshot = await planRef.once('value');
    const planData = planSnapshot.val();
    
    if (!planData) {
      return {
        allowed: false,
        remaining: 0,
        planType: planType,
        upgradeRequired: true,
        error: {
          code: 'plan-not-found',
          message: 'Subscription plan not found'
        }
      };
    }
    
    // Get current usage
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
    
    return {
      allowed,
      remaining,
      planType,
      upgradeRequired
    };
  } catch (error) {
    console.error('Error validating transcription usage:', error);
    
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
}

/**
 * Track usage for a specific service
 * 
 * @param {string} userId - The user ID to track usage for
 * @param {string} serviceType - The type of service (transcription, translation, tts, ai)
 * @param {number} amount - The amount to track
 * @returns {Promise<Object>} - Updated usage data
 */
async function trackUsage(userId, serviceType, amount) {
  try {
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

    // Get current usage
    const userRef = firebase.database().ref(`users/${userId}`);
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

    await firebase.database().ref().update(updates);

    return {
      success: true,
      currentPeriodUsage: newCurrentPeriodUsage,
      totalUsage: newTotalUsage
    };
  } catch (error) {
    console.error('Error tracking usage:', error);
    
    return {
      success: false,
      error: {
        code: 'internal-error',
        message: 'An error occurred while tracking usage',
        details: error.message
      }
    };
  }
}

// Export functions for use in other modules
window.usageValidation = {
  validateTranscriptionUsage,
  trackUsage
};
```

### 3.2. Include the Script in Your HTML

Add this script to your main HTML templates:

```html
<!-- Firebase SDK -->
<script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js"></script>
<script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-database.js"></script>
<script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-auth.js"></script>

<!-- Usage Validation -->
<script src="{{ url_for('static', filename='js/usage-validation.js') }}"></script>
```

### 3.3. Use the Validation Functions

Use these functions in your application code:

```javascript
// Example: Check if user has enough transcription minutes
async function checkTranscriptionAvailability(userId, minutes) {
  const result = await window.usageValidation.validateTranscriptionUsage(userId, minutes);
  
  if (result.allowed) {
    console.log(`You have ${result.remaining} minutes remaining.`);
    return true;
  } else {
    console.log(`Not enough minutes available. You need to upgrade your plan.`);
    return false;
  }
}

// Example: Track usage after transcription
async function recordTranscriptionUsage(userId, minutes) {
  const result = await window.usageValidation.trackUsage(userId, 'transcription', minutes);
  
  if (result.success) {
    console.log(`Recorded ${minutes} minutes of transcription usage.`);
  } else {
    console.error('Error tracking usage:', result.error);
  }
}
```

## 4. Server-Side Implementation (Optional)

If you need to validate usage on the server side, you can implement similar logic in your Python code using the Firebase Admin SDK.

## 5. Testing

1. Create a test user account
2. Initialize their subscription plan and usage data
3. Test the validation functions to ensure they correctly check available resources
4. Test the tracking functions to ensure they correctly update usage data

## Conclusion

This setup allows you to implement usage validation and tracking without using Firebase Cloud Functions, which are not available on the free Spark plan. The security rules you've already created will ensure that users can only access their own data and cannot manipulate their usage limits.
