"""
Admin routes for VocalLocal
"""
import traceback
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from flask_login import current_user
from models.firebase_models import User, UserActivity, Transcription, Translation
from services.admin_subscription_service import AdminSubscriptionService
from services.user_account_service import UserAccountService
from services.payment_service import PaymentService
# Import RBAC decorators (will be used as we update routes)
try:
    from rbac import require_admin_or_special_auth, require_admin, api_require_admin, check_permission
except ImportError:
    # Fallback if RBAC module is not available
    def require_admin_or_special_auth():
        def decorator(f):
            return f
        return decorator

    def require_admin():
        def decorator(f):
            return f
        return decorator

    def api_require_admin():
        def decorator(f):
            return f
        return decorator

    def check_permission(permission):
        return False

# Create a blueprint for the admin routes
bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Admin dashboard for viewing metrics"""
    today_date = datetime.now().strftime("%Y-%m-%d")
    return render_template('admin_dashboard.html', today_date=today_date)

@bp.route('/user-usage', methods=['GET'])
def user_usage():
    """Admin dashboard for viewing user-specific usage metrics"""
    # Check if already authenticated with special admin credentials
    if session.get('special_admin_auth') != True:
        return redirect(url_for('admin.users'))

    # Get all users from Firebase
    users = User.get_all_users()

    # Get user transcriptions and translations
    user_data = {}
    for user in users:
        email = user.get('email')
        if not email:
            continue

        # Get user's transcriptions
        transcriptions = Transcription.get_by_user(email, limit=1000)

        # Get user's translations
        translations = Translation.get_by_user(email, limit=1000)

        # Calculate usage statistics
        transcription_count = len(transcriptions) if transcriptions else 0
        translation_count = len(translations) if translations else 0

        # Calculate total text length as a proxy for token usage
        transcription_chars = sum(len(t.get('text', '')) for t in transcriptions.values()) if transcriptions else 0
        translation_chars = sum(len(t.get('translated_text', '')) for t in translations.values()) if translations else 0

        # Store user data
        user_data[email] = {
            'username': user.get('username', email.split('@')[0]),
            'transcription_count': transcription_count,
            'translation_count': translation_count,
            'transcription_chars': transcription_chars,
            'translation_chars': translation_chars,
            'total_operations': transcription_count + translation_count,
            'total_chars': transcription_chars + translation_chars
        }

    return render_template('admin_user_usage.html', user_data=user_data)

@bp.route('/logout', methods=['GET'])
def logout():
    """Logout from special admin session"""
    if 'special_admin_auth' in session:
        session.pop('special_admin_auth')
        flash("You have been logged out from the admin area.", "info")
    return redirect(url_for('main.index'))

@bp.route('/api/users/<user_email>/role', methods=['PUT'])
def update_user_role(user_email):
    """API endpoint to update a user's role (admin only)"""
    # Check if already authenticated with special admin credentials OR has admin role
    if not (session.get('special_admin_auth') == True or
            (current_user.is_authenticated and getattr(current_user, 'role', 'normal_user') == 'admin')):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        new_role = data.get('role')

        if not new_role or new_role not in User.VALID_ROLES:
            return jsonify({
                'success': False,
                'error': f'Invalid role. Must be one of: {", ".join(User.VALID_ROLES)}'
            }), 400

        # Prevent demoting the current admin user if they're using role-based auth
        if (current_user.is_authenticated and
            current_user.email == user_email and
            getattr(current_user, 'role', 'normal_user') == 'admin' and
            new_role != 'admin'):
            return jsonify({
                'success': False,
                'error': 'Cannot demote yourself from admin role'
            }), 400

        # Update the user's role
        success = User.update_user_role(user_email, new_role)

        if success:
            # Log the role change
            admin_email = current_user.email if current_user.is_authenticated else 'special_admin@vocallocal.com'
            UserActivity.log(
                user_email=admin_email,
                activity_type='role_change',
                details=f'Changed role of {user_email} to {new_role}'
            )

            return jsonify({
                'success': True,
                'message': f'User role updated to {new_role}',
                'new_role': new_role
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update user role'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/users/<user_email>/role', methods=['GET'])
def get_user_role(user_email):
    """API endpoint to get a user's role (admin only)"""
    # Check if already authenticated with special admin credentials OR has admin role
    if not (session.get('special_admin_auth') == True or
            (current_user.is_authenticated and getattr(current_user, 'role', 'normal_user') == 'admin')):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        role = User.get_user_role(user_email)
        if role is None:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'email': user_email,
            'role': role,
            'valid_roles': User.VALID_ROLES
        })

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

