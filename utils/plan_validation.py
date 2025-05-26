"""
Plan validation decorators and utilities for API endpoints.
"""
import functools
import logging
from flask import request, jsonify, current_app
from flask_login import current_user
from services.plan_access_control import PlanAccessControl

logger = logging.getLogger(__name__)

def validate_model_access(service_type):
    """
    Decorator to validate model access based on user plan.
    
    Args:
        service_type (str): Type of service ('transcription', 'translation', 'tts', 'interpretation')
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get model from request
                model = None
                
                if request.method == 'POST':
                    if request.is_json:
                        data = request.get_json()
                        model = data.get('model') or data.get(f'{service_type}_model')
                    else:
                        # Form data
                        model = request.form.get('model') or request.form.get(f'{service_type}_model')
                elif request.method == 'GET':
                    model = request.args.get('model') or request.args.get(f'{service_type}_model')
                
                # If no model specified, use default for user's plan
                if not model:
                    user_plan = PlanAccessControl.get_user_plan()
                    accessible_models = PlanAccessControl.get_accessible_models(service_type, user_plan)
                    model = accessible_models[0] if accessible_models else 'gemini-2.0-flash-lite'
                    
                    # Update request with default model
                    if request.is_json:
                        request.json['model'] = model
                    else:
                        request.form = request.form.copy()
                        request.form['model'] = model
                
                # Validate model access
                is_allowed, validation_result = PlanAccessControl.validate_model_access(model, service_type)
                
                if not is_allowed:
                    logger.warning(f"Model access denied: {validation_result}")
                    return jsonify({
                        'error': 'Model access denied',
                        'details': validation_result['error'],
                        'status': 'access_denied'
                    }), 403
                
                # Log successful validation
                logger.info(f"Model access validated: {model} for {service_type} (plan: {validation_result['plan']})")
                
                # Continue with original function
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in model access validation: {str(e)}")
                return jsonify({
                    'error': 'Validation error',
                    'details': str(e),
                    'status': 'validation_error'
                }), 500
        
        return decorated_function
    return decorator

def validate_usage_limits(service_type):
    """
    Decorator to validate usage limits based on user plan.
    
    Args:
        service_type (str): Type of service for usage validation
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if not current_user.is_authenticated:
                    return jsonify({
                        'error': 'Authentication required',
                        'status': 'unauthenticated'
                    }), 401
                
                # Get usage amount from request
                usage_amount = 0
                
                if service_type == 'transcription':
                    # Estimate transcription minutes based on file size or duration
                    if 'file' in request.files:
                        file = request.files['file']
                        # Rough estimate: 1MB ≈ 1 minute of audio
                        file_size_mb = len(file.read()) / (1024 * 1024)
                        file.seek(0)  # Reset file pointer
                        usage_amount = max(1, file_size_mb)  # Minimum 1 minute
                    else:
                        usage_amount = 1  # Default for live recording
                        
                elif service_type == 'translation':
                    # Count words in text
                    text = ''
                    if request.is_json:
                        text = request.get_json().get('text', '')
                    else:
                        text = request.form.get('text', '')
                    usage_amount = len(text.split())
                    
                elif service_type == 'tts':
                    # Estimate TTS minutes based on text length
                    text = ''
                    if request.is_json:
                        text = request.get_json().get('text', '')
                    else:
                        text = request.form.get('text', '')
                    # Rough estimate: 150 words per minute
                    usage_amount = max(0.1, len(text.split()) / 150)
                    
                elif service_type == 'interpretation':
                    # AI credits usage
                    usage_amount = 1  # 1 credit per interpretation
                
                # Validate usage with existing usage validation system
                try:
                    from static.js.usage_validation import validate_usage
                    validation_result = validate_usage(current_user.email, service_type, usage_amount)
                    
                    if not validation_result.get('allowed', False):
                        return jsonify({
                            'error': 'Usage limit exceeded',
                            'details': validation_result,
                            'status': 'usage_limit_exceeded'
                        }), 429
                        
                except ImportError:
                    # Fallback if usage validation is not available
                    logger.warning("Usage validation system not available, proceeding without validation")
                
                # Continue with original function
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in usage validation: {str(e)}")
                return jsonify({
                    'error': 'Usage validation error',
                    'details': str(e),
                    'status': 'validation_error'
                }), 500
        
        return decorated_function
    return decorator

def require_plan(required_plan):
    """
    Decorator to require a specific plan level.
    
    Args:
        required_plan (str): Required plan ('basic', 'professional')
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if not current_user.is_authenticated:
                    return jsonify({
                        'error': 'Authentication required',
                        'status': 'unauthenticated'
                    }), 401
                
                user_plan = PlanAccessControl.get_user_plan()
                
                # Plan hierarchy: free < basic < professional
                plan_hierarchy = {'free': 0, 'basic': 1, 'professional': 2}
                
                user_level = plan_hierarchy.get(user_plan, 0)
                required_level = plan_hierarchy.get(required_plan, 2)
                
                if user_level < required_level:
                    plan_names = {
                        'basic': 'Basic Plan ($4.99/month)',
                        'professional': 'Professional Plan ($12.99/month)'
                    }
                    
                    return jsonify({
                        'error': 'Plan upgrade required',
                        'details': {
                            'current_plan': user_plan,
                            'required_plan': required_plan,
                            'upgrade_message': f'This feature requires {plan_names.get(required_plan, required_plan)}'
                        },
                        'status': 'plan_upgrade_required'
                    }), 403
                
                # Continue with original function
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in plan validation: {str(e)}")
                return jsonify({
                    'error': 'Plan validation error',
                    'details': str(e),
                    'status': 'validation_error'
                }), 500
        
        return decorated_function
    return decorator

def get_user_plan_info():
    """Get comprehensive user plan information."""
    try:
        user_plan = PlanAccessControl.get_user_plan()
        
        return {
            'plan_type': user_plan,
            'accessible_models': {
                'transcription': PlanAccessControl.get_accessible_models('transcription', user_plan),
                'translation': PlanAccessControl.get_accessible_models('translation', user_plan),
                'tts': PlanAccessControl.get_accessible_models('tts', user_plan),
                'interpretation': PlanAccessControl.get_accessible_models('interpretation', user_plan)
            },
            'upgrade_suggestions': PlanAccessControl.get_plan_upgrade_suggestions(user_plan)
        }
    except Exception as e:
        logger.error(f"Error getting user plan info: {str(e)}")
        return {
            'plan_type': 'free',
            'accessible_models': {
                'transcription': ['gemini-2.0-flash-lite'],
                'translation': ['gemini-2.0-flash-lite'],
                'tts': ['gemini-2.5-flash-tts'],
                'interpretation': ['gemini-2.0-flash-lite']
            },
            'upgrade_suggestions': []
        }
