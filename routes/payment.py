"""
Payment routes for VocalLocal
Handles Stripe checkout, webhooks, and customer portal
"""

import logging
from flask import Blueprint, request, jsonify, redirect, url_for, current_app
from flask_login import login_required, current_user
from services.payment_service import PaymentService

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('payment', __name__, url_prefix='/payment')

# Initialize payment service
payment_service = PaymentService()

@bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """
    Create Stripe checkout session for subscription upgrade
    
    Expected JSON payload:
    {
        "plan_type": "basic" or "professional"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        plan_type = data.get('plan_type')
        if not plan_type:
            return jsonify({'error': 'Plan type is required'}), 400
        
        if plan_type not in ['basic', 'professional']:
            return jsonify({'error': 'Invalid plan type'}), 400
        
        # Get user email
        user_email = current_user.email
        
        # Create success and cancel URLs
        success_url = request.url_root + 'dashboard?payment=success&plan=' + plan_type
        cancel_url = request.url_root + 'dashboard?payment=cancelled'
        
        # Create checkout session
        result = payment_service.create_checkout_session(
            user_email=user_email,
            plan_type=plan_type,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if 'error' in result:
            logger.error(f"Checkout session creation failed for {user_email}: {result['error']}")
            return jsonify({'error': result['error']}), 400
        
        logger.info(f"Created checkout session for {user_email}, plan: {plan_type}")
        
        return jsonify({
            'success': True,
            'session_id': result['session_id'],
            'checkout_url': result['checkout_url']
        })
        
    except Exception as e:
        logger.error(f"Error in create_checkout_session: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhook events
    This endpoint receives notifications from Stripe about payment events
    """
    try:
        # Get raw payload and signature
        payload = request.get_data()
        signature = request.headers.get('Stripe-Signature')
        
        if not signature:
            logger.error("Missing Stripe signature in webhook request")
            return jsonify({'error': 'Missing signature'}), 400
        
        # Process webhook event
        result = payment_service.handle_webhook_event(payload, signature)
        
        if 'error' in result:
            status_code = result.get('status_code', 400)
            logger.error(f"Webhook processing failed: {result['error']}")
            return jsonify({'error': result['error']}), status_code
        
        logger.info("Webhook processed successfully")
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in webhook handler: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/customer-portal', methods=['POST'])
@login_required
def customer_portal():
    """
    Create customer portal session for subscription management
    Allows users to update payment methods, view invoices, cancel subscriptions
    """
    try:
        # Get user's Stripe customer ID
        user_email = current_user.email
        customer = payment_service.get_customer_by_email(user_email)
        
        if not customer:
            return jsonify({'error': 'No subscription found'}), 404
        
        # Create return URL
        return_url = request.url_root + 'dashboard'
        
        # Create customer portal session
        result = payment_service.create_customer_portal_session(
            customer_id=customer.id,
            return_url=return_url
        )
        
        if 'error' in result:
            logger.error(f"Customer portal creation failed for {user_email}: {result['error']}")
            return jsonify({'error': result['error']}), 400
        
        logger.info(f"Created customer portal session for {user_email}")
        
        return jsonify({
            'success': True,
            'portal_url': result['portal_url']
        })
        
    except Exception as e:
        logger.error(f"Error in customer_portal: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/subscription-status', methods=['GET'])
@login_required
def subscription_status():
    """
    Get current subscription status for the user
    """
    try:
        user_email = current_user.email
        customer = payment_service.get_customer_by_email(user_email)
        
        if not customer:
            return jsonify({
                'success': True,
                'has_subscription': False,
                'plan_type': 'free'
            })
        
        # Get active subscriptions
        import stripe
        subscriptions = stripe.Subscription.list(
            customer=customer.id,
            status='active',
            limit=1
        )
        
        if not subscriptions.data:
            return jsonify({
                'success': True,
                'has_subscription': False,
                'plan_type': 'free'
            })
        
        subscription = subscriptions.data[0]
        plan_type = subscription.metadata.get('plan_type', 'unknown')
        
        return jsonify({
            'success': True,
            'has_subscription': True,
            'plan_type': plan_type,
            'status': subscription.status,
            'current_period_end': subscription.current_period_end
        })
        
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/test-webhook', methods=['GET'])
def test_webhook():
    """
    Test endpoint to verify webhook URL is accessible
    Returns 200 for GET requests to confirm endpoint exists
    """
    return jsonify({
        'message': 'Webhook endpoint is accessible',
        'method': 'GET',
        'note': 'Actual webhooks should use POST method'
    }), 200

@bp.route('/health', methods=['GET'])
def payment_health():
    """
    Health check endpoint for payment system
    """
    try:
        # Test Stripe API connectivity
        import stripe
        import os
        
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        # Simple API call to test connectivity
        stripe.Account.retrieve()
        
        return jsonify({
            'status': 'healthy',
            'stripe_connected': True,
            'webhook_endpoint': '/payment/webhook'
        }), 200
        
    except Exception as e:
        logger.error(f"Payment health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'stripe_connected': False,
            'error': str(e)
        }), 500

# Error handlers for payment blueprint
@bp.errorhandler(404)
def payment_not_found(error):
    return jsonify({'error': 'Payment endpoint not found'}), 404

@bp.errorhandler(500)
def payment_internal_error(error):
    logger.error(f"Payment internal error: {str(error)}")
    return jsonify({'error': 'Payment system error'}), 500
