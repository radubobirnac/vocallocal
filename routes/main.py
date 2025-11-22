"""
Main routes for VocalLocal
"""
from flask import Blueprint, render_template, send_from_directory, request, flash, redirect, url_for, jsonify, make_response, current_app
from flask_login import current_user, login_required
import logging
from services.user_account_service import UserAccountService
from services.usage_validation_service import UsageValidationService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the missing function
def get_user_usage_data():
    """Get usage data for the current user."""
    try:
        # Get user email
        user_email = current_user.email
        
        # Get usage data from UsageValidationService
        usage_data = UsageValidationService.get_user_usage_data(user_email)
        
        # Format data for dashboard display
        formatted_data = {
            'transcription': {
                'used': usage_data.get('used', {}).get('transcriptionMinutes', 0),
                'limit': usage_data.get('limits', {}).get('transcriptionMinutes', 60),
                'remaining': max(0, usage_data.get('limits', {}).get('transcriptionMinutes', 60) - 
                              usage_data.get('used', {}).get('transcriptionMinutes', 0)),
                'remaining_display': 'Unlimited' if usage_data.get('plan_type') in ['professional', 'unlimited'] else None,
                'restricted': False
            },
            'translation': {
                'used': usage_data.get('used', {}).get('translationWords', 0),
                'limit': usage_data.get('limits', {}).get('translationWords', 1000),
                'remaining': max(0, usage_data.get('limits', {}).get('translationWords', 1000) - 
                              usage_data.get('used', {}).get('translationWords', 0)),
                'remaining_display': 'Unlimited' if usage_data.get('plan_type') in ['professional', 'unlimited'] else None,
                'restricted': usage_data.get('plan_type') == 'free'
            },
            'tts': {
                'used': usage_data.get('used', {}).get('ttsMinutes', 0),
                'limit': usage_data.get('limits', {}).get('ttsMinutes', 5),
                'remaining': max(0, usage_data.get('limits', {}).get('ttsMinutes', 5) - 
                              usage_data.get('used', {}).get('ttsMinutes', 0)),
                'remaining_display': 'Unlimited' if usage_data.get('plan_type') in ['professional', 'unlimited'] else None,
                'restricted': usage_data.get('plan_type') == 'free'
            },
            'ai_credits': {
                'used': usage_data.get('used', {}).get('aiCredits', 0),
                'limit': usage_data.get('limits', {}).get('aiCredits', 5),
                'remaining': max(0, usage_data.get('limits', {}).get('aiCredits', 5) - 
                              usage_data.get('used', {}).get('aiCredits', 0)),
                'remaining_display': 'Unlimited' if usage_data.get('plan_type') in ['professional', 'unlimited'] else None,
                'restricted': usage_data.get('plan_type') == 'free'
            }
        }
        
        return formatted_data
    except Exception as e:
        logger.error(f"Error getting user usage data: {e}")
        # Return default data structure for error cases
        return {
            'transcription': {'used': 0, 'limit': 60, 'remaining': 60, 'restricted': False},
            'translation': {'used': 0, 'limit': 1000, 'remaining': 1000, 'restricted': True},
            'tts': {'used': 0, 'limit': 5, 'remaining': 5, 'restricted': True},
            'ai_credits': {'used': 0, 'limit': 5, 'remaining': 5, 'restricted': True}
        }

# Import the Transcription and Translation classes
# Use a more robust approach to ensure they are available
import sys
import os
import importlib.util

# Define the Transcription and Translation classes globally to ensure they're available
# even if imports fail
class TranscriptionFallback:
    @staticmethod
    def get_by_user(email, limit=10):
        print(f"Using fallback Transcription class for {email}")
        return {}

    @staticmethod
    def get_ref(path):
        class RefObj:
            @staticmethod
            def get():
                return {}
        return RefObj()

class TranslationFallback:
    @staticmethod
    def get_by_user(email, limit=10):
        print(f"Using fallback Translation class for {email}")
        return {}

    @staticmethod
    def get_ref(path):
        class RefObj:
            @staticmethod
            def get():
                return {}
        return RefObj()

# Initialize with fallback classes first
Transcription = TranscriptionFallback
Translation = TranslationFallback

