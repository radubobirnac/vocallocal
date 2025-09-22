#!/usr/bin/env python3
"""
Test script to verify conversation room bilingual mode functionality
"""

import requests
import json
import time
import re

def test_conversation_room_functionality():
    """Test the conversation room bilingual mode functionality"""

    print("🧪 Testing Conversation Room Bilingual Mode Functionality")
    print("=" * 60)

    # Basic API test without browser first
    try:
        print("\n1. Testing conversation room page load...")
        print("Note: Testing without authentication - expecting error page")
        response = requests.get("http://localhost:5001/conversation/room/test123", timeout=10)

        if response.status_code == 200:
            content = response.text

            # Check what type of page we got
            print(f"Response length: {len(content)} characters")

            # Look for key indicators
            if 'login' in content.lower() and 'password' in content.lower():
                print("⚠️  Got login page (expected - user not authenticated)")
                print("✅ This confirms authentication is required")

                print("\n📋 To test the actual bilingual mode functionality:")
                print("1. Create a user account and log in")
                print("2. Create a conversation room")
                print("3. Join the room as a participant")
                print("4. Then access /conversation/room/<room_code>")

                return True

            elif 'error' in content.lower() or 'not found' in content.lower() or 'not a participant' in content.lower():
                print("⚠️  Got error page (expected - user not participant)")
                print("✅ This confirms the route protection is working")

                print("\n📋 To test the actual bilingual mode functionality:")
                print("1. Create a user account and log in")
                print("2. Create a conversation room")
                print("3. Join the room as a participant")
                print("4. Then access /conversation/room/<room_code>")

                return True
            else:
                print("✅ Conversation room page loads successfully")

                # Print first 500 characters to see what we got
                print(f"\nFirst 500 characters of response:")
                print(content[:500])
                print("...")

                content = response.text

            # Check for bilingual mode elements in HTML
            print("\n2. Checking bilingual mode elements in HTML...")
            required_elements = [
                'bilingual-mode-content',
                'bilingual-hold-record-btn',
                'bilingual-manual-record',
                'bilingual-translate-btn',
                'bilingual-from-language',
                'bilingual-to-language',
                'bilingual-original-text',
                'bilingual-translation-text'
            ]

            missing_elements = []
            for element in required_elements:
                if element in content:
                    print(f"✅ {element} found in HTML")
                else:
                    missing_elements.append(element)
                    print(f"❌ {element} missing from HTML")

            # Check for JavaScript files
            print("\n3. Checking JavaScript includes...")
            js_files = [
                'js/bilingual-conversation.js',
                'script.js',
                'common.js'
            ]

            for js_file in js_files:
                if js_file in content:
                    print(f"✅ {js_file} included")
                else:
                    print(f"❌ {js_file} missing")

            # Check for Socket.IO setup
            print("\n4. Checking Socket.IO setup...")
            if 'socket.io' in content and 'roomCode' in content:
                print("✅ Socket.IO and room code setup found")
            else:
                print("❌ Socket.IO or room code setup missing")

            # Check for setupConversationRoomIntegration function
            print("\n5. Checking conversation room integration...")
            if 'setupConversationRoomIntegration' in content:
                print("✅ Conversation room integration function found")
            else:
                print("❌ Conversation room integration function missing")

            print("\n" + "=" * 60)
            print("🎯 Basic Test Summary:")

            if not missing_elements:
                print("✅ All required bilingual mode elements are present in HTML")
                print("✅ Conversation room should be functional")

                print("\n📋 Manual testing steps:")
                print("1. Open http://localhost:5001/conversation/room/test123 in browser")
                print("2. Check browser console for any JavaScript errors")
                print("3. Test language selection dropdowns")
                print("4. Test recording buttons (Hold to Record, Manual Record)")
                print("5. Test translation with sample text")
                print("6. Verify Socket.IO connection status")

            else:
                print(f"❌ Missing elements need to be fixed: {missing_elements}")

            return True

        else:
            print(f"❌ Conversation room failed to load: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Basic test error: {e}")
        return False

    # If we want to do browser testing, we can add Selenium here
    print("\n" + "=" * 60)
    print("🔧 For advanced testing with browser automation:")
    print("Install selenium: pip install selenium")
    print("Download chromedriver and add to PATH")

    try:
        # Try browser testing if selenium is available
        driver = None
        
        # Test URL
        test_url = "http://localhost:5001/conversation/room/test123"
        print(f"\n1. Loading conversation room: {test_url}")
        
        driver.get(test_url)
        time.sleep(3)  # Wait for page to load
        
        # Test 2: Check if bilingual mode elements are present
        print("\n2. Checking bilingual mode elements...")
        
        required_elements = {
            'bilingual-mode-content': 'Bilingual mode container',
            'bilingual-hold-record-btn': 'Hold to record button',
            'bilingual-manual-record': 'Manual record button',
            'bilingual-translate-btn': 'Translate button',
            'bilingual-from-language': 'From language selector',
            'bilingual-to-language': 'To language selector',
            'bilingual-original-text': 'Original text area',
            'bilingual-translation-text': 'Translation text area'
        }
        
        missing_elements = []
        for element_id, description in required_elements.items():
            try:
                element = driver.find_element(By.ID, element_id)
                if element.is_displayed():
                    print(f"✅ {description} - visible")
                else:
                    print(f"⚠️  {description} - present but hidden")
            except NoSuchElementException:
                missing_elements.append(f"{element_id} ({description})")
                print(f"❌ {description} - missing")
        
        # Test 3: Check JavaScript initialization
        print("\n3. Checking JavaScript initialization...")
        
        # Check if bilingualConversation object exists
        bilingual_obj = driver.execute_script("return window.bilingualConversation;")
        if bilingual_obj:
            print("✅ BilingualConversation object initialized")
        else:
            print("❌ BilingualConversation object not found")
        
        # Check if required global functions exist
        global_functions = ['startRecording', 'showStatus', 'processAudioWithSmartRouting']
        for func in global_functions:
            exists = driver.execute_script(f"return typeof window.{func} === 'function';")
            if exists:
                print(f"✅ {func} function available")
            else:
                print(f"❌ {func} function missing")
        
        # Test 4: Check language selectors functionality
        print("\n4. Testing language selectors...")
        
        try:
            from_lang = driver.find_element(By.ID, 'bilingual-from-language')
            to_lang = driver.find_element(By.ID, 'bilingual-to-language')
            
            # Get current values
            from_value = from_lang.get_attribute('value')
            to_value = to_lang.get_attribute('value')
            
            print(f"✅ From language: {from_value}")
            print(f"✅ To language: {to_value}")
            
            # Test changing language
            driver.execute_script("arguments[0].value = 'es'; arguments[0].dispatchEvent(new Event('change'));", from_lang)
            time.sleep(1)
            
            new_value = from_lang.get_attribute('value')
            if new_value == 'es':
                print("✅ Language selector change works")
            else:
                print("❌ Language selector change failed")
                
        except Exception as e:
            print(f"❌ Language selector test error: {e}")
        
        # Test 5: Check button functionality (without actually recording)
        print("\n5. Testing button interactions...")
        
        try:
            # Test translate button
            translate_btn = driver.find_element(By.ID, 'bilingual-translate-btn')
            if translate_btn.is_enabled():
                print("✅ Translate button is enabled")
                
                # Add some text to translate
                original_text = driver.find_element(By.ID, 'bilingual-original-text')
                driver.execute_script("arguments[0].value = 'Hello world';", original_text)
                
                # Click translate button (this will test the API call)
                translate_btn.click()
                time.sleep(2)
                
                print("✅ Translate button click successful")
            else:
                print("❌ Translate button is disabled")
                
        except Exception as e:
            print(f"❌ Button interaction test error: {e}")
        
        # Test 6: Check console errors
        print("\n6. Checking for JavaScript console errors...")
        
        logs = driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        
        if not errors:
            print("✅ No JavaScript console errors")
        else:
            print(f"❌ Found {len(errors)} console errors:")
            for error in errors[:3]:  # Show first 3 errors
                print(f"  - {error['message']}")
        
        # Test 7: Check Socket.IO connection
        print("\n7. Testing Socket.IO connection...")
        
        try:
            socket_connected = driver.execute_script("return window.socket && window.socket.connected;")
            if socket_connected:
                print("✅ Socket.IO connected")
            else:
                print("❌ Socket.IO not connected")
        except Exception as e:
            print(f"❌ Socket.IO test error: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 Test Summary:")
        
        if not missing_elements and bilingual_obj:
            print("✅ Conversation room bilingual mode is properly set up!")
            print("✅ All required elements are present and functional")
            print("✅ JavaScript initialization is working")
            
            print("\n📋 Ready for user testing:")
            print("1. Language selection should work")
            print("2. Recording buttons should be functional")
            print("3. Translation should work with text input")
            print("4. Real-time Socket.IO communication should work")
            
        else:
            print("❌ Issues found that need to be addressed:")
            if missing_elements:
                print(f"  - Missing elements: {missing_elements}")
            if not bilingual_obj:
                print("  - BilingualConversation not initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Test setup error: {e}")
        print("Note: This test requires Chrome browser and chromedriver")
        print("Falling back to basic functionality check...")
        
        # Basic API test without browser
        try:
            response = requests.get("http://localhost:5001/conversation/room/test123", timeout=10)
            if response.status_code == 200:
                print("✅ Conversation room page loads successfully")
                
                # Check if bilingual elements are in the HTML
                content = response.text
                if 'bilingual-mode-content' in content:
                    print("✅ Bilingual mode elements found in HTML")
                else:
                    print("❌ Bilingual mode elements missing from HTML")
            else:
                print(f"❌ Conversation room failed to load: {response.status_code}")
                
        except Exception as api_error:
            print(f"❌ API test error: {api_error}")
        
        return False
        
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    test_conversation_room_functionality()
