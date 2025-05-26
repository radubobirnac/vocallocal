"""
Script to initialize subscription plans in Firebase.

This script creates the default subscription plans in the Firebase Realtime Database
if they don't already exist.
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

def initialize_subscription_plans():
    """Initialize subscription plans in Firebase."""
    logger.info("Initializing subscription plans...")
    
    # Initialize Firebase connection
    try:
        # Call the service to initialize subscription plans
        result = AdminSubscriptionService.initialize_subscription_plans()
        
        if result["success"]:
            if result["created"]:
                logger.info(f"Created subscription plans: {', '.join(result['created'])}")
            if result["existing"]:
                logger.info(f"Subscription plans already exist: {', '.join(result['existing'])}")
            
            # Get all subscription plans
            all_plans = AdminSubscriptionService.get_all_subscription_plans(include_inactive=True)
            
            # Print all plans
            logger.info("Current subscription plans:")
            for plan_id, plan_data in all_plans.items():
                logger.info(f"  - {plan_id}: {plan_data.get('name')} (${plan_data.get('price')})")
                
            return True
        else:
            logger.error(f"Error initializing subscription plans: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"Error initializing subscription plans: {str(e)}")
        return False

def update_subscription_plan(plan_id, updated_data):
    """
    Update an existing subscription plan.
    
    Args:
        plan_id (str): The ID of the plan to update
        updated_data (dict): The new data to update the plan with
        
    Returns:
        bool: True if the update was successful, False otherwise
    """
    logger.info(f"Updating subscription plan: {plan_id}")
    
    try:
        # Call the service to update the subscription plan
        result = AdminSubscriptionService.update_subscription_plan(plan_id, updated_data)
        
        if result["success"]:
            logger.info(f"Successfully updated subscription plan: {plan_id}")
            logger.info(f"Updated fields: {', '.join(result['updated_fields'])}")
            
            # Get the updated plan
            updated_plan = AdminSubscriptionService.get_subscription_plan(plan_id)
            logger.info(f"Updated plan: {json.dumps(updated_plan, indent=2)}")
            
            return True
        else:
            logger.error(f"Error updating subscription plan: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating subscription plan: {str(e)}")
        return False

if __name__ == "__main__":
    # Initialize subscription plans
    initialize_subscription_plans()
    
    # Example of updating a plan (uncomment to use)
    # update_subscription_plan("basic", {
    #     "price": 5.99,
    #     "transcriptionMinutes": 300,
    #     "isActive": True
    # })
