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

        # Check for existing active subscriptions
        subscription_check = payment_service.check_existing_subscription(user_email, plan_type)

        if subscription_check.get('error'):
            return jsonify({'error': subscription_check['error']}), 500

        if subscription_check.get('has_subscription'):
            current_plan = subscription_check.get('current_plan', subscription_check.get('plan_type'))

            if current_plan == plan_type:
                # User already has the exact same plan
                return jsonify({
                    'error': f'You already have an active {plan_type.title()} Plan subscription. Please manage your existing subscription instead.',
                    'subscription_exists': True,
                    'current_plan': current_plan
                }), 400
            else:
                # User has a different plan - this could be an upgrade/downgrade
                plan_hierarchy = {'basic': 1, 'professional': 2}
                current_level = plan_hierarchy.get(current_plan, 0)
                requested_level = plan_hierarchy.get(plan_type, 0)

                if requested_level <= current_level:
                    # Trying to downgrade or get same level plan
                    return jsonify({
                        'error': f'You already have an active {current_plan.title()} Plan subscription. To change plans, please manage your subscription through the customer portal.',
                        'subscription_exists': True,
                        'current_plan': current_plan,
                        'requested_plan': plan_type
                    }), 400
        
        # Create success and cancel URLs
        success_url = request.url_root + '?payment=success&plan=' + plan_type
        cancel_url = request.url_root + 'pricing?payment=cancelled'
        
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
        return_url = request.url_root + 'pricing'
        
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

@bp.route('/manual-upgrade', methods=['POST'])
@login_required
def manual_upgrade():
    """
    Manual endpoint to upgrade user subscription
    This is a temporary solution for when webhooks fail
    """
    try:
        data = request.get_json()
        user_email = data.get('user_email') or current_user.email
        plan_type = data.get('plan_type', 'basic')

        if not user_email:
            return jsonify({'error': 'User email required'}), 400

        # Update user subscription
        user_id = user_email.replace('.', ',')

        from services.user_account_service import UserAccountService
        UserAccountService.update_subscription(
            user_id=user_id,
            plan_type=plan_type,
            status='active',
            billing_cycle='monthly',
            payment_method='stripe'
        )

        logger.info(f"Manually upgraded {user_email} to {plan_type} plan")

        return jsonify({
            'success': True,
            'message': f'User {user_email} upgraded to {plan_type} plan',
            'user_email': user_email,
            'plan_type': plan_type
        }), 200

    except Exception as e:
        logger.error(f"Error in manual upgrade: {str(e)}")
        return jsonify({'error': str(e)}), 500

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

@bp.route('/billing-history', methods=['GET'])
@login_required
def billing_history():
    """
    Get billing history for the current user
    """
    try:
        from services.user_account_service import UserAccountService

        user_email = current_user.email
        user_id = user_email.replace('.', ',')

        # Get billing history from Firebase
        billing_ref = UserAccountService.get_ref(f'users/{user_id}/billing/invoices')
        billing_data = billing_ref.get()

        invoices = []
        if billing_data:
            # Convert Firebase data to list format
            for invoice_key, invoice_data in billing_data.items():
                invoices.append({
                    'id': invoice_key,
                    'invoiceId': invoice_data.get('invoiceId'),
                    'amount': invoice_data.get('amount', 0),
                    'currency': invoice_data.get('currency', 'USD'),
                    'paymentDate': invoice_data.get('paymentDate'),
                    'planName': invoice_data.get('planName', 'Unknown Plan'),
                    'planType': invoice_data.get('planType'),
                    'status': invoice_data.get('status', 'paid')
                })

            # Sort by payment date (newest first)
            invoices.sort(key=lambda x: x.get('paymentDate', 0), reverse=True)

        return jsonify({
            'success': True,
            'invoices': invoices
        })

    except Exception as e:
        logger.error(f"Error retrieving billing history for {current_user.email}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Unable to retrieve billing history'
        }), 500

@bp.route('/download-invoice/<invoice_id>', methods=['GET'])
@login_required
def download_invoice(invoice_id):
    """
    Download invoice from Stripe
    """
    try:
        import stripe

        # Verify the invoice belongs to the current user
        user_email = current_user.email
        customer = payment_service.get_customer_by_email(user_email)

        if not customer:
            return jsonify({'error': 'No customer found'}), 404

        # Retrieve invoice from Stripe
        invoice = stripe.Invoice.retrieve(invoice_id)

        # Verify the invoice belongs to this customer
        if invoice.customer != customer.id:
            return jsonify({'error': 'Invoice not found'}), 404

        # Redirect to Stripe's hosted invoice page
        if invoice.hosted_invoice_url:
            return redirect(invoice.hosted_invoice_url)
        else:
            return jsonify({'error': 'Invoice not available for download'}), 404

    except stripe.error.InvalidRequestError:
        return jsonify({'error': 'Invoice not found'}), 404
    except Exception as e:
        logger.error(f"Error downloading invoice {invoice_id}: {str(e)}")
        return jsonify({'error': 'Unable to download invoice'}), 500

# Error handlers for payment blueprint
@bp.errorhandler(404)
def payment_not_found(error):
    return jsonify({'error': 'Payment endpoint not found'}), 404

@bp.errorhandler(500)
def payment_internal_error(error):
    logger.error(f"Payment internal error: {str(error)}")
    return jsonify({'error': 'Payment system error'}), 500
