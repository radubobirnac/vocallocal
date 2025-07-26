#!/usr/bin/env python3
"""
Test script to verify that the toggle switch has been reverted to original state
while keeping TTS checkbox removal and other bilingual mode improvements.
"""

import os
import re

def test_toggle_switch_reverted():
    """Test that toggle switch is back to original dimensions and styling"""
    print("🔄 Testing Toggle Switch Revert")
    print("=" * 40)
    
    css_path = "static/styles.css"
    if not os.path.exists(css_path):
        print(f"❌ File not found: {css_path}")
        return False
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for original toggle switch dimensions
    original_patterns = [
        r'\.toggle-switch\s*{[^}]*width:\s*50px',
        r'\.toggle-switch\s*{[^}]*height:\s*28px',
        r'\.slider:before\s*{[^}]*height:\s*20px',
        r'\.slider:before\s*{[^}]*width:\s*20px',
        r'input:checked\s*\+\s*\.slider:before\s*{[^}]*transform:\s*translateX\(22px\)',
        r'\.slider\.round\s*{[^}]*border-radius:\s*28px'
    ]
    
    missing_original = []
    for pattern in original_patterns:
        if not re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            missing_original.append(pattern)
    
    # Check that enhanced features are removed
    enhanced_patterns = [
        r'width:\s*56px',
        r'height:\s*32px',
        r'margin-left:\s*8px',
        r'linear-gradient.*slider',
        r'content:\s*"✓"',
        r'border:\s*2px\s+solid\s+transparent'
    ]
    
    found_enhanced = []
    for pattern in enhanced_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            found_enhanced.extend(matches)
    
    if missing_original:
        print("❌ Missing original toggle switch properties:")
        for prop in missing_original:
            print(f"   - {prop}")
        return False
    
    if found_enhanced:
        print("❌ Enhanced toggle switch properties still found:")
        for prop in found_enhanced:
            print(f"   - {prop}")
        return False
    
    print("✅ Toggle switch successfully reverted to original styling")
    return True

def test_header_center_reverted():
    """Test that header-center container is back to original simple styling"""
    print("\n🏠 Testing Header Center Revert")
    print("=" * 40)
    
    css_path = "static/styles.css"
    if not os.path.exists(css_path):
        print(f"❌ File not found: {css_path}")
        return False
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that enhanced header-center styles are removed
    enhanced_header_patterns = [
        r'\.header-center\s*{[^}]*background:\s*linear-gradient',
        r'\.header-center\s*{[^}]*padding:\s*8px\s+16px',
        r'\.header-center\s*{[^}]*border-radius:\s*12px',
        r'\.header-center\s*{[^}]*border:\s*1px\s+solid',
        r'\.header-center:hover',
        r'\.bilingual-active'
    ]
    
    found_enhanced_header = []
    for pattern in enhanced_header_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        if matches:
            found_enhanced_header.extend(matches)
    
    if found_enhanced_header:
        print("❌ Enhanced header-center properties still found:")
        for prop in found_enhanced_header:
            print(f"   - {prop[:50]}...")
        return False
    
    print("✅ Header center successfully reverted to original styling")
    return True

def test_html_template_reverted():
    """Test that HTML template is back to original structure"""
    print("\n📄 Testing HTML Template Revert")
    print("=" * 40)
    
    index_path = "templates/index.html"
    if not os.path.exists(index_path):
        print(f"❌ File not found: {index_path}")
        return False
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that enhanced IDs and classes are removed
    enhanced_html_patterns = [
        r'id="bilingual-toggle-container"',
        r'id="bilingual-mode-label"',
        r'Enhanced Bilingual Mode Toggle',
        r'showBilingualFeedback',
        r'bilingual-active',
        r'mouseenter.*mouseleave'
    ]
    
    found_enhanced_html = []
    for pattern in enhanced_html_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        if matches:
            found_enhanced_html.extend(matches)
    
    if found_enhanced_html:
        print("❌ Enhanced HTML elements still found:")
        for element in found_enhanced_html:
            print(f"   - {element}")
        return False
    
    # Check that original structure is preserved
    original_patterns = [
        r'<span[^>]*class="[^"]*bilingual-mode-label[^"]*">Bilingual Mode</span>',
        r'title="Toggle bilingual mode"'
    ]
    
    missing_original_html = []
    for pattern in original_patterns:
        if not re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            missing_original_html.append(pattern)
    
    if missing_original_html:
        print("❌ Missing original HTML structure:")
        for element in missing_original_html:
            print(f"   - {element}")
        return False
    
    print("✅ HTML template successfully reverted to original structure")
    return True

def test_tts_removal_preserved():
    """Test that TTS checkbox removal is still in place"""
    print("\n🗑️ Testing TTS Removal Preserved")
    print("=" * 40)
    
    index_path = "templates/index.html"
    if not os.path.exists(index_path):
        print(f"❌ File not found: {index_path}")
        return False
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that TTS checkboxes are still removed
    tts_patterns = [
        r'id="enable-tts-1"',
        r'id="enable-tts-2"',
        r'Read translations aloud'
    ]
    
    found_tts = []
    for pattern in tts_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            found_tts.extend(matches)
    
    if found_tts:
        print("❌ TTS checkboxes found - removal was not preserved:")
        for tts in found_tts:
            print(f"   - {tts}")
        return False
    
    print("✅ TTS checkbox removal successfully preserved")
    return True

def test_bilingual_content_improvements_preserved():
    """Test that bilingual content area improvements are preserved"""
    print("\n🎨 Testing Bilingual Content Improvements Preserved")
    print("=" * 40)
    
    css_path = "static/styles.css"
    if not os.path.exists(css_path):
        print(f"❌ File not found: {css_path}")
        return False
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that bilingual content improvements are preserved
    content_patterns = [
        r'\.speaker-card-1\s*\.card-header\s*{[^}]*background:\s*linear-gradient',
        r'\.speaker-card-2\s*\.card-header\s*{[^}]*background:\s*linear-gradient',
        r'#bilingual-mode-content\s*{[^}]*transition',
        r'@keyframes\s+slideInUp'
    ]
    
    missing_content = []
    for pattern in content_patterns:
        if not re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            missing_content.append(pattern)
    
    if missing_content:
        print("❌ Missing bilingual content improvements:")
        for improvement in missing_content:
            print(f"   - {improvement}")
        return False
    
    print("✅ Bilingual content improvements successfully preserved")
    return True

def main():
    """Run all revert verification tests"""
    print("🧪 Toggle Switch Revert Verification Tests")
    print("=" * 60)
    
    tests = [
        ("Toggle Switch Reverted", test_toggle_switch_reverted),
        ("Header Center Reverted", test_header_center_reverted),
        ("HTML Template Reverted", test_html_template_reverted),
        ("TTS Removal Preserved", test_tts_removal_preserved),
        ("Bilingual Content Improvements Preserved", test_bilingual_content_improvements_preserved)
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
        print("🎉 All tests passed! Toggle switch successfully reverted while preserving other improvements.")
        print("\n📋 Revert Summary:")
        print("✅ Toggle switch back to original 50x28px dimensions")
        print("✅ Original toggle switch styling and colors restored")
        print("✅ Header container back to simple styling")
        print("✅ Enhanced JavaScript functionality removed")
        print("✅ TTS checkbox removal preserved")
        print("✅ Bilingual content area improvements preserved")
    else:
        print("⚠️ Some tests failed. Please check the revert implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