def get_user_current_plan(user_email):
    """
    Get user's current plan with enhanced accuracy by checking both Firebase and Stripe.

    Args:
        user_email (str): User's email address

    Returns:
        tuple: (plan_type, plan_display)
    """
    try:
        # Import payment service for subscription checking
        from services.payment_service import PaymentService

        payment_service = PaymentService()

        # Check subscription status for basic plan (we just need to know if they have any active subscription)
        subscription_check = payment_service.check_existing_subscription(user_email, 'basic')

        if subscription_check.get('error'):
            logger.warning(f"Error checking subscription for {user_email}: {subscription_check['error']}")
            # Fallback to Firebase only
            return get_user_plan_from_firebase(user_email)

        if subscription_check.get('has_subscription'):
            current_plan = subscription_check.get('plan_type') or subscription_check.get('current_plan')

            if current_plan == 'professional':
                return 'professional', 'Professional Plan'
            elif current_plan == 'basic':
                return 'basic', 'Basic Plan'

        # If no active subscription found, check if there's a sync issue warning
        if subscription_check.get('sync_issue'):
            logger.warning(f"Subscription sync issue detected for {user_email}")
            # Still return the Firebase plan but log the issue
            firebase_plan = subscription_check.get('plan_type', 'free')
            if firebase_plan == 'professional':
                return 'professional', 'Professional Plan (Verify Billing)'
            elif firebase_plan == 'basic':
                return 'basic', 'Basic Plan (Verify Billing)'

        # Default to free plan
        return 'free', 'Free Plan'

    except Exception as e:
        logger.error(f"Error getting current plan for {user_email}: {str(e)}")
        # Fallback to Firebase only
        return get_user_plan_from_firebase(user_email)

def get_user_plan_from_firebase(user_email):
    """
    Fallback method to get user plan from Firebase only.

    Args:
        user_email (str): User's email address

    Returns:
        tuple: (plan_type, plan_display)
    """
    try:
        user_id = user_email.replace('.', ',')
        user_account = UserAccountService.get_user_account(user_id)

        if user_account and 'subscription' in user_account:
            plan_type = user_account['subscription'].get('planType', 'free')
            status = user_account['subscription'].get('status', 'inactive')

            # Only return paid plans if status is active
            if status == 'active':
                if plan_type == 'professional':
                    return 'professional', 'Professional Plan'
                elif plan_type == 'basic':
                    return 'basic', 'Basic Plan'

        return 'free', 'Free Plan'

    except Exception as e:
        logger.error(f"Error getting Firebase plan for {user_email}: {str(e)}")
        return 'free', 'Free Plan'

def should_show_upgrade_prompts(plan_type, usage_data, is_admin, is_super_user):
    """
    Determine if user should see upgrade prompts based on their plan and usage.

    Args:
        plan_type (str): User's current plan type
        usage_data (dict): User's usage data
        is_admin (bool): Whether user is admin
        is_super_user (bool): Whether user is super user

    Returns:
        bool: True if upgrade prompts should be shown
    """
    # Never show upgrade prompts for admin or super users
    if is_admin or is_super_user:
        return False

    # Always show upgrade prompts for free users
    if plan_type == 'free':
        return True

    # For paid users, only show upgrade prompts if they've used 80% of any service
    if plan_type in ['basic', 'professional']:
        services = ['transcription', 'translation', 'tts', 'ai_credits']

        for service in services:
            service_data = usage_data.get(service, {})
            used = service_data.get('used', 0)
            limit = service_data.get('limit', 0)

            # Skip services with unlimited or zero limits
            if limit == 0 or limit == float('inf'):
                continue

            # Calculate usage percentage
            usage_percentage = (used / limit) * 100 if limit > 0 else 0

            # If any service is at 80% or higher usage, show upgrade prompts
            if usage_percentage >= 80:
                return True

    # Default: don't show upgrade prompts for paid users with low usage
    return False

