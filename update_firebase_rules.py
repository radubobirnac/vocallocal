"""
Script to update Firebase database rules.
"""
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_firebase_rules():
    """Update Firebase database rules for user accounts and usage tracking."""
    # Get Firebase database URL from environment
    db_url = os.getenv('FIREBASE_DATABASE_URL')
    if not db_url:
        db_url = "https://vocal-local-e1e70-default-rtdb.firebaseio.com"
        print(f"Warning: Using default Firebase URL: {db_url}")

    # Get Firebase auth token (this would require additional authentication)
    # For this example, we'll just provide instructions

    # Load rules from file
    try:
        # First try to load the standard JSON file (no comments)
        with open('firebase-rules.json', 'r') as f:
            rules = json.load(f)
        rules_file = 'firebase-rules.json'
    except (json.JSONDecodeError, FileNotFoundError):
        try:
            # If that fails, try the file with comments (for Firebase Console)
            with open('firebase-rules-with-comments.json', 'r') as f:
                # This will fail if there are actual JSON syntax errors
                # but will work with comments
                rules_text = f.read()
                # Remove comments for local processing
                import re
                rules_text = re.sub(r'//.*$', '', rules_text, flags=re.MULTILINE)
                rules = json.loads(rules_text)
            rules_file = 'firebase-rules-with-comments.json'
            print("Using rules file with comments. This file works in the Firebase Console but may not be valid JSON.")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading Firebase rules: {str(e)}")
            return

    print(f"Loaded rules from: {rules_file}")
    print("\nFirebase Database Rules:")
    print(json.dumps(rules, indent=2))
    print("\nTo update your Firebase database rules:")
    print("1. Go to the Firebase Console: https://console.firebase.google.com/")
    print("2. Select your project")
    print("3. Go to Realtime Database")
    print("4. Click on the 'Rules' tab")
    print("5. Replace the rules with the content from the file:")
    print(f"   {os.path.abspath(rules_file)}")
    print("\nAlternatively, you can use the Firebase Admin SDK or REST API to update the rules programmatically.")
    print("See: https://firebase.google.com/docs/database/security/get-started#update_rules")

    print("\nDatabase Structure:")
    print("""
User Account Structure:
- /users/{userId}/profile
  - email (string): User's email address
  - displayName (string): User's display name
  - createdAt (timestamp): Account creation date
  - lastLoginAt (timestamp): Last login date
  - status (string): Account status (e.g., "active", "suspended", "inactive")

- /users/{userId}/subscription
  - planType (string): Type of subscription plan (e.g., "free", "basic", "premium")
  - status (string): Subscription status (e.g., "active", "canceled", "expired")
  - startDate (timestamp): Subscription start date
  - endDate (timestamp): Subscription end date
  - renewalDate (timestamp): Next renewal date
  - paymentMethod (string): Payment method used
  - billingCycle (string): Billing frequency (e.g., "monthly", "annual")

- /users/{userId}/usage/currentPeriod
  - transcriptionMinutes (number): Minutes of audio transcribed in current period
  - translationWords (number): Number of words translated in current period
  - ttsMinutes (number): Minutes of text-to-speech generated in current period
  - aiCredits (number): AI credits used in current period
  - resetDate (timestamp): Date when usage counters will reset

- /users/{userId}/usage/totalUsage
  - transcriptionMinutes (number): Total minutes of audio transcribed
  - translationWords (number): Total number of words translated
  - ttsMinutes (number): Total minutes of text-to-speech generated
  - aiCredits (number): Total AI credits used

- /users/{userId}/billing/payAsYouGo
  - unitsRemaining (object): Remaining units by service type
    - transcriptionMinutes (number)
    - translationWords (number)
    - ttsMinutes (number)
    - aiCredits (number)
  - purchaseHistory (array): List of previous purchases
    - Each entry contains: date, amount, serviceType, unitsPurchased
""")

if __name__ == "__main__":
    update_firebase_rules()
