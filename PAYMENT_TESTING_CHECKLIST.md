# Payment Integration Testing Checklist

## Phase 1: Pre-Implementation Testing ✅

### 1.1 Stripe Account Setup
- [ ] Stripe account created and verified
- [ ] Test API keys obtained from Dashboard > Developers > API keys
- [ ] Live API keys obtained (for production later)
- [ ] Account has charges_enabled and payouts_enabled

### 1.2 Environment Configuration
- [ ] STRIPE_PUBLISHABLE_KEY set (starts with pk_test_)
- [ ] STRIPE_SECRET_KEY set (starts with sk_test_)
- [ ] STRIPE_WEBHOOK_SECRET set (starts with whsec_)
- [ ] Environment variables loaded correctly

### 1.3 Stripe Library Installation
- [ ] `pip install stripe>=7.0.0` completed
- [ ] Stripe library imports successfully
- [ ] API connectivity test passes

### 1.4 Products and Prices Setup
- [ ] VocalLocal Basic Plan product created
- [ ] VocalLocal Professional Plan product created
- [ ] Monthly recurring prices created for both plans
- [ ] STRIPE_BASIC_PRICE_ID environment variable set
- [ ] STRIPE_PROFESSIONAL_PRICE_ID environment variable set

### 1.5 Webhook Endpoint Configuration
- [ ] Webhook endpoint URL accessible
- [ ] Required webhook events selected in Stripe Dashboard:
  - [ ] checkout.session.completed
  - [ ] customer.subscription.created
  - [ ] customer.subscription.updated
  - [ ] customer.subscription.deleted
  - [ ] invoice.payment_succeeded
  - [ ] invoice.payment_failed
  - [ ] customer.created
- [ ] Webhook signing secret obtained and configured

## Phase 2: Backend Implementation Testing

### 2.1 Payment Service Testing
- [ ] PaymentService class created
- [ ] Stripe API key configuration works
- [ ] create_checkout_session() method implemented
- [ ] handle_webhook_event() method implemented
- [ ] Error handling for Stripe API failures

### 2.2 Webhook Handler Testing
- [ ] Webhook signature verification implemented
- [ ] Webhook endpoint returns 200 for valid requests
- [ ] Webhook endpoint returns 400 for invalid signatures
- [ ] Event processing logic handles all required events
- [ ] Database updates work correctly

### 2.3 Payment Routes Testing
- [ ] /payment/create-checkout-session endpoint works
- [ ] /payment/webhook endpoint works
- [ ] /payment/customer-portal endpoint works
- [ ] Proper authentication and authorization
- [ ] Error responses are properly formatted

## Phase 3: Frontend Implementation Testing

### 3.1 Payment UI Components
- [ ] Stripe.js library loads correctly
- [ ] Payment buttons render properly
- [ ] Upgrade modals display correctly
- [ ] Loading states work during payment processing
- [ ] Error messages display properly

### 3.2 Checkout Flow Testing
- [ ] Upgrade button click triggers checkout
- [ ] Checkout session creation works
- [ ] Redirect to Stripe Checkout works
- [ ] Return URLs work correctly
- [ ] Cancel URLs work correctly

## Phase 4: Integration Testing

### 4.1 User Account Integration
- [ ] User subscription status updates in Firebase
- [ ] Plan type changes reflect in user interface
- [ ] Usage limits update based on new plan
- [ ] User role/permissions update correctly

### 4.2 Existing System Integration
- [ ] Dashboard displays correct plan information
- [ ] Usage tracking respects new plan limits
- [ ] Model access control works with new plans
- [ ] Admin interface shows subscription status

## Phase 5: End-to-End Testing

### 5.1 Successful Payment Flow
- [ ] Free user can upgrade to Basic plan
- [ ] Basic user can upgrade to Professional plan
- [ ] Subscription status updates immediately
- [ ] User gains access to premium features
- [ ] Usage limits increase correctly

### 5.2 Payment Failure Scenarios
- [ ] Declined card handling works
- [ ] Insufficient funds handling works
- [ ] Invalid card handling works
- [ ] User remains on current plan after failure
- [ ] Error messages are user-friendly

### 5.3 Webhook Failure Scenarios
- [ ] Webhook signature verification failures
- [ ] Webhook processing errors
- [ ] Database update failures
- [ ] Retry mechanisms work
- [ ] Admin notifications for failures

## Phase 6: Security Testing

### 6.1 Webhook Security
- [ ] Webhook signature verification prevents spoofing
- [ ] Invalid signatures are rejected
- [ ] Replay attacks are prevented
- [ ] Rate limiting on webhook endpoint

### 6.2 Payment Security
- [ ] No sensitive data stored locally
- [ ] API keys are properly secured
- [ ] HTTPS enforced for all payment endpoints
- [ ] User authentication required for payment actions

## Phase 7: Performance Testing

### 7.1 Load Testing
- [ ] Multiple concurrent checkout sessions
- [ ] High volume webhook processing
- [ ] Database performance under load
- [ ] Response times within acceptable limits

### 7.2 Error Recovery Testing
- [ ] Graceful handling of Stripe API downtime
- [ ] Database connection failures
- [ ] Network timeout handling
- [ ] Partial payment processing recovery

## Testing Commands

### Run Pre-Implementation Tests
```bash
cd vocallocal
python test_stripe_setup.py
```

### Setup Stripe Products
```bash
python setup_stripe_products.py
```

### Test Webhook Locally (requires Stripe CLI)
```bash
stripe listen --forward-to localhost:5001/payment/webhook
```

### Test Specific Webhook Events
```bash
stripe trigger checkout.session.completed
stripe trigger customer.subscription.deleted
stripe trigger invoice.payment_failed
```

### Test Payment Flow
```bash
# Start local server
python app.py

# Navigate to dashboard and test upgrade buttons
# Use test card: 4242424242424242
```

## Test Card Numbers

### Successful Payments
- **Visa**: 4242424242424242
- **Visa (debit)**: 4000056655665556
- **Mastercard**: 5555555555554444

### Failed Payments
- **Declined**: 4000000000000002
- **Insufficient funds**: 4000000000009995
- **Lost card**: 4000000000009987

### Special Cases
- **3D Secure**: 4000002500003155
- **Expired card**: 4000000000000069

## Monitoring and Logging

### What to Monitor
- [ ] Payment success/failure rates
- [ ] Webhook processing times
- [ ] Database update success rates
- [ ] User upgrade conversion rates
- [ ] Error frequencies and types

### Log Events
- [ ] All payment attempts
- [ ] Webhook events received
- [ ] Database updates
- [ ] Error conditions
- [ ] User plan changes

## Production Readiness Checklist

### Before Going Live
- [ ] All tests pass in staging environment
- [ ] Live Stripe keys configured
- [ ] Webhook endpoint accessible from internet
- [ ] HTTPS certificate valid
- [ ] Monitoring and alerting configured
- [ ] Error handling tested thoroughly
- [ ] Customer support procedures documented
