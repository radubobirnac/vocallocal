# Firebase Cloud Functions Setup Guide for VocalLocal

This guide provides step-by-step instructions for setting up and deploying the Firebase Cloud Functions for usage validation in the VocalLocal application.

## Prerequisites

Before you begin, make sure you have:

1. A Firebase project created in the [Firebase Console](https://console.firebase.google.com/)
2. Node.js and npm installed on your computer
3. Firebase CLI installed (`npm install -g firebase-tools`)

## Step 1: Firebase Project Setup

### 1.1. Create or Select a Firebase Project

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" or select your existing VocalLocal project
3. Follow the setup wizard if creating a new project

### 1.2. Enable Billing (Required for Cloud Functions)

1. In the Firebase Console, click on "Upgrade" to select a billing plan
2. Choose the "Blaze" (pay-as-you-go) plan
   - This is required for Cloud Functions, but there's a generous free tier
   - You won't be charged unless you exceed the free tier limits

### 1.3. Enable Realtime Database

1. In the Firebase Console, go to "Build" > "Realtime Database"
2. Click "Create Database"
3. Choose a location (preferably close to your users)
4. Start in test mode, we'll update the security rules later

## Step 2: Local Setup

### 2.1. Login to Firebase from CLI

Open a terminal and run:

```bash
firebase login
```

This will open a browser window to authenticate with your Google account.

### 2.2. Initialize Firebase in Your Project

Navigate to your project directory and run:

```bash
cd git_vocal_local
firebase init
```

When prompted:
1. Select "Functions" (use spacebar to select, then Enter)
2. Select your Firebase project
3. Choose JavaScript for the language
4. Say "Yes" to ESLint
5. Say "Yes" to installing dependencies

This will create a `functions` directory with the necessary configuration files.

### 2.3. Copy the Cloud Functions Files

Copy the files from `git_vocal_local/vocallocal/firebase-functions/` to the newly created `functions` directory:

```bash
cp vocallocal/firebase-functions/usage-validation-functions.js functions/
cp vocallocal/firebase-functions/index.js functions/
```

Or manually copy:
- `usage-validation-functions.js`
- `index.js`

Note: You can replace the existing `index.js` file that was created during initialization.

## Step 3: Update Security Rules

### 3.1. Copy Security Rules to Firebase Console

1. Go to the Firebase Console > "Build" > "Realtime Database"
2. Click on the "Rules" tab
3. Copy the content from `git_vocal_local/vocallocal/firebase-security-rules.json`
4. Paste it into the rules editor in the Firebase Console
5. Click "Publish"

### 3.2. Important Note About Indexes

The security rules include indexes for the following collections:
- `transcripts` with indexes on `timestamp` and `user_email`
- `transcriptions` with indexes on `timestamp` and `user_email`, and a nested index on `timestamp` for each user
- `translations` with indexes on `timestamp` and `user_email`, and a nested index on `timestamp` for each user

These indexes are required for the application to properly sort and query data. If you encounter errors like:
```
Index not defined, add ".indexOn": "timestamp", for path "/transcriptions/user@example,com", to the rules
```
Make sure the security rules have been properly published with all the required indexes.

## Step 4: Deploy Cloud Functions

### 4.1. Deploy the Functions

From your project directory, run:

```bash
cd functions
npm install
firebase deploy --only functions
```

This will deploy all the Cloud Functions to Firebase.

### 4.2. Verify Deployment

1. Go to the Firebase Console > "Build" > "Functions"
2. You should see all the functions listed:
   - validateTranscriptionUsage
   - validateTranslationUsage
   - validateTTSUsage
   - validateAICredits
   - trackUsage
   - deductUsage
   - deductTranscriptionUsage
   - deductTranslationUsage
   - deductTTSUsage
   - deductAICredits

## Step 5: Set Up Admin Users

For admin functionality to work, you need to create admin users in your database:

1. Go to the Firebase Console > "Build" > "Realtime Database"
2. Click on the "Data" tab
3. Create a new node called "admins"
4. Add your admin user's UID as a child node with the value `true`

Example structure:
```
/admins/
  YOUR_ADMIN_USER_UID: true
```

To find a user's UID:
1. Go to Firebase Console > "Build" > "Authentication"
2. Click on the "Users" tab
3. Find the user and copy their UID

## Step 6: Initialize Subscription Plans

If you haven't already set up subscription plans, run the initialization script:

```bash
cd git_vocal_local/vocallocal
python initialize_subscription_plans.py
```

This will create the default subscription plans in your Firebase Realtime Database.

## Step 7: Client-Side Integration

### 7.1. Web Client (JavaScript)

Add this code to your client-side JavaScript to call the Cloud Functions:

```javascript
// Initialize Firebase (you should already have this)
const firebaseConfig = {
  // Your Firebase config
};
firebase.initializeApp(firebaseConfig);

// Get a reference to the functions
const functions = firebase.functions();

// Example: Validate transcription usage
async function checkTranscriptionAvailability(userId, minutes) {
  try {
    const validateTranscriptionUsage = functions.httpsCallable('validateTranscriptionUsage');
    const result = await validateTranscriptionUsage({
      userId: userId,
      minutesRequested: minutes
    });

    const validationResult = result.data;
    if (validationResult.allowed) {
      console.log(`You have ${validationResult.remaining} minutes remaining.`);
      return true;
    } else {
      console.log(`Not enough minutes available. You need to upgrade your plan.`);
      return false;
    }
  } catch (error) {
    console.error('Error validating transcription usage:', error);
    return false;
  }
}

// Example: Track usage after transcription
async function recordTranscriptionUsage(userId, minutes) {
  try {
    const trackUsage = functions.httpsCallable('trackUsage');
    await trackUsage({
      userId: userId,
      serviceType: 'transcription',
      amount: minutes
    });
    console.log(`Recorded ${minutes} minutes of transcription usage.`);
  } catch (error) {
    console.error('Error tracking usage:', error);
  }
}
```

### 7.2. Python Client

For server-side Python code, use the Firebase Admin SDK:

```python
import firebase_admin
from firebase_admin import credentials, functions

# Initialize Firebase Admin SDK (you should already have this)
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Example: Validate transcription usage
def check_transcription_availability(user_id, minutes):
    try:
        validate_function = functions.https_fn.call('validateTranscriptionUsage', {
            'userId': user_id,
            'minutesRequested': minutes
        })

        validation_result = validate_function
        if validation_result.get('allowed'):
            print(f"User has {validation_result.get('remaining')} minutes remaining.")
            return True
        else:
            print("Not enough minutes available. User needs to upgrade their plan.")
            return False
    except Exception as e:
        print(f"Error validating transcription usage: {e}")
        return False
```

## Troubleshooting

### Function Deployment Errors

If you encounter errors during deployment:

1. Check the Firebase CLI output for specific error messages
2. Verify that you've enabled billing on your Firebase project
3. Make sure your `package.json` has the correct dependencies
4. Check the Firebase Console > "Functions" > "Logs" for detailed error logs

### Function Execution Errors

If functions fail when called:

1. Check the Firebase Console > "Functions" > "Logs" for error messages
2. Verify that your security rules are correctly set up
3. Ensure that the database structure matches what the functions expect
4. Check that users have the correct permissions

### Security Rules Errors

If security rules aren't working as expected:

1. Use the Rules Playground in the Firebase Console to test different scenarios
2. Check for syntax errors in your rules JSON
3. Verify that the paths in the rules match your actual database structure

## Additional Resources

- [Firebase Cloud Functions Documentation](https://firebase.google.com/docs/functions)
- [Firebase Realtime Database Documentation](https://firebase.google.com/docs/database)
- [Firebase Security Rules Documentation](https://firebase.google.com/docs/database/security)

## Next Steps

After setting up the Cloud Functions:

1. Implement client-side validation before performing operations
2. Track usage after successful operations
3. Display usage information to users
4. Implement upgrade prompts when users are approaching their limits

These Cloud Functions provide the backend infrastructure for managing usage limits in your VocalLocal application. With proper integration, they ensure that users can only use resources they have available and provide clear feedback when they need to upgrade their plan.
