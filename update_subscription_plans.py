"""
Script to update subscription plans in Firebase to match exact specifications.

This script updates the existing subscription plans in Firebase to match
the exact requirements specified by the user.
"""

import os
import json
import logging
from dotenv import load_dotenv
from services.admin_subscription_service import AdminSubscriptionService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def update_subscription_plans():
    """Update subscription plans to match exact specifications."""
    logger.info("Updating subscription plans to match exact specifications...")

    try:
        # First, initialize any missing plans
        logger.info("Initializing any missing subscription plans...")
        init_result = AdminSubscriptionService.initialize_subscription_plans()

        if init_result["success"]:
            if init_result["created"]:
                logger.info(f"Created new subscription plans: {', '.join(init_result['created'])}")
            if init_result["existing"]:
                logger.info(f"Found existing subscription plans: {', '.join(init_result['existing'])}")
        else:
            logger.error(f"Error initializing subscription plans: {init_result.get('error')}")
            return False

        # Force update all plans to match exact specifications
        logger.info("Force updating all plans to match exact specifications...")

        force_update_result = AdminSubscriptionService.force_update_all_plans()

        if force_update_result["success"]:
            logger.info("Successfully force updated all subscription plans")
            logger.info(f"Updated plans: {', '.join(force_update_result['updated'])}")
        else:
            logger.error(f"Error force updating plans: {force_update_result.get('error')}")
            return False

        # Verify all plans match specifications
        logger.info("Verifying all subscription plans...")
        all_plans = AdminSubscriptionService.get_all_subscription_plans(include_inactive=True)

        # Expected specifications
        expected_specs = {
            "free": {
                "name": "Free Plan",
                "price": 0,
                "transcriptionMinutes": 60,
                "translationWords": 0,
                "ttsMinutes": 0,
                "aiCredits": 0,
                "transcriptionModel": "gemini-2.0-flash-lite"
            },
            "basic": {
                "name": "Basic Plan",
                "price": 4.99,
                "transcriptionMinutes": 280,
                "translationWords": 50000,
                "ttsMinutes": 60,
                "aiCredits": 50,
                "transcriptionModel": "premium"
            },
            "professional": {
                "name": "Professional Plan",
                "price": 12.99,
                "transcriptionMinutes": 800,
                "translationWords": 160000,
                "ttsMinutes": 200,
                "aiCredits": 150,
                "transcriptionModel": "premium"
            },
            "payg": {
                "name": "Pay-as-you-go Credits",
                "price": 3.99,
                "credits": 300,
                "requiresSubscription": True
            }
        }

        # Verify each plan
        all_match = True
        for plan_id, expected in expected_specs.items():
            if plan_id in all_plans:
                current = all_plans[plan_id]
                logger.info(f"\n{plan_id.upper()} PLAN:")
                logger.info(f"  Name: {current.get('name')} (Expected: {expected['name']})")
                logger.info(f"  Price: ${current.get('price')} (Expected: ${expected['price']})")

                if 'transcriptionMinutes' in expected:
                    logger.info(f"  Transcription Minutes: {current.get('transcriptionMinutes')} (Expected: {expected['transcriptionMinutes']})")
                if 'translationWords' in expected:
                    logger.info(f"  Translation Words: {current.get('translationWords')} (Expected: {expected['translationWords']})")
                if 'ttsMinutes' in expected:
                    logger.info(f"  TTS Minutes: {current.get('ttsMinutes')} (Expected: {expected['ttsMinutes']})")
                if 'aiCredits' in expected:
                    logger.info(f"  AI Credits: {current.get('aiCredits')} (Expected: {expected['aiCredits']})")
                if 'transcriptionModel' in expected:
                    logger.info(f"  Transcription Model: {current.get('transcriptionModel')} (Expected: {expected['transcriptionModel']})")
                if 'credits' in expected:
                    logger.info(f"  Credits: {current.get('credits')} (Expected: {expected['credits']})")
                if 'requiresSubscription' in expected:
                    logger.info(f"  Requires Subscription: {current.get('requiresSubscription')} (Expected: {expected['requiresSubscription']})")

                # Check if all fields match
                for field, expected_value in expected.items():
                    if current.get(field) != expected_value:
                        logger.warning(f"  ⚠️  {field} mismatch: {current.get(field)} != {expected_value}")
                        all_match = False
                    else:
                        logger.info(f"  ✅ {field} matches")
            else:
                logger.error(f"Plan {plan_id} not found!")
                all_match = False

        if all_match:
            logger.info("\n🎉 All subscription plans match the exact specifications!")
        else:
            logger.warning("\n⚠️  Some subscription plans don't match the specifications.")

        return True

    except Exception as e:
        logger.error(f"Error updating subscription plans: {str(e)}")
        return False

def display_current_plans():
    """Display all current subscription plans."""
    logger.info("Current subscription plans in Firebase:")

    try:
        all_plans = AdminSubscriptionService.get_all_subscription_plans(include_inactive=True)

        for plan_id, plan_data in all_plans.items():
            logger.info(f"\n{plan_id.upper()}:")
            logger.info(f"  {json.dumps(plan_data, indent=2)}")

    except Exception as e:
        logger.error(f"Error fetching subscription plans: {str(e)}")

if __name__ == "__main__":
    # Update subscription plans
    success = update_subscription_plans()

    if success:
        logger.info("\n" + "="*50)
        display_current_plans()
    else:
        logger.error("Failed to update subscription plans")
