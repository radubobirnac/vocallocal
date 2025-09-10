"""
Model Access Service for VocalLocal.

This service handles model access restrictions based on user roles and subscription plans.
"""

from flask_login import current_user
from models.firebase_models import User


class ModelAccessService:
    """Service to manage AI model access based on user roles and subscriptions."""

    # Define model categories
    FREE_MODELS = [
        'gemini-2.5-flash-preview'
    ]

    PREMIUM_MODELS = [
        # OpenAI Transcription Models
        'gpt-4o-mini-transcribe',
        'gpt-4o-transcribe',

        # OpenAI Translation Models
        'gpt-4.1-mini',

        # OpenAI TTS Models
        'gpt4o-mini',
        'openai',  # OpenAI TTS-1

        # Gemini Premium Models
        'gemini-2.5-flash-preview-04-17',  # Kept for UI compatibility (maps to 05-20 in service)
        'gemini-2.5-flash-preview-05-20',  # Working model - direct access
        'gemini-2.5-flash',
        'gemini-2.5-flash-tts'
    ]

    ALL_MODELS = FREE_MODELS + PREMIUM_MODELS

    @staticmethod
    def can_access_model(model_name, user_email=None):
        """
        Check if a user can access a specific model.

        Args:
            model_name (str): The name of the model to check
            user_email (str, optional): User email. If not provided, uses current_user

        Returns:
            dict: Access information with 'allowed', 'reason', and 'upgrade_required' keys
        """
        # Use current user if no email provided
        if user_email is None:
            if not current_user.is_authenticated:
                return {
                    'allowed': False,
                    'reason': 'Authentication required',
                    'upgrade_required': False
                }
            user_email = current_user.email

        # Get user role
        user_role = User.get_user_role(user_email)

        if not user_role:
            return {
                'allowed': False,
                'reason': 'User not found',
                'upgrade_required': False
            }

        # Admin and Super Users have access to all models
        if user_role in [User.ROLE_ADMIN, User.ROLE_SUPER_USER]:
            return {
                'allowed': True,
                'reason': f'Access granted for {user_role} role',
                'upgrade_required': False
            }

        # Normal users - check model restrictions
        if user_role == User.ROLE_NORMAL_USER:
            # Free models are always accessible
            if model_name in ModelAccessService.FREE_MODELS:
                return {
                    'allowed': True,
                    'reason': 'Free model access',
                    'upgrade_required': False
                }

            # Premium models require subscription check
            if model_name in ModelAccessService.PREMIUM_MODELS:
                # This will integrate with existing subscription validation
                # For now, return upgrade required
                return {
                    'allowed': False,
                    'reason': 'Premium model requires subscription or role upgrade',
                    'upgrade_required': True
                }

        # Unknown model or role
        return {
            'allowed': False,
            'reason': 'Unknown model or insufficient permissions',
            'upgrade_required': True
        }

    @staticmethod
    def get_available_models(user_email=None):
        """
        Get list of models available to a user.

        Args:
            user_email (str, optional): User email. If not provided, uses current_user

        Returns:
            dict: Available models categorized by access level
        """
        # Use current user if no email provided
        if user_email is None:
            if not current_user.is_authenticated:
                return {
                    'free_models': [],
                    'premium_models': [],
                    'accessible_models': [],
                    'restricted_models': ModelAccessService.ALL_MODELS
                }
            user_email = current_user.email

        # Get user role
        user_role = User.get_user_role(user_email)

        if not user_role:
            return {
                'free_models': [],
                'premium_models': [],
                'accessible_models': [],
                'restricted_models': ModelAccessService.ALL_MODELS
            }

        # Admin and Super Users have access to all models
        if user_role in [User.ROLE_ADMIN, User.ROLE_SUPER_USER]:
            return {
                'free_models': ModelAccessService.FREE_MODELS,
                'premium_models': ModelAccessService.PREMIUM_MODELS,
                'accessible_models': ModelAccessService.ALL_MODELS,
                'restricted_models': []
            }

        # Normal users - limited access
        if user_role == User.ROLE_NORMAL_USER:
            # For now, only free models are accessible
            # This will be enhanced with subscription checking
            return {
                'free_models': ModelAccessService.FREE_MODELS,
                'premium_models': ModelAccessService.PREMIUM_MODELS,
                'accessible_models': ModelAccessService.FREE_MODELS,
                'restricted_models': ModelAccessService.PREMIUM_MODELS
            }

        # Default to no access
        return {
            'free_models': ModelAccessService.FREE_MODELS,
            'premium_models': ModelAccessService.PREMIUM_MODELS,
            'accessible_models': [],
            'restricted_models': ModelAccessService.ALL_MODELS
        }

    @staticmethod
    def validate_model_request(model_name, user_email=None):
        """
        Validate if a user can make a request with a specific model.

        Args:
            model_name (str): The model being requested
            user_email (str, optional): User email. If not provided, uses current_user

        Returns:
            dict: Validation result with 'valid', 'message', and 'suggested_model' keys
        """
        access_info = ModelAccessService.can_access_model(model_name, user_email)

        if access_info['allowed']:
            return {
                'valid': True,
                'message': 'Model access granted',
                'suggested_model': model_name
            }

        # If access denied, suggest an alternative
        available_models = ModelAccessService.get_available_models(user_email)

        if available_models['accessible_models']:
            suggested_model = available_models['accessible_models'][0]  # Suggest first available
            return {
                'valid': False,
                'message': f'Access denied to {model_name}. {access_info["reason"]}',
                'suggested_model': suggested_model
            }

        return {
            'valid': False,
            'message': f'Access denied to {model_name}. {access_info["reason"]}',
            'suggested_model': None
        }

    @staticmethod
    def get_model_restrictions_info(user_email=None):
        """
        Get comprehensive model restriction information for a user.

        Args:
            user_email (str, optional): User email. If not provided, uses current_user

        Returns:
            dict: Comprehensive restriction information
        """
        # Use current user if no email provided
        if user_email is None:
            if not current_user.is_authenticated:
                user_email = None
                user_role = None
            else:
                user_email = current_user.email
                user_role = getattr(current_user, 'role', User.ROLE_NORMAL_USER)
        else:
            user_role = User.get_user_role(user_email)

        available_models = ModelAccessService.get_available_models(user_email)

        return {
            'user_email': user_email,
            'user_role': user_role,
            'has_premium_access': user_role in [User.ROLE_ADMIN, User.ROLE_SUPER_USER] if user_role else False,
            'available_models': available_models,
            'restrictions': {
                'free_models_only': user_role == User.ROLE_NORMAL_USER if user_role else True,
                'requires_subscription_for_premium': user_role == User.ROLE_NORMAL_USER if user_role else True,
                'unlimited_access': user_role in [User.ROLE_ADMIN, User.ROLE_SUPER_USER] if user_role else False
            }
        }
