"""
User Account Service for VocalLocal

This service manages user account data in Firebase Realtime Database,
including profile information, subscription details, usage tracking,
and billing information.
"""

import time
from datetime import datetime, timedelta
from firebase_config import initialize_firebase
from models.firebase_models import FirebaseModel

class UserAccountService(FirebaseModel):
    """Service for managing user account data in Firebase."""

    @staticmethod
    def initialize_user_account(user_id, email, display_name):
        """
        Initialize a new user account with default values.

        Args:
            user_id (str): Firebase user ID
            email (str): User's email address
            display_name (str): User's display name

        Returns:
            dict: The created user account data
        """
        current_time = int(time.time() * 1000)  # Current time in milliseconds

        # Calculate reset date (first day of next month)
        today = datetime.now()
        first_of_next_month = datetime(today.year, today.month + 1 if today.month < 12 else 1, 1)
        reset_timestamp = int(first_of_next_month.timestamp() * 1000)

        # Calculate subscription end date (30 days from now for free trial)
        end_date = int((datetime.now() + timedelta(days=30)).timestamp() * 1000)

        # Create user account structure
        user_account = {
            "profile": {
                "email": email,
                "displayName": display_name,
                "createdAt": current_time,
                "lastLoginAt": current_time,
                "status": "active"
            },
            "subscription": {
                "planType": "free",
                "status": "trial",
                "startDate": current_time,
                "endDate": end_date,
                "renewalDate": end_date,
                "paymentMethod": "none",
                "billingCycle": "monthly"
            },
            "usage": {
                "currentPeriod": {
                    "transcriptionMinutes": 0,
                    "translationWords": 0,
                    "ttsMinutes": 0,
                    "aiCredits": 0,
                    "resetDate": reset_timestamp
                },
                "totalUsage": {
                    "transcriptionMinutes": 0,
                    "translationWords": 0,
                    "ttsMinutes": 0,
                    "aiCredits": 0
                }
            },
            "billing": {
                "payAsYouGo": {
                    "unitsRemaining": {
                        "transcriptionMinutes": 10,  # Free trial minutes
                        "translationWords": 1000,    # Free trial translation words
                        "ttsMinutes": 0,             # No TTS for free users
                        "aiCredits": 0               # No AI credits for free users
                    },
                    "purchaseHistory": []
                }
            }
        }

        # Save to Firebase
        UserAccountService.get_ref(f'users/{user_id}').set(user_account)

        return user_account

    @staticmethod
    def get_user_account(user_id):
        """
        Get a user's account data.

        Args:
            user_id (str): Firebase user ID

        Returns:
            dict: User account data or None if not found
        """
        return UserAccountService.get_ref(f'users/{user_id}').get()

    @staticmethod
    def update_last_login(user_id):
        """
        Update user's last login timestamp.

        Args:
            user_id (str): Firebase user ID
        """
        current_time = int(time.time() * 1000)  # Current time in milliseconds
        UserAccountService.get_ref(f'users/{user_id}/profile/lastLoginAt').set(current_time)

    @staticmethod
    def update_subscription(user_id, plan_type, status, billing_cycle, payment_method=None):
        """
        Update user's subscription information.

        Args:
            user_id (str): Firebase user ID
            plan_type (str): Subscription plan type ('free', 'basic', 'premium', 'enterprise')
            status (str): Subscription status ('active', 'canceled', 'expired', 'trial')
            billing_cycle (str): Billing frequency ('monthly', 'annual', 'quarterly')
            payment_method (str, optional): Payment method used

        Returns:
            dict: Updated subscription data
        """
        current_time = int(time.time() * 1000)  # Current time in milliseconds

        # Calculate end date based on billing cycle
        if billing_cycle == "monthly":
            days = 30
        elif billing_cycle == "quarterly":
            days = 90
        elif billing_cycle == "annual":
            days = 365
        else:
            days = 30  # Default to monthly

        end_date = int((datetime.now() + timedelta(days=days)).timestamp() * 1000)

        subscription_data = {
            "planType": plan_type,
            "status": status,
            "startDate": current_time,
            "endDate": end_date,
            "renewalDate": end_date,
            "billingCycle": billing_cycle
        }

        if payment_method:
            subscription_data["paymentMethod"] = payment_method

        # Update in Firebase
        UserAccountService.get_ref(f'users/{user_id}/subscription').update(subscription_data)

        return subscription_data

    @staticmethod
    def track_usage(user_id, service_type, amount):
        """
        Track usage of a service and update both current period and total usage.

        Args:
            user_id (str): Firebase user ID
            service_type (str): Type of service ('transcriptionMinutes', 'translationWords', 'ttsMinutes', 'aiCredits')
            amount (float): Amount to add to usage

        Returns:
            dict: Updated usage data
        """
        # Get current usage
        current_usage = UserAccountService.get_ref(f'users/{user_id}/usage/currentPeriod/{service_type}').get() or 0
        total_usage = UserAccountService.get_ref(f'users/{user_id}/usage/totalUsage/{service_type}').get() or 0

        # Update usage
        new_current_usage = current_usage + amount
        new_total_usage = total_usage + amount

        # Save to Firebase
        UserAccountService.get_ref(f'users/{user_id}/usage/currentPeriod/{service_type}').set(new_current_usage)
        UserAccountService.get_ref(f'users/{user_id}/usage/totalUsage/{service_type}').set(new_total_usage)

        # Check if we need to reset current period usage
        reset_date = UserAccountService.get_ref(f'users/{user_id}/usage/currentPeriod/resetDate').get()
        current_time = int(time.time() * 1000)  # Current time in milliseconds

        if reset_date and current_time > reset_date:
            # Try to use Firebase Cloud Function for reset (preferred method)
            try:
                from services.firebase_service import FirebaseService
                firebase_service = FirebaseService()

                # Call the checkAndResetUsage function for this specific user
                result = firebase_service.call_function('checkAndResetUsage', {})

                if result.get('success') and result.get('resetTriggered'):
                    print(f"Successfully reset usage for user {user_id} via Cloud Function")
                    return  # Exit early since reset was handled by Cloud Function
                else:
                    print(f"Cloud Function reset not triggered for user {user_id}, falling back to local reset")
            except Exception as e:
                print(f"Error calling Cloud Function for reset, falling back to local reset: {str(e)}")

            # Fallback: Local reset logic
            # Calculate new reset date (first day of next month)
            today = datetime.now()
            first_of_next_month = datetime(today.year, today.month + 1 if today.month < 12 else 1, 1)
            new_reset_timestamp = int(first_of_next_month.timestamp() * 1000)

            # Get current usage for archiving
            current_usage_ref = UserAccountService.get_ref(f'users/{user_id}/usage/currentPeriod')
            current_usage = current_usage_ref.get() or {}

            # Archive current usage data
            current_month = datetime.now().strftime('%Y-%m')
            archive_data = {
                "transcriptionMinutes": current_usage.get("transcriptionMinutes", 0),
                "translationWords": current_usage.get("translationWords", 0),
                "ttsMinutes": current_usage.get("ttsMinutes", 0),
                "aiCredits": current_usage.get("aiCredits", 0),
                "resetDate": reset_date,
                "archivedAt": current_time,
                "planType": "unknown"  # Will be updated if subscription info is available
            }

            # Try to get subscription info for archive
            try:
                subscription_ref = UserAccountService.get_ref(f'users/{user_id}/subscription/planType')
                plan_type = subscription_ref.get()
                if plan_type:
                    archive_data["planType"] = plan_type
            except Exception:
                pass  # Use default "unknown" if subscription info is not available

            # Archive the usage data
            UserAccountService.get_ref(f'usage/history/{current_month}/{user_id}').set(archive_data)

            # Reset all current period usage
            UserAccountService.get_ref(f'users/{user_id}/usage/currentPeriod').update({
                "transcriptionMinutes": 0,
                "translationWords": 0,
                "ttsMinutes": 0,
                "aiCredits": 0,
                "resetDate": new_reset_timestamp
            })

            # Update last reset timestamp
            UserAccountService.get_ref(f'users/{user_id}/usage/lastResetAt').set(current_time)

            print(f"Local usage reset completed for user {user_id}")

        return {
            "currentUsage": new_current_usage,
            "totalUsage": new_total_usage
        }

    @staticmethod
    def add_purchase(user_id, service_type, amount, units_purchased):
        """
        Add a purchase to the user's purchase history and update available units.

        Args:
            user_id (str): Firebase user ID
            service_type (str): Type of service ('transcription', 'translation', 'tts', 'ai', 'bundle')
            amount (float): Amount paid
            units_purchased (int): Number of units purchased

        Returns:
            str: Purchase ID
        """
        current_time = int(time.time() * 1000)  # Current time in milliseconds

        # Create purchase record
        purchase_data = {
            "date": current_time,
            "amount": amount,
            "serviceType": service_type,
            "unitsPurchased": units_purchased
        }

        # Add to purchase history
        purchase_ref = UserAccountService.get_ref(f'users/{user_id}/billing/payAsYouGo/purchaseHistory').push(purchase_data)

        # Update available units
        if service_type != 'bundle':
            # Map service type to the corresponding units field
            units_field_map = {
                'transcription': 'transcriptionMinutes',
                'translation': 'translationWords',
                'tts': 'ttsMinutes',
                'ai': 'aiCredits'
            }

            units_field = units_field_map.get(service_type)
            if units_field:
                # Get current units
                current_units = UserAccountService.get_ref(f'users/{user_id}/billing/payAsYouGo/unitsRemaining/{units_field}').get() or 0

                # Update units
                new_units = current_units + units_purchased
                UserAccountService.get_ref(f'users/{user_id}/billing/payAsYouGo/unitsRemaining/{units_field}').set(new_units)

        return purchase_ref.key
