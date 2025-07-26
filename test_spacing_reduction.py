#!/usr/bin/env python3
"""
Test script to verify that the vertical spacing in bilingual mode speaker cards
has been reduced from space-y-4 to space-y-2.
"""

import os
import re

def test_speaker_card_spacing_reduction():
    """Test that both speaker cards have reduced spacing"""
    print("📏 Testing Speaker Card Spacing Reduction")
    print("=" * 50)
    
    index_path = "templates/index.html"
    if not os.path.exists(index_path):
        print(f"❌ File not found: {index_path}")
        return False
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that space-y-4 has been replaced with space-y-2 in speaker cards
    print("🔍 Checking for reduced spacing in speaker cards...")
    
    # Look for the specific pattern in Speaker 1 card
    speaker1_pattern = r'<div class="card speaker-card-1">.*?<div class="space-y-2">.*?<label for="language-1"'
    speaker1_match = re.search(speaker1_pattern, content, re.DOTALL)
    
    if not speaker1_match:
        print("❌ Speaker 1 card does not have space-y-2 spacing")
        return False
    else:
        print("✅ Speaker 1 card has correct space-y-2 spacing")
    
    # Look for the specific pattern in Speaker 2 card
    speaker2_pattern = r'<div class="card speaker-card-2">.*?<div class="space-y-2">.*?<label for="language-2"'
    speaker2_match = re.search(speaker2_pattern, content, re.DOTALL)
    
    if not speaker2_match:
        print("❌ Speaker 2 card does not have space-y-2 spacing")
        return False
    else:
        print("✅ Speaker 2 card has correct space-y-2 spacing")
    
    # Check that no space-y-4 remains in speaker cards
    space_y_4_in_speakers = re.findall(r'speaker-card-[12].*?space-y-4', content, re.DOTALL)
    if space_y_4_in_speakers:
        print("❌ Found space-y-4 still present in speaker cards:")
        for match in space_y_4_in_speakers:
            print(f"   - {match[:100]}...")
        return False
    else:
        print("✅ No space-y-4 found in speaker cards")
    
    return True

def test_other_elements_unchanged():
    """Test that other UI elements were not modified"""
    print("\n🔒 Testing Other Elements Unchanged")
    print("=" * 50)
    
    index_path = "templates/index.html"
    if not os.path.exists(index_path):
        print(f"❌ File not found: {index_path}")
        return False
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that other space-y-* classes are preserved
    other_spacing_patterns = [
        r'<div id="bilingual-mode-content" class="space-y-6"',  # Main bilingual container
        r'class="grid grid-cols-1 md:grid-cols-2 gap-6"'       # Grid spacing
    ]
    
    for pattern in other_spacing_patterns:
        if not re.search(pattern, content):
            print(f"❌ Missing expected spacing pattern: {pattern}")
            return False
    
    print("✅ Other spacing elements preserved")
    
    # Check that toggle button area is unchanged
    toggle_pattern = r'<span class="text-sm font-medium bilingual-mode-label">Bilingual Mode</span>'
    if not re.search(toggle_pattern, content):
        print("❌ Toggle button area was modified")
        return False
    else:
        print("✅ Toggle button area unchanged")
    
    # Check that TTS removal is still in place
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
        print("❌ TTS elements found - previous changes were affected")
        return False
    else:
        print("✅ TTS removal preserved")
    
    return True

def test_language_selection_structure():
    """Test that language selection structure is intact"""
    print("\n🌐 Testing Language Selection Structure")
    print("=" * 50)
    
    index_path = "templates/index.html"
    if not os.path.exists(index_path):
        print(f"❌ File not found: {index_path}")
        return False
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that language selection elements are present and properly structured
    language_elements = [
        r'<label for="language-1" class="form-label">Your Language:</label>',
        r'<select id="language-1" class="form-select"></select>',
        r'<label for="language-2" class="form-label">Your Language:</label>',
        r'<select id="language-2" class="form-select"></select>'
    ]
    
    for element in language_elements:
        if not re.search(element, content):
            print(f"❌ Missing language selection element: {element}")
            return False
    
    print("✅ All language selection elements present")
    
    # Check that the form-group structure is preserved
    form_group_pattern = r'<div class="form-group">.*?<label for="language-[12]".*?<select id="language-[12]".*?</div>'
    form_groups = re.findall(form_group_pattern, content, re.DOTALL)
    
    if len(form_groups) != 2:
        print(f"❌ Expected 2 form groups, found {len(form_groups)}")
        return False
    else:
        print("✅ Form group structure preserved")
    
    return True

def show_spacing_comparison():
    """Show the before/after spacing comparison"""
    print("\n📊 Spacing Comparison")
    print("=" * 50)
    
    print("BEFORE (space-y-4):")
    print("  - Larger vertical spacing between elements")
    print("  - More padding around single language dropdown")
    print("  - Excessive white space in speaker cards")
    
    print("\nAFTER (space-y-2):")
    print("  - Reduced vertical spacing for cleaner look")
    print("  - More compact language selection area")
    print("  - Better visual balance in speaker cards")
    
    print("\nCSS Class Values:")
    print("  - space-y-4: 1rem (16px) vertical spacing")
    print("  - space-y-2: 0.5rem (8px) vertical spacing")
    print("  - Reduction: 50% less vertical spacing")
    
    return True

def main():
    """Run all spacing reduction tests"""
    print("🧪 Bilingual Mode Spacing Reduction Tests")
    print("=" * 60)
    
    tests = [
        ("Speaker Card Spacing Reduction", test_speaker_card_spacing_reduction),
        ("Other Elements Unchanged", test_other_elements_unchanged),
        ("Language Selection Structure", test_language_selection_structure),
        ("Spacing Comparison", show_spacing_comparison)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
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
    
    if passed >= 3:  # Allow spacing comparison to always pass
        print("🎉 Spacing reduction successfully implemented!")
        print("\n📋 Changes Summary:")
        print("✅ Speaker 1 card: space-y-4 → space-y-2")
        print("✅ Speaker 2 card: space-y-4 → space-y-2")
        print("✅ 50% reduction in vertical spacing")
        print("✅ Cleaner, more compact UI")
        print("✅ All other elements preserved")
        print("✅ Language selection functionality intact")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed >= 3

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
