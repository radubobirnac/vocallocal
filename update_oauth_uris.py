"""
Script to update the redirect URIs in the OAuth.json file.
This ensures that both HTTP and HTTPS URIs are included for local development.
"""
import os
import json
import argparse

def update_oauth_redirect_uris(port=5001):
    """Update the OAuth.json file with both HTTP and HTTPS redirect URIs."""
    oauth_file_path = os.path.join(os.path.dirname(__file__), 'Oauth.json')
    
    if not os.path.exists(oauth_file_path):
        print(f"Error: OAuth.json file not found at {oauth_file_path}")
        return False
    
    try:
        # Read the current OAuth.json file
        with open(oauth_file_path, 'r') as f:
            oauth_data = json.load(f)
        
        if 'web' not in oauth_data:
            print("Error: Invalid OAuth.json format - missing 'web' key")
            return False
        
        # Define the URIs we want to ensure are included
        required_uris = [
            f"http://localhost:{port}/auth/callback",
            f"https://localhost:{port}/auth/callback",
            f"http://localhost:{port}/auth/google/callback",
            f"https://localhost:{port}/auth/google/callback",
            f"http://127.0.0.1:{port}/auth/callback",
            f"https://127.0.0.1:{port}/auth/callback",
            f"http://127.0.0.1:{port}/auth/google/callback",
            f"https://127.0.0.1:{port}/auth/google/callback",
            "https://vocallocal.onrender.com/auth/callback",
            "https://vocallocal-aj6b.onrender.com/auth/callback",
            "https://vocallocal-l5et5.ondigitalocean.app/auth/callback",
            "https://test-vocallocal-x9n74.ondigitalocean.app/auth/callback"
        ]
        
        # Get current redirect URIs or initialize empty list
        current_uris = oauth_data['web'].get('redirect_uris', [])
        
        # Add any missing URIs
        for uri in required_uris:
            if uri not in current_uris:
                current_uris.append(uri)
        
        # Update the OAuth data
        oauth_data['web']['redirect_uris'] = current_uris
        
        # Write the updated data back to the file
        with open(oauth_file_path, 'w') as f:
            json.dump(oauth_data, f, indent=2)
        
        print(f"Updated OAuth.json with the following redirect URIs:")
        for uri in current_uris:
            print(f"  - {uri}")
        
        print("\nIMPORTANT: You must also update these redirect URIs in the Google Cloud Console:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Select your project")
        print("3. Go to APIs & Services > Credentials")
        print("4. Edit your OAuth 2.0 Client ID")
        print("5. Add all the above URIs to the 'Authorized redirect URIs' section")
        print("6. Save your changes")
        
        return True
    
    except Exception as e:
        print(f"Error updating OAuth.json: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update OAuth.json redirect URIs')
    parser.add_argument('--port', type=int, default=5001,
                        help='Port to use for redirect URIs (default: 5001)')
    
    args = parser.parse_args()
    update_oauth_redirect_uris(args.port)
