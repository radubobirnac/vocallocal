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
from services.email_service import email_service

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
            
            # Create checkout session (invoices are automatically created for subscription mode)
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
                },
                # Automatic tax calculation (if configured)
                automatic_tax={'enabled': False},  # Set to True if tax calculation is needed
                # Customer email collection
                customer_email=user_email if not customer.email else None
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

            elif event['type'] == 'invoice.created':
                return self._handle_invoice_created(event['data']['object'])

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

            # Call UserAccountService.update_subscription with correct parameters
            UserAccountService.update_subscription(
                user_id=user_id,
                plan_type=plan_type,
                status='active',
                billing_cycle='monthly',
                payment_method='stripe'
            )

            # Also update additional Stripe-specific fields
            additional_data = {
                'stripeCustomerId': session.get('customer'),
                'stripeSubscriptionId': session.get('subscription')
            }

            # Update additional Stripe fields directly
            UserAccountService.get_ref(f'users/{user_id}/subscription').update(additional_data)

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
        """Handle successful payment and send invoice/receipt email"""
        try:
            logger.info(f"Payment succeeded for invoice: {invoice['id']}")

            # Extract invoice details
            invoice_id = invoice['id']
            amount_paid = invoice['amount_paid'] / 100  # Convert from cents to dollars
            currency = invoice['currency'].upper()
            payment_date = datetime.fromtimestamp(invoice['created'])

            # Get customer and subscription information
            customer_id = invoice.get('customer')
            subscription_id = invoice.get('subscription')

            if not customer_id:
                logger.warning(f"No customer ID found for invoice {invoice_id}")
                return {'success': True, 'message': 'No customer ID found'}

            # Retrieve customer details from Stripe
            customer = stripe.Customer.retrieve(customer_id)
            user_email = customer.email

            if not user_email:
                logger.warning(f"No email found for customer {customer_id}")
                return {'success': True, 'message': 'No customer email found'}

            # Get subscription details if available
            plan_type = 'unknown'
            plan_name = 'Unknown Plan'
            billing_cycle = 'monthly'

            if subscription_id:
                logger.info(f"Retrieving subscription details for: {subscription_id}")
                subscription = stripe.Subscription.retrieve(subscription_id)
                plan_type = subscription.get('metadata', {}).get('plan_type', 'unknown')
                logger.info(f"Plan type from subscription metadata: {plan_type}")

                # Get plan details from subscription items
                if subscription.get('items') and subscription['items']['data']:
                    price = subscription['items']['data'][0]['price']
                    logger.info(f"Getting plan name from subscription price")
                    plan_name = self._get_plan_name_from_price(price)
                    billing_cycle = price.get('recurring', {}).get('interval', 'monthly')
                    logger.info(f"Plan name from price: {plan_name}, billing cycle: {billing_cycle}")

                # Fallback: if plan_name is still unknown, use plan_type from metadata
                if plan_name == 'Unknown Plan' and plan_type != 'unknown':
                    logger.info(f"Using fallback plan name from type: {plan_type}")
                    plan_name = self._get_plan_name_from_type(plan_type)
            else:
                # If no subscription, try to get plan info from invoice line items
                logger.info("No subscription ID, checking invoice line items")
                if invoice.get('lines') and invoice['lines']['data']:
                    for line_item in invoice['lines']['data']:
                        if line_item.get('price'):
                            price = line_item['price']
                            logger.info(f"Getting plan name from invoice line item price")
                            plan_name = self._get_plan_name_from_price(price)
                            billing_cycle = price.get('recurring', {}).get('interval', 'monthly')

                            # Try to determine plan type from the plan name
                            if 'Basic' in plan_name:
                                plan_type = 'basic'
                            elif 'Professional' in plan_name:
                                plan_type = 'professional'

                            logger.info(f"Plan from invoice line item - Name: {plan_name}, Type: {plan_type}")
                            break

            logger.info(f"Final plan details - Type: {plan_type}, Name: {plan_name}, Billing: {billing_cycle}")

            # Store billing history in Firebase
            self._store_billing_history(user_email, {
                'invoiceId': invoice_id,
                'amount': amount_paid,
                'currency': currency,
                'paymentDate': int(payment_date.timestamp() * 1000),
                'planType': plan_type,
                'planName': plan_name,
                'billingCycle': billing_cycle,
                'status': 'paid',
                'stripeInvoiceId': invoice_id,
                'stripeCustomerId': customer_id,
                'stripeSubscriptionId': subscription_id
            })

            # Generate PDF invoice
            pdf_invoice = self._generate_pdf_invoice(
                user_email=user_email,
                invoice_id=invoice_id,
                amount=amount_paid,
                currency=currency,
                payment_date=payment_date,
                plan_type=plan_type,
                plan_name=plan_name,
                billing_cycle=billing_cycle
            )

            # Send payment confirmation email with PDF attachment
            email_result = self._send_payment_confirmation_email(
                user_email=user_email,
                invoice_id=invoice_id,
                amount=amount_paid,
                currency=currency,
                payment_date=payment_date,
                plan_type=plan_type,
                plan_name=plan_name,
                billing_cycle=billing_cycle,
                pdf_attachment=pdf_invoice
            )

            if email_result.get('success'):
                logger.info(f"Payment confirmation email sent successfully to {user_email}")
            else:
                logger.error(f"Failed to send payment confirmation email to {user_email}: {email_result.get('message')}")

            return {'success': True, 'message': 'Payment processed and email sent'}

        except Exception as e:
            logger.error(f"Error handling payment success for invoice {invoice.get('id', 'unknown')}: {str(e)}")
            return {'error': str(e)}
    
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

    def _handle_invoice_created(self, invoice):
        """Handle invoice creation and customize it with VocalLocal branding"""
        try:
            logger.info(f"Invoice created: {invoice['id']}")

            # Get subscription info to determine plan type
            subscription_id = invoice.get('subscription')
            if not subscription_id:
                logger.info(f"No subscription found for invoice {invoice['id']}")
                return {'success': True}

            # Retrieve subscription to get plan type
            subscription = stripe.Subscription.retrieve(subscription_id)
            plan_type = subscription.get('metadata', {}).get('plan_type', 'unknown')

            # Update invoice with custom fields and description
            try:
                stripe.Invoice.modify(
                    invoice['id'],
                    description=f'VocalLocal {plan_type.title()} Plan Subscription',
                    metadata={
                        'service': 'vocallocal_subscription',
                        'plan_type': plan_type
                    },
                    custom_fields=[
                        {
                            'name': 'Service',
                            'value': 'VocalLocal AI Transcription Platform'
                        },
                        {
                            'name': 'Plan Type',
                            'value': f'{plan_type.title()} Plan'
                        }
                    ],
                    footer='Thank you for choosing VocalLocal! For support, contact support@vocallocal.com'
                )

                logger.info(f"Invoice {invoice['id']} customized successfully")

            except stripe.error.StripeError as e:
                logger.warning(f"Could not customize invoice {invoice['id']}: {str(e)}")
                # Don't fail the webhook if customization fails

            return {'success': True, 'message': 'Invoice created and customized'}

        except Exception as e:
            logger.error(f"Error handling invoice creation for {invoice.get('id', 'unknown')}: {str(e)}")
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

    def _get_plan_name_from_price(self, price):
        """Get human-readable plan name from Stripe price object"""
        try:
            logger.info(f"Getting plan name from price object: {price}")

            # Map price IDs to plan names
            price_id = price.get('id')
            logger.info(f"Price ID: {price_id}")

            # Get environment price IDs
            basic_price_id = os.getenv('STRIPE_BASIC_PRICE_ID')
            professional_price_id = os.getenv('STRIPE_PROFESSIONAL_PRICE_ID')

            logger.info(f"Basic Price ID from env: {basic_price_id}")
            logger.info(f"Professional Price ID from env: {professional_price_id}")

            if price_id == basic_price_id:
                logger.info("Matched Basic Plan by price ID")
                return 'Basic Plan'
            elif price_id == professional_price_id:
                logger.info("Matched Professional Plan by price ID")
                return 'Professional Plan'

            # Check if price has a product with a name
            if price.get('product'):
                try:
                    product = stripe.Product.retrieve(price['product'])
                    if product.get('name'):
                        product_name = product['name']
                        logger.info(f"Product name: {product_name}")
                        # Extract plan name from product name
                        if 'Basic' in product_name:
                            logger.info("Matched Basic Plan by product name")
                            return 'Basic Plan'
                        elif 'Professional' in product_name or 'Premium' in product_name:
                            logger.info("Matched Professional Plan by product name")
                            return 'Professional Plan'
                        return product_name
                except Exception as e:
                    logger.warning(f"Error retrieving product: {str(e)}")

            # Fallback to price nickname
            if price.get('nickname'):
                nickname = price['nickname']
                logger.info(f"Price nickname: {nickname}")
                if 'Basic' in nickname:
                    logger.info("Matched Basic Plan by nickname")
                    return 'Basic Plan'
                elif 'Professional' in nickname or 'Premium' in nickname:
                    logger.info("Matched Professional Plan by nickname")
                    return 'Professional Plan'
                return nickname

            # Final fallback to amount-based name
            amount = price.get('unit_amount', 0) / 100
            currency = price.get('currency', 'usd').upper()
            logger.info(f"Price amount: {amount} {currency}")

            # Try to map common amounts to plan names
            if amount == 4.99:
                logger.info("Matched Basic Plan by amount ($4.99)")
                return 'Basic Plan'
            elif amount == 12.99:
                logger.info("Matched Professional Plan by amount ($12.99)")
                return 'Professional Plan'

            logger.warning(f"No plan match found, using fallback: {currency} {amount:.2f} Plan")
            return f"{currency} {amount:.2f} Plan"

        except Exception as e:
            logger.error(f"Error getting plan name from price: {str(e)}")
            return 'Unknown Plan'

    def _get_plan_name_from_type(self, plan_type):
        """Get human-readable plan name from plan type string"""
        try:
            plan_names = {
                'basic': 'Basic Plan',
                'professional': 'Professional Plan',
                'premium': 'Professional Plan',  # Legacy support
                'enterprise': 'Enterprise Plan'
            }

            return plan_names.get(plan_type.lower(), f'{plan_type.title()} Plan')

        except Exception as e:
            logger.error(f"Error getting plan name from type: {str(e)}")
            return 'Unknown Plan'

    def _store_billing_history(self, user_email, billing_data):
        """Store billing history in Firebase"""
        try:
            user_id = user_email.replace('.', ',')

            # Add to billing history
            billing_ref = UserAccountService.get_ref(f'users/{user_id}/billing/invoices')
            billing_ref.push(billing_data)

            logger.info(f"Stored billing history for {user_email}, invoice: {billing_data['invoiceId']}")

        except Exception as e:
            logger.error(f"Error storing billing history for {user_email}: {str(e)}")
            raise

    def _generate_pdf_invoice(self, user_email, invoice_id, amount, currency,
                            payment_date, plan_type, plan_name, billing_cycle):
        """Generate PDF invoice for the payment"""
        try:
            from services.pdf_invoice_service import PDFInvoiceService

            # Get user's display name (fallback to email prefix)
            display_name = user_email.split('@')[0]

            # Try to get actual display name from Firebase
            try:
                user_id = user_email.replace('.', ',')
                user_data = UserAccountService.get_user_account(user_id)
                if user_data and user_data.get('profile', {}).get('displayName'):
                    display_name = user_data['profile']['displayName']
            except Exception:
                pass  # Use fallback display name

            # Prepare invoice data
            invoice_data = {
                'invoice_id': invoice_id,
                'customer_name': display_name,
                'customer_email': user_email,
                'amount': amount,
                'currency': currency,
                'payment_date': payment_date,
                'plan_name': plan_name,
                'plan_type': plan_type,
                'billing_cycle': billing_cycle,
                'payment_method': 'Credit Card',
                'transaction_id': invoice_id  # Use invoice ID as transaction reference
            }

            # Generate PDF
            pdf_service = PDFInvoiceService()
            pdf_content = pdf_service.generate_invoice_pdf(invoice_data)

            if pdf_content:
                logger.info(f"Generated PDF invoice for {user_email}, size: {len(pdf_content)} bytes")
            else:
                logger.warning(f"Failed to generate PDF invoice for {user_email}")

            return pdf_content

        except Exception as e:
            logger.error(f"Error generating PDF invoice for {user_email}: {str(e)}")
            return None

    def _send_payment_confirmation_email(self, user_email, invoice_id, amount, currency,
                                       payment_date, plan_type, plan_name, billing_cycle,
                                       pdf_attachment=None):
        """Send payment confirmation email with invoice details and PDF attachment"""
        try:
            # Get user's display name (fallback to email prefix)
            display_name = user_email.split('@')[0]

            # Try to get actual display name from Firebase
            try:
                user_id = user_email.replace('.', ',')
                user_data = UserAccountService.get_user_account(user_id)
                if user_data and user_data.get('profile', {}).get('displayName'):
                    display_name = user_data['profile']['displayName']
            except Exception:
                pass  # Use fallback display name

            # Send the payment confirmation email
            return email_service.send_payment_confirmation_email(
                username=display_name,
                email=user_email,
                invoice_id=invoice_id,
                amount=amount,
                currency=currency,
                payment_date=payment_date,
                plan_type=plan_type,
                plan_name=plan_name,
                billing_cycle=billing_cycle,
                pdf_attachment=pdf_attachment
            )

        except Exception as e:
            logger.error(f"Error sending payment confirmation email to {user_email}: {str(e)}")
            return {'success': False, 'message': str(e)}

    def get_customer_by_email(self, email):
        """Get Stripe customer by email address"""
        try:
            customers = stripe.Customer.list(email=email, limit=1)
            return customers.data[0] if customers.data else None
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving customer by email {email}: {str(e)}")
            return None
    
    def get_customer_by_email(self, email):
        """Get Stripe customer by email"""
        try:
            customers = stripe.Customer.list(email=email, limit=1)
            return customers.data[0] if customers.data else None
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving customer: {str(e)}")
            return None

    def check_existing_subscription(self, user_email, plan_type):
        """
        Check if user already has an active subscription for the requested plan type.
        This method checks both Stripe and Firebase to ensure accurate subscription status.
        """
        try:
            logger.info(f"Checking subscription for {user_email}, requested plan: {plan_type}")

            # First check Firebase for subscription data (faster and more reliable for app logic)
            firebase_subscription = self._check_firebase_subscription(user_email, plan_type)
            logger.info(f"Firebase subscription check result: {firebase_subscription}")

            # Then check Stripe for billing subscription status
            stripe_subscription = self._check_stripe_subscription(user_email, plan_type)
            logger.info(f"Stripe subscription check result: {stripe_subscription}")

            # Determine final result based on both sources
            return self._reconcile_subscription_status(firebase_subscription, stripe_subscription, user_email, plan_type)

        except Exception as e:
            logger.error(f"Error checking subscription for {user_email}: {str(e)}")
            return {'error': f'Error checking subscription: {str(e)}'}

    def _check_firebase_subscription(self, user_email, plan_type):
        """Check Firebase for user subscription data"""
        try:
            from services.user_account_service import UserAccountService

            user_id = user_email.replace('.', ',')
            user_account = UserAccountService.get_user_account(user_id)

            if not user_account or 'subscription' not in user_account:
                return {'has_subscription': False, 'source': 'firebase', 'message': 'No Firebase subscription data'}

            subscription = user_account['subscription']
            current_plan = subscription.get('planType', 'free')
            status = subscription.get('status', 'inactive')

            # Check if user has an active subscription
            if status == 'active' and current_plan in ['basic', 'professional']:
                if current_plan == plan_type:
                    return {
                        'has_subscription': True,
                        'source': 'firebase',
                        'plan_type': current_plan,
                        'status': status,
                        'message': f'User has active {current_plan} subscription in Firebase'
                    }
                else:
                    return {
                        'has_subscription': True,
                        'source': 'firebase',
                        'plan_type': current_plan,
                        'current_plan': current_plan,
                        'requested_plan': plan_type,
                        'status': status,
                        'message': f'User has active {current_plan} subscription, requesting {plan_type}'
                    }

            return {
                'has_subscription': False,
                'source': 'firebase',
                'plan_type': current_plan,
                'status': status,
                'message': f'Firebase shows {current_plan} plan with {status} status'
            }

        except Exception as e:
            logger.error(f"Error checking Firebase subscription: {str(e)}")
            return {'has_subscription': False, 'source': 'firebase', 'error': str(e)}

    def _check_stripe_subscription(self, user_email, plan_type):
        """Check Stripe for active billing subscriptions"""
        try:
            # Get customer from Stripe
            customer = self.get_customer_by_email(user_email)
            if not customer:
                return {'has_subscription': False, 'source': 'stripe', 'message': 'No Stripe customer found'}

            # Get all active subscriptions for this customer
            subscriptions = stripe.Subscription.list(
                customer=customer.id,
                status='active',
                limit=10
            )

            if not subscriptions.data:
                return {'has_subscription': False, 'source': 'stripe', 'message': 'No active Stripe subscriptions'}

            for subscription in subscriptions.data:
                # Check subscription metadata for plan type
                sub_plan_type = subscription.get('metadata', {}).get('plan_type')

                if sub_plan_type == plan_type:
                    return {
                        'has_subscription': True,
                        'source': 'stripe',
                        'subscription_id': subscription.id,
                        'plan_type': sub_plan_type,
                        'message': f'User has active {plan_type} subscription in Stripe'
                    }

                # Check if user has any active subscription (for upgrade logic)
                if sub_plan_type in ['basic', 'professional']:
                    return {
                        'has_subscription': True,
                        'source': 'stripe',
                        'subscription_id': subscription.id,
                        'plan_type': sub_plan_type,
                        'current_plan': sub_plan_type,
                        'requested_plan': plan_type,
                        'message': f'User has active {sub_plan_type} subscription in Stripe, requesting {plan_type}'
                    }

            return {'has_subscription': False, 'source': 'stripe', 'message': 'No matching active subscriptions in Stripe'}

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error checking subscription for {user_email}: {str(e)}")
            return {'has_subscription': False, 'source': 'stripe', 'error': f'Stripe error: {str(e)}'}

    def _reconcile_subscription_status(self, firebase_result, stripe_result, user_email, plan_type):
        """
        Reconcile subscription status between Firebase and Stripe.
        Priority: Stripe (billing truth) > Firebase (app state)
        """
        try:
            # If both have errors, return error
            if firebase_result.get('error') and stripe_result.get('error'):
                return {'error': 'Unable to check subscription status in both Firebase and Stripe'}

            # If Stripe has an active subscription, it's the source of truth for billing
            if stripe_result.get('has_subscription'):
                logger.info(f"Stripe shows active subscription for {user_email}")
                return stripe_result

            # If Firebase shows active subscription but Stripe doesn't, there might be a sync issue
            if firebase_result.get('has_subscription') and firebase_result.get('status') == 'active':
                logger.warning(f"Firebase shows active subscription for {user_email} but Stripe doesn't - possible sync issue")

                # For safety, we'll trust Firebase if it shows a paid plan but warn about the discrepancy
                if firebase_result.get('plan_type') in ['basic', 'professional']:
                    # Add a warning to the result
                    result = firebase_result.copy()
                    result['warning'] = 'Subscription found in Firebase but not in Stripe - please verify billing status'
                    result['sync_issue'] = True
                    return result

            # If neither has active subscription, user is free
            logger.info(f"No active subscription found for {user_email} in either Firebase or Stripe")
            return {
                'has_subscription': False,
                'message': 'No active subscription found',
                'firebase_status': firebase_result.get('message', 'Unknown'),
                'stripe_status': stripe_result.get('message', 'Unknown')
            }

        except Exception as e:
            logger.error(f"Error reconciling subscription status: {str(e)}")
            return {'error': f'Error reconciling subscription status: {str(e)}'}
