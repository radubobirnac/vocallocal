"""
Overage Tracking Service for VocalLocal
Tracks usage beyond subscription limits and calculates pay-as-you-go charges
"""

import logging
import time
from datetime import datetime
from services.user_account_service import UserAccountService
from services.usage_validation_service import UsageValidationService

logger = logging.getLogger(__name__)

class OverageTrackingService:
    """Service for tracking usage overages and calculating PAYG charges"""
    
    # Pay-as-you-go pricing per unit (when subscription limits are exceeded)
    PAYG_PRICING = {
        'transcription': 0.10,    # $0.10 per minute
        'translation': 0.001,     # $0.001 per word  
        'tts': 0.15,             # $0.15 per minute
        'interpretation': 0.25    # $0.25 per request
    }
    
    # Minimum charge thresholds (to avoid micro-transactions)
    MIN_CHARGE_THRESHOLDS = {
        'transcription': 1.0,     # Minimum 1 minute
        'translation': 100.0,     # Minimum 100 words
        'tts': 1.0,              # Minimum 1 minute  
        'interpretation': 1.0     # Minimum 1 request
    }
    
    @staticmethod
    def get_user_overage_status(user_email):
        """
        Get user's current overage status across all services
        
        Args:
            user_email (str): User's email address
            
        Returns:
            dict: Overage status and outstanding charges
        """
        try:
            user_id = user_email.replace('.', ',')
            user_account = UserAccountService.get_user_account(user_id)
            
            if not user_account:
                return {'error': 'User not found'}
            
            # Check if user is eligible for PAYG (Basic or Professional plan)
            subscription = user_account.get('subscription', {})
            plan_type = subscription.get('planType', 'free')
            status = subscription.get('status', 'inactive')
            
            # Check if user is eligible AND has enabled PAYG
            eligible = plan_type in ['basic', 'professional'] and status == 'active'
            payg_enabled = subscription.get('payAsYouGo', {}).get('enabled', False)

            if not eligible:
                return {
                    'eligible': False,
                    'enabled': False,
                    'reason': 'Pay-as-you-go requires an active Basic or Professional subscription',
                    'current_plan': plan_type,
                    'status': status
                }

            if not payg_enabled:
                return {
                    'eligible': True,
                    'enabled': False,
                    'reason': 'Pay-as-you-go is not enabled. Enable it on the pricing page.',
                    'current_plan': plan_type,
                    'status': status
                }
            
            # Get usage data
            usage_data = UsageValidationService.get_user_usage_data(user_email)
            
            # Calculate overages for each service
            overages = {}
            total_outstanding = 0.0
            has_overages = False
            
            for service in ['transcription', 'translation', 'tts']:
                service_key = f'{service}Minutes' if service in ['transcription', 'tts'] else f'{service}Words'
                
                used = usage_data['used'].get(service_key, 0)
                limit = usage_data['limits'].get(service_key, 0)
                overage_amount = max(0, used - limit)
                
                if overage_amount > 0:
                    # Check if overage meets minimum threshold
                    threshold = OverageTrackingService.MIN_CHARGE_THRESHOLDS.get(service, 0)
                    if overage_amount >= threshold:
                        charge = overage_amount * OverageTrackingService.PAYG_PRICING[service]
                        overages[service] = {
                            'amount': overage_amount,
                            'unit': 'minutes' if service in ['transcription', 'tts'] else 'words',
                            'rate': OverageTrackingService.PAYG_PRICING[service],
                            'charge': charge,
                            'used': used,
                            'limit': limit
                        }
                        total_outstanding += charge
                        has_overages = True
            
            # Get existing outstanding charges from Firebase
            existing_outstanding = user_account.get('billing', {}).get('payAsYouGo', {}).get('outstandingCharges', 0)
            
            return {
                'eligible': True,
                'enabled': True,
                'has_overages': has_overages,
                'overages': overages,
                'total_outstanding': total_outstanding,
                'existing_outstanding': existing_outstanding,
                'combined_outstanding': total_outstanding + existing_outstanding,
                'plan_type': plan_type,
                'billing_cycle_end': usage_data.get('reset_date'),
                'pricing': OverageTrackingService.PAYG_PRICING
            }
            
        except Exception as e:
            logger.error(f"Error getting overage status for {user_email}: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def record_overage_usage(user_email, service_type, amount):
        """
        Record usage that exceeds subscription limits
        
        Args:
            user_email (str): User's email address
            service_type (str): Type of service (transcription, translation, tts)
            amount (float): Amount of overage usage
            
        Returns:
            dict: Recording result
        """
        try:
            user_id = user_email.replace('.', ',')
            user_ref = UserAccountService.get_ref(f'users/{user_id}')
            user_data = user_ref.get()
            
            if not user_data:
                return {'success': False, 'error': 'User not found'}
            
            # Calculate charge for this overage
            rate = OverageTrackingService.PAYG_PRICING.get(service_type, 0)
            charge = amount * rate
            
            # Get current overage data
            current_overages = user_data.get('billing', {}).get('payAsYouGo', {}).get('overageUsage', {})
            current_outstanding = user_data.get('billing', {}).get('payAsYouGo', {}).get('outstandingCharges', 0)
            
            # Update overage usage
            service_overages = current_overages.get(service_type, {'amount': 0, 'charge': 0})
            service_overages['amount'] += amount
            service_overages['charge'] += charge
            service_overages['lastUpdated'] = int(time.time() * 1000)
            
            current_overages[service_type] = service_overages
            
            # Update outstanding charges
            new_outstanding = current_outstanding + charge
            
            # Prepare update data
            update_data = {
                'billing/payAsYouGo/overageUsage': current_overages,
                'billing/payAsYouGo/outstandingCharges': new_outstanding,
                'billing/payAsYouGo/lastOverageUpdate': int(time.time() * 1000)
            }
            
            # Apply update
            user_ref.update(update_data)
            
            logger.info(f"Recorded overage for {user_email}: {amount} {service_type} = ${charge:.2f}")
            
            return {
                'success': True,
                'service_type': service_type,
                'overage_amount': amount,
                'charge': charge,
                'total_outstanding': new_outstanding
            }
            
        except Exception as e:
            logger.error(f"Error recording overage usage: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_payg_pricing_display():
        """
        Get formatted pricing information for display
        
        Returns:
            dict: Formatted pricing information
        """
        return {
            'transcription': {
                'rate': OverageTrackingService.PAYG_PRICING['transcription'],
                'unit': 'per minute',
                'description': 'Additional transcription beyond your plan limit'
            },
            'translation': {
                'rate': OverageTrackingService.PAYG_PRICING['translation'], 
                'unit': 'per word',
                'description': 'Additional translation beyond your plan limit'
            },
            'tts': {
                'rate': OverageTrackingService.PAYG_PRICING['tts'],
                'unit': 'per minute', 
                'description': 'Additional text-to-speech beyond your plan limit'
            },
            'interpretation': {
                'rate': OverageTrackingService.PAYG_PRICING['interpretation'],
                'unit': 'per request',
                'description': 'AI interpretation requests'
            }
        }
    
    @staticmethod
    def clear_outstanding_charges(user_email, payment_intent_id=None):
        """
        Clear outstanding charges after payment
        
        Args:
            user_email (str): User's email address
            payment_intent_id (str): Stripe payment intent ID (optional)
            
        Returns:
            dict: Clear result
        """
        try:
            user_id = user_email.replace('.', ',')
            user_ref = UserAccountService.get_ref(f'users/{user_id}')
            user_data = user_ref.get()
            
            if not user_data:
                return {'success': False, 'error': 'User not found'}
            
            # Get current outstanding amount for record keeping
            outstanding_amount = user_data.get('billing', {}).get('payAsYouGo', {}).get('outstandingCharges', 0)
            
            # Create payment record
            payment_record = {
                'amount': outstanding_amount,
                'paymentDate': int(time.time() * 1000),
                'paymentIntentId': payment_intent_id,
                'type': 'payg_overage',
                'status': 'completed'
            }
            
            # Clear outstanding charges and overage usage
            update_data = {
                'billing/payAsYouGo/outstandingCharges': 0,
                'billing/payAsYouGo/overageUsage': {},
                'billing/payAsYouGo/lastPayment': payment_record,
                'billing/payAsYouGo/paymentCleared': int(time.time() * 1000)
            }
            
            # Add to payment history
            payment_history = user_data.get('billing', {}).get('payAsYouGo', {}).get('paymentHistory', [])
            payment_history.append(payment_record)
            update_data['billing/payAsYouGo/paymentHistory'] = payment_history
            
            # Apply update
            user_ref.update(update_data)
            
            logger.info(f"Cleared outstanding charges for {user_email}: ${outstanding_amount:.2f}")
            
            return {
                'success': True,
                'amount_cleared': outstanding_amount,
                'payment_record': payment_record
            }
            
        except Exception as e:
            logger.error(f"Error clearing outstanding charges: {str(e)}")
            return {'success': False, 'error': str(e)}
