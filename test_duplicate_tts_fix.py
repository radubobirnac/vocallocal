#!/usr/bin/env python3
"""
Test script to verify that the duplicate TTS issue has been fixed.
This script checks that:
1. Only one set of event listeners exists for bilingual mode TTS buttons
2. The bilingual-conversation.js no longer has duplicate TTS calls
3. The main script.js properly handles bilingual mode buttons
"""

import os
import re

def test_no_duplicate_event_listeners():
    """Test that bilingual-conversation.js no longer has duplicate TTS event listeners"""
    print("\n🔍 Testing for Duplicate Event Listeners Removal")
    print("=" * 60)
    
    bilingual_js_path = "static/js/bilingual-conversation.js"
    if not os.path.exists(bilingual_js_path):
        print(f"❌ File not found: {bilingual_js_path}")
        return False
    
    with open(bilingual_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that the duplicate event listeners have been removed
    duplicate_patterns = [
        r'playOriginalBtn\.addEventListener',
        r'playTranslationBtn\.addEventListener',
        r'window\.speakText\(.*bilingual-original-text',
        r'window\.speakText\(.*bilingual-translation-text'
    ]
    
    duplicates_found = []
    for pattern in duplicate_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            duplicates_found.append(pattern)
    
    if duplicates_found:
        print("❌ Found duplicate TTS event listeners:")
        for pattern in duplicates_found:
            print(f"   - {pattern}")
        return False
    else:
        print("✅ No duplicate TTS event listeners found in bilingual-conversation.js")
    
    # Check that the file now has a comment explaining the change
    if "TTS button functionality is now handled by the main script.js" in content:
        print("✅ Found explanatory comment about TTS handling")
    else:
        print("⚠️ No explanatory comment found")
    
    return True

def test_main_script_bilingual_support():
    """Test that main script.js properly supports bilingual mode TTS"""
    print("\n🎵 Testing Main Script Bilingual TTS Support")
    print("=" * 60)
    
    script_js_path = "static/script.js"
    if not os.path.exists(script_js_path):
        print(f"❌ File not found: {script_js_path}")
        return False
    
    with open(script_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for bilingual mode button event listeners in main script
    required_elements = [
        r'getElementById\([\'"]play-original[\'"]',
        r'getElementById\([\'"]stop-original[\'"]',
        r'getElementById\([\'"]play-translation[\'"]',
        r'getElementById\([\'"]stop-translation[\'"]',
        r'bilingual-original-text.*addEventListener',
        r'bilingual-translation-text.*addEventListener'
    ]
    
    found_elements = []
    for pattern in required_elements:
        if re.search(pattern, content, re.IGNORECASE):
            found_elements.append(pattern)
    
    print(f"✅ Found {len(found_elements)}/{len(required_elements)} required bilingual TTS elements")
    
    # Check for proper sourceId handling
    sourceId_patterns = [
        r'sourceId === [\'"]bilingual-original-text[\'"]',
        r'sourceId === [\'"]bilingual-translation-text[\'"]'
    ]
    
    sourceId_support = all(re.search(pattern, content) for pattern in sourceId_patterns)
    
    if sourceId_support:
        print("✅ Proper sourceId handling for bilingual mode found")
    else:
        print("❌ Missing sourceId handling for bilingual mode")
    
    return len(found_elements) >= 4 and sourceId_support

def test_single_tts_call_pattern():
    """Test that the code structure supports single TTS calls"""
    print("\n🔧 Testing Single TTS Call Pattern")
    print("=" * 60)
    
    script_js_path = "static/script.js"
    if not os.path.exists(script_js_path):
        print(f"❌ File not found: {script_js_path}")
        return False
    
    with open(script_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count how many times speakText is called for bilingual buttons
    bilingual_speaktext_calls = len(re.findall(r'speakText\([\'"]bilingual-[^\'\"]*[\'"]', content))
    
    print(f"✅ Found {bilingual_speaktext_calls} speakText calls for bilingual mode")
    
    # Check that there's proper event listener setup
    event_listener_count = len(re.findall(r'bilingual.*addEventListener\([\'"]click[\'"]', content, re.IGNORECASE))

    print(f"✅ Found {event_listener_count} click event listeners for bilingual buttons")

    # The ideal is 2 speakText calls (one for original, one for translation)
    # and 4 event listeners (2 play + 2 stop)
    return bilingual_speaktext_calls == 2 and event_listener_count >= 4

def test_no_conflicting_tts_systems():
    """Test that there are no conflicting TTS systems"""
    print("\n⚠️ Testing for Conflicting TTS Systems")
    print("=" * 60)
    
    # Check if sync-tts.js is disabled
    index_path = "templates/index.html"
    if not os.path.exists(index_path):
        print(f"❌ File not found: {index_path}")
        return False
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that sync-tts.js is commented out
    sync_tts_disabled = "<!-- <script src=" in content and "sync-tts.js" in content
    
    if sync_tts_disabled:
        print("✅ sync-tts.js is properly disabled (commented out)")
    else:
        print("⚠️ sync-tts.js status unclear - check if it's causing conflicts")
    
    # Check for direct-tts.js conflicts
    direct_tts_present = "direct-tts.js" in content
    
    if direct_tts_present:
        print("⚠️ direct-tts.js is present - ensure it doesn't conflict")
    else:
        print("✅ No direct-tts.js conflicts detected")
    
    return sync_tts_disabled

def main():
    """Run all tests for duplicate TTS fix verification"""
    print("🧪 Duplicate TTS Fix Verification Tests")
    print("=" * 70)
    
    tests = [
        ("Duplicate Event Listeners Removal", test_no_duplicate_event_listeners),
        ("Main Script Bilingual Support", test_main_script_bilingual_support),
        ("Single TTS Call Pattern", test_single_tts_call_pattern),
        ("No Conflicting TTS Systems", test_no_conflicting_tts_systems)
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
    print("📊 DUPLICATE TTS FIX VERIFICATION SUMMARY")
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
        print("🎉 All tests passed! Duplicate TTS issue should be fixed.")
        print("\n📋 Fix Summary:")
        print("✅ Removed duplicate event listeners from bilingual-conversation.js")
        print("✅ Added proper bilingual TTS support to main script.js")
        print("✅ Ensured single TTS call per button click")
        print("✅ Verified no conflicting TTS systems")
        print("\n🔧 Next Steps:")
        print("1. Test the bilingual mode in your browser")
        print("2. Click play buttons and verify only one voice plays")
        print("3. Check browser console for single TTS debug messages")
    else:
        print("⚠️ Some tests failed. The duplicate TTS issue may still exist.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
