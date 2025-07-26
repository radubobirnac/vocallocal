#!/usr/bin/env python3
"""
Test script to verify the bilingual mode UI enhancements.
This script checks that:
1. TTS checkboxes have been removed from the HTML
2. Enhanced bilingual mode styling is present
3. JavaScript references to TTS checkboxes have been removed
"""

import os
import re

def test_tts_checkbox_removal():
    """Test that TTS checkboxes have been removed from index.html"""
    print("🔍 Testing TTS Checkbox Removal")
    print("=" * 40)
    
    index_path = "templates/index.html"
    if not os.path.exists(index_path):
        print(f"❌ File not found: {index_path}")
        return False
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that TTS checkboxes are removed
    tts_checkbox_patterns = [
        r'<input[^>]*id="enable-tts-1"[^>]*>',
        r'<input[^>]*id="enable-tts-2"[^>]*>',
        r'<label[^>]*for="enable-tts-1"[^>]*>.*?</label>',
        r'<label[^>]*for="enable-tts-2"[^>]*>.*?</label>',
        r'Read translations aloud'
    ]
    
    found_tts_elements = []
    for pattern in tts_checkbox_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        if matches:
            found_tts_elements.extend(matches)
    
    if found_tts_elements:
        print("❌ TTS checkbox elements still found:")
        for element in found_tts_elements:
            print(f"   - {element[:100]}...")
        return False
    else:
        print("✅ TTS checkboxes successfully removed from HTML")
        return True

def test_enhanced_bilingual_styling():
    """Test that enhanced bilingual mode styling is present"""
    print("\n🎨 Testing Enhanced Bilingual Mode Styling")
    print("=" * 40)
    
    css_path = "static/styles.css"
    if not os.path.exists(css_path):
        print(f"❌ File not found: {css_path}")
        return False
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for enhanced styling elements
    required_styles = [
        r'\.header-center\s*{[^}]*background:\s*linear-gradient',
        r'\.toggle-switch\s*{[^}]*width:\s*56px',
        r'\.toggle-switch\s*{[^}]*height:\s*32px',
        r'input:checked\s*\+\s*\.slider:after\s*{[^}]*content:\s*"✓"',
        r'\.bilingual-active',
        r'@keyframes\s+slideInUp'
    ]
    
    missing_styles = []
    for pattern in required_styles:
        if not re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            missing_styles.append(pattern)
    
    if missing_styles:
        print("❌ Missing enhanced styling elements:")
        for style in missing_styles:
            print(f"   - {style}")
        return False
    else:
        print("✅ Enhanced bilingual mode styling found")
        return True

def test_javascript_tts_removal():
    """Test that JavaScript TTS references have been removed"""
    print("\n🔧 Testing JavaScript TTS Reference Removal")
    print("=" * 40)
    
    js_files = [
        "static/script.js",
        "static/sync-tts.js"
    ]
    
    all_clean = True
    
    for js_file in js_files:
        if not os.path.exists(js_file):
            print(f"⚠️ File not found: {js_file}")
            continue
        
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for problematic TTS references
        problematic_patterns = [
            r'getElementById\([\'"]enable-tts-1[\'"]',
            r'getElementById\([\'"]enable-tts-2[\'"]',
            r'enableTTS\s*&&\s*enableTTS\.checked',
            r'\.enableTTS\s*&&\s*.*\.enableTTS\.checked'
        ]
        
        found_issues = []
        for pattern in problematic_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                found_issues.extend(matches)
        
        if found_issues:
            print(f"❌ TTS references still found in {js_file}:")
            for issue in found_issues:
                print(f"   - {issue}")
            all_clean = False
        else:
            print(f"✅ {js_file} - TTS references cleaned")
    
    return all_clean

def test_enhanced_javascript():
    """Test that enhanced JavaScript functionality is present"""
    print("\n⚡ Testing Enhanced JavaScript Functionality")
    print("=" * 40)
    
    index_path = "templates/index.html"
    if not os.path.exists(index_path):
        print(f"❌ File not found: {index_path}")
        return False
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for enhanced JavaScript features
    required_js_features = [
        r'bilingual-toggle-container',
        r'bilingual-mode-label',
        r'bilingual-active',
        r'showBilingualFeedback',
        r'Two-Way Conversation Tool',
        r'mouseenter.*mouseleave'
    ]
    
    missing_features = []
    for pattern in required_js_features:
        if not re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            missing_features.append(pattern)
    
    if missing_features:
        print("❌ Missing enhanced JavaScript features:")
        for feature in missing_features:
            print(f"   - {feature}")
        return False
    else:
        print("✅ Enhanced JavaScript functionality found")
        return True

def test_mobile_responsiveness():
    """Test that mobile responsive styles are present"""
    print("\n📱 Testing Mobile Responsiveness")
    print("=" * 40)
    
    css_path = "static/styles.css"
    if not os.path.exists(css_path):
        print(f"❌ File not found: {css_path}")
        return False
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for mobile responsive styles
    mobile_patterns = [
        r'@media\s*\([^)]*max-width:\s*480px[^)]*\)',
        r'\.toggle-switch\s*{[^}]*width:\s*44px',
        r'\.header-center\s*{[^}]*padding:\s*6px\s+12px'
    ]
    
    missing_mobile = []
    for pattern in mobile_patterns:
        if not re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            missing_mobile.append(pattern)
    
    if missing_mobile:
        print("❌ Missing mobile responsive styles:")
        for style in missing_mobile:
            print(f"   - {style}")
        return False
    else:
        print("✅ Mobile responsive styles found")
        return True

def main():
    """Run all tests for bilingual UI enhancements"""
    print("🧪 Bilingual Mode UI Enhancement Tests")
    print("=" * 60)
    
    tests = [
        ("TTS Checkbox Removal", test_tts_checkbox_removal),
        ("Enhanced Bilingual Styling", test_enhanced_bilingual_styling),
        ("JavaScript TTS Removal", test_javascript_tts_removal),
        ("Enhanced JavaScript", test_enhanced_javascript),
        ("Mobile Responsiveness", test_mobile_responsiveness)
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
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<8} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bilingual mode UI enhancements are working correctly.")
        print("\n📋 Changes Summary:")
        print("✅ TTS checkboxes removed from both speakers")
        print("✅ Enhanced bilingual mode toggle with better visibility")
        print("✅ Improved styling with gradients and animations")
        print("✅ JavaScript TTS references cleaned up")
        print("✅ Mobile responsive design maintained")
        print("✅ Enhanced user feedback and interactions")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
