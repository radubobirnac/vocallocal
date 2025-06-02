#!/usr/bin/env python3
"""
Push Changes to GitHub and Deploy to DigitalOcean
This script handles the complete deployment pipeline
"""

import subprocess
import requests
import json
import time
import sys
import os

def run_command(command, description):
    """Run a command and return success/failure"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"✅ {description} successful")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def push_to_github():
    """Push all changes to GitHub"""
    print("\n📤 PUSHING CHANGES TO GITHUB")
    print("=" * 50)
    
    # Check git status
    print("🔍 Checking git status...")
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print(f"📝 Found changes to commit:")
        for line in result.stdout.strip().split('\n'):
            print(f"   {line}")
    else:
        print("ℹ️  No changes detected")
        return True
    
    # Add all changes
    if not run_command("git add .", "Adding all changes"):
        return False
    
    # Commit changes
    commit_message = "Fix missing routes and Firebase authentication"
    if not run_command(f'git commit -m "{commit_message}"', "Committing changes"):
        # Check if it's because there's nothing to commit
        result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
        if not result.stdout.strip():
            print("ℹ️  No changes to commit")
            return True
        return False
    
    # Push to main branch
    if not run_command("git push origin main", "Pushing to GitHub"):
        return False
    
    print("✅ All changes pushed to GitHub successfully!")
    return True

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
        print("🚀 Triggering new deployment from GitHub...")
        
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
    
    def test_key_routes(self):
        """Test the most important routes"""
        print("\n🧪 TESTING KEY ROUTES")
        print("=" * 50)
        
        routes_to_test = [
            ('/', 'Home page'),
            ('/login', 'Login page'),
            ('/health', 'Health check'),
            ('/transcribe', 'Transcribe page'),
            ('/translate', 'Translate page'),
            ('/pricing', 'Pricing page'),
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
    api_token = "os.environ.get("DIGITALOCEAN_API_TOKEN")"
    
    print("🚀 VOCALLOCAL COMPLETE DEPLOYMENT PIPELINE")
    print("=" * 60)
    print("This script will:")
    print("1. ✅ Push your local changes to GitHub")
    print("2. ✅ Trigger DigitalOcean deployment from GitHub")
    print("3. ✅ Test the results")
    print("")
    
    try:
        # Step 1: Push to GitHub
        if not push_to_github():
            print("❌ Failed to push to GitHub. Cannot proceed.")
            return False
        
        # Wait a moment for GitHub to process
        print("\n⏳ Waiting for GitHub to process changes...")
        time.sleep(5)
        
        # Step 2: Deploy from DigitalOcean
        print("\n🚀 DEPLOYING FROM DIGITALOCEAN")
        print("=" * 50)
        
        deployer = DigitalOceanDeployer(api_token)
        
        if not deployer.find_vocallocal_app():
            return False
        
        deployment_id = deployer.trigger_deployment()
        if not deployment_id:
            print("❌ Could not trigger deployment")
            return False
        
        deployment_success = deployer.wait_for_deployment(deployment_id)
        
        # Step 3: Test the results
        working_count, total_count = deployer.test_key_routes()
        
        print(f"\n📊 FINAL RESULTS:")
        print("=" * 50)
        print(f"✅ Working routes: {working_count}/{total_count}")
        
        if working_count >= 5:
            print("\n🎉 SUCCESS! VOCALLOCAL IS WORKING!")
            print(f"\n🔗 Your app: {deployer.app_url}")
            print("🎯 Key pages that should work:")
            print(f"   🏠 Home: {deployer.app_url}")
            print(f"   🔐 Login: {deployer.app_url}/login")
            print(f"   🎤 Transcribe: {deployer.app_url}/transcribe")
            print(f"   🌍 Translate: {deployer.app_url}/translate")
            return True
        else:
            print(f"\n⚠️  STILL HAVING ISSUES")
            print("Let's try a different approach...")
            return False
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False
    
    finally:
        input("\n👆 Press ENTER to close this window...")

if __name__ == "__main__":
    main()
