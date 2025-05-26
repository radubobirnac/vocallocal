# VocalLocal Subscription Plans Guide

This guide explains how to set up and manage subscription plans in the VocalLocal application.

## Overview

The VocalLocal application includes a comprehensive subscription plans system with the following features:

- **Firebase Integration**: Plans are stored in Firebase Realtime Database
- **Admin Management**: Web-based admin interface for managing plans
- **API Endpoints**: RESTful API for programmatic access
- **Type Safety**: TypeScript interfaces for client-side development
- **Security**: Firebase security rules protect plan data

## Subscription Plans Structure

### Current Plans

The system includes four subscription plans with exact specifications:

#### 1. Free Plan
- **Price**: $0.00
- **Transcription**: 60 minutes
- **Translation**: 0 words
- **TTS**: 0 minutes
- **AI Credits**: 0
- **Model**: gemini-2.0-flash-lite

#### 2. Basic Plan
- **Price**: $4.99
- **Transcription**: 280 minutes
- **Translation**: 50,000 words
- **TTS**: 60 minutes
- **AI Credits**: 50
- **Model**: premium

#### 3. Professional Plan
- **Price**: $12.99
- **Transcription**: 800 minutes
- **Translation**: 160,000 words
- **TTS**: 200 minutes
- **AI Credits**: 150
- **Model**: premium

#### 4. Pay-as-you-go Add-on
- **Price**: $3.99
- **Credits**: 300
- **Requires**: Basic or Professional subscription
- **Compatible Plans**: Basic, Professional

## Setup Instructions

### 1. Initialize Subscription Plans

#### Using Python Script
```bash
cd vocallocal
python initialize_subscription_plans.py
```

#### Using Update Script (Recommended)
```bash
cd vocallocal
python update_subscription_plans.py
```

#### Using Admin Web Interface
1. Navigate to `/admin/users`
2. Login with admin credentials (username: Radu, password: Fasteasy)
3. Go to `/admin/subscription-plans`
4. Click "Initialize Plans" or "Force Update All"

### 2. Firebase Setup

The subscription plans are stored in Firebase under the `subscriptionPlans` collection:

```
/subscriptionPlans/
  free/
    id: "free"
    name: "Free Plan"
    price: 0
    transcriptionMinutes: 60
    translationWords: 0
    ttsMinutes: 0
    aiCredits: 0
    transcriptionModel: "gemini-2.0-flash-lite"
    isActive: true
  basic/
    id: "basic"
    name: "Basic Plan"
    price: 4.99
    transcriptionMinutes: 280
    translationWords: 50000
    ttsMinutes: 60
    aiCredits: 50
    transcriptionModel: "premium"
    isActive: true
  professional/
    id: "professional"
    name: "Professional Plan"
    price: 12.99
    transcriptionMinutes: 800
    translationWords: 160000
    ttsMinutes: 200
    aiCredits: 150
    transcriptionModel: "premium"
    isActive: true
  payg/
    id: "payg"
    name: "Pay-as-you-go Credits"
    price: 3.99
    credits: 300
    requiresSubscription: true
    compatiblePlans:
      basic: true
      professional: true
    isActive: true
```

## Admin Functions

### Python API

```python
from services.admin_subscription_service import AdminSubscriptionService

# Initialize all plans
result = AdminSubscriptionService.initialize_subscription_plans()

# Force update all plans to match specifications
result = AdminSubscriptionService.force_update_all_plans()

# Update a specific plan
result = AdminSubscriptionService.update_subscription_plan("basic", {
    "price": 5.99,
    "transcriptionMinutes": 300
})

# Get all plans
plans = AdminSubscriptionService.get_all_subscription_plans()

# Get a specific plan
plan = AdminSubscriptionService.get_subscription_plan("basic")
```

### Web Admin Interface

Access the admin interface at:
1. `/admin/users` - Login with admin credentials
2. `/admin/subscription-plans` - Manage subscription plans

Available actions:
- **Initialize Plans**: Create missing plans
- **Force Update All**: Overwrite all plans with default specifications
- **Refresh**: Reload the page to see current plans

### REST API Endpoints

All endpoints require admin authentication:

```bash
# Get all plans
GET /admin/api/subscription-plans

# Get all plans including inactive
GET /admin/api/subscription-plans?include_inactive=true

# Initialize plans
POST /admin/api/subscription-plans/initialize

# Force update all plans
POST /admin/api/subscription-plans/force-update

# Update a specific plan
PUT /admin/api/subscription-plans/{plan_id}
Content-Type: application/json
{
  "price": 5.99,
  "transcriptionMinutes": 300
}
```

## Client-Side Usage

### JavaScript

```javascript
// Get all active subscription plans
subscriptionPlansService.getAllSubscriptionPlans().then(plans => {
  console.log('Active plans:', plans);
});

// Get service plans (excluding pay-as-you-go)
subscriptionPlansService.getServicePlans().then(plans => {
  console.log('Service plans:', plans);
});

// Get a specific plan
subscriptionPlansService.getSubscriptionPlan('basic').then(plan => {
  console.log('Basic plan:', plan);
});
```

### TypeScript

```typescript
import { SubscriptionPlansMap, ServicePlan } from './types/subscription-plans';

// Type-safe access to plans
const plans: SubscriptionPlansMap = await subscriptionPlansService.getAllSubscriptionPlans();
const basicPlan: ServicePlan = plans.basic as ServicePlan;
```

## Troubleshooting

### Common Issues

1. **Plans not appearing**: Run the initialization script
2. **Incorrect specifications**: Use force update to reset all plans
3. **Permission errors**: Ensure admin authentication is working
4. **Firebase errors**: Check Firebase credentials and security rules

### Verification

To verify plans are correctly set up:

1. Run the update script with verification
2. Check the admin web interface
3. Use the API endpoints to fetch plans
4. Check Firebase console directly

### Logs

The system provides detailed logging:
- Initialization results
- Update operations
- Error messages
- Verification status

## Security

- Only authenticated admin users can modify plans
- Firebase security rules protect the data
- All API endpoints require admin authentication
- Plans are validated before updates

## Files Involved

- `services/admin_subscription_service.py` - Main service class
- `initialize_subscription_plans.py` - Initialization script
- `update_subscription_plans.py` - Update and verification script
- `routes/admin.py` - Admin web routes and API endpoints
- `templates/admin_subscription_plans.html` - Admin web interface
- `static/js/subscription-plans.js` - Client-side utilities
- `static/types/subscription-plans.d.ts` - TypeScript interfaces
- `firebase-security-rules.json` - Firebase security rules
