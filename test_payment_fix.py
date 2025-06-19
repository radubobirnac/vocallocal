#!/usr/bin/env python3
"""
Test script to verify that the payment fetch binding fix is working correctly.
This script starts a local server and runs automated tests to check for the
"Illegal invocation" error in payment processing.
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

def test_fetch_binding_fix(driver):
    """Test the fetch binding fix using the debug page."""
    try:
        print("\n🧪 Testing fetch binding fix...")
        
        # Navigate to the debug page
        debug_url = 'http://127.0.0.1:5000/debug_payment_fetch.html'
        driver.get(debug_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        # Run all tests
        run_tests_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Run All Tests')]")
        run_tests_button.click()
        
        # Wait for tests to complete (up to 30 seconds)
        time.sleep(5)
        
        # Check for any "Illegal invocation" errors in the console
        logs = driver.get_log('browser')
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
        
        # Check test results on the page
        test_results = driver.find_elements(By.CLASS_NAME, 'test-result')
        
        success_count = 0
        error_count = 0
        
        for result in test_results:
            if 'success' in result.get_attribute('class'):
                success_count += 1
            elif 'error' in result.get_attribute('class'):
                error_count += 1
                print(f"❌ Test error: {result.text}")
        
        print(f"📊 Test results: {success_count} passed, {error_count} failed")
        
        return error_count == 0
        
    except TimeoutException:
        print("❌ Timeout waiting for debug page to load")
        return False
    except Exception as e:
        print(f"❌ Error during fetch binding test: {e}")
        return False

def test_payment_page_functionality(driver):
    """Test the actual payment functionality on the dashboard."""
    try:
        print("\n💳 Testing payment page functionality...")
        
        # Navigate to the dashboard
        dashboard_url = 'http://127.0.0.1:5000/dashboard'
        driver.get(dashboard_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        # Check if there are any JavaScript errors
        logs = driver.get_log('browser')
        js_errors = [
            log for log in logs 
            if log['level'] == 'SEVERE' and 'illegal invocation' in log['message'].lower()
        ]
        
        if js_errors:
            print("❌ Found JavaScript errors on dashboard:")
            for error in js_errors:
                print(f"   {error['message']}")
            return False
        else:
            print("✅ No JavaScript errors found on dashboard")
        
        # Look for upgrade buttons (they might not be visible if user is logged in)
        upgrade_buttons = driver.find_elements(By.CSS_SELECTOR, '[data-plan]')
        
        if upgrade_buttons:
            print(f"✅ Found {len(upgrade_buttons)} upgrade buttons")
            
            # Try clicking one (this should not cause illegal invocation errors)
            try:
                upgrade_buttons[0].click()
                time.sleep(2)  # Wait for any JavaScript to execute
                
                # Check for new errors after clicking
                new_logs = driver.get_log('browser')
                new_errors = [
                    log for log in new_logs 
                    if log['level'] == 'SEVERE' and 'illegal invocation' in log['message'].lower()
                ]
                
                if new_errors:
                    print("❌ Illegal invocation error occurred after clicking upgrade button")
                    return False
                else:
                    print("✅ No errors after clicking upgrade button")
                
            except Exception as e:
                print(f"⚠️ Could not click upgrade button (expected if not visible): {e}")
        else:
            print("ℹ️ No upgrade buttons found (user might be logged in)")
        
        return True
        
    except TimeoutException:
        print("❌ Timeout waiting for dashboard to load")
        return False
    except Exception as e:
        print(f"❌ Error during payment page test: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Starting Payment Fetch Binding Fix Test")
    print("=" * 50)
    
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
        test1_passed = test_fetch_binding_fix(driver)
        test2_passed = test_payment_page_functionality(driver)
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 TEST SUMMARY")
        print("=" * 50)
        
        if test1_passed and test2_passed:
            print("✅ ALL TESTS PASSED - Fetch binding fix is working correctly!")
            print("✅ Payment functionality should work without 'Illegal invocation' errors")
            return True
        else:
            print("❌ SOME TESTS FAILED - There may still be fetch binding issues")
            if not test1_passed:
                print("   - Fetch binding fix test failed")
            if not test2_passed:
                print("   - Payment page functionality test failed")
            return False
            
    finally:
        driver.quit()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