# Note: /api/user/available-models endpoint moved to main.py to avoid URL prefix conflicts

@bp.route('/users', methods=['GET', 'POST'])
def users():
    """Admin dashboard for viewing registered users with special authentication"""
    # Check if already authenticated with special admin credentials
    if session.get('special_admin_auth') == True:
        # User is authenticated with special admin credentials
        # Get all users from Firebase
        users = User.get_all_users()

        # Get recent user activities
        activities = []
        try:
            activities_data = UserActivity.get_ref('user_activities').order_by_child('timestamp').limit_to_last(50).get()
            if activities_data:
                for activity_id, activity in activities_data.items():
                    activities.append(activity)
                # Sort activities by timestamp (newest first)
                activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        except Exception as e:
            print(f"Error fetching user activities: {str(e)}")

        return render_template('admin_users.html', users=users, activities=activities)

    # Not authenticated with special admin credentials yet
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check for specific credentials
        if username == 'Radu' and password == 'Fasteasy':
            # Set session variable to indicate special admin authentication
            session['special_admin_auth'] = True

            # Log this special admin login
            if current_user.is_authenticated:
                user_email = current_user.email
            else:
                user_email = 'special_admin@vocallocal.com'

            UserActivity.log(
                user_email=user_email,
                activity_type='admin_login',
                details='Special admin authentication'
            )

            # Redirect to the same page to show the admin dashboard
            return redirect(url_for('admin.users'))
        else:
            flash("Invalid admin credentials. Please try again.", "danger")

    # Show the admin login form
    return render_template('admin_login.html')

@bp.route('/api/metrics', methods=['GET'])
def get_metrics():
    """API endpoint to get metrics data"""
    try:
        # Import metrics tracker
        from metrics_tracker import metrics_tracker

        # Get metrics from the tracker
        metrics_data = metrics_tracker.get_metrics()

        return jsonify(metrics_data)
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Metrics API error: {str(e)}\n{error_details}")

        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/api/reset-metrics', methods=['POST'])
def reset_metrics():
    """API endpoint to reset all metrics data"""
    try:
        # Import metrics tracker
        from metrics_tracker import metrics_tracker

        # Reset all metrics
        metrics_tracker.reset_metrics()

        return jsonify({
            'status': 'success',
            'message': 'All metrics have been reset successfully'
        })
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Metrics reset error: {str(e)}\n{error_details}")

        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/api/test-translations', methods=['GET'])
def test_translations():
    """Debug endpoint to test translations for all supported languages"""
    # Sample text to translate (English)
    sample_text = "Hello, this is a test of the translation system. We are checking if all languages work correctly."

    # Get the translation model from query parameter or default to gemini
    translation_model = request.args.get('model', 'gemini-2.0-flash-lite')

    # Import necessary modules
    from services.translation import TranslationService
    from utils.language_utils import get_supported_languages, get_language_name_from_code

    # Initialize the translation service
    translation_service = TranslationService()

    # Get all supported languages
    languages = get_supported_languages()

    results = {}

    # Test translation to each language
    for lang_name, lang_details in languages.items():
        lang_code = lang_details['code']
        if lang_code == 'en':  # Skip English as it's our source
            continue

        try:
            # Get the language name for better prompting
            language_name = get_language_name_from_code(lang_code)

            # Translate using the service
            translated_text = translation_service.translate(sample_text, lang_code, translation_model)

            # Store result
            results[lang_code] = {
                'language': lang_name,
                'success': True,
                'translation': translated_text,
                'native_name': lang_details['native']
            }

        except Exception as e:
            # Log error
            print(f"Error translating to {lang_name} ({lang_code}): {str(e)}")

            # Store error
            results[lang_code] = {
                'language': lang_name,
                'success': False,
                'error': str(e),
                'native_name': lang_details['native']
            }

    # Return all results
    return jsonify({
        'model': translation_model,
        'source_text': sample_text,
        'results': results
    })

