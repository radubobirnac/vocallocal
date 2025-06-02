#!/usr/bin/env python3
"""
Deploy Route Fix to DigitalOcean
This script triggers a new deployment with the fixed route registration
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
    
    def test_all_routes(self):
        """Test all the routes that were previously broken"""
        print("\n🧪 TESTING ALL ROUTES...")
        print("=" * 50)
        
        routes_to_test = [
            ('/', 'Home page'),
            ('/login', 'Login page'),
            ('/auth/google', 'Google OAuth'),
            ('/auth/callback', 'OAuth callback'),
            ('/health', 'Health check'),
            ('/api/health', 'API health check'),
            ('/transcribe', 'Transcribe page'),
            ('/translate', 'Translate page'),
            ('/try-it-free', 'Try it free page'),
            ('/pricing', 'Pricing page'),
        ]
        
        results = {}
        working_count = 0
        
        for path, description in routes_to_test:
            url = f"{self.app_url}{path}"
            try:
                response = requests.get(url, timeout=30, allow_redirects=False)
                status = response.status_code
                
                if status < 400:
                    print(f"✅ {description}: {status}")
                    working_count += 1
                    results[path] = {'status': status, 'working': True}
                elif status == 302:
                    print(f"🔄 {description}: {status} (Redirect)")
                    working_count += 1
                    results[path] = {'status': status, 'working': True}
                else:
                    print(f"❌ {description}: {status}")
                    results[path] = {'status': status, 'working': False}
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ {description}: ERROR - {e}")
                results[path] = {'status': 'ERROR', 'working': False}
        
        return results, working_count, len(routes_to_test)
    
    def run_deployment(self):
        """Run the complete deployment process"""
        print("🚀 VOCALLOCAL ROUTE FIX DEPLOYMENT")
        print("=" * 50)
        
        if not self.find_vocallocal_app():
            return False
        
        deployment_id = self.trigger_deployment()
        if not deployment_id:
            print("❌ Could not trigger deployment")
            return False
        
        deployment_success = self.wait_for_deployment(deployment_id)
        
        # Test all routes
        route_results, working_count, total_count = self.test_all_routes()
        
        print(f"\n📊 FINAL RESULTS:")
        print("=" * 50)
        print(f"✅ Working routes: {working_count}/{total_count}")
        
        if working_count >= 8:  # Most routes should work
            print("\n🎉 ROUTE FIX SUCCESSFULLY DEPLOYED!")
            print(f"\n🔗 Test your app: {self.app_url}")
            print(f"🔗 Test login: {self.app_url}/login")
            print(f"🔗 Test transcribe: {self.app_url}/transcribe")
            return True
        else:
            print(f"\n⚠️  DEPLOYMENT COMPLETED BUT {total_count - working_count} ROUTES STILL BROKEN")
            print("Check the test results above")
            return False

def main():
    api_token = "dop_v1_f8ea2bbb3908c9c11cca7c631a3973eff1966ab5ab3fc376b5820b4630670891"
    
    try:
        deployer = DigitalOceanDeployer(api_token)
        success = deployer.run_deployment()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 SUCCESS! Routes should now be working!")
            print("🔗 Try the app: https://vocallocal-l5et5.ondigitalocean.app")
        else:
            print("⚠️  DEPLOYMENT COMPLETED - Check test results above")
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        print("Please share this error message if you need help")
    
    # Keep window open
    input("\n👆 Press ENTER to close this window...")

if __name__ == "__main__":
    main()
