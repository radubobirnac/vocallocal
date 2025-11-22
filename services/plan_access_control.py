"""
Plan-based access control service for VocalLocal application.
Manages model access restrictions based on user subscription plans.
"""
import logging
from typing import Dict, List, Optional, Tuple
from flask_login import current_user

logger = logging.getLogger(__name__)

class PlanAccessControl:
    """Service for managing plan-based access control."""

    # Model access matrix by plan type (Updated November 2025)
    PLAN_MODEL_ACCESS = {
        'free': {
            'transcription': ['gemini-2.5-flash', 'gemini-2.5-flash-preview'],  # Allow both for backward compatibility
            'translation': ['gemini-2.5-flash', 'gemini-2.5-flash-preview'],
            'tts': [],  # No free TTS models - all require upgrade
            'interpretation': ['gemini-2.5-flash', 'gemini-2.5-flash-preview']
        },
        'basic': {
            'transcription': [
                'gemini-2.5-flash',  # Stable model (current)
                'gemini-2.5-flash-preview',  # Backward compatibility
                'gpt-4o-mini-transcribe',
                'gpt-4o-transcribe',
                'gemini-2.5-flash-preview-09-2025'  # Latest preview (Sept 2025)
            ],
            'translation': [
                'gemini-2.5-flash',  # Stable model (current)
                'gemini-2.5-flash-preview',  # Backward compatibility
                'gpt-4.1-mini'
            ],
            'tts': [
                'gemini-2.5-flash-tts',
                'gpt4o-mini',
                'openai'
            ],
            'interpretation': [
                'gemini-2.5-flash',  # Stable model (current)
                'gemini-2.5-flash-preview',  # Backward compatibility
                'gemini-2.5-flash-preview-09-2025'
            ]
        },
        'professional': {
            'transcription': [
                'gemini-2.5-flash',  # Stable model (current)
                'gemini-2.5-flash-preview',  # Backward compatibility
                'gpt-4o-mini-transcribe',
                'gpt-4o-transcribe',
                'gemini-2.5-flash-preview-09-2025',  # Latest preview (Sept 2025)
                'gemini-2.5-pro'  # Pro model
            ],
            'translation': [
                'gemini-2.5-flash',  # Stable model (current)
                'gemini-2.5-flash-preview',  # Backward compatibility
                'gpt-4.1-mini'
            ],
            'tts': [
                'gemini-2.5-flash-tts',
                'gpt4o-mini',
                'openai'
            ],
            'interpretation': [
                'gemini-2.5-flash',  # Stable model (current)
                'gemini-2.5-flash-preview',  # Backward compatibility
                'gemini-2.5-flash-preview-09-2025',
                'gemini-2.5-pro'
            ]
        }
    }

    # Model display names and descriptions (Updated November 2025)
    MODEL_INFO = {
        'gemini-2.5-flash': {
            'name': 'Gemini 2.5 Flash (Stable)',
            'description': 'Fast and efficient stable model',
            'tier': 'free'
        },
        'gemini-2.5-flash-preview': {
            'name': 'Gemini 2.5 Flash Preview (Legacy)',
            'description': 'Legacy preview model - use gemini-2.5-flash instead',
            'tier': 'free'
        },
        'gpt-4o-mini-transcribe': {
            'name': 'OpenAI GPT-4o Mini',
            'description': 'High-quality transcription with OpenAI',
            'tier': 'basic'
        },
        'gpt-4o-transcribe': {
            'name': 'OpenAI GPT-4o',
            'description': 'Premium transcription with latest OpenAI model (available to Basic Plan users)',
            'tier': 'basic'
        },
        'gemini-2.5-flash-preview-09-2025': {
            'name': 'Gemini 2.5 Flash Preview (Sept 2025)',
            'description': 'Latest preview model with enhanced capabilities',
            'tier': 'basic'
        },
        'gemini-2.5-pro': {
            'name': 'Gemini 2.5 Pro',
            'description': 'Most capable Gemini model for complex tasks',
            'tier': 'professional'
        },
        'gemini-2.5-flash': {
            'name': 'Gemini 2.5 Flash Preview',
            'description': 'Advanced AI interpretation with Gemini 2.5',
            'tier': 'basic'
        },
        'gpt-4.1-mini': {
            'name': 'GPT-4.1 Mini',
            'description': 'OpenAI translation model with enhanced capabilities',
            'tier': 'basic'
        },
        'gemini-2.5-flash-tts': {
            'name': 'Gemini 2.5 Flash TTS',
            'description': 'High-quality text-to-speech',
            'tier': 'basic'
        },
        'gpt4o-mini': {
            'name': 'GPT-4o Mini TTS',
            'description': 'Premium TTS with OpenAI',
            'tier': 'basic'
        },
        'openai': {
            'name': 'OpenAI TTS-1',
            'description': 'Professional-grade TTS',
            'tier': 'professional'
        }
    }

    @classmethod
    def get_user_plan(cls) -> str:
        """Get the current user's plan type."""
        if not current_user.is_authenticated:
            return 'free'

        try:
            # Get user plan from Firebase - same logic as dashboard and other components
            from services.user_account_service import UserAccountService
            user_id = current_user.email.replace('.', ',')
            user_account = UserAccountService.get_user_account(user_id)

            if user_account and 'subscription' in user_account:
                subscription = user_account['subscription']
                plan_type = subscription.get('planType', 'free')
                status = subscription.get('status', 'inactive')

                # Only return paid plan if subscription is active
                if status == 'active' and plan_type in cls.PLAN_MODEL_ACCESS:
                    return plan_type

            return 'free'
        except Exception as e:
            logger.error(f"Error getting user plan: {e}")
            return 'free'

    @classmethod
    def get_accessible_models(cls, service_type: str, user_plan: str = None) -> List[str]:
        """Get list of models accessible to user for a specific service."""
        if user_plan is None:
            user_plan = cls.get_user_plan()

        return cls.PLAN_MODEL_ACCESS.get(user_plan, {}).get(service_type, [])

    @classmethod
    def is_model_accessible(cls, model: str, service_type: str, user_plan: str = None) -> bool:
        """Check if a model is accessible to the user."""
        if user_plan is None:
            user_plan = cls.get_user_plan()

        accessible_models = cls.get_accessible_models(service_type, user_plan)
        return model in accessible_models

    @classmethod
    def get_model_restriction_info(cls, model: str, service_type: str, user_plan: str = None) -> Dict:
        """Get restriction information for a model."""
        if user_plan is None:
            user_plan = cls.get_user_plan()

        is_accessible = cls.is_model_accessible(model, service_type, user_plan)
        model_info = cls.MODEL_INFO.get(model, {})

        if is_accessible:
            return {
                'accessible': True,
                'restriction_reason': None,
                'required_plan': None,
                'upgrade_message': None
            }

        # Determine required plan
        required_plan = None
        for plan, services in cls.PLAN_MODEL_ACCESS.items():
            if model in services.get(service_type, []):
                required_plan = plan
                break

        plan_names = {
            'basic': 'Basic Plan ($4.99/month)',
            'professional': 'Professional Plan ($12.99/month)'
        }

        return {
            'accessible': False,
            'restriction_reason': f'Model requires {plan_names.get(required_plan, "higher plan")}',
            'required_plan': required_plan,
            'upgrade_message': f'Upgrade to {plan_names.get(required_plan, "a higher plan")} to access {model_info.get("name", model)}'
        }

    @classmethod
    def get_model_info(cls, model: str) -> Dict:
        """Get model information including name, description, and tier."""
        return cls.MODEL_INFO.get(model, {})

    @classmethod
    def validate_model_access(cls, model: str, service_type: str, user_plan: str = None) -> Tuple[bool, Dict]:
        """Validate model access and return detailed response."""
        if user_plan is None:
            user_plan = cls.get_user_plan()

        restriction_info = cls.get_model_restriction_info(model, service_type, user_plan)

        if restriction_info['accessible']:
            return True, {
                'allowed': True,
                'model': model,
                'plan': user_plan
            }

        return False, {
            'allowed': False,
            'model': model,
            'plan': user_plan,
            'error': {
                'code': 'model_access_denied',
                'message': restriction_info['restriction_reason'],
                'required_plan': restriction_info['required_plan'],
                'upgrade_message': restriction_info['upgrade_message']
            }
        }

    @classmethod
    def get_plan_upgrade_suggestions(cls, current_plan: str) -> List[Dict]:
        """Get upgrade suggestions for the current plan."""
        suggestions = []

        if current_plan == 'free':
            suggestions.extend([
                {
                    'plan': 'basic',
                    'name': 'Basic Plan',
                    'price': 4.99,
                    'benefits': [
                        'Access to premium transcription models',
                        '280 transcription minutes/month',
                        '50k translation words/month',
                        '60 TTS minutes/month',
                        '50 AI credits/month'
                    ]
                },
                {
                    'plan': 'professional',
                    'name': 'Professional Plan',
                    'price': 12.99,
                    'benefits': [
                        'Access to all premium models',
                        '800 transcription minutes/month',
                        '160k translation words/month',
                        '200 TTS minutes/month',
                        '150 AI credits/month'
                    ]
                }
            ])
        elif current_plan == 'basic':
            suggestions.append({
                'plan': 'professional',
                'name': 'Professional Plan',
                'price': 12.99,
                'benefits': [
                    'Access to latest OpenAI models',
                    '800 transcription minutes/month',
                    '160k translation words/month',
                    '200 TTS minutes/month',
                    '150 AI credits/month'
                ]
            })

        return suggestions
