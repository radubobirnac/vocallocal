#!/usr/bin/env python3
"""
VocalLocal Debug Script
Comprehensive debugging to identify what's wrong
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

class VocalLocalDebugger:
    def __init__(self, app_url):
        self.app_url = app_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
    
    def test_endpoint(self, path, description):
        """Test a specific endpoint and return detailed results"""
        url = f"{self.app_url}{path}"
        print(f"\n🔍 Testing {description}")
        print(f"   URL: {url}")
        
        try:
            response = self.session.get(url, allow_redirects=False)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 302:
                location = response.headers.get('Location', 'No location header')
                print(f"   Redirect to: {location}")
            
            # Check for specific error messages
            if response.text:
                content = response.text.lower()
                
                # Firebase errors
                if 'firebase' in content and 'error' in content:
                    print("   ❌ Firebase error detected")
                    # Extract the error message
                    lines = response.text.split('\n')
                    for line in lines:
                        if 'firebase' in line.lower() and ('error' in line.lower() or 'could not' in line.lower()):
                            print(f"   Error: {line.strip()}")
                
                # OAuth errors
                if 'oauth' in content or 'redirect_uri' in content:
                    print("   ⚠️  OAuth-related content detected")
                
                # Check if it's an HTML error page
                if '<title>' in content:
                    import re
                    title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
                    if title_match:
                        print(f"   Page title: {title_match.group(1)}")
                
                # Check for 404 content
                if response.status_code == 404:
                    if 'not found' in content or '404' in content:
                        print("   ❌ Confirmed 404 - Page not found")
                    else:
                        print("   ⚠️  404 status but unusual content")
            
            return {
                'status_code': response.status_code,
                'success': response.status_code < 400,
                'has_firebase_error': 'firebase' in response.text.lower() and 'error' in response.text.lower(),
                'content_length': len(response.text),
                'headers': dict(response.headers)
            }
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
            return {
                'status_code': None,
                'success': False,
                'error': str(e)
            }
    
    def check_available_routes(self):
        """Try to discover what routes are actually available"""
        print("\n🗺️  CHECKING AVAILABLE ROUTES")
        print("=" * 50)
        
        # Common routes to test
        routes_to_test = [
            ('/', 'Home page'),
            ('/login', 'Login page'),
            ('/auth/google', 'Google OAuth'),
            ('/auth/callback', 'OAuth callback'),
            ('/auth/google/callback', 'Google OAuth callback'),
            ('/health', 'Health check'),
            ('/api/health', 'API health check'),
            ('/transcribe', 'Transcribe page'),
            ('/translate', 'Translate page'),
            ('/try-it-free', 'Try it free page'),
            ('/pricing', 'Pricing page'),
        ]
        
        results = {}
        for path, description in routes_to_test:
            results[path] = self.test_endpoint(path, description)
        
        return results
    
    def check_logs_and_errors(self):
        """Try to get more detailed error information"""
        print("\n📋 CHECKING FOR DETAILED ERRORS")
        print("=" * 50)
        
        # Test the main page and look for any JavaScript errors or console logs
        try:
            response = self.session.get(self.app_url)
            if response.status_code == 200:
                content = response.text
                
                # Look for JavaScript console errors
                if 'console.error' in content or 'console.log' in content:
                    print("   📝 JavaScript console messages found")
                
                # Look for Flask debug information
                if 'werkzeug' in content.lower() or 'traceback' in content.lower():
                    print("   🐛 Flask debug information detected")
                
                # Look for specific error patterns
                error_patterns = [
                    'Internal Server Error',
                    'Application Error',
                    'ModuleNotFoundError',
                    'ImportError',
                    'AttributeError',
                    'KeyError',
                    'ValueError'
                ]
                
                for pattern in error_patterns:
                    if pattern.lower() in content.lower():
                        print(f"   ❌ Found error pattern: {pattern}")
                
        except Exception as e:
            print(f"   ⚠️  Could not check for detailed errors: {e}")
    
    def test_firebase_specifically(self):
        """Test Firebase-specific functionality"""
        print("\n🔥 FIREBASE-SPECIFIC TESTS")
        print("=" * 50)
        
        # Test if we can access any Firebase-dependent pages
        firebase_dependent_routes = [
            '/login',
            '/register', 
            '/dashboard',
            '/profile',
            '/history'
        ]
        
        firebase_working = True
        for route in firebase_dependent_routes:
            result = self.test_endpoint(route, f"Firebase-dependent route: {route}")
            if result.get('has_firebase_error', False):
                firebase_working = False
                print(f"   ❌ Firebase error on {route}")
        
        return firebase_working
    
    def run_comprehensive_debug(self):
        """Run all debugging tests"""
        print("🔍 VOCALLOCAL COMPREHENSIVE DEBUG")
        print("=" * 60)
        print(f"🎯 Target: {self.app_url}")
        
        # Test 1: Check available routes
        route_results = self.check_available_routes()
        
        # Test 2: Check for detailed errors
        self.check_logs_and_errors()
        
        # Test 3: Test Firebase specifically
        firebase_working = self.test_firebase_specifically()
        
        # Summary
        print("\n📊 DEBUG SUMMARY")
        print("=" * 50)
        
        working_routes = [path for path, result in route_results.items() if result.get('success', False)]
        broken_routes = [path for path, result in route_results.items() if not result.get('success', False)]
        
        print(f"✅ Working routes ({len(working_routes)}):")
        for route in working_routes:
            print(f"   {route}")
        
        print(f"\n❌ Broken routes ({len(broken_routes)}):")
        for route in broken_routes:
            status = route_results[route].get('status_code', 'ERROR')
            print(f"   {route} (Status: {status})")
        
        if firebase_working:
            print("\n✅ Firebase appears to be working")
        else:
            print("\n❌ Firebase has issues")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS")
        print("=" * 50)
        
        if '/login' in broken_routes:
            print("🔧 Login route is broken - this suggests:")
            print("   - Authentication blueprint not registered properly")
            print("   - Route definition issues")
            print("   - Import errors in auth module")
        
        if len(working_routes) == 0:
            print("🔧 No routes working - this suggests:")
            print("   - App failed to start properly")
            print("   - Major configuration issue")
            print("   - Import errors preventing app initialization")
        
        if '/' in working_routes and '/login' in broken_routes:
            print("🔧 Main app works but auth doesn't - this suggests:")
            print("   - Authentication module has specific issues")
            print("   - Blueprint registration problem")
            print("   - OAuth configuration issue")
        
        return route_results

def main():
    app_url = "https://vocallocal-l5et5.ondigitalocean.app"
    
    try:
        debugger = VocalLocalDebugger(app_url)
        results = debugger.run_comprehensive_debug()
        
        print(f"\n🔗 Manual testing URLs:")
        print(f"   Main app: {app_url}")
        print(f"   Try each route manually to see detailed error messages")
        
    except Exception as e:
        print(f"\n❌ DEBUG SCRIPT ERROR: {e}")
        print("Please share this error message if you need help")
    
    # Keep window open
    input("\n👆 Press ENTER to close this window...")

if __name__ == "__main__":
    main()