@bp.route('/subscription-plans', methods=['GET'])
def subscription_plans():
    """Admin page for managing subscription plans"""
    # Check if already authenticated with special admin credentials
    if session.get('special_admin_auth') != True:
        return redirect(url_for('admin.users'))

    try:
        # Get all subscription plans
        plans = AdminSubscriptionService.get_all_subscription_plans(include_inactive=True)

        return render_template('admin_subscription_plans.html', plans=plans)
    except Exception as e:
        flash(f"Error loading subscription plans: {str(e)}", "danger")
        return redirect(url_for('admin.users'))

@bp.route('/api/subscription-plans/initialize', methods=['POST'])
def initialize_subscription_plans():
    """API endpoint to initialize subscription plans"""
    # Check if already authenticated with special admin credentials
    if session.get('special_admin_auth') != True:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        result = AdminSubscriptionService.initialize_subscription_plans()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/subscription-plans/force-update', methods=['POST'])
def force_update_subscription_plans():
    """API endpoint to force update all subscription plans"""
    # Check if already authenticated with special admin credentials
    if session.get('special_admin_auth') != True:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        result = AdminSubscriptionService.force_update_all_plans()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/subscription-plans/<plan_id>', methods=['PUT'])
def update_subscription_plan(plan_id):
    """API endpoint to update a specific subscription plan"""
    # Check if already authenticated with special admin credentials
    if session.get('special_admin_auth') != True:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        updated_data = request.get_json()
        result = AdminSubscriptionService.update_subscription_plan(plan_id, updated_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/subscription-plans', methods=['GET'])
def get_subscription_plans():
    """API endpoint to get all subscription plans"""
    # Check if already authenticated with special admin credentials
    if session.get('special_admin_auth') != True:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        plans = AdminSubscriptionService.get_all_subscription_plans(include_inactive=include_inactive)
        return jsonify(plans)
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500



@bp.route('/usage-reset', methods=['GET'])
def usage_reset():
    """Admin page for managing monthly usage reset"""
    # Check if already authenticated with special admin credentials
    if session.get('special_admin_auth') != True:
        return redirect(url_for('admin.users'))

    return render_template('admin_usage_reset.html')

@bp.route('/api/usage-statistics', methods=['GET'])
def get_usage_statistics():
    """API endpoint to get usage statistics"""
    # Check if already authenticated with special admin credentials
    if session.get('special_admin_auth') != True:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Import Firebase service
        from services.firebase_service import FirebaseService

        # Get usage statistics from Firebase function
        firebase_service = FirebaseService()
        result = firebase_service.call_function('getUsageStatistics', {})

        if result.get('success'):
            return jsonify(result['statistics'])
        else:
            return jsonify({
                'error': result.get('message', 'Failed to get usage statistics')
            }), 500

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@bp.route('/api/reset-monthly-usage', methods=['POST'])
def reset_monthly_usage():
    """API endpoint to trigger monthly usage reset"""
    # Check if already authenticated with special admin credentials
    if session.get('special_admin_auth') != True:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get force reset parameter
        force_reset = request.json.get('forceReset', False) if request.is_json else False

        # Import Firebase service
        from services.firebase_service import FirebaseService

        # Call the reset function
        firebase_service = FirebaseService()
        result = firebase_service.call_function('resetMonthlyUsage', {
            'forceReset': force_reset
        })

        if result.get('success'):
            # Log this admin action
            if current_user.is_authenticated:
                user_email = current_user.email
            else:
                user_email = 'special_admin@vocallocal.com'

            UserActivity.log(
                user_email=user_email,
                activity_type='admin_usage_reset',
                details=f'Monthly usage reset triggered. Users processed: {result.get("usersProcessed", 0)}'
            )

            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Usage reset error: {str(e)}\n{error_details}")

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/check-reset-status', methods=['GET'])
def check_reset_status():
    """API endpoint to check if users need usage reset"""
    # Check if already authenticated with special admin credentials
    if session.get('special_admin_auth') != True:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Import Firebase service
        from services.firebase_service import FirebaseService

        # Check reset status
        firebase_service = FirebaseService()
        result = firebase_service.call_function('checkAndResetUsage', {})

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@bp.route('/api/user/plan', methods=['GET'])
def get_user_plan():
    """API endpoint to get current user's plan information"""
    try:
        plan_info = get_user_plan_info()
        return jsonify(plan_info)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'plan_type': 'free',
            'accessible_models': {
                'transcription': ['gemini-2.0-flash-lite'],
                'translation': ['gemini-2.0-flash-lite'],
                'tts': ['gemini-2.5-flash-tts'],
                'interpretation': ['gemini-2.0-flash-lite']
            }
        }), 500

