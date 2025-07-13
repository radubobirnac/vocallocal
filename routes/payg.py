"""
Pay-As-You-Go routes for VocalLocal
Handles overage tracking, pricing display, and payment processing
"""

import logging
from flask import Blueprint, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from services.overage_tracking_service import OverageTrackingService
from services.payg_service import PayAsYouGoService
from services.payment_service import PaymentService
import stripe
import os

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('payg', __name__, url_prefix='/payg')

@bp.route('/status', methods=['GET'])
@login_required
def get_overage_status():
    """
    Get user's current overage status and outstanding charges
    """
    try:
        user_email = current_user.email
        status = OverageTrackingService.get_user_overage_status(user_email)
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Error getting overage status for {current_user.email}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/pricing', methods=['GET'])
@login_required
def get_pricing():
    """
    Get pay-as-you-go pricing information
    """
    try:
        pricing = OverageTrackingService.get_payg_pricing_display()
        
        return jsonify({
            'success': True,
            'pricing': pricing
        })
        
    except Exception as e:
        logger.error(f"Error getting PAYG pricing: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/create-payment-session', methods=['POST'])
@login_required
def create_payment_session():
    """
    Create Stripe checkout session for paying outstanding charges
    """
    try:
        user_email = current_user.email
        
        # Get current overage status
        status = OverageTrackingService.get_user_overage_status(user_email)
        
        if not status.get('eligible'):
            return jsonify({
                'error': status.get('reason', 'Not eligible for pay-as-you-go')
            }), 400
        
        outstanding_amount = status.get('combined_outstanding', 0)
        
        if outstanding_amount <= 0:
            return jsonify({
                'error': 'No outstanding charges to pay'
            }), 400
        
        # Create Stripe checkout session
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        # Get or create customer
        payment_service = PaymentService()
        customer = payment_service._get_or_create_customer(user_email)
        
        # Create success and cancel URLs
        success_url = request.url_root + 'dashboard?payg_payment=success'
        cancel_url = request.url_root + 'dashboard?payg_payment=cancelled'
        
        # Create checkout session for one-time payment
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'VocalLocal Pay-as-you-go Usage',
                        'description': f'Outstanding usage charges for {user_email}',
                        'metadata': {
                            'type': 'payg_overage',
                            'user_email': user_email
                        }
                    },
                    'unit_amount': int(outstanding_amount * 100),  # Convert to cents
                },
                'quantity': 1,
            }],
            mode='payment',  # One-time payment
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_email': user_email,
                'type': 'payg_overage',
                'amount': outstanding_amount
            }
        )
        
        logger.info(f"Created PAYG payment session for {user_email}: ${outstanding_amount:.2f}")
        
        return jsonify({
            'success': True,
            'session_id': session.id,
            'checkout_url': session.url,
            'amount': outstanding_amount
        })
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating PAYG payment session: {str(e)}")
        return jsonify({
            'error': f'Payment system error: {str(e)}'
        }), 500
    except Exception as e:
        logger.error(f"Error creating PAYG payment session: {str(e)}")
        return jsonify({
            'error': f'Unexpected error: {str(e)}'
        }), 500

@bp.route('/simulate-overage', methods=['POST'])
@login_required
def simulate_overage():
    """
    Simulate overage usage for testing (admin only)
    """
    try:
        # Check if user is admin
        if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'super_user']:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_email = data.get('user_email', current_user.email)
        service_type = data.get('service_type')
        amount = data.get('amount')
        
        if not service_type or not amount:
            return jsonify({'error': 'service_type and amount are required'}), 400
        
        # Record the overage
        result = OverageTrackingService.record_overage_usage(user_email, service_type, amount)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error simulating overage: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/payment-history', methods=['GET'])
@login_required
def get_payment_history():
    """
    Get user's PAYG payment history
    """
    try:
        from services.user_account_service import UserAccountService
        
        user_email = current_user.email
        user_id = user_email.replace('.', ',')
        user_account = UserAccountService.get_user_account(user_id)
        
        if not user_account:
            return jsonify({
                'success': True,
                'payments': []
            })
        
        payment_history = user_account.get('billing', {}).get('payAsYouGo', {}).get('paymentHistory', [])
        
        # Sort by payment date (newest first)
        sorted_history = sorted(payment_history, key=lambda x: x.get('paymentDate', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'payments': sorted_history[:10]  # Last 10 payments
        })
        
    except Exception as e:
        logger.error(f"Error getting PAYG payment history: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/enable', methods=['POST'])
@login_required
def enable_payg():
    """
    Enable pay-as-you-go for the current user
    """
    try:
        user_email = current_user.email
        result = PayAsYouGoService.enable_payg(user_email)

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error enabling PAYG for {current_user.email}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/disable', methods=['POST'])
@login_required
def disable_payg():
    """
    Disable pay-as-you-go for the current user
    """
    try:
        user_email = current_user.email
        result = PayAsYouGoService.disable_payg(user_email)

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error disabling PAYG for {current_user.email}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/service-status', methods=['GET'])
@login_required
def get_service_status():
    """
    Get service-specific PAYG status for pricing page display
    """
    try:
        user_email = current_user.email

        # Get overall PAYG status
        payg_status = PayAsYouGoService.get_user_payg_status(user_email)

        # Get service-specific status
        service_status = PayAsYouGoService.get_service_specific_status(user_email)

        return jsonify({
            'success': True,
            'payg_status': payg_status,
            'service_status': service_status
        })

    except Exception as e:
        logger.error(f"Error getting service status for {current_user.email}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/clear-charges', methods=['POST'])
@login_required
def clear_charges():
    """
    Clear outstanding charges (admin only, for testing)
    """
    try:
        # Check if user is admin
        if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'super_user']:
            return jsonify({'error': 'Admin access required'}), 403

        data = request.get_json()
        user_email = data.get('user_email', current_user.email) if data else current_user.email

        result = OverageTrackingService.clear_outstanding_charges(user_email)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error clearing charges: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers for PAYG blueprint
@bp.errorhandler(404)
def payg_not_found(error):
    return jsonify({'error': 'PAYG endpoint not found'}), 404

@bp.errorhandler(500)
def payg_internal_error(error):
    logger.error(f"PAYG internal error: {str(error)}")
    return jsonify({'error': 'PAYG system error'}), 500
