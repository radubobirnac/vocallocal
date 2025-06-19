"""
Payment Service for VocalLocal
Handles Stripe integration for subscription management
"""

import os
import stripe
import logging
from datetime import datetime, timedelta
from flask import current_app
from services.user_account_service import UserAccountService

logger = logging.getLogger(__name__)

class PaymentService:
    """Service for handling Stripe payments and subscriptions"""
    
    def __init__(self):
        """Initialize Stripe with API key"""
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        # Price IDs from environment
        self.price_ids = {
            'basic': os.getenv('STRIPE_BASIC_PRICE_ID'),
            'professional': os.getenv('STRIPE_PROFESSIONAL_PRICE_ID')
        }
        
        if not stripe.api_key:
            logger.error("STRIPE_SECRET_KEY not found in environment variables")
            raise ValueError("Stripe secret key not configured")
    
    def create_checkout_session(self, user_email, plan_type, success_url, cancel_url):
        """
        Create a Stripe checkout session for subscription
        
        Args:
            user_email (str): User's email address
            plan_type (str): 'basic' or 'professional'
            success_url (str): URL to redirect after successful payment
            cancel_url (str): URL to redirect if payment is cancelled
            
        Returns:
            dict: Checkout session data or error
        """
        try:
            # Validate plan type
            if plan_type not in self.price_ids:
                return {'error': f'Invalid plan type: {plan_type}'}
            
            price_id = self.price_ids[plan_type]
            if not price_id:
                return {'error': f'Price ID not configured for {plan_type} plan'}
            
            # Create or retrieve customer
            customer = self._get_or_create_customer(user_email)
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_email': user_email,
                    'plan_type': plan_type
                },
                subscription_data={
                    'metadata': {
                        'user_email': user_email,
                        'plan_type': plan_type
                    }
                }
            )
            
            logger.info(f"Created checkout session for {user_email}, plan: {plan_type}")
            
            return {
                'session_id': session.id,
                'checkout_url': session.url,
                'success': True
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {str(e)}")
            return {'error': f'Payment system error: {str(e)}'}
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return {'error': f'Unexpected error: {str(e)}'}
    
    def _get_or_create_customer(self, email):
        """Get existing customer or create new one"""
        try:
            # Search for existing customer
            customers = stripe.Customer.list(email=email, limit=1)
            
            if customers.data:
                return customers.data[0]
            
            # Create new customer
            customer = stripe.Customer.create(
                email=email,
                metadata={'app': 'vocallocal'}
            )
            
            logger.info(f"Created new Stripe customer for {email}")
            return customer
            
        except stripe.error.StripeError as e:
            logger.error(f"Error managing customer: {str(e)}")
            raise
    
    def handle_webhook_event(self, payload, signature):
        """
        Handle Stripe webhook events
        
        Args:
            payload (bytes): Raw webhook payload
            signature (str): Stripe signature header
            
        Returns:
            dict: Processing result
        """
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            logger.info(f"Processing webhook event: {event['type']}")
            
            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                return self._handle_checkout_completed(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.created':
                return self._handle_subscription_created(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.updated':
                return self._handle_subscription_updated(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(event['data']['object'])
            
            elif event['type'] == 'invoice.payment_succeeded':
                return self._handle_payment_succeeded(event['data']['object'])
            
            elif event['type'] == 'invoice.payment_failed':
                return self._handle_payment_failed(event['data']['object'])
            
            else:
                logger.info(f"Unhandled webhook event type: {event['type']}")
                return {'success': True, 'message': 'Event type not handled'}
            
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return {'error': 'Invalid signature', 'status_code': 400}
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return {'error': str(e), 'status_code': 500}
    
    def _handle_checkout_completed(self, session):
        """Handle successful checkout completion"""
        try:
            user_email = session.get('metadata', {}).get('user_email')
            plan_type = session.get('metadata', {}).get('plan_type')
            
            if not user_email or not plan_type:
                logger.error("Missing user_email or plan_type in checkout session metadata")
                return {'error': 'Missing required metadata'}
            
            # Update user subscription in Firebase
            user_id = user_email.replace('.', ',')
            subscription_data = {
                'planType': plan_type,
                'status': 'active',
                'startDate': int(datetime.now().timestamp() * 1000),
                'paymentMethod': 'stripe',
                'billingCycle': 'monthly',
                'stripeCustomerId': session.get('customer'),
                'stripeSubscriptionId': session.get('subscription')
            }
            
            UserAccountService.update_subscription(user_id, subscription_data)
            
            logger.info(f"Updated subscription for {user_email} to {plan_type}")
            return {'success': True, 'message': 'Subscription activated'}
            
        except Exception as e:
            logger.error(f"Error handling checkout completion: {str(e)}")
            return {'error': str(e)}
    
    def _handle_subscription_created(self, subscription):
        """Handle subscription creation"""
        # Usually handled by checkout.session.completed
        logger.info(f"Subscription created: {subscription['id']}")
        return {'success': True}
    
    def _handle_subscription_updated(self, subscription):
        """Handle subscription updates"""
        try:
            # Get customer email from subscription metadata
            user_email = subscription.get('metadata', {}).get('user_email')
            if not user_email:
                logger.warning("No user_email in subscription metadata")
                return {'success': True}
            
            user_id = user_email.replace('.', ',')
            
            # Update subscription status
            status = subscription['status']  # active, past_due, canceled, etc.
            
            update_data = {
                'status': status,
                'stripeSubscriptionId': subscription['id']
            }
            
            # If subscription is canceled, downgrade to free
            if status == 'canceled':
                update_data['planType'] = 'free'
            
            UserAccountService.update_subscription(user_id, update_data)
            
            logger.info(f"Updated subscription status for {user_email}: {status}")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error handling subscription update: {str(e)}")
            return {'error': str(e)}
    
    def _handle_subscription_deleted(self, subscription):
        """Handle subscription cancellation"""
        try:
            user_email = subscription.get('metadata', {}).get('user_email')
            if not user_email:
                logger.warning("No user_email in subscription metadata")
                return {'success': True}
            
            user_id = user_email.replace('.', ',')
            
            # Downgrade to free plan
            subscription_data = {
                'planType': 'free',
                'status': 'canceled',
                'endDate': int(datetime.now().timestamp() * 1000)
            }
            
            UserAccountService.update_subscription(user_id, subscription_data)
            
            logger.info(f"Downgraded {user_email} to free plan due to subscription cancellation")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error handling subscription deletion: {str(e)}")
            return {'error': str(e)}
    
    def _handle_payment_succeeded(self, invoice):
        """Handle successful payment"""
        logger.info(f"Payment succeeded for invoice: {invoice['id']}")
        # Payment success is usually handled by subscription events
        return {'success': True}
    
    def _handle_payment_failed(self, invoice):
        """Handle failed payment"""
        try:
            # Get subscription info
            subscription_id = invoice.get('subscription')
            if subscription_id:
                subscription = stripe.Subscription.retrieve(subscription_id)
                user_email = subscription.get('metadata', {}).get('user_email')
                
                if user_email:
                    logger.warning(f"Payment failed for {user_email}, invoice: {invoice['id']}")
                    # Could implement email notification here
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error handling payment failure: {str(e)}")
            return {'error': str(e)}
    
    def create_customer_portal_session(self, customer_id, return_url):
        """
        Create customer portal session for subscription management
        
        Args:
            customer_id (str): Stripe customer ID
            return_url (str): URL to return to after portal session
            
        Returns:
            dict: Portal session data or error
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            
            return {
                'portal_url': session.url,
                'success': True
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating customer portal session: {str(e)}")
            return {'error': str(e)}
    
    def get_customer_by_email(self, email):
        """Get Stripe customer by email"""
        try:
            customers = stripe.Customer.list(email=email, limit=1)
            return customers.data[0] if customers.data else None
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving customer: {str(e)}")
            return None