@bp.route('/test-plan-access', methods=['GET'])
def test_plan_access():
    """Test page for plan access control"""
    return render_template('test_plan_access.html')

@bp.route('/api/users/<user_email>/payment-history', methods=['GET'])
def get_user_payment_history(user_email):
    """API endpoint to get user's payment and subscription history"""
    # Check if already authenticated with special admin credentials
    if session.get('special_admin_auth') != True:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get user account data
        user_id = user_email.replace('.', ',')
        user_account = UserAccountService.get_user_account(user_id)

        if not user_account:
            return jsonify({'error': 'User not found'}), 404

        # Get payment history from billing data
        billing_data = user_account.get('billing', {})
        invoices = billing_data.get('invoices', {})

        # Convert Firebase data to list format
        payment_history = []
        for invoice_id, invoice_data in invoices.items():
            payment_history.append({
                'id': invoice_id,
                'date': invoice_data.get('paymentDate'),
                'amount': invoice_data.get('amount', 0),
                'currency': invoice_data.get('currency', 'USD'),
                'status': invoice_data.get('status', 'unknown'),
                'plan_type': invoice_data.get('planType', 'unknown'),
                'plan_name': invoice_data.get('planName', 'Unknown Plan'),
                'billing_cycle': invoice_data.get('billingCycle', 'monthly'),
                'stripe_invoice_id': invoice_data.get('stripeInvoiceId'),
                'stripe_subscription_id': invoice_data.get('stripeSubscriptionId')
            })

        # Sort by date (newest first)
        payment_history.sort(key=lambda x: x.get('date', 0), reverse=True)

        # Get current subscription info
        subscription = user_account.get('subscription', {})
        current_plan = {
            'plan_type': subscription.get('planType', 'free'),
            'status': subscription.get('status', 'unknown'),
            'start_date': subscription.get('startDate'),
            'end_date': subscription.get('endDate'),
            'billing_cycle': subscription.get('billingCycle', 'monthly')
        }

        # Calculate total lifetime value
        total_lifetime_value = sum(payment.get('amount', 0) for payment in payment_history)

        # Get PAYG purchase history
        payg_data = billing_data.get('payAsYouGo', {})
        payg_history = payg_data.get('purchaseHistory', [])

        return jsonify({
            'success': True,
            'user_email': user_email,
            'payment_history': payment_history,
            'current_plan': current_plan,
            'total_lifetime_value': total_lifetime_value,
            'payg_history': payg_history
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500