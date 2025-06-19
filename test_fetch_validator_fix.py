#!/usr/bin/env python3
"""
Test script to verify that the fetch validator TypeError fix is working correctly.
This script checks for the specific "Cannot read properties of undefined" error.
"""

import os
import sys
import time
import subprocess
import threading
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

def start_flask_server():
    """Start the Flask development server in a separate thread."""
    def run_server():
        try:
            # Change to the vocallocal directory
            os.chdir('vocallocal')
            
            # Start the Flask server
            subprocess.run([
                sys.executable, '-m', 'flask', 'run', 
                '--host=127.0.0.1', '--port=5000', '--debug'
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error starting Flask server: {e}")
        except Exception as e:
            print(f"Unexpected error starting server: {e}")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    print("Starting Flask server...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get('http://127.0.0.1:5000/', timeout=5)
            if response.status_code in [200, 302, 404]:  # Any valid HTTP response
                print("✅ Flask server is running")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        print(f"Waiting for server... ({i+1}/30)")
    
    print("❌ Failed to start Flask server")
    return False

def setup_webdriver():
    """Set up Chrome WebDriver with appropriate options."""
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Enable logging to capture JavaScript errors
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--log-level=0')
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except WebDriverException as e:
        print(f"❌ Failed to setup WebDriver: {e}")
        print("Make sure Chrome and ChromeDriver are installed")
        return None

def test_fetch_validator_fix(driver):
    """Test the fetch validator TypeError fix."""
    try:
        print("\n🔧 Testing Fetch Validator TypeError Fix...")
        
        # Navigate to the manual test page
        test_url = 'http://127.0.0.1:5000/manual_payment_test.html'
        driver.get(test_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        print("✅ Test page loaded successfully")
        
        # Test fetch validator functionality
        try:
            test_validator_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Test Fetch Validator')]")
            test_validator_button.click()
            time.sleep(2)
            print("✅ Fetch validator test button clicked")
        except Exception as e:
            print(f"⚠️ Could not click fetch validator test button: {e}")
        
        # Test upgrade button simulation
        try:
            simulate_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Simulate Upgrade Click')]")
            simulate_button.click()
            time.sleep(2)
            print("✅ Upgrade simulation button clicked")
        except Exception as e:
            print(f"⚠️ Could not click upgrade simulation button: {e}")
        
        # Test actual upgrade buttons
        try:
            upgrade_buttons = driver.find_elements(By.CSS_SELECTOR, '.upgrade-button')
            if upgrade_buttons:
                upgrade_buttons[0].click()
                time.sleep(2)
                print("✅ Upgrade button clicked")
            else:
                print("ℹ️ No upgrade buttons found")
        except Exception as e:
            print(f"⚠️ Could not click upgrade button: {e}")
        
        # Check for the specific TypeError we're trying to fix
        logs = driver.get_log('browser')
        
        # Look for the specific error we fixed
        target_errors = [
            'Cannot read properties of undefined (reading \'call\')',
            'TypeError: Cannot read properties of undefined',
            'fetch-fix-validator.js:73'
        ]
        
        found_target_error = False
        other_errors = []
        
        for log in logs:
            if log['level'] == 'SEVERE':
                message = log['message']
                if any(error in message for error in target_errors):
                    found_target_error = True
                    print(f"❌ Found target error: {message}")
                else:
                    other_errors.append(message)
        
        if found_target_error:
            print("❌ FETCH VALIDATOR TYPEERROR STILL PRESENT")
            return False
        else:
            print("✅ No fetch validator TypeError found")
        
        # Check for any illegal invocation errors (original issue)
        illegal_invocation_errors = [
            log for log in logs 
            if 'illegal invocation' in log['message'].lower() or 
               'failed to execute' in log['message'].lower()
        ]
        
        if illegal_invocation_errors:
            print("❌ Found illegal invocation errors:")
            for error in illegal_invocation_errors:
                print(f"   {error['message']}")
            return False
        else:
            print("✅ No illegal invocation errors found")
        
        # Report other errors for awareness
        if other_errors:
            print("ℹ️ Other JavaScript errors found (may be unrelated):")
            for error in other_errors[:3]:  # Show first 3 only
                print(f"   {error}")
        
        return True
        
    except TimeoutException:
        print("❌ Timeout waiting for test page to load")
        return False
    except Exception as e:
        print(f"❌ Error during fetch validator test: {e}")
        return False

def test_dashboard_functionality(driver):
    """Test the actual dashboard payment functionality."""
    try:
        print("\n💳 Testing Dashboard Payment Functionality...")
        
        # Navigate to the dashboard
        dashboard_url = 'http://127.0.0.1:5000/dashboard'
        driver.get(dashboard_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        print("✅ Dashboard loaded successfully")
        
        # Check for JavaScript errors on page load
        logs = driver.get_log('browser')
        severe_errors = [log for log in logs if log['level'] == 'SEVERE']
        
        target_error_found = False
        for error in severe_errors:
            if 'Cannot read properties of undefined (reading \'call\')' in error['message']:
                target_error_found = True
                print(f"❌ Found target error on dashboard: {error['message']}")
        
        if target_error_found:
            return False
        else:
            print("✅ No target TypeError found on dashboard")
        
        # Look for upgrade buttons and try to interact with them
        upgrade_buttons = driver.find_elements(By.CSS_SELECTOR, '[data-plan]')
        
        if upgrade_buttons:
            print(f"✅ Found {len(upgrade_buttons)} upgrade buttons")
            
            # Try clicking one
            try:
                upgrade_buttons[0].click()
                time.sleep(3)  # Wait for any JavaScript to execute
                
                # Check for new errors after clicking
                new_logs = driver.get_log('browser')
                new_severe_errors = [log for log in new_logs if log['level'] == 'SEVERE']
                
                new_target_errors = [
                    error for error in new_severe_errors 
                    if 'Cannot read properties of undefined (reading \'call\')' in error['message']
                ]
                
                if new_target_errors:
                    print("❌ Target TypeError occurred after clicking upgrade button")
                    for error in new_target_errors:
                        print(f"   {error['message']}")
                    return False
                else:
                    print("✅ No target TypeError after clicking upgrade button")
                
            except Exception as e:
                print(f"⚠️ Could not click upgrade button: {e}")
        else:
            print("ℹ️ No upgrade buttons found (user might be logged in)")
        
        return True
        
    except TimeoutException:
        print("❌ Timeout waiting for dashboard to load")
        return False
    except Exception as e:
        print(f"❌ Error during dashboard test: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Starting Fetch Validator TypeError Fix Test")
    print("=" * 60)
    
    # Start Flask server
    if not start_flask_server():
        print("❌ Cannot proceed without Flask server")
        return False
    
    # Setup WebDriver
    driver = setup_webdriver()
    if not driver:
        print("❌ Cannot proceed without WebDriver")
        return False
    
    try:
        # Run tests
        test1_passed = test_fetch_validator_fix(driver)
        test2_passed = test_dashboard_functionality(driver)
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        if test1_passed and test2_passed:
            print("✅ ALL TESTS PASSED - Fetch validator TypeError fix is working!")
            print("✅ Payment functionality should work without TypeError errors")
            return True
        else:
            print("❌ SOME TESTS FAILED - TypeError may still be present")
            if not test1_passed:
                print("   - Fetch validator fix test failed")
            if not test2_passed:
                print("   - Dashboard functionality test failed")
            return False
            
    finally:
        driver.quit()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