def import_firebase_models():
    """Import Firebase models with comprehensive error handling."""
    global Transcription, Translation

    try:
        # Add the current directory to sys.path to ensure imports work
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)

        for path in [current_dir, parent_dir]:
            if path not in sys.path:
                sys.path.insert(0, path)

        # Try different import strategies
        import_strategies = [
            # Strategy 1: Direct import from models
            lambda: __import__('models.firebase_models', fromlist=['Transcription', 'Translation']),
            # Strategy 2: Import firebase_models directly
            lambda: __import__('firebase_models'),
            # Strategy 3: Using importlib
            lambda: importlib.import_module('models.firebase_models'),
            # Strategy 4: Alternative importlib
            lambda: importlib.import_module('firebase_models')
        ]

        for i, strategy in enumerate(import_strategies):
            try:
                module = strategy()
                if hasattr(module, 'Transcription') and hasattr(module, 'Translation'):
                    Transcription = module.Transcription
                    Translation = module.Translation
                    print(f"Successfully imported Transcription and Translation using strategy {i+1}")
                    return True
            except (ImportError, AttributeError, ModuleNotFoundError) as e:
                print(f"Strategy {i+1} failed: {str(e)}")
                continue

        # Try direct file loading as last resort
        try:
            models_path = os.path.join(parent_dir, 'models', 'firebase_models.py')
            if os.path.exists(models_path):
                spec = importlib.util.spec_from_file_location("firebase_models", models_path)
                firebase_models = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(firebase_models)
                if hasattr(firebase_models, 'Transcription') and hasattr(firebase_models, 'Translation'):
                    Transcription = firebase_models.Transcription
                    Translation = firebase_models.Translation
                    print(f"Successfully imported from file: {models_path}")
                    return True
        except Exception as e:
            print(f"Failed to import from file: {str(e)}")

        print("All import strategies failed, using fallback classes")
        return False

    except Exception as e:
        print(f"Error in import_firebase_models: {str(e)}")
        return False

# Attempt to import the real models
import_firebase_models()

# Create a blueprint for the main routes
bp = Blueprint('main', __name__)

@bp.route('/main')
def index():
    """Main index route - handles both authenticated and non-authenticated users."""
    if current_user.is_authenticated:
        # User is logged in, show the main application
        return render_template('index.html')
    else:
        # User is not logged in, show the home page
        return render_template('home.html')



@bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    # No longer fetching transcriptions and translations for the profile page
    # as they are now accessed exclusively through the History dropdown

    return render_template('profile.html',
                          user=current_user)

@bp.route('/history')
@login_required
def history():
    """History page for transcriptions and translations with improved data handling."""
    history_type = request.args.get('type', 'all')
    sort_order = request.args.get('sort', 'newest')  # newest or oldest
    limit = int(request.args.get('limit', '100'))  # Number of items to fetch

    # Import the improved history service
    try:
        from services.history_service import HistoryService
    except ImportError:
        # Fallback to original method if service not available
        return history_fallback(history_type)

    print(f"Loading history page for user: {current_user.email}, type: {history_type}, sort: {sort_order}")

    sort_desc = sort_order == 'newest'
    transcriptions = {}
    translations = {}
    history_metadata = {}

    try:
        if history_type == 'all':
            # Get combined history
            combined_result = HistoryService.get_combined_history(current_user.email, limit, sort_desc)

            # Separate back into transcriptions and translations for template compatibility
            for item in combined_result['items']:
                if item['type'] == 'transcription':
                    transcriptions[item['id']] = item['data']
                elif item['type'] == 'translation':
                    translations[item['id']] = item['data']

            history_metadata = {
                'total_items': combined_result['total_count'],
                'total_available': combined_result['total_available'],
                'transcriptions_count': combined_result['transcriptions_count'],
                'translations_count': combined_result['translations_count'],
                'transcriptions_method': combined_result['transcriptions_method'],
                'translations_method': combined_result['translations_method'],
                'sorted': combined_result['sorted']
            }

            print(f"Combined history: {combined_result['total_count']} items "
                  f"({combined_result['transcriptions_count']} transcriptions, "
                  f"{combined_result['translations_count']} translations)")

        elif history_type == 'transcription':
            # Get only transcriptions
            transcriptions_result = HistoryService.get_user_transcriptions(current_user.email, limit, sort_desc)
            transcriptions = transcriptions_result['data']

            history_metadata = {
                'total_items': transcriptions_result['count'],
                'transcriptions_count': transcriptions_result['count'],
                'translations_count': 0,
                'method': transcriptions_result['method'],
                'sorted': transcriptions_result['sorted']
            }

            print(f"Transcriptions only: {transcriptions_result['count']} items using {transcriptions_result['method']}")

        elif history_type == 'translation':
            # Get only translations
            translations_result = HistoryService.get_user_translations(current_user.email, limit, sort_desc)
            translations = translations_result['data']

            history_metadata = {
                'total_items': translations_result['count'],
                'transcriptions_count': 0,
                'translations_count': translations_result['count'],
                'method': translations_result['method'],
                'sorted': translations_result['sorted']
            }

            print(f"Translations only: {translations_result['count']} items using {translations_result['method']}")

        # Log success
        print(f"Successfully loaded history: {len(transcriptions)} transcriptions, {len(translations)} translations")

        # Check for indexing issues and provide user feedback
        indexing_warning = None
        if history_metadata.get('transcriptions_method') == 'manual_sorted' or history_metadata.get('translations_method') == 'manual_sorted':
            indexing_warning = "Database indexing is being optimized. Data is sorted manually for now."
        elif history_metadata.get('method') == 'manual_sorted':
            indexing_warning = "Database indexing is being optimized. Data is sorted manually for now."

    except Exception as e:
        print(f"Error in improved history service: {str(e)}")
        import traceback
        traceback.print_exc()

        # Fallback to original method
        return history_fallback(history_type)

    return render_template('history.html',
                          history_type=history_type,
                          transcriptions=transcriptions,
                          translations=translations,
                          history_metadata=history_metadata,
                          indexing_warning=indexing_warning,
                          sort_order=sort_order)

