# Firebase Security Rules for VocalLocal

This document explains the Firebase Realtime Database security rules for the VocalLocal application.

## Overview

The security rules implement the following access controls:

1. **User Profile and Subscription Data**:
   - Users can read and write only their own profile data
   - Users can read and write only their own subscription data
   - Validation ensures required fields are present and have correct data types

2. **Usage Data Protection**:
   - Users cannot directly modify their usage data
   - Usage data is read-only for the user who owns it
   - Only server-side processes (using admin authentication) can write to usage data

3. **Subscription Plans Access**:
   - All authenticated users can read subscription plans
   - Only admin users can write to subscription plans
   - Validation is included for subscription plan fields

4. **Billing Data Security**:
   - Billing data is readable only by the authenticated user who owns it
   - Regular users cannot directly modify billing data
   - Admin users can update billing information

## File Structure

Two versions of the security rules are provided:

1. `firebase-security-rules.json`: Contains comments explaining each section (use in Firebase Console)
2. `firebase-security-rules-no-comments.json`: Version without comments (for programmatic use)

## How to Apply the Rules

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Navigate to "Realtime Database" in the left sidebar
4. Click on the "Rules" tab
5. Copy the content from `firebase-security-rules.json` (with comments)
6. Paste it into the rules editor
7. Click "Publish" to apply the rules

## Admin Users

The rules rely on an `admins` node in the database to identify admin users. To set up an admin user:

1. Create a node at `/admins/{userId}` where `{userId}` is the Firebase Auth UID of the admin user
2. Set the value to `true`

Example:
```json
{
  "admins": {
    "user123": true
  }
}
```

## Data Structure

The rules are designed for the following database structure:

### User Data

```
/users/{userId}/
  profile/
    email: string
    displayName: string
    createdAt: number (timestamp)
    lastLoginAt: number (timestamp)
    status: string ("active", "suspended", "inactive")
  
  subscription/
    planType: string ("free", "basic", "professional", "enterprise")
    status: string ("active", "canceled", "expired", "trial")
    startDate: number (timestamp)
    endDate: number (timestamp)
    renewalDate: number (timestamp)
    paymentMethod: string
    billingCycle: string ("monthly", "annual", "quarterly")
  
  usage/
    currentPeriod/
      transcriptionMinutes: number
      translationWords: number
      ttsMinutes: number
      aiCredits: number
      resetDate: number (timestamp)
    
    totalUsage/
      transcriptionMinutes: number
      translationWords: number
      ttsMinutes: number
      aiCredits: number
  
  billing/
    payAsYouGo/
      unitsRemaining/
        transcriptionMinutes: number
        translationWords: number
        ttsMinutes: number
        aiCredits: number
      
      purchaseHistory/
        {purchaseId}/
          date: number (timestamp)
          amount: number
          serviceType: string
          unitsPurchased: number
    
    paymentMethods/
      {methodId}/
        type: string ("credit", "debit", "paypal")
        lastFour: string (4 digits)
        expiryDate: string (MM/YY format)
        isDefault: boolean
    
    invoices/
      {invoiceId}/
        date: number (timestamp)
        amount: number
        status: string ("paid", "pending", "failed")
        items/
          {itemId}/
            description: string
            amount: number
```

### Subscription Plans

```
/subscriptionPlans/{planId}/
  id: string
  name: string
  price: number
  transcriptionMinutes: number
  translationWords: number
  ttsMinutes: number
  aiCredits: number
  credits: number
  transcriptionModel: string
  isActive: boolean
  requiresSubscription: boolean
  compatiblePlans: object
```

### Admin Users

```
/admins/{userId}: boolean
```

### Transcripts

```
/transcripts/{userId}/{transcriptId}/
  text: string
  language: string
  timestamp: number
  ...
```

### System Settings

```
/settings/
  ...
```

## Security Considerations

1. **Server-Side Operations**: For operations that modify usage data or billing information, use Firebase Admin SDK with service account credentials.

2. **Client-Side Security**: Never store admin credentials in client-side code. Use Cloud Functions for sensitive operations.

3. **Data Validation**: The rules include validation to ensure data integrity, but additional validation should be performed in your application code.

4. **Testing**: Test the rules thoroughly using the Firebase Rules Playground before deploying to production.

## Testing the Rules

You can test the rules using the Firebase Rules Playground:

1. Go to the Firebase Console
2. Navigate to Realtime Database > Rules
3. Click on the "Rules Playground" tab
4. Set up test scenarios with different authentication states and data operations
5. Verify that the rules allow legitimate operations and block unauthorized access
