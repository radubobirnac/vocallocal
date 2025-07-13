"""
Pay-As-You-Go Service for VocalLocal
Handles credit purchases, usage tracking, and validation
"""

import logging
import time
from datetime import datetime, timedelta
from services.user_account_service import UserAccountService
from services.payment_service import PaymentService
import stripe
import os

logger = logging.getLogger(__name__)

class PayAsYouGoService:
    """Service for managing pay-as-you-go credits"""
    
    # Credit conversion rates (how much service 1 credit provides)
    CREDIT_CONVERSION_RATES = {
        'transcription': 1.0,      # 1 credit = 1 minute
        'translation': 100.0,      # 1 credit = 100 words  
        'tts': 1.0,               # 1 credit = 1 minute
        'interpretation': 1.0      # 1 credit = 1 request
    }
    
    # Credit packages available for purchase
    CREDIT_PACKAGES = {
        'small': {
            'id': 'small',
            'name': 'Small Package',
            'credits': 50,
            'price': 4.99,
            'description': '50 credits for light usage'
        },
        'medium': {
            'id': 'medium', 
            'name': 'Medium Package',
            'credits': 150,
            'price': 12.99,
            'description': '150 credits for regular usage'
        },
        'large': {
            'id': 'large',
            'name': 'Large Package', 
            'credits': 300,
            'price': 19.99,
            'description': '300 credits for heavy usage'
        },
        'bulk': {
            'id': 'bulk',
            'name': 'Bulk Package',
            'credits': 1000, 
            'price': 59.99,
            'description': '1000 credits for enterprise usage'
        }
    }
    
    def __init__(self):
        """Initialize the service"""
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
    @staticmethod
    def get_user_payg_status(user_email):
        """
        Get user's pay-as-you-go status and eligibility

        Args:
            user_email (str): User's email address

        Returns:
            dict: PAYG status information
        """
        try:
            user_id = user_email.replace('.', ',')
            user_account = UserAccountService.get_user_account(user_id)

            if not user_account:
                return {'enabled': False, 'eligible': False, 'reason': 'User account not found'}

            # Check eligibility (Basic or Professional plan)
            subscription = user_account.get('subscription', {})
            plan_type = subscription.get('planType', 'free')
            status = subscription.get('status', 'inactive')

            eligible = plan_type in ['basic', 'professional'] and status == 'active'
            enabled = subscription.get('payAsYouGo', {}).get('enabled', False)

            # Get outstanding charges
            payg_billing = user_account.get('billing', {}).get('payAsYouGo', {})
            outstanding_charges = payg_billing.get('outstandingCharges', 0)

            return {
                'enabled': enabled,
                'eligible': eligible,
                'plan_type': plan_type,
                'status': status,
                'outstanding_charges': outstanding_charges,
                'reason': 'Pay-as-you-go requires an active Basic or Professional subscription' if not eligible else None,
                'enabled_date': subscription.get('payAsYouGo', {}).get('enabledDate'),
                'last_payment': payg_billing.get('lastPayment')
            }

        except Exception as e:
            logger.error(f"Error getting PAYG status for {user_email}: {str(e)}")
            return {'enabled': False, 'eligible': False, 'error': str(e)}
    
    @staticmethod
    def calculate_credits_needed(service_type, amount):
        """
        Calculate how many credits are needed for a service
        
        Args:
            service_type (str): Type of service (transcription, translation, tts, interpretation)
            amount (float): Amount of service (minutes, words, requests)
            
        Returns:
            float: Credits needed
        """
        if service_type not in PayAsYouGoService.CREDIT_CONVERSION_RATES:
            raise ValueError(f"Unknown service type: {service_type}")
            
        rate = PayAsYouGoService.CREDIT_CONVERSION_RATES[service_type]
        credits_needed = amount / rate
        
        logger.info(f"Credits calculation: {amount} {service_type} = {credits_needed:.2f} credits")
        return credits_needed
    
    @staticmethod
    def validate_credit_usage(user_email, service_type, amount):
        """
        Validate if user has enough credits for a service
        
        Args:
            user_email (str): User's email address
            service_type (str): Type of service
            amount (float): Amount of service needed
            
        Returns:
            dict: Validation result
        """
        try:
            credits_needed = PayAsYouGoService.calculate_credits_needed(service_type, amount)
            user_credits = PayAsYouGoService.get_user_credits(user_email)
            
            available_credits = user_credits.get('credits', 0)
            has_enough = available_credits >= credits_needed
            
            return {
                'allowed': has_enough,
                'credits_needed': credits_needed,
                'credits_available': available_credits,
                'credits_remaining': max(0, available_credits - credits_needed),
                'service_type': service_type,
                'amount': amount,
                'message': f"{'✓' if has_enough else '✗'} {credits_needed:.1f} credits needed, {available_credits:.1f} available"
            }
            
        except Exception as e:
            logger.error(f"Error validating credit usage: {str(e)}")
            return {
                'allowed': False,
                'error': str(e),
                'message': 'Error validating credit usage'
            }
    
    @staticmethod
    def deduct_credits(user_email, service_type, amount):
        """
        Deduct credits from user's account
        
        Args:
            user_email (str): User's email address
            service_type (str): Type of service
            amount (float): Amount of service used
            
        Returns:
            dict: Deduction result
        """
        try:
            credits_needed = PayAsYouGoService.calculate_credits_needed(service_type, amount)
            user_id = user_email.replace('.', ',')
            
            # Get current user data
            user_ref = UserAccountService.get_ref(f'users/{user_id}')
            user_data = user_ref.get()
            
            if not user_data:
                return {'success': False, 'error': 'User not found'}
            
            # Get current credits
            current_credits = user_data.get('billing', {}).get('payAsYouGo', {}).get('creditsRemaining', 0)
            current_used = user_data.get('billing', {}).get('payAsYouGo', {}).get('creditsUsed', 0)
            
            if current_credits < credits_needed:
                return {
                    'success': False,
                    'error': 'Insufficient credits',
                    'credits_needed': credits_needed,
                    'credits_available': current_credits
                }
            
            # Update credits
            new_credits = current_credits - credits_needed
            new_used = current_used + credits_needed
            
            # Prepare update data
            update_data = {
                f'billing/payAsYouGo/creditsRemaining': new_credits,
                f'billing/payAsYouGo/creditsUsed': new_used,
                f'billing/payAsYouGo/lastUsed': int(time.time() * 1000)
            }
            
            # Apply update
            user_ref.update(update_data)
            
            logger.info(f"Deducted {credits_needed:.2f} credits from {user_email} for {service_type}")
            
            return {
                'success': True,
                'credits_deducted': credits_needed,
                'credits_remaining': new_credits,
                'service_type': service_type,
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"Error deducting credits: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_available_packages():
        """
        Get all available credit packages
        
        Returns:
            dict: Available packages
        """
        return PayAsYouGoService.CREDIT_PACKAGES
    
    def create_credit_purchase_session(self, user_email, package_id, success_url, cancel_url):
        """
        Create Stripe checkout session for credit purchase
        
        Args:
            user_email (str): User's email address
            package_id (str): ID of the credit package
            success_url (str): Success redirect URL
            cancel_url (str): Cancel redirect URL
            
        Returns:
            dict: Checkout session data or error
        """
        try:
            if package_id not in self.CREDIT_PACKAGES:
                return {'error': f'Invalid package ID: {package_id}'}
            
            package = self.CREDIT_PACKAGES[package_id]
            
            # Create or retrieve customer
            payment_service = PaymentService()
            customer = payment_service._get_or_create_customer(user_email)
            
            # Create checkout session for one-time payment
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': package['name'],
                            'description': package['description'],
                            'metadata': {
                                'type': 'payg_credits',
                                'package_id': package_id,
                                'credits': package['credits']
                            }
                        },
                        'unit_amount': int(package['price'] * 100),  # Convert to cents
                    },
                    'quantity': 1,
                }],
                mode='payment',  # One-time payment, not subscription
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_email': user_email,
                    'package_id': package_id,
                    'credits': package['credits'],
                    'type': 'payg_credits'
                }
            )
            
            logger.info(f"Created credit purchase session for {user_email}, package: {package_id}")
            
            return {
                'session_id': session.id,
                'checkout_url': session.url,
                'success': True,
                'package': package
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating credit purchase session: {str(e)}")
            return {'error': f'Payment system error: {str(e)}'}
        except Exception as e:
            logger.error(f"Error creating credit purchase session: {str(e)}")
            return {'error': f'Unexpected error: {str(e)}'}

    @staticmethod
    def fulfill_credit_purchase(user_email, package_id, payment_intent_id, amount_paid):
        """
        Fulfill credit purchase after successful payment

        Args:
            user_email (str): User's email address
            package_id (str): ID of the purchased package
            payment_intent_id (str): Stripe payment intent ID
            amount_paid (float): Amount paid in dollars

        Returns:
            dict: Fulfillment result
        """
        try:
            if package_id not in PayAsYouGoService.CREDIT_PACKAGES:
                return {'success': False, 'error': f'Invalid package ID: {package_id}'}

            package = PayAsYouGoService.CREDIT_PACKAGES[package_id]
            credits_to_add = package['credits']

            user_id = user_email.replace('.', ',')
            user_ref = UserAccountService.get_ref(f'users/{user_id}')
            user_data = user_ref.get()

            if not user_data:
                return {'success': False, 'error': 'User not found'}

            # Get current credits
            current_credits = user_data.get('billing', {}).get('payAsYouGo', {}).get('creditsRemaining', 0)
            new_credits = current_credits + credits_to_add

            # Create purchase record
            purchase_record = {
                'packageId': package_id,
                'credits': credits_to_add,
                'amount': amount_paid,
                'purchaseDate': int(time.time() * 1000),
                'stripePaymentIntentId': payment_intent_id,
                'status': 'completed'
            }

            # Update user account
            update_data = {
                'billing/payAsYouGo/creditsRemaining': new_credits,
                'billing/payAsYouGo/lastPurchase': int(time.time() * 1000),
                'subscription/payAsYouGo/enabled': True
            }

            # Add purchase to history
            purchase_history = user_data.get('subscription', {}).get('payAsYouGo', {}).get('purchaseHistory', [])
            purchase_history.append(purchase_record)
            update_data['subscription/payAsYouGo/purchaseHistory'] = purchase_history

            # Apply updates
            user_ref.update(update_data)

            logger.info(f"Fulfilled credit purchase for {user_email}: {credits_to_add} credits added")

            return {
                'success': True,
                'credits_added': credits_to_add,
                'total_credits': new_credits,
                'package': package,
                'purchase_record': purchase_record
            }

        except Exception as e:
            logger.error(f"Error fulfilling credit purchase: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_purchase_history(user_email, limit=10):
        """
        Get user's credit purchase history

        Args:
            user_email (str): User's email address
            limit (int): Maximum number of records to return

        Returns:
            list: Purchase history records
        """
        try:
            user_id = user_email.replace('.', ',')
            user_account = UserAccountService.get_user_account(user_id)

            if not user_account:
                return []

            purchase_history = user_account.get('subscription', {}).get('payAsYouGo', {}).get('purchaseHistory', [])

            # Sort by purchase date (newest first) and limit
            sorted_history = sorted(purchase_history, key=lambda x: x.get('purchaseDate', 0), reverse=True)
            return sorted_history[:limit]

        except Exception as e:
            logger.error(f"Error getting purchase history for {user_email}: {str(e)}")
            return []

    @staticmethod
    def enable_payg_for_user(user_email):
        """
        Enable pay-as-you-go for a user (typically called when they have a subscription)

        Args:
            user_email (str): User's email address

        Returns:
            dict: Result of enabling PAYG
        """
        try:
            user_id = user_email.replace('.', ',')
            user_ref = UserAccountService.get_ref(f'users/{user_id}')

            # Check if user has an active subscription
            user_data = user_ref.get()
            if not user_data:
                return {'success': False, 'error': 'User not found'}

            subscription = user_data.get('subscription', {})
            plan_type = subscription.get('planType', 'free')
            status = subscription.get('status', 'inactive')

            # Only enable PAYG for users with active Basic or Professional subscriptions
            if plan_type in ['basic', 'professional'] and status == 'active':
                update_data = {
                    'subscription/payAsYouGo/enabled': True
                }
                user_ref.update(update_data)

                logger.info(f"Enabled PAYG for {user_email} with {plan_type} plan")
                return {'success': True, 'message': f'Pay-as-you-go enabled for {plan_type} plan'}
            else:
                return {
                    'success': False,
                    'error': 'Pay-as-you-go requires an active Basic or Professional subscription',
                    'plan_type': plan_type,
                    'status': status
                }

        except Exception as e:
            logger.error(f"Error enabling PAYG for {user_email}: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def enable_payg(user_email):
        """
        Enable pay-as-you-go for an eligible user

        Args:
            user_email (str): User's email address

        Returns:
            dict: Result of enabling PAYG
        """
        try:
            # Check eligibility first
            status = PayAsYouGoService.get_user_payg_status(user_email)

            if not status.get('eligible'):
                return {
                    'success': False,
                    'error': status.get('reason', 'Not eligible for pay-as-you-go'),
                    'plan_type': status.get('plan_type'),
                    'status': status.get('status')
                }

            if status.get('enabled'):
                return {
                    'success': True,
                    'message': 'Pay-as-you-go is already enabled',
                    'already_enabled': True
                }

            # Enable PAYG
            user_id = user_email.replace('.', ',')
            user_ref = UserAccountService.get_ref(f'users/{user_id}')

            update_data = {
                'subscription/payAsYouGo/enabled': True,
                'subscription/payAsYouGo/enabledDate': int(time.time() * 1000),
                'subscription/payAsYouGo/enabledBy': 'user'
            }

            user_ref.update(update_data)

            logger.info(f"Enabled PAYG for {user_email}")

            return {
                'success': True,
                'message': 'Pay-as-you-go has been enabled',
                'enabled_date': update_data['subscription/payAsYouGo/enabledDate']
            }

        except Exception as e:
            logger.error(f"Error enabling PAYG for {user_email}: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def disable_payg(user_email):
        """
        Disable pay-as-you-go for a user

        Args:
            user_email (str): User's email address

        Returns:
            dict: Result of disabling PAYG
        """
        try:
            user_id = user_email.replace('.', ',')
            user_ref = UserAccountService.get_ref(f'users/{user_id}')
            user_data = user_ref.get()

            if not user_data:
                return {'success': False, 'error': 'User not found'}

            # Check if there are outstanding charges
            outstanding_charges = user_data.get('billing', {}).get('payAsYouGo', {}).get('outstandingCharges', 0)

            if outstanding_charges > 0:
                return {
                    'success': False,
                    'error': f'Cannot disable pay-as-you-go with outstanding charges of ${outstanding_charges:.2f}. Please pay outstanding charges first.',
                    'outstanding_charges': outstanding_charges
                }

            # Disable PAYG
            update_data = {
                'subscription/payAsYouGo/enabled': False,
                'subscription/payAsYouGo/disabledDate': int(time.time() * 1000),
                'subscription/payAsYouGo/disabledBy': 'user'
            }

            user_ref.update(update_data)

            logger.info(f"Disabled PAYG for {user_email}")

            return {
                'success': True,
                'message': 'Pay-as-you-go has been disabled'
            }

        except Exception as e:
            logger.error(f"Error disabling PAYG for {user_email}: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_service_specific_status(user_email):
        """
        Get service-specific PAYG status showing which services are on plan vs PAYG

        Args:
            user_email (str): User's email address

        Returns:
            dict: Service-specific status
        """
        try:
            from services.usage_validation_service import UsageValidationService

            # Get current usage data
            usage_data = UsageValidationService.get_user_usage_data(user_email)
            payg_status = PayAsYouGoService.get_user_payg_status(user_email)

            if not payg_status.get('enabled'):
                return {
                    'payg_enabled': False,
                    'services': {}
                }

            services_status = {}

            # Check each service
            for service in ['transcription', 'translation', 'tts']:
                if service == 'translation':
                    used_key = 'translationWords'
                    limit_key = 'translationWords'
                    unit = 'words'
                else:
                    used_key = f'{service}Minutes'
                    limit_key = f'{service}Minutes'
                    unit = 'minutes'

                used = usage_data['used'].get(used_key, 0)
                limit = usage_data['limits'].get(limit_key, 0)
                overage = max(0, used - limit)

                services_status[service] = {
                    'used': used,
                    'limit': limit,
                    'overage': overage,
                    'status': 'payg_active' if overage > 0 else 'on_plan',
                    'unit': unit,
                    'rate': PayAsYouGoService.CREDIT_CONVERSION_RATES.get(service, 0)
                }

            return {
                'payg_enabled': True,
                'services': services_status,
                'plan_type': usage_data.get('plan_type'),
                'outstanding_charges': payg_status.get('outstanding_charges', 0)
            }

        except Exception as e:
            logger.error(f"Error getting service-specific status for {user_email}: {str(e)}")
            return {'payg_enabled': False, 'error': str(e)}
