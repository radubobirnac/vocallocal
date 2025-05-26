"""
Script to set up subscription plans in Firebase.

This script initializes the subscription plans in Firebase and provides
instructions for updating the Firebase rules.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Main function to set up subscription plans."""
    logger.info("Setting up subscription plans for VocalLocal...")
    
    # Step 1: Update Firebase rules
    logger.info("\nStep 1: Update Firebase Rules")
    from update_firebase_rules import update_firebase_rules
    update_firebase_rules()
    
    # Step 2: Initialize subscription plans
    logger.info("\nStep 2: Initialize Subscription Plans")
    from initialize_subscription_plans import initialize_subscription_plans
    result = initialize_subscription_plans()
    
    if result:
        logger.info("\nSubscription plans setup completed successfully!")
        logger.info("You can now use the subscription plans in your application.")
    else:
        logger.error("\nFailed to initialize subscription plans.")
        logger.error("Please check the logs for more information.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
