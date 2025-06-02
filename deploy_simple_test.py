#!/usr/bin/env python3
"""
Deploy Simple Test Version to DigitalOcean
This temporarily replaces app.py with a simplified version for debugging
"""

import requests
import json
import time
import sys
import shutil
import os

# Auto-install requests if not available
try:
    import requests
except ImportError:
    print("📦 Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

def backup_and_replace_app():
    """Backup current app.py and replace with simple version"""
    print("🔄 BACKING UP AND REPLACING APP.PY")
    print("=" * 50)
    
    try:
        # Backup current app.py
        if os.path.exists('app.py'):
            shutil.copy2('app.py', 'app_backup.py')
            print("✅ Backed up app.py to app_backup.py")
        
        # Replace with simple version
        if os.path.exists('app_simple.py'):
            shutil.copy2('app_simple.py', 'app.py')
            print("✅ Replaced app.py with simplified version")
            return True
        else:
            print("❌ app_simple.py not found")
            return False
            
    except Exception as e:
        print(f"❌ Error during backup/replace: {e}")
        return False

def restore_app():
    """Restore original app.py"""
    print("\n🔄 RESTORING ORIGINAL APP.PY")
    print("=" * 50)
    
    try:
        if os.path.exists('app_backup.py'):
            shutil.copy2('app_backup.py', 'app.py')
            print("✅ Restored original app.py")
            return True
        else:
            print("❌ app_backup.py not found")
            return False
    except Exception as e:
        print(f"❌ Error during restore: {e}")
        return False

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
        """Trigger a new deployment"""
        print("🚀 Triggering new deployment...")
        
        try:
            deployment_data = {'force_build': True}
            
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
        
        for i in range(60):
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
                        return False
                    else:
                        dots = "." * (i % 4)
                        print(f"⏳ Deployment status: {phase}{dots} ({i+1}/60)")
                
                time.sleep(10)
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Error checking deployment: {e}")
                time.sleep(10)
        
        print("⚠️  Deployment taking longer than expected")
        return True
    
    def test_simple_version(self):
        """Test the simple version"""
        print("\n🧪 TESTING SIMPLE VERSION")
        print("=" * 50)
        
        routes_to_test = [
            ('/', 'Home page'),
            ('/login', 'Login page'),
            ('/health', 'Health check'),
            ('/api/health', 'API health check'),
            ('/pricing', 'Pricing page'),
            ('/transcribe', 'Transcribe page'),
            ('/translate', 'Translate page'),
            ('/debug-test', 'Debug test page'),
            ('/debug-routes', 'Debug routes list'),
        ]
        
        working_count = 0
        
        for path, description in routes_to_test:
            url = f"{self.app_url}{path}"
            try:
                response = requests.get(url, timeout=30)
                status = response.status_code
                
                if status < 400:
                    print(f"✅ {description}: {status}")
                    working_count += 1
                else:
                    print(f"❌ {description}: {status}")
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ {description}: ERROR - {e}")
        
        return working_count, len(routes_to_test)

def main():
    api_token = "dop_v1_f8ea2bbb3908c9c11cca7c631a3973eff1966ab5ab3fc376b5820b4630670891"
    
    print("🧪 VOCALLOCAL SIMPLE VERSION TEST")
    print("=" * 60)
    print("This will temporarily replace your app with a simplified version for testing")
    
    try:
        # Step 1: Backup and replace app.py
        if not backup_and_replace_app():
            print("❌ Failed to backup/replace app.py")
            return
        
        # Step 2: Deploy
        deployer = DigitalOceanDeployer(api_token)
        
        if not deployer.find_vocallocal_app():
            restore_app()
            return
        
        deployment_id = deployer.trigger_deployment()
        if not deployment_id:
            print("❌ Could not trigger deployment")
            restore_app()
            return
        
        deployment_success = deployer.wait_for_deployment(deployment_id)
        
        # Step 3: Test the simple version
        working_count, total_count = deployer.test_simple_version()
        
        print(f"\n📊 SIMPLE VERSION RESULTS:")
        print("=" * 50)
        print(f"✅ Working routes: {working_count}/{total_count}")
        
        if working_count >= 7:
            print("\n🎉 SIMPLE VERSION WORKS!")
            print("This means the issue is with blueprint imports in the complex version")
            print("\n🔗 Test the simple version:")
            print(f"   Main app: {deployer.app_url}")
            print(f"   Debug routes: {deployer.app_url}/debug-routes")
            print(f"   Debug test: {deployer.app_url}/debug-test")
        else:
            print(f"\n⚠️  SIMPLE VERSION STILL HAS ISSUES")
            print("This suggests a more fundamental problem")
        
        # Step 4: Ask user what to do next
        print(f"\n🤔 WHAT WOULD YOU LIKE TO DO?")
        print("1. Keep the simple version running (for testing)")
        print("2. Restore the original version")
        
        choice = input("Enter your choice (1 or 2): ").strip()
        
        if choice == "2":
            restore_app()
            print("✅ Original app.py restored")
            print("You can now work on fixing the blueprint issues")
        else:
            print("✅ Simple version kept running")
            print("You can test it and then manually restore app.py later")
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        print("Attempting to restore original app.py...")
        restore_app()
    
    input("\n👆 Press ENTER to close this window...")

if __name__ == "__main__":
    main()