def history_fallback(history_type):
    """Fallback history function using original method."""
    transcriptions = {}
    translations = {}

    print(f"Using fallback history method for user: {current_user.email}, type: {history_type}")

    try:
        # Fetch user's transcription history if needed
        if history_type in ['all', 'transcription']:
            print(f"Attempting to fetch transcriptions for user: {current_user.email}")
            transcriptions = Transcription.get_by_user(current_user.email, limit=50)
            print(f"Fetched transcriptions: {len(transcriptions) if transcriptions else 0} items")

            # Debug: Print the first transcription if available
            if transcriptions and len(transcriptions) > 0:
                first_key = list(transcriptions.keys())[0]
                print(f"First transcription: {transcriptions[first_key]}")
            else:
                print("No transcriptions found")

                # Check if the user's transcription path exists
                user_id = current_user.email.replace('.', ',')
                path_exists = Transcription.get_ref(f'transcriptions/{user_id}').get() is not None
                print(f"Transcription path exists: {path_exists}")
    except Exception as e:
        print(f"Error fetching transcriptions: {str(e)}")
        import traceback
        traceback.print_exc()

        # Try to fetch without ordering if index is not defined
        try:
            user_id = current_user.email.replace('.', ',')
            transcriptions = Transcription.get_ref(f'transcriptions/{user_id}').get()
            print(f"Fetched transcriptions without ordering: {len(transcriptions) if transcriptions else 0} items")
        except Exception as e2:
            print(f"Error fetching transcriptions without ordering: {str(e2)}")
            traceback.print_exc()

    try:
        # Fetch user's translation history if needed
        if history_type in ['all', 'translation']:
            print(f"Attempting to fetch translations for user: {current_user.email}")
            translations = Translation.get_by_user(current_user.email, limit=50)
            print(f"Fetched translations: {len(translations) if translations else 0} items")
    except Exception as e:
        print(f"Error fetching translations: {str(e)}")
        import traceback
        traceback.print_exc()

        # Try to fetch without ordering if index is not defined
        try:
            user_id = current_user.email.replace('.', ',')
            translations = Translation.get_ref(f'translations/{user_id}').get()
            print(f"Fetched translations without ordering: {len(translations) if translations else 0} items")
        except Exception as e2:
            print(f"Error fetching translations without ordering: {str(e2)}")
            traceback.print_exc()

    return render_template('history.html',
                          history_type=history_type,
                          transcriptions=transcriptions if transcriptions else {},
                          translations=translations if translations else {},
                          indexing_warning="Using fallback data retrieval method.")

@bp.route('/try-it-free')
def try_it_free():
    """Try It Free page - allows users to test transcription without signing up."""
    return render_template('try_it_free.html')

