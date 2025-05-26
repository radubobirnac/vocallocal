# Subscription Plans for VocalLocal

This document describes the subscription plans system for the VocalLocal application.

## Overview

VocalLocal offers different subscription plans to users, each with different features and limits. The subscription plans are stored in the Firebase Realtime Database and can be managed through the admin interface.

## Subscription Plan Types

### Service Plans

Service plans provide users with a set of features and usage limits:

1. **Free Plan**
   - 60 minutes of AI transcription (gemini-2.0-flash-lite model)
   - 5,000 words of translation
   - No text-to-speech minutes
   - No AI credits
   - Price: Free

2. **Basic Plan**
   - 280 minutes of AI transcription (premium model)
   - 50,000 words of translation
   - 60 minutes of text-to-speech
   - 50 AI credits
   - Price: $4.99/month

3. **Professional Plan**
   - 800 minutes of AI transcription (premium model)
   - 160,000 words of translation
   - 200 minutes of text-to-speech
   - 150 AI credits
   - Price: $12.99/month

### Add-on Plans

Add-on plans provide additional credits or features to users with an existing subscription:

1. **Pay-as-you-go Credits**
   - 300 additional credits
   - Compatible with Basic and Professional plans
   - Price: $3.99

## Database Structure

Subscription plans are stored in the Firebase Realtime Database under the `subscriptionPlans` collection:

```
/subscriptionPlans/{planId}
```

### Service Plan Schema

```json
{
  "id": "basic",
  "name": "Basic Plan",
  "price": 4.99,
  "transcriptionMinutes": 280,
  "translationWords": 50000,
  "ttsMinutes": 60,
  "aiCredits": 50,
  "transcriptionModel": "premium",
  "isActive": true
}
```

### Pay-as-you-go Add-on Schema

```json
{
  "id": "payg",
  "name": "Pay-as-you-go Credits",
  "price": 3.99,
  "credits": 300,
  "requiresSubscription": true,
  "compatiblePlans": {"basic": true, "professional": true},
  "isActive": true
}
```

## Admin Functions

The `admin_subscription_service.py` file provides functions for managing subscription plans:

### Initialize Subscription Plans

```python
from services.admin_subscription_service import AdminSubscriptionService

# Initialize subscription plans
result = AdminSubscriptionService.initialize_subscription_plans()
if result["success"]:
    print(f"Created plans: {result['created']}")
    print(f"Existing plans: {result['existing']}")
else:
    print(f"Error: {result['error']}")
```

### Update Subscription Plan

```python
from services.admin_subscription_service import AdminSubscriptionService

# Update a subscription plan
result = AdminSubscriptionService.update_subscription_plan("basic", {
    "price": 5.99,
    "transcriptionMinutes": 300,
    "isActive": True
})
if result["success"]:
    print(f"Updated fields: {result['updated_fields']}")
else:
    print(f"Error: {result['error']}")
```

### Get All Subscription Plans

```python
from services.admin_subscription_service import AdminSubscriptionService

# Get all subscription plans
plans = AdminSubscriptionService.get_all_subscription_plans(include_inactive=False)
for plan_id, plan_data in plans.items():
    print(f"{plan_id}: {plan_data['name']} (${plan_data['price']})")
```

## Client-Side Usage

The `subscription-plans.js` file provides client-side utilities for working with subscription plans:

### Get All Subscription Plans

```javascript
// Get all active subscription plans
subscriptionPlansService.getAllSubscriptionPlans().then(plans => {
  console.log('Active plans:', plans);
});

// Include inactive plans
subscriptionPlansService.getAllSubscriptionPlans(true).then(plans => {
  console.log('All plans:', plans);
});
```

### Get Service Plans

```javascript
// Get all service plans (excluding pay-as-you-go add-ons)
subscriptionPlansService.getServicePlans().then(plans => {
  console.log('Service plans:', plans);
});
```

### Get Pay-as-you-go Plans

```javascript
// Get all pay-as-you-go add-on plans
subscriptionPlansService.getPayAsYouGoPlans().then(plans => {
  console.log('Pay-as-you-go plans:', plans);
});

// Get pay-as-you-go plans compatible with a specific plan
subscriptionPlansService.getPayAsYouGoPlans('basic').then(plans => {
  console.log('Compatible pay-as-you-go plans:', plans);
});
```

### Calculate Subscription Price

```javascript
// Calculate the total price of a subscription with add-ons
subscriptionPlansService.calculateSubscriptionPrice('basic', ['payg']).then(price => {
  console.log('Total price:', subscriptionPlansService.formatPrice(price));
});
```

## TypeScript Interfaces

TypeScript interfaces for subscription plans are available in the `static/types/subscription-plans.d.ts` file. These interfaces provide type safety when accessing subscription plans from TypeScript code.

## Firebase Security Rules

The Firebase security rules for subscription plans are defined in the `firebase-rules.json` file:

- All authenticated users can read subscription plans
- Only administrators can write to subscription plans
- Data validation ensures that subscription plans have the required fields and correct data types
