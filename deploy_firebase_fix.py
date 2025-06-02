#!/usr/bin/env python3
"""
Deploy Firebase fix to DigitalOcean
This script triggers a new deployment with the fixed firebase_config.py
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

class DigitalOceanDeployer:
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
    
    def trigger_deployment(self):
        """Trigger a new deployment to pick up the code changes"""
        print("🚀 Triggering new deployment...")
        
        try:
            # Create a new deployment
            deployment_data = {
                'force_build': True
            }
            
            response = requests.post(
                f'{self.base_url}/apps/{self.app_id}/deployments',
                headers=self.headers,
                json=deployment_data
            )
            response.raise_for_status()
            
            deployment = response.json().get('deployment', {})
            deployment_id = deployment.get('id')
            
            print(f"✅ New deployment triggered: {deployment_id}")
            return deployment_id
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error triggering deployment: {e}")
            return None
    
    def wait_for_deployment(self, deployment_id=None):
        """Wait for deployment to complete"""
        print("⏳ Waiting for deployment to complete...")
        
        for i in range(60):  # Wait up to 10 minutes
            try:
                response = requests.get(f'{self.base_url}/apps/{self.app_id}/deployments', headers=self.headers)
                response.raise_for_status()
                
                deployments = response.json().get('deployments', [])
                if deployments:
                    latest = deployments[0]
                    phase = latest.get('phase', 'UNKNOWN')
                    
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
        
        print("⚠️  Deployment taking longer than expected")
        return True  # Continue anyway
    
    def validate_firebase_fix(self):
        """Test if Firebase is now working"""
        print("\n🧪 TESTING FIREBASE FIX...")
        print("=" * 50)
        
        validation_results = {
            'app_responding': False,
            'firebase_error_gone': False,
            'login_page_working': False
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
            if response.status_code == 200:
                validation_results['login_page_working'] = True
                if "Could not initialize Firebase" not in response.text and "FIREBASE_CREDENTIALS_PATH" not in response.text:
                    print("✅ Firebase error appears to be fixed!")
                    validation_results['firebase_error_gone'] = True
                else:
                    print("❌ Firebase error still present")
            else:
                print(f"⚠️  Login page responded with status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Could not test Firebase: {e}")
        
        return validation_results
    
    def run_deployment(self):
        """Run the complete deployment process"""
        print("🚀 VOCALLOCAL FIREBASE FIX DEPLOYMENT")
        print("=" * 50)
        
        if not self.find_vocallocal_app():
            return False
        
        deployment_id = self.trigger_deployment()
        if not deployment_id:
            print("❌ Could not trigger deployment")
            return False
        
        deployment_success = self.wait_for_deployment(deployment_id)
        
        # Always validate, even if deployment seemed to fail
        validation_results = self.validate_firebase_fix()
        
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
        
        if validation_results['login_page_working']:
            print("✅ Login page is accessible")
        else:
            print("❌ Login page has issues")
        
        if validation_results['firebase_error_gone'] and validation_results['app_responding']:
            print("\n🎉 FIREBASE FIX SUCCESSFULLY DEPLOYED!")
            print(f"\n🔗 Test your app: {self.app_url}")
            print(f"🔗 Test login: {self.app_url}/login")
            return True
        else:
            print("\n⚠️  DEPLOYMENT COMPLETED BUT ISSUES REMAIN")
            print("Check the validation results above")
            return False

def main():
    api_token = "dop_v1_f8ea2bbb3908c9c11cca7c631a3973eff1966ab5ab3fc376b5820b4630670891"
    
    try:
        deployer = DigitalOceanDeployer(api_token)
        success = deployer.run_deployment()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 SUCCESS! Firebase should now be working!")
            print("🔗 Try logging in: https://vocallocal-l5et5.ondigitalocean.app/login")
        else:
            print("⚠️  DEPLOYMENT COMPLETED - Check validation results above")
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        print("Please share this error message if you need help")
    
    # Keep window open
    input("\n👆 Press ENTER to close this window...")

if __name__ == "__main__":
    main()