@bp.route('/api/user/role-info')
@login_required
def user_role_info():
    """API endpoint to get user role and plan information for frontend RBAC."""
    try:
        # Import User model for role checking
        try:
            from models.firebase_models import User
        except ImportError:
            try:
                from firebase_models import User
            except ImportError:
                return jsonify({
                    'error': 'User model not available',
                    'role': 'normal_user',
                    'plan_type': 'free',
                    'permissions': {},
                    'has_premium_access': False,
                    'has_admin_privileges': False
                }), 500

        # Get user role
        user_role = User.get_user_role(current_user.email)

        # Import RBAC for permissions
        try:
            import rbac
            permissions = rbac.RolePermissions.get_permissions(user_role)
            has_premium_access = user_role in [User.ROLE_ADMIN, User.ROLE_SUPER_USER]
            has_admin_privileges = user_role == User.ROLE_ADMIN
        except ImportError:
            permissions = {}
            has_premium_access = False
            has_admin_privileges = False

        # Get user plan (for future subscription integration)
        user_plan = 'free'  # Default for now

        # Try to get plan from dashboard data if available
        try:
            from services.user_account_service import UserAccountService
            user_id = current_user.email.replace('.', ',')
            user_ref = UserAccountService.get_ref(f'users/{user_id}')
            user_data = user_ref.get()
            if user_data and 'subscription' in user_data:
                user_plan = user_data['subscription'].get('planType', 'free')
        except Exception as e:
            print(f"Could not get user plan: {e}")

        return jsonify({
            'role': user_role,
            'plan_type': user_plan,
            'email': current_user.email,
            'username': current_user.username,
            'permissions': permissions,
            'has_premium_access': has_premium_access,
            'has_admin_privileges': has_admin_privileges
        })

    except Exception as e:
        print(f"Error in user_role_info: {str(e)}")
        return jsonify({
            'error': 'Failed to get user info',
            'role': 'normal_user',
            'plan_type': 'free',
            'permissions': {},
            'has_premium_access': False,
            'has_admin_privileges': False
        }), 500

@bp.route('/api/user/info')
@login_required
def user_info():
    """API endpoint to get basic user information."""
    try:
        return jsonify({
            'email': current_user.email,
            'username': current_user.username,
            'authenticated': True
        })
    except Exception as e:
        print(f"Error in user_info: {str(e)}")
        return jsonify({
            'error': 'Failed to get user info',
            'authenticated': False
        }), 500

@bp.route('/api/user/available-models', methods=['GET'])
def get_user_available_models():
    """API endpoint to get available models for the current user"""
    try:
        from services.model_access_service import ModelAccessService
        from flask_login import current_user

        if not current_user.is_authenticated:
            # Return free models for non-authenticated users
            return jsonify({
                'transcription_models': [
                    {'value': 'gemini-2.0-flash-lite', 'label': 'Gemini 2.0 Flash Lite', 'free': True}
                ],
                'translation_models': [
                    {'value': 'gemini-2.0-flash-lite', 'label': 'Gemini 2.0 Flash Lite', 'free': True}
                ],
                'user_role': None,
                'has_premium_access': False
            })

        # Get user's available models
        available_models = ModelAccessService.get_available_models(current_user.email)
        user_role = getattr(current_user, 'role', 'normal_user')

        # Define authorized models by category (Updated November 2025)
        authorized_models = {
            'transcription': [
                {'value': 'gemini-2.5-flash', 'label': 'Gemini 2.5 Flash (Stable)', 'free': True},
                {'value': 'gpt-4o-mini-transcribe', 'label': 'OpenAI GPT-4o Mini', 'free': False},
                {'value': 'gpt-4o-transcribe', 'label': 'OpenAI GPT-4o', 'free': False},
                {'value': 'gemini-2.5-flash-preview-09-2025', 'label': 'Gemini 2.5 Flash Preview (Sept 2025)', 'free': False}
            ],
            'translation': [
                {'value': 'gemini-2.5-flash', 'label': 'Gemini 2.5 Flash (Stable)', 'free': True},
                {'value': 'gpt-4.1-mini', 'label': 'GPT-4.1 Mini', 'free': False}
            ]
        }

        # Build response with authorized models only
        transcription_models = []
        translation_models = []

        # Add transcription models based on user access
        for model in authorized_models['transcription']:
            if model['free'] or user_role in ['admin', 'super_user']:
                transcription_models.append(model)
            elif user_role == 'normal_user':
                # Add locked premium models for normal users
                locked_model = model.copy()
                locked_model['label'] += ' 🔒'
                locked_model['locked'] = True
                transcription_models.append(locked_model)

        # Add translation models based on user access
        for model in authorized_models['translation']:
            if model['free'] or user_role in ['admin', 'super_user']:
                translation_models.append(model)
            elif user_role == 'normal_user':
                # Add locked premium models for normal users
                locked_model = model.copy()
                locked_model['label'] += ' 🔒'
                locked_model['locked'] = True
                translation_models.append(locked_model)

        # Get user plan type for proper messaging
        user_plan = 'free'  # Default
        try:
            from services.user_account_service import UserAccountService
            user_id = current_user.email.replace('.', ',')
            user_account = UserAccountService.get_user_account(user_id)
            if user_account and 'subscription' in user_account:
                subscription = user_account['subscription']
                plan_type = subscription.get('planType', 'free')
                status = subscription.get('status', 'inactive')
                # Only return paid plan if subscription is active
                if status == 'active' and plan_type in ['basic', 'professional']:
                    user_plan = plan_type
        except Exception as e:
            print(f"Could not get user plan: {e}")

        return jsonify({
            'transcription_models': transcription_models,
            'translation_models': translation_models,
            'user_role': user_role,
            'user_plan': user_plan,
            'has_premium_access': user_role in ['admin', 'super_user'] or user_plan in ['basic', 'professional'],
            'restrictions': available_models.get('restrictions', {})
        })

    except Exception as e:
        print(f"Error getting available models: {str(e)}")
        return jsonify({
            'error': 'Failed to get available models',
            'details': str(e)
        }), 500

