#!/usr/bin/env python3
"""
Test Script for User Dashboard and Usage Tracking System

This script tests the complete user flow including:
1. User registration and login
2. Dashboard access and usage display
3. Usage limit enforcement
4. Upgrade prompts
5. Monthly usage reset functionality
"""

import requests
import json
import time
from datetime import datetime

class VocalLocalTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_user_email = f"test_user_{int(time.time())}@example.com"
        self.test_user_password = "TestPassword123!"
        
    def log(self, message):
        """Log test messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_user_registration(self):
        """Test user registration process."""
        self.log("Testing user registration...")
        
        try:
            response = self.session.post(f"{self.base_url}/auth/register", data={
                'username': self.test_user_email.split('@')[0],
                'email': self.test_user_email,
                'password': self.test_user_password,
                'confirm_password': self.test_user_password
            })
            
            if response.status_code == 200 or "successfully" in response.text.lower():
                self.log("✅ User registration successful")
                return True
            else:
                self.log(f"❌ User registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ User registration error: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test user login process."""
        self.log("Testing user login...")
        
        try:
            response = self.session.post(f"{self.base_url}/auth/login", data={
                'email': self.test_user_email,
                'password': self.test_user_password
            })
            
            if response.status_code == 200 and "dashboard" in response.text.lower():
                self.log("✅ User login successful")
                return True
            else:
                self.log(f"❌ User login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ User login error: {str(e)}")
            return False
    
    def test_dashboard_access(self):
        """Test dashboard page access and data display."""
        self.log("Testing dashboard access...")
        
        try:
            response = self.session.get(f"{self.base_url}/dashboard")
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Check for key dashboard elements
                checks = [
                    ("dashboard title", "dashboard" in content),
                    ("usage statistics", "transcription" in content and "minutes" in content),
                    ("plan information", "plan" in content),
                    ("upgrade section", "upgrade" in content or "basic" in content),
                    ("navigation buttons", "history" in content and "profile" in content)
                ]
                
                all_passed = True
                for check_name, passed in checks:
                    if passed:
                        self.log(f"  ✅ {check_name} found")
                    else:
                        self.log(f"  ❌ {check_name} missing")
                        all_passed = False
                
                if all_passed:
                    self.log("✅ Dashboard access successful")
                    return True
                else:
                    self.log("❌ Dashboard missing required elements")
                    return False
            else:
                self.log(f"❌ Dashboard access failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Dashboard access error: {str(e)}")
            return False
    
    def test_usage_validation(self):
        """Test usage validation for transcription."""
        self.log("Testing usage validation...")
        
        try:
            # Test with a small audio file (should be allowed for free plan)
            test_data = {
                'service': 'transcription',
                'amount': 5.0  # 5 minutes
            }
            
            response = self.session.post(
                f"{self.base_url}/api/validate-usage",
                json=test_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('allowed'):
                    self.log("✅ Usage validation allows small request")
                else:
                    self.log("❌ Usage validation blocks small request")
                    return False
            else:
                self.log(f"❌ Usage validation failed: {response.status_code}")
                return False
            
            # Test with a large audio file (should be blocked for free plan)
            test_data = {
                'service': 'transcription',
                'amount': 100.0  # 100 minutes (exceeds free plan limit)
            }
            
            response = self.session.post(
                f"{self.base_url}/api/validate-usage",
                json=test_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if not result.get('allowed'):
                    self.log("✅ Usage validation blocks large request")
                    return True
                else:
                    self.log("❌ Usage validation allows large request (should block)")
                    return False
            else:
                self.log(f"❌ Usage validation failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Usage validation error: {str(e)}")
            return False
    
    def test_transcription_limit_enforcement(self):
        """Test transcription limit enforcement."""
        self.log("Testing transcription limit enforcement...")
        
        try:
            # Create a dummy audio file
            dummy_audio = b"dummy audio content" * 1000  # Simulate audio file
            
            files = {'file': ('test_audio.wav', dummy_audio, 'audio/wav')}
            data = {
                'language': 'en',
                'model': 'gemini-2.0-flash-lite'
            }
            
            response = self.session.post(
                f"{self.base_url}/api/transcribe",
                files=files,
                data=data
            )
            
            # For a new free user, this should either work or show usage limit
            if response.status_code == 200:
                self.log("✅ Transcription request processed")
                return True
            elif response.status_code == 429:  # Too Many Requests
                result = response.json()
                if result.get('errorType') == 'UsageLimitExceeded':
                    self.log("✅ Transcription limit enforcement working")
                    return True
                else:
                    self.log("❌ Unexpected 429 error")
                    return False
            else:
                self.log(f"❌ Transcription request failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Transcription limit test error: {str(e)}")
            return False
    
    def test_translation_limit_enforcement(self):
        """Test translation limit enforcement."""
        self.log("Testing translation limit enforcement...")
        
        try:
            # Test translation (should be blocked for free plan)
            test_data = {
                'text': 'Hello, this is a test translation.',
                'target_language': 'es',
                'translation_model': 'gemini-2.0-flash-lite'
            }
            
            response = self.session.post(
                f"{self.base_url}/api/translate",
                json=test_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 429:  # Too Many Requests
                result = response.json()
                if result.get('errorType') == 'UsageLimitExceeded':
                    self.log("✅ Translation limit enforcement working (blocked for free plan)")
                    return True
                else:
                    self.log("❌ Unexpected 429 error")
                    return False
            elif response.status_code == 200:
                self.log("❌ Translation allowed for free plan (should be blocked)")
                return False
            else:
                self.log(f"❌ Translation request failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Translation limit test error: {str(e)}")
            return False
    
    def test_upgrade_prompts(self):
        """Test upgrade prompt functionality."""
        self.log("Testing upgrade prompts...")
        
        try:
            # Access dashboard and check for upgrade prompts
            response = self.session.get(f"{self.base_url}/dashboard")
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Check for upgrade-related content
                upgrade_indicators = [
                    "upgrade" in content,
                    "basic" in content and "professional" in content,
                    "$4.99" in content or "$12.99" in content,
                    "plan" in content
                ]
                
                if any(upgrade_indicators):
                    self.log("✅ Upgrade prompts found on dashboard")
                    return True
                else:
                    self.log("❌ No upgrade prompts found")
                    return False
            else:
                self.log(f"❌ Dashboard access failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Upgrade prompt test error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        self.log("Starting VocalLocal User Dashboard and Usage Tracking Tests")
        self.log("=" * 60)
        
        tests = [
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Dashboard Access", self.test_dashboard_access),
            ("Usage Validation", self.test_usage_validation),
            ("Transcription Limit Enforcement", self.test_transcription_limit_enforcement),
            ("Translation Limit Enforcement", self.test_translation_limit_enforcement),
            ("Upgrade Prompts", self.test_upgrade_prompts)
        ]
        
        results = []
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                self.log(f"❌ {test_name} failed with exception: {str(e)}")
                results.append((test_name, False))
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("TEST SUMMARY")
        self.log("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status} - {test_name}")
            if result:
                passed += 1
        
        self.log(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All tests passed! User dashboard and usage tracking system is working correctly.")
        else:
            self.log("⚠️  Some tests failed. Please check the implementation.")
        
        return passed == total

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test VocalLocal User Dashboard and Usage Tracking")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL of the VocalLocal application")
    args = parser.parse_args()
    
    tester = VocalLocalTester(args.url)
    success = tester.run_all_tests()
    
    exit(0 if success else 1)
