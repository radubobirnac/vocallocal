#!/usr/bin/env python3
"""
Debug script to test conversation room bilingual mode functionality
"""

import requests
import json
import time
import re

def test_conversation_room_debug():
    """Debug the conversation room bilingual mode implementation"""
    
    base_url = "http://localhost:5001"
    
    print("🔧 Debugging Conversation Room Bilingual Mode")
    print("=" * 50)
    
    # Test 1: Check if conversation room template has required elements
    print("\n1. Testing conversation room template structure...")
    template_path = "templates/conversation/room.html"
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for critical elements that bilingual-conversation.js needs
        required_elements = {
            'bilingual-mode-content': 'Main bilingual mode container',
            'bilingual-hold-record-btn': 'Hold to record button',
            'bilingual-manual-record': 'Manual record button',
            'bilingual-translate-btn': 'Translate button',
            'bilingual-from-language': 'From language selector',
            'bilingual-to-language': 'To language selector',
            'bilingual-original-text': 'Original text area',
            'bilingual-translation-text': 'Translation text area',
            'global-transcription-model': 'Transcription model selector',
            'translation-model-select': 'Translation model selector',
            'bilingual-mode': 'Bilingual mode toggle (hidden)',
            'bilingual-conversation.js': 'Bilingual conversation script'
        }
        
        missing_elements = []
        for element_id, description in required_elements.items():
            if element_id not in content:
                missing_elements.append(f"{element_id} ({description})")
        
        if not missing_elements:
            print("✅ All required elements found in template")
        else:
            print(f"❌ Missing elements: {missing_elements}")
            
    except Exception as e:
        print(f"❌ Template check error: {e}")
    
    # Test 2: Check JavaScript dependencies
    print("\n2. Testing JavaScript dependencies...")
    js_dependencies = [
        'script.js',
        'js/bilingual-conversation.js',  # Correct path
        'common.js',
        'auth.js'
    ]
    
    for js_file in js_dependencies:
        try:
            response = requests.get(f"{base_url}/static/{js_file}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {js_file} - accessible")
                
                # Check for key functions in script.js
                if js_file == 'script.js':
                    content = response.text
                    key_functions = ['startRecording', 'showStatus', 'processAudioWithSmartRouting']
                    for func in key_functions:
                        if func in content:
                            print(f"  ✅ {func} function found")
                        else:
                            print(f"  ❌ {func} function missing")
                            
            else:
                print(f"❌ {js_file} - failed ({response.status_code})")
        except Exception as e:
            print(f"❌ {js_file} - error: {e}")
    
    # Test 3: Check CSS dependencies
    print("\n3. Testing CSS dependencies...")
    css_dependencies = [
        'styles.css',
        'css/mobile-icon-theme-fix.css'
    ]
    
    for css_file in css_dependencies:
        try:
            response = requests.get(f"{base_url}/static/{css_file}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {css_file} - accessible")
            else:
                print(f"❌ {css_file} - failed ({response.status_code})")
        except Exception as e:
            print(f"❌ {css_file} - error: {e}")
    
    # Test 4: Check for potential JavaScript initialization issues
    print("\n4. Analyzing JavaScript initialization order...")
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find script tags and DOMContentLoaded listeners
        script_tags = re.findall(r'<script[^>]*src="([^"]*)"[^>]*></script>', content)
        dom_listeners = re.findall(r'document\.addEventListener\([\'"]DOMContentLoaded[\'"]', content)
        
        print(f"Script tags found: {len(script_tags)}")
        print(f"DOMContentLoaded listeners: {len(dom_listeners)}")
        
        if len(dom_listeners) > 1:
            print("⚠️  Multiple DOMContentLoaded listeners detected - potential conflict")
        else:
            print("✅ DOMContentLoaded listeners look good")
            
    except Exception as e:
        print(f"❌ JavaScript analysis error: {e}")
    
    # Test 5: Check for missing global variables
    print("\n5. Testing global variable setup...")
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        global_vars = [
            'window.currentUserRole',
            'window.currentUserPlan', 
            'window.showStatus',
            'window.updateTranscript'
        ]
        
        missing_vars = []
        for var in global_vars:
            if var not in content:
                missing_vars.append(var)
        
        if not missing_vars:
            print("✅ All required global variables found")
        else:
            print(f"❌ Missing global variables: {missing_vars}")
            
    except Exception as e:
        print(f"❌ Global variables check error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Debug Summary:")
    print("- Check if all required HTML elements are present")
    print("- Verify JavaScript dependencies are loading")
    print("- Ensure global functions are available")
    print("- Check for initialization order conflicts")
    
    print("\n📋 Next Steps:")
    print("1. Fix any missing elements or dependencies")
    print("2. Test conversation room in browser")
    print("3. Check browser console for JavaScript errors")
    print("4. Test recording and translation functionality")
    
    return True

if __name__ == "__main__":
    test_conversation_room_debug()