@bp.route('/api/check-usage', methods=['POST'])
@login_required
def check_usage():
    """API endpoint to check if user has sufficient usage for a service."""
    try:
        # Import User model for role checking
        try:
            from firebase_models import User
        except ImportError:
            return jsonify({
                'allowed': True,  # Allow if User model not available
                'message': 'Usage checking unavailable'
            })

        data = request.get_json()
        if not data:
            return jsonify({
                'allowed': False,
                'message': 'Invalid request data'
            }), 400

        service = data.get('service')
        amount = data.get('amount', 0)

        # Check user role first
        user_role = User.get_user_role(current_user.email)

        # Admins and super users have unlimited access
        if user_role in ['admin', 'super_user']:
            return jsonify({
                'allowed': True,
                'message': f'Unlimited access for {user_role} role',
                'role': user_role
            })

        # For normal users, implement proper usage checking
        # This should integrate with the subscription system
        try:
            # Import Firebase service for usage validation
            from services.firebase_service import FirebaseService

            firebase_service = FirebaseService()
            user_id = current_user.email.replace('.', ',')

            # Call appropriate validation function based on service type
            if service == 'transcription':
                result = firebase_service.call_function('validateTranscriptionUsage', {
                    'userId': user_id,
                    'minutesRequested': amount
                })
            elif service == 'translation':
                result = firebase_service.call_function('validateTranslationUsage', {
                    'userId': user_id,
                    'wordsRequested': amount
                })
            elif service == 'tts':
                result = firebase_service.call_function('validateTTSUsage', {
                    'userId': user_id,
                    'minutesRequested': amount
                })
            else:
                # Default to allowing for unknown services
                result = {'allowed': True, 'remaining': 0, 'planType': 'free'}

            return jsonify({
                'allowed': result.get('allowed', True),
                'remaining': result.get('remaining', 0),
                'planType': result.get('planType', 'free'),
                'upgradeRequired': result.get('upgradeRequired', False),
                'message': 'Usage validation completed',
                'role': user_role,
                'service': service,
                'amount': amount
            })

        except Exception as e:
            print(f"Error validating usage for normal user: {str(e)}")
            # Allow operation to continue if validation fails
            return jsonify({
                'allowed': True,
                'message': 'Usage validation failed, allowing operation',
                'role': user_role,
                'service': service,
                'amount': amount,
                'error': str(e)
            })

    except Exception as e:
        print(f"Error in check_usage: {str(e)}")
        return jsonify({
            'allowed': True,  # Allow on error to prevent blocking
            'message': 'Usage check failed, allowing operation'
        }), 200

@bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page showing usage statistics and available features."""
    try:
        logger.info(f"Dashboard route accessed by user: {current_user.email}")

        # Check if user is admin or super_user
        user_role = getattr(current_user, 'role', 'normal_user')
        is_admin = user_role == 'admin'
        is_super_user = user_role == 'super_user'

        logger.info(f"User role: {user_role}, is_admin: {is_admin}, is_super_user: {is_super_user}")
        
        # Set plan based on role
        if is_admin or is_super_user:
            plan_type = 'professional'
            plan_display = 'Professional Plan'
        else:
            # Get accurate plan information using enhanced subscription checking
            plan_type, plan_display = get_user_current_plan(current_user.email)
            logger.info(f"User {current_user.email} current plan: {plan_type} ({plan_display})")
        
        # Get usage data
        logger.info("Getting user usage data...")
        usage_data = get_user_usage_data()
        logger.info(f"Usage data retrieved: {usage_data}")
        
        # Override usage limits for admin/super_user
        if is_admin or is_super_user:
            usage_data['transcription']['limit'] = float('inf')
            usage_data['translation']['limit'] = float('inf')
            usage_data['tts']['limit'] = float('inf')
            usage_data['ai_credits']['limit'] = float('inf')
            
            # Set remaining to "Unlimited" for display
            usage_data['transcription']['remaining_display'] = 'Unlimited'
            usage_data['translation']['remaining_display'] = 'Unlimited'
            usage_data['tts']['remaining_display'] = 'Unlimited'
            usage_data['ai_credits']['remaining_display'] = 'Unlimited'
            
            # Remove restrictions
            usage_data['translation']['restricted'] = False
            usage_data['tts']['restricted'] = False
            usage_data['ai_credits']['restricted'] = False
        
        # Calculate reset date (next month)
        from datetime import datetime, timedelta
        import calendar

        today = datetime.now()
        if today.month == 12:
            reset_date = datetime(today.year + 1, 1, 1)
        else:
            reset_date = datetime(today.year, today.month + 1, 1)

        # Calculate if user should see upgrade prompts
        show_upgrade_prompts = should_show_upgrade_prompts(plan_type, usage_data, is_admin, is_super_user)

        logger.info("Rendering dashboard template with variables:")
        logger.info(f"  - usage: {type(usage_data)}")
        logger.info(f"  - plan_type: {plan_type}")
        logger.info(f"  - plan_display: {plan_display}")
        logger.info(f"  - is_admin: {is_admin}")
        logger.info(f"  - is_super_user: {is_super_user}")
        logger.info(f"  - unlimited_access: {is_admin or is_super_user}")
        logger.info(f"  - reset_date: {reset_date}")
        logger.info(f"  - show_upgrade_prompts: {show_upgrade_prompts}")

        return render_template(
            'dashboard.html',
            usage=usage_data,
            plan_type=plan_type,
            plan_display=plan_display,
            is_admin=is_admin,
            is_super_user=is_super_user,
            unlimited_access=(is_admin or is_super_user),
            reset_date=reset_date,
            show_upgrade_prompts=show_upgrade_prompts,
            config=current_app.config
        )
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return redirect(url_for('main.index'))

@bp.route('/static/<path:path>')
def serve_static(path):
    """Serve static files with proper cache headers."""
    from flask import request, make_response
    import time

    try:
        # First try to serve from the static directory
        response = make_response(send_from_directory('static', path))
    except Exception as e:
        # If that fails, try to serve from the vocallocal/static directory
        try:
            response = make_response(send_from_directory('vocallocal/static', path))
        except Exception as e2:
            # If that also fails, try with a different path
            try:
                import os
                static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
                response = make_response(send_from_directory(static_folder, path))
            except Exception as e3:
                print(f"Error serving static file {path}: {str(e3)}")
                return f"Static file {path} not found", 404

    # Add cache control headers based on whether version parameter is present
    if 'v' in request.args:
        # Versioned files - cache for 1 year
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        response.headers['Expires'] = time.strftime(
            '%a, %d %b %Y %H:%M:%S GMT',
            time.gmtime(time.time() + 31536000)
        )
    else:
        # Non-versioned files - cache for 1 hour
        response.headers['Cache-Control'] = 'public, max-age=3600'
        response.headers['Expires'] = time.strftime(
            '%a, %d %b %Y %H:%M:%S GMT',
            time.gmtime(time.time() + 3600)
        )

    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'

    return response

@bp.route('/debug_payment_fetch.html')
def debug_payment_fetch():
    """Debug page for testing payment fetch functionality."""
    return send_from_directory('.', 'debug_payment_fetch.html')

@bp.route('/manual_payment_test.html')
def manual_payment_test():
    """Manual test page for payment functionality."""
    return send_from_directory('.', 'manual_payment_test.html')

@bp.route('/test_fetch_binding_fix.html')
def test_fetch_binding_fix():
    """Test page for fetch binding fix."""
    return send_from_directory('.', 'test_fetch_binding_fix.html')

@bp.route('/simple_payment_test.html')
def simple_payment_test():
    """Simple test page for payment functionality without fetch validator."""
    return send_from_directory('.', 'simple_payment_test.html')
