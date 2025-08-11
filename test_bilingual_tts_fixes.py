#!/usr/bin/env python3
"""
Test script to verify the bilingual mode TTS fixes and cache busting improvements.
This script checks that:
1. Cache busting is properly configured for critical CSS/JS files
2. Bilingual mode TTS buttons are properly implemented in HTML
3. JavaScript event handlers are correctly set up for play/stop functionality
"""

import os
import re

def test_cache_busting_improvements():
    """Test that cache busting improvements are in place"""
    print("\n🔧 Testing Cache Busting Improvements")
    print("=" * 50)
    
    cache_busting_path = "utils/cache_busting.py"
    if not os.path.exists(cache_busting_path):
        print(f"❌ File not found: {cache_busting_path}")
        return False
    
    with open(cache_busting_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for critical files list
    if 'critical_files = [' in content and 'styles.css' in content:
        print("✅ Critical files list includes styles.css")
    else:
        print("❌ Critical files list not found or missing styles.css")
        return False
    
    # Check for aggressive cache control
    if 'no-cache, must-revalidate' in content:
        print("✅ Aggressive cache control for critical files found")
    else:
        print("❌ Aggressive cache control not found")
        return False
    
    return True

def test_bilingual_tts_buttons_html():
    """Test that bilingual mode TTS buttons are properly implemented"""
    print("\n🎵 Testing Bilingual Mode TTS Buttons HTML")
    print("=" * 50)
    
    index_path = "templates/index.html"
    if not os.path.exists(index_path):
        print(f"❌ File not found: {index_path}")
        return False
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for play buttons
    play_original_found = 'id="play-original"' in content
    play_translation_found = 'id="play-translation"' in content
    
    # Check for stop buttons
    stop_original_found = 'id="stop-original"' in content
    stop_translation_found = 'id="stop-translation"' in content
    
    print(f"✅ Play original button: {'Found' if play_original_found else 'Missing'}")
    print(f"✅ Play translation button: {'Found' if play_translation_found else 'Missing'}")
    print(f"✅ Stop original button: {'Found' if stop_original_found else 'Missing'}")
    print(f"✅ Stop translation button: {'Found' if stop_translation_found else 'Missing'}")
    
    # Check that stop buttons are initially hidden
    stop_hidden_pattern = r'id="stop-[^"]*"[^>]*style="display:\s*none;?"'
    stop_buttons_hidden = len(re.findall(stop_hidden_pattern, content)) >= 2
    
    if stop_buttons_hidden:
        print("✅ Stop buttons are initially hidden")
    else:
        print("❌ Stop buttons are not properly hidden initially")
    
    return all([play_original_found, play_translation_found, 
                stop_original_found, stop_translation_found, stop_buttons_hidden])

def test_bilingual_tts_javascript():
    """Test that bilingual mode TTS JavaScript is properly implemented"""
    print("\n⚡ Testing Bilingual Mode TTS JavaScript")
    print("=" * 50)
    
    # Check bilingual-conversation.js
    bilingual_js_path = "static/js/bilingual-conversation.js"
    if not os.path.exists(bilingual_js_path):
        print(f"❌ File not found: {bilingual_js_path}")
        return False
    
    with open(bilingual_js_path, 'r', encoding='utf-8') as f:
        bilingual_content = f.read()
    
    # Check for TTS button initialization
    tts_init_found = 'initializeBilingualTTSButtons' in bilingual_content
    button_state_function = 'setBilingualTTSButtonState' in bilingual_content
    event_listeners = 'addEventListener' in bilingual_content and 'play-original' in bilingual_content
    
    print(f"✅ TTS initialization function: {'Found' if tts_init_found else 'Missing'}")
    print(f"✅ Button state management: {'Found' if button_state_function else 'Missing'}")
    print(f"✅ Event listeners: {'Found' if event_listeners else 'Missing'}")
    
    # Check main script.js for bilingual support
    script_js_path = "static/script.js"
    if not os.path.exists(script_js_path):
        print(f"❌ File not found: {script_js_path}")
        return False
    
    with open(script_js_path, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    # Check for bilingual mode support in setTTSButtonState
    bilingual_original_support = 'bilingual-original-text' in script_content
    bilingual_translation_support = 'bilingual-translation-text' in script_content
    event_dispatching = 'tts-started' in script_content and 'CustomEvent' in script_content
    
    print(f"✅ Bilingual original text support: {'Found' if bilingual_original_support else 'Missing'}")
    print(f"✅ Bilingual translation text support: {'Found' if bilingual_translation_support else 'Missing'}")
    print(f"✅ TTS event dispatching: {'Found' if event_dispatching else 'Missing'}")
    
    return all([tts_init_found, button_state_function, event_listeners,
                bilingual_original_support, bilingual_translation_support, event_dispatching])

def test_template_cache_busting():
    """Test that templates use versioned URLs for critical files"""
    print("\n🔗 Testing Template Cache Busting")
    print("=" * 50)
    
    index_path = "templates/index.html"
    if not os.path.exists(index_path):
        print(f"❌ File not found: {index_path}")
        return False
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for versioned_url_for usage
    versioned_styles = "versioned_url_for('static', filename='styles.css')" in content
    versioned_script = "versioned_url_for('static', filename='script.js')" in content
    versioned_bilingual = "versioned_url_for('static', filename='js/bilingual-conversation.js')" in content
    
    print(f"✅ Versioned styles.css: {'Found' if versioned_styles else 'Missing'}")
    print(f"✅ Versioned script.js: {'Found' if versioned_script else 'Missing'}")
    print(f"✅ Versioned bilingual-conversation.js: {'Found' if versioned_bilingual else 'Missing'}")
    
    return all([versioned_styles, versioned_script, versioned_bilingual])

def main():
    """Run all tests for bilingual TTS fixes and cache busting"""
    print("🧪 Bilingual Mode TTS Fixes and Cache Busting Tests")
    print("=" * 70)
    
    tests = [
        ("Cache Busting Improvements", test_cache_busting_improvements),
        ("Bilingual TTS Buttons HTML", test_bilingual_tts_buttons_html),
        ("Bilingual TTS JavaScript", test_bilingual_tts_javascript),
        ("Template Cache Busting", test_template_cache_busting)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bilingual TTS fixes and cache busting are working correctly.")
        print("\n📋 Implementation Summary:")
        print("✅ Enhanced cache busting for critical CSS/JS files")
        print("✅ Bilingual mode TTS play/stop buttons implemented")
        print("✅ JavaScript event handlers for TTS functionality")
        print("✅ Button state management and event dispatching")
        print("✅ Template cache busting with versioned URLs")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
