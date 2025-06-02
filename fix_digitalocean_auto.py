#!/usr/bin/env python3
"""
VocalLocal DigitalOcean Auto-Fix Script
Automatically fixes environment variables using DigitalOcean API
"""

import requests
import json
import time
import sys

# Auto-install requests if not available
try:
    import requests
except ImportError:
    print("📦 Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

class DigitalOceanFixer:
    def __init__(self, api_token):
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        self.base_url = 'https://api.digitalocean.com/v2'
        self.app_id = None
        self.app_url = None
    
    def find_vocallocal_app(self):
        """Find the VocalLocal app"""
        print("🔍 Finding your VocalLocal app...")
        
        try:
            response = requests.get(f'{self.base_url}/apps', headers=self.headers)
            response.raise_for_status()
            
            apps = response.json().get('apps', [])
            
            for app in apps:
                if 'vocallocal' in app.get('spec', {}).get('name', '').lower():
                    self.app_id = app['id']
                    self.app_url = app.get('live_url', '')
                    print(f"✅ Found VocalLocal app: {app['spec']['name']}")
                    print(f"📱 URL: {self.app_url}")
                    return True
            
            print("❌ Could not find VocalLocal app")
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error finding app: {e}")
            return False
    
    def get_current_env_vars(self):
        """Get current environment variables"""
        print("📋 Getting current environment variables...")
        
        try:
            response = requests.get(f'{self.base_url}/apps/{self.app_id}', headers=self.headers)
            response.raise_for_status()
            
            app_spec = response.json()['app']['spec']
            services = app_spec.get('services', [])
            
            if services:
                return services[0].get('environment_slug', None), services[0].get('envs', [])
            
            return None, []
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting environment variables: {e}")
            return None, []
    
    def fix_firebase_credentials(self, current_envs):
        """Fix Firebase credentials environment variable"""
        print("🔧 Fixing Firebase credentials...")
        
        firebase_json = {
            "type": "service_account",
            "project_id": "vocal-local-e1e70",
            "private_key_id": "98a96a0f6dc2c3e7900912b92742b2b180ee742e",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDj+FAM4vpdVgvI\n5yyvbxJe7x+n/12aDBkqg/n9r+Hl8DJqiqgdA8YIr1AZScLM06yjSCAKAa7/o4F/\n3lk3Tnnf1C1NI0+8RnITaKGPX5S8mLtpD+zsie6Tu38BzoVD3iDVyIN49v7KY9b9\n4mAzZGIaCI7wSqqOdNg8+11bsC5Jo3+TSS1vvt4zQKFThc+x7ahnMA6RSkEdYNMh\nU6JA8zEWYDD3NQAz2PdCzwH4w6YbQyzgcB5gbkwLraw5IxkGgWlQvHTLpv5tWf+m\nOwl+/njfRLubdxMAfKMdUZKaJ7frJO0pUhv+S3ma56oMDM9v4jGfDsBpxAabC4UD\nSFJZ2XqJAgMBAAECggEAEUJMQC+CdCTGq2D6GHWMouCQaVn7WoVqNdZsS50gWXXK\nAVgqQlkV6fQo2KNFktd/MVTtbQiD2NGGhTlekIH51tzjyZxf5eGA8zB3k8jRFEat\nYJa+sYk/RVK7erXpj7HuUzUVJAgyEb1Fim7UKOvjg/RMKwvCFhspQFOo9Z803+jy\n6wyskHlBgcJSbNvmHJQk1EVEbZ1Y6Yikb/a6VEdN01gbPeyeJIEhhdHXTfr1oAJI\nHrB9TpLrcDA2RK5tynStlK+it/omkuKaSUd9kB/xUn3vL1imUaIFcKUFlZ0eDi6Z\ndcA+v2Y9UzgZIRbOpN2ctPg3N5Btzs29irAFbNcIQQKBgQD8iRWeEesnfSglvfWa\nduS9443zfqwgkXyKd2ZxLvSkhJ0OJuT1jivYXMaVBMmpRxEyLaRy5yZ6izxaoSEp\nE121b3ZFmjjA+Ku8AG4vVpNQifwa2ISPXkXJXogrDv4kU5RJVCh5M9JYl0RPOyDN\nMc23I5RuturwcxEnaGsIkxu3QQKBgQDnGPP+jFtFMwgB9o9aBrJk8xANktUZ7c/J\n8ENAaCjDHJJn1AdDEUqYw7CdngX3IRCv0JSG207FMmv3xu/VwgI/SVasl2J17P5V\nF9u1Al9ox6im4w+8HDijx7pLW9alhosRFP7jgRJyon/sLZxnSMrT7sRAxgpmSsbp\nvk6/mLT5SQKBgQDuL4nRJktqWnSkbG+bOepzY44+jEpjCXWyz/0yYbxi86WCdJLd\nPDQEhTTT1skxvRLuBfimW3iCepL5VCKHsHlhKHkgGt7Ou3yW/LzwLzMQ8qRy2abl\n5l/iFyRNoH15287v/s2Ry5vo7PuD01wTzZae1pMofaRIF++lAKp7Uu0AQQKBgGxg\n0HTNQDSIxTWeewYeY+Vh9GJZPSVm2O78hZ2b+5ndOXAGCM3UOya/h4GzzVpjoF7D\ntBQ2n49toSLXojyeOs2RSFuyt1NUrMYdZUVTcolCMX7qt8NhfNKaZWzYCicgnPGK\n5iqtqogmW1XY4iOyCKUxscoq1k+4u+Z9AJNsO1s5AoGBAKaAc1TZnye9+vYMmojp\nXt6iOnku6MJZ6YccSyKgxiFyoxGgbLayYQYFTpnLyUVCoj1aFlvSs1zNOpAIqwkt\nsqacZt2sWP+AmVc3RFQaQHO+/omJj6VESX28KSqkhDqjxwRMXFIJuE3Z7DJ9ZpWY\nGYNL19wEf2zuQ/tz+yW2Wl3G\n-----END PRIVATE KEY-----\n",
            "client_email": "firebase-adminsdk-fbsvc@vocal-local-e1e70.iam.gserviceaccount.com",
            "client_id": "103578034737972704669",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40vocal-local-e1e70.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }
        
        # Remove old FIREBASE_CREDENTIALS_JSON if it exists
        updated_envs = [env for env in current_envs if env.get('key') != 'FIREBASE_CREDENTIALS_JSON']
        
        # Add correct FIREBASE_CREDENTIALS
        updated_envs.append({
            'key': 'FIREBASE_CREDENTIALS',
            'value': json.dumps(firebase_json),
            'scope': 'RUN_TIME'
        })
        
        return updated_envs
    
    def update_app_config(self, updated_envs):
        """Update the app configuration"""
        print("🚀 Updating app configuration...")
        
        try:
            # Get current app spec
            response = requests.get(f'{self.base_url}/apps/{self.app_id}', headers=self.headers)
            response.raise_for_status()
            
            app_spec = response.json()['app']['spec']
            
            # Update environment variables
            if 'services' in app_spec and app_spec['services']:
                app_spec['services'][0]['envs'] = updated_envs
            
            # Update the app
            update_data = {'spec': app_spec}
            response = requests.put(
                f'{self.base_url}/apps/{self.app_id}',
                headers=self.headers,
                json=update_data
            )
            response.raise_for_status()
            
            print("✅ App configuration updated successfully!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error updating app: {e}")
            return False
    
    def wait_for_deployment(self):
        """Wait for deployment to complete with better feedback"""
        print("⏳ Waiting for deployment to complete...")

        for i in range(60):  # Wait up to 10 minutes
            try:
                response = requests.get(f'{self.base_url}/apps/{self.app_id}/deployments', headers=self.headers)
                response.raise_for_status()

                deployments = response.json().get('deployments', [])
                if deployments:
                    latest = deployments[0]
                    phase = latest.get('phase', 'UNKNOWN')
                    progress = latest.get('progress', {})

                    if phase == 'ACTIVE':
                        print("✅ Deployment completed successfully!")
                        return True
                    elif phase in ['FAILED', 'CANCELED']:
                        print(f"❌ Deployment failed: {phase}")
                        if 'error' in latest:
                            print(f"   Error details: {latest['error']}")
                        return False
                    else:
                        dots = "." * (i % 4)
                        print(f"⏳ Deployment status: {phase}{dots} ({i+1}/60)")

                time.sleep(10)

            except requests.exceptions.RequestException as e:
                print(f"⚠️  Error checking deployment: {e}")
                time.sleep(10)

        print("⚠️  Deployment taking longer than expected, but may still succeed")
        return True  # Continue anyway
    
    def print_oauth_instructions(self):
        """Print OAuth setup instructions"""
        print("\n🔧 GOOGLE OAUTH SETUP (MANUAL STEP)")
        print("=" * 50)
        print("📍 Go to: https://console.cloud.google.com/apis/credentials")
        print("📍 Select project: vocal-local-e1e70")
        print("📍 Click on 'Radu' OAuth client")
        print("\n✅ ADD THESE REDIRECT URIs:")
        print(f"   {self.app_url}/auth/callback")
        print(f"   {self.app_url}/auth/google/callback")
        print("\n✅ ADD THIS JAVASCRIPT ORIGIN:")
        print(f"   {self.app_url}")
        print("\n💾 Click SAVE and wait 5 minutes")
    
    def validate_fix(self):
        """Validate that the fix worked"""
        print("\n🧪 VALIDATING THE FIX...")
        print("=" * 50)

        validation_results = {
            'app_responding': False,
            'firebase_error_gone': False,
            'oauth_needs_setup': True
        }

        # Test 1: Check if app is responding
        try:
            print("🔍 Testing if app is responding...")
            response = requests.get(f"{self.app_url}", timeout=30)
            if response.status_code == 200:
                print("✅ App is responding!")
                validation_results['app_responding'] = True
            else:
                print(f"⚠️  App responded with status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ App is not responding: {e}")

        # Test 2: Check if Firebase error is gone
        try:
            print("🔍 Testing Firebase initialization...")
            response = requests.get(f"{self.app_url}/login", timeout=30)
            if "Could not initialize Firebase" not in response.text:
                print("✅ Firebase error appears to be fixed!")
                validation_results['firebase_error_gone'] = True
            else:
                print("❌ Firebase error still present")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Could not test Firebase: {e}")

        return validation_results

    def run_fix(self):
        """Run the complete fix process"""
        print("🚀 VOCALLOCAL DIGITALOCEAN AUTO-FIX")
        print("=" * 50)

        if not self.find_vocallocal_app():
            return False

        _, current_envs = self.get_current_env_vars()
        if not current_envs:
            print("❌ Could not get current environment variables")
            return False

        updated_envs = self.fix_firebase_credentials(current_envs)

        if not self.update_app_config(updated_envs):
            return False

        deployment_success = self.wait_for_deployment()

        # Always validate, even if deployment seemed to fail
        validation_results = self.validate_fix()

        print("\n📊 FINAL RESULTS:")
        print("=" * 50)

        if validation_results['app_responding']:
            print("✅ App is working")
        else:
            print("❌ App is not responding")

        if validation_results['firebase_error_gone']:
            print("✅ Firebase error fixed")
        else:
            print("❌ Firebase error still present")

        if validation_results['firebase_error_gone'] and validation_results['app_responding']:
            print("\n🎉 DIGITALOCEAN CONFIGURATION SUCCESSFULLY FIXED!")
            self.print_oauth_instructions()
            print(f"\n🔗 Test your app: {self.app_url}")
            return True
        else:
            print("\n⚠️  PARTIAL SUCCESS - Some issues remain")
            self.print_oauth_instructions()
            return False

def main():
    api_token = "dop_v1_f8ea2bbb3908c9c11cca7c631a3973eff1966ab5ab3fc376b5820b4630670891"

    try:
        fixer = DigitalOceanFixer(api_token)
        success = fixer.run_fix()

        print("\n" + "=" * 60)
        if success:
            print("🎉 SUCCESS! Your VocalLocal app should now work!")
            print("📝 Next step: Add the OAuth URLs shown above to Google Cloud Console")
            print("⏰ Wait 5 minutes after adding OAuth URLs, then test your app")
        else:
            print("⚠️  PARTIAL SUCCESS - Check the validation results above")
            print("📝 You may still need to add OAuth URLs manually")

        print("\n🔗 Your app URL: https://vocallocal-l5et5.ondigitalocean.app")
        print("🧪 Test login after OAuth setup: https://vocallocal-l5et5.ondigitalocean.app/login")

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        print("Please share this error message if you need help")

    # Keep window open
    input("\n👆 Press ENTER to close this window...")

if __name__ == "__main__":
    main()
