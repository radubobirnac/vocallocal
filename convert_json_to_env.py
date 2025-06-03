"""
Script to convert JSON credential files to environment variable format for secure deployment.
Run this LOCALLY to convert your credential files to environment variables.
DO NOT commit or push your credential files or the output of this script to GitHub.

This script converts:
- Oauth.json -> GOOGLE_OAUTH_CREDENTIALS_JSON
- firebase-credentials.json -> FIREBASE_CREDENTIALS_JSON

These environment variables provide better security than committing JSON files.
"""
import json
import os

def convert_json_to_env_var(json_file_path, var_name):
    """Convert a JSON file to a string that can be used as an environment variable."""
    try:
        with open(json_file_path, 'r') as f:
            json_data = json.load(f)
        
        # Convert to a compact JSON string
        json_str = json.dumps(json_data, separators=(',', ':'))
        
        print(f"\n{var_name}={json_str}\n")
        print("Copy the above line and add it to your deployment platform environment variables.")
        print("(Render, DigitalOcean, Heroku, etc.)")
        print("DO NOT commit this value to GitHub or share it publicly.")
        
        return True
    except Exception as e:
        print(f"Error converting {json_file_path}: {str(e)}")
        return False

if __name__ == "__main__":
    print("VocalLocal Credential Converter")
    print("=" * 40)
    print("Converting JSON credential files to secure environment variables...")
    print()

    # Convert OAuth.json
    oauth_path = os.path.join(os.path.dirname(__file__), 'Oauth.json')
    if os.path.exists(oauth_path):
        print("Converting OAuth.json to environment variable...")
        convert_json_to_env_var(oauth_path, 'GOOGLE_OAUTH_CREDENTIALS_JSON')
    else:
        print("OAuth.json not found.")

    # Convert firebase-credentials.json
    firebase_path = os.path.join(os.path.dirname(__file__), 'firebase-credentials.json')
    if os.path.exists(firebase_path):
        print("Converting firebase-credentials.json to environment variable...")
        convert_json_to_env_var(firebase_path, 'FIREBASE_CREDENTIALS_JSON')
    else:
        print("firebase-credentials.json not found.")

    print()
    print("Security Notes:")
    print("- Keep these environment variables secure")
    print("- Never commit them to version control")
    print("- Use your deployment platform's secure environment variable storage")
    print("- The original JSON files are already in .gitignore")