#!/usr/bin/env python3
"""
Diagnose VocalLocal Server Issues
This script checks what's actually happening on the server
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

class VocalLocalDiagnostic:
    def __init__(self, app_url):
        self.app_url = app_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
    
    def check_flask_routes(self):
        """Try to access Flask's route listing if available"""
        print("🔍 CHECKING FLASK ROUTES")
        print("=" * 50)
        
        # Try common debug endpoints
        debug_endpoints = [
            '/debug-test',
            '/routes',
            '/api/routes',
            '/debug/routes',
            '/_debug',
            '/status'
        ]
        
        for endpoint in debug_endpoints:
            try:
                response = self.session.get(f"{self.app_url}{endpoint}")
                if response.status_code == 200:
                    print(f"✅ Found debug endpoint: {endpoint}")
                    if 'route' in response.text.lower() or 'endpoint' in response.text.lower():
                        print(f"   Content preview: {response.text[:200]}...")
                        return response.text
            except:
                pass
        
        print("❌ No debug endpoints found")
        return None
    
    def check_error_pages(self):
        """Check what error pages are showing"""
        print("\n🚨 CHECKING ERROR DETAILS")
        print("=" * 50)
        
        broken_routes = ['/login', '/health', '/transcribe', '/translate', '/pricing']
        
        for route in broken_routes:
            try:
                response = self.session.get(f"{self.app_url}{route}")
                print(f"\n🔍 Route: {route}")
                print(f"   Status: {response.status_code}")
                
                if response.text:
                    # Look for specific error patterns
                    content = response.text.lower()
                    
                    if 'importerror' in content:
                        print("   ❌ Import Error detected")
                    if 'modulenotfounderror' in content:
                        print("   ❌ Module Not Found Error detected")
                    if 'blueprint' in content:
                        print("   ⚠️  Blueprint-related content found")
                    if 'traceback' in content:
                        print("   🐛 Python traceback found")
                    if 'werkzeug' in content:
                        print("   🔧 Werkzeug error page")
                    
                    # Extract title if it's HTML
                    if '<title>' in content:
                        import re
                        title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
                        if title_match:
                            print(f"   Page title: {title_match.group(1)}")
                    
                    # Look for error messages in the first 500 characters
                    if len(response.text) > 100:
                        preview = response.text[:500]
                        if 'error' in preview.lower():
                            print(f"   Error preview: {preview}")
                            
            except Exception as e:
                print(f"   ❌ Request failed: {e}")
    
    def check_working_routes(self):
        """Analyze what's different about working routes"""
        print("\n✅ ANALYZING WORKING ROUTES")
        print("=" * 50)
        
        working_routes = ['/', '/try-it-free', '/auth/google']
        
        for route in working_routes:
            try:
                response = self.session.get(f"{self.app_url}{route}", allow_redirects=False)
                print(f"\n✅ Route: {route}")
                print(f"   Status: {response.status_code}")
                
                # Check if it's a redirect
                if response.status_code == 302:
                    location = response.headers.get('Location', 'No location')
                    print(f"   Redirects to: {location}")
                
                # Check response headers for clues
                server = response.headers.get('Server', 'Unknown')
                print(f"   Server: {server}")
                
                # Check if it's served by Flask
                if 'flask' in server.lower() or 'werkzeug' in server.lower():
                    print("   ✅ Served by Flask")
                elif 'gunicorn' in server.lower():
                    print("   ✅ Served by Gunicorn")
                
            except Exception as e:
                print(f"   ❌ Request failed: {e}")
    
    def check_app_logs(self):
        """Try to get application logs or error information"""
        print("\n📋 CHECKING FOR APPLICATION LOGS")
        print("=" * 50)
        
        # Try to trigger an error that might show logs
        try:
            # Make a request to a definitely non-existent route
            response = self.session.get(f"{self.app_url}/definitely-not-a-real-route-12345")
            
            if response.status_code == 404:
                content = response.text
                
                # Look for Flask debug information
                if 'werkzeug' in content.lower():
                    print("✅ Flask/Werkzeug is running")
                    
                    # Look for route information in debug output
                    if 'available methods' in content.lower():
                        print("   🔍 Route debug information available")
                    
                    # Look for import errors
                    if 'import' in content.lower() and 'error' in content.lower():
                        print("   ❌ Import errors detected in debug output")
                        
                        # Try to extract the error
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if 'import' in line.lower() and 'error' in line.lower():
                                print(f"   Error line: {line.strip()}")
                                # Print a few lines around it for context
                                for j in range(max(0, i-2), min(len(lines), i+3)):
                                    if j != i:
                                        print(f"   Context: {lines[j].strip()}")
                
        except Exception as e:
            print(f"❌ Could not check logs: {e}")
    
    def run_comprehensive_diagnosis(self):
        """Run all diagnostic tests"""
        print("🔍 VOCALLOCAL SERVER DIAGNOSIS")
        print("=" * 60)
        print(f"🎯 Target: {self.app_url}")
        
        # Test 1: Check for debug endpoints
        debug_info = self.check_flask_routes()
        
        # Test 2: Check error details
        self.check_error_pages()
        
        # Test 3: Analyze working routes
        self.check_working_routes()
        
        # Test 4: Check for logs
        self.check_app_logs()
        
        # Summary and recommendations
        print("\n💡 DIAGNOSIS SUMMARY")
        print("=" * 50)
        
        print("🔧 LIKELY ISSUES:")
        print("   1. Blueprint import errors - routes module not loading")
        print("   2. Missing template files - pricing.html, etc.")
        print("   3. Auth blueprint URL prefix issue not fully resolved")
        print("   4. Import errors in route modules")
        
        print("\n🎯 NEXT STEPS:")
        print("   1. Check if all route modules exist and import correctly")
        print("   2. Verify template files exist")
        print("   3. Check for Python import errors in logs")
        print("   4. Simplify app.py to isolate the issue")
        
        return True

def main():
    app_url = "https://vocallocal-l5et5.ondigitalocean.app"
    
    try:
        diagnostic = VocalLocalDiagnostic(app_url)
        diagnostic.run_comprehensive_diagnosis()
        
        print(f"\n🔗 Manual testing:")
        print(f"   Main app: {app_url}")
        print(f"   Debug test: {app_url}/debug-test")
        print(f"   Try accessing broken routes manually to see full error messages")
        
    except Exception as e:
        print(f"\n❌ DIAGNOSTIC ERROR: {e}")
        print("Please share this error message if you need help")
    
    # Keep window open
    input("\n👆 Press ENTER to close this window...")

if __name__ == "__main__":
    main()
