"""
Admin Subscription Service for VocalLocal

This service manages subscription plans in Firebase Realtime Database,
including creating initial plans and updating existing ones.
"""

import logging
from firebase_config import initialize_firebase
from models.firebase_models import FirebaseModel

# Set up logging
logger = logging.getLogger(__name__)

class AdminSubscriptionService(FirebaseModel):
    """Service for managing subscription plans in Firebase."""

    # Default subscription plans
    DEFAULT_PLANS = {
        "free": {
            "id": "free",
            "name": "Free Plan",
            "price": 0,
            "transcriptionMinutes": 60,  # 60 minutes for transcription
            "translationWords": 10000,   # 10,000 words for translation (shared quota concept)
            "ttsMinutes": 0,             # No TTS access for free users
            "aiCredits": 0,              # No AI credits for free users
            "transcriptionModel": "gemini-2.0-flash-lite",
            "isActive": True
        },
        "basic": {
            "id": "basic",
            "name": "Basic Plan",
            "price": 4.99,
            "transcriptionMinutes": 280,
            "translationWords": 50000,
            "ttsMinutes": 60,
            "aiCredits": 50,
            "transcriptionModel": "premium",
            "isActive": True
        },
        "professional": {
            "id": "professional",
            "name": "Professional Plan",
            "price": 12.99,
            "transcriptionMinutes": 800,
            "translationWords": 160000,
            "ttsMinutes": 200,
            "aiCredits": 150,
            "transcriptionModel": "premium",
            "isActive": True
        },
        "payg": {
            "id": "payg",
            "name": "Pay-as-you-go Credits",
            "price": 3.99,
            "credits": 300,
            "requiresSubscription": True,
            "compatiblePlans": {"basic": True, "professional": True},
            "isActive": True
        }
    }

    @staticmethod
    def initialize_subscription_plans():
        """
        Initialize subscription plans in Firebase if they don't exist.

        This function creates the default subscription plans in the Firebase
        Realtime Database if they don't already exist. It checks each plan
        individually and only creates plans that are missing.

        Returns:
            dict: A dictionary with the results of the operation
                {
                    "success": bool,
                    "created": list of plan IDs that were created,
                    "existing": list of plan IDs that already existed,
                    "error": error message if any
                }
        """
        try:
            # Get reference to subscriptionPlans collection
            plans_ref = AdminSubscriptionService.get_ref('subscriptionPlans')

            # Get existing plans
            existing_plans = plans_ref.get() or {}

            # Track results
            result = {
                "success": True,
                "created": [],
                "existing": [],
                "error": None
            }

            # Check each default plan
            for plan_id, plan_data in AdminSubscriptionService.DEFAULT_PLANS.items():
                if plan_id not in existing_plans:
                    # Plan doesn't exist, create it
                    plans_ref.child(plan_id).set(plan_data)
                    result["created"].append(plan_id)
                    logger.info(f"Created subscription plan: {plan_id}")
                else:
                    # Plan already exists
                    result["existing"].append(plan_id)
                    logger.info(f"Subscription plan already exists: {plan_id}")

            return result

        except Exception as e:
            logger.error(f"Error initializing subscription plans: {str(e)}")
            return {
                "success": False,
                "created": [],
                "existing": [],
                "error": str(e)
            }

    @staticmethod
    def update_subscription_plan(plan_id, updated_data):
        """
        Update an existing subscription plan with new data.

        This function updates an existing subscription plan in the Firebase
        Realtime Database. It performs validation to ensure data consistency
        and only updates fields that are allowed to be changed.

        Args:
            plan_id (str): The ID of the plan to update
            updated_data (dict): The new data to update the plan with

        Returns:
            dict: A dictionary with the results of the operation
                {
                    "success": bool,
                    "plan_id": the ID of the updated plan,
                    "updated_fields": list of fields that were updated,
                    "error": error message if any
                }
        """
        try:
            # Get reference to the specific plan
            plan_ref = AdminSubscriptionService.get_ref(f'subscriptionPlans/{plan_id}')

            # Check if plan exists
            existing_plan = plan_ref.get()
            if not existing_plan:
                return {
                    "success": False,
                    "plan_id": plan_id,
                    "updated_fields": [],
                    "error": f"Plan with ID '{plan_id}' does not exist"
                }

            # Fields that are not allowed to be updated
            protected_fields = ["id"]

            # Validate updated data
            if "id" in updated_data and updated_data["id"] != plan_id:
                return {
                    "success": False,
                    "plan_id": plan_id,
                    "updated_fields": [],
                    "error": "Cannot change the 'id' field of a subscription plan"
                }

            # Remove protected fields from updated_data
            for field in protected_fields:
                if field in updated_data:
                    del updated_data[field]

            # Validate numeric fields
            numeric_fields = ["price", "transcriptionMinutes", "translationWords", "ttsMinutes", "aiCredits", "credits"]
            for field in numeric_fields:
                if field in updated_data and not isinstance(updated_data[field], (int, float)):
                    return {
                        "success": False,
                        "plan_id": plan_id,
                        "updated_fields": [],
                        "error": f"Field '{field}' must be a number"
                    }
                if field in updated_data and updated_data[field] < 0:
                    return {
                        "success": False,
                        "plan_id": plan_id,
                        "updated_fields": [],
                        "error": f"Field '{field}' cannot be negative"
                    }

            # Validate boolean fields
            boolean_fields = ["isActive", "requiresSubscription"]
            for field in boolean_fields:
                if field in updated_data and not isinstance(updated_data[field], bool):
                    return {
                        "success": False,
                        "plan_id": plan_id,
                        "updated_fields": [],
                        "error": f"Field '{field}' must be a boolean"
                    }

            # Validate compatiblePlans if present
            if "compatiblePlans" in updated_data:
                if not isinstance(updated_data["compatiblePlans"], dict):
                    return {
                        "success": False,
                        "plan_id": plan_id,
                        "updated_fields": [],
                        "error": "Field 'compatiblePlans' must be a dictionary"
                    }

                # Check if all compatible plans exist
                all_plans = AdminSubscriptionService.get_ref('subscriptionPlans').get() or {}
                for compatible_plan_id in updated_data["compatiblePlans"].keys():
                    if compatible_plan_id not in all_plans:
                        return {
                            "success": False,
                            "plan_id": plan_id,
                            "updated_fields": [],
                            "error": f"Compatible plan '{compatible_plan_id}' does not exist"
                        }

                    # Ensure values are boolean
                    if not isinstance(updated_data["compatiblePlans"][compatible_plan_id], bool):
                        return {
                            "success": False,
                            "plan_id": plan_id,
                            "updated_fields": [],
                            "error": f"Value for compatible plan '{compatible_plan_id}' must be a boolean"
                        }

            # Update the plan
            plan_ref.update(updated_data)

            return {
                "success": True,
                "plan_id": plan_id,
                "updated_fields": list(updated_data.keys()),
                "error": None
            }

        except Exception as e:
            logger.error(f"Error updating subscription plan: {str(e)}")
            return {
                "success": False,
                "plan_id": plan_id,
                "updated_fields": [],
                "error": str(e)
            }

    @staticmethod
    def get_all_subscription_plans(include_inactive=False):
        """
        Get all subscription plans.

        Args:
            include_inactive (bool): Whether to include inactive plans

        Returns:
            dict: Dictionary of subscription plans
        """
        plans = AdminSubscriptionService.get_ref('subscriptionPlans').get() or {}

        if not include_inactive:
            # Filter out inactive plans
            plans = {k: v for k, v in plans.items() if v.get('isActive', True)}

        return plans

    @staticmethod
    def get_subscription_plan(plan_id):
        """
        Get a specific subscription plan.

        Args:
            plan_id (str): The ID of the plan to get

        Returns:
            dict: The subscription plan data or None if not found
        """
        return AdminSubscriptionService.get_ref(f'subscriptionPlans/{plan_id}').get()

    @staticmethod
    def force_update_all_plans():
        """
        Force update all subscription plans to match the DEFAULT_PLANS specifications.

        This function overwrites existing plans with the current DEFAULT_PLANS data,
        ensuring all plans match the exact specifications.

        Returns:
            dict: A dictionary with the results of the operation
        """
        try:
            # Get reference to subscriptionPlans collection
            plans_ref = AdminSubscriptionService.get_ref('subscriptionPlans')

            # Track results
            result = {
                "success": True,
                "updated": [],
                "error": None
            }

            # Update each default plan
            for plan_id, plan_data in AdminSubscriptionService.DEFAULT_PLANS.items():
                plans_ref.child(plan_id).set(plan_data)
                result["updated"].append(plan_id)
                logger.info(f"Force updated subscription plan: {plan_id}")

            return result

        except Exception as e:
            logger.error(f"Error force updating subscription plans: {str(e)}")
            return {
                "success": False,
                "updated": [],
                "error": str(e)
            }
