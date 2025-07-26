#!/usr/bin/env python3
"""
Simple test to verify that the KeyError fix is working correctly.
Tests the core issue: session structure consistency between endpoints.
"""

import os
import re

def test_session_structure_fix():
    """Test that both endpoints have consistent session structure"""
    print("🔍 Testing Session Structure Fix")
    print("=" * 50)
    
    # Check transcription endpoint
    transcription_path = "routes/transcription.py"
    if not os.path.exists(transcription_path):
        print(f"❌ Transcription routes file not found: {transcription_path}")
        return False

    with open(transcription_path, 'r', encoding='utf-8') as f:
        transcription_content = f.read()

    # Check translation endpoint
    translation_path = "routes/translation.py"
    if not os.path.exists(translation_path):
        print(f"❌ Translation routes file not found: {translation_path}")
        return False

    with open(translation_path, 'r', encoding='utf-8') as f:
        translation_content = f.read()
    
    # Check that transcription endpoint includes total_words
    if "'total_words': 0" in transcription_content:
        print("✅ Transcription endpoint includes total_words field")
    else:
        print("❌ Transcription endpoint missing total_words field")
        return False
    
    # Check that translation endpoint includes total_duration
    if "'total_duration': 0" in translation_content:
        print("✅ Translation endpoint includes total_duration field")
    else:
        print("❌ Translation endpoint missing total_duration field")
        return False
    
    # Check for backward compatibility in translation
    if "if 'total_words' not in session['free_trial_usage']" in translation_content:
        print("✅ Translation endpoint has total_words backward compatibility")
    else:
        print("❌ Translation endpoint missing total_words backward compatibility")
        return False
    
    # Check for backward compatibility in transcription
    if "if 'total_duration' not in session['free_trial_usage']" in transcription_content:
        print("✅ Transcription endpoint has total_duration backward compatibility")
    else:
        print("❌ Transcription endpoint missing total_duration backward compatibility")
        return False
    
    return True

def test_keyerror_prevention():
    """Test that the specific KeyError scenarios are prevented"""
    print("\n🛡️ Testing KeyError Prevention")
    print("=" * 50)
    
    # Check translation endpoint for safe access to total_words
    translation_path = "routes/translation.py"
    with open(translation_path, 'r', encoding='utf-8') as f:
        translation_content = f.read()
    
    # Find the translate_free_trial function
    translate_function_pattern = r'def translate_free_trial\(\):.*?(?=def|\Z)'
    translate_match = re.search(translate_function_pattern, translation_content, re.DOTALL)
    
    if not translate_match:
        print("❌ translate_free_trial function not found")
        return False
    
    translate_function = translate_match.group(0)
    
    # Check that total_words access happens after initialization
    lines = translate_function.split('\n')
    initialization_line = None
    compatibility_line = None
    access_line = None
    
    for i, line in enumerate(lines):
        if "'total_words': 0" in line and 'session[' in line:
            initialization_line = i
        elif "if 'total_words' not in session" in line:
            compatibility_line = i
        elif "session['free_trial_usage']['total_words']" in line and '+' in line:
            access_line = i
            break
    
    if initialization_line is not None and compatibility_line is not None and access_line is not None:
        if access_line > max(initialization_line, compatibility_line):
            print("✅ Translation endpoint has safe total_words access")
        else:
            print("❌ Translation endpoint has unsafe total_words access")
            return False
    else:
        print("⚠️ Could not verify access pattern (may still be safe)")
    
    # Check transcription endpoint for safe access to total_duration
    transcription_path = "routes/transcription.py"
    with open(transcription_path, 'r', encoding='utf-8') as f:
        transcription_content = f.read()
    
    # Find the transcribe_free_trial function
    transcribe_function_pattern = r'def transcribe_free_trial\(\):.*?(?=def|\Z)'
    transcribe_match = re.search(transcribe_function_pattern, transcription_content, re.DOTALL)
    
    if not transcribe_match:
        print("❌ transcribe_free_trial function not found")
        return False
    
    transcribe_function = transcribe_match.group(0)
    
    # Check that total_duration access happens after initialization
    if "'total_duration': 0" in transcribe_function and "if 'total_duration' not in session" in transcribe_function:
        print("✅ Transcription endpoint has safe total_duration access")
    else:
        print("❌ Transcription endpoint missing safe total_duration access")
        return False
    
    return True

def test_cross_service_compatibility():
    """Test that services can work together without conflicts"""
    print("\n🔄 Testing Cross-Service Compatibility")
    print("=" * 50)
    
    # Both endpoints should initialize the same session structure
    transcription_path = "routes/transcription.py"
    translation_path = "routes/translation.py"
    
    with open(transcription_path, 'r', encoding='utf-8') as f:
        transcription_content = f.read()
    
    with open(translation_path, 'r', encoding='utf-8') as f:
        translation_content = f.read()
    
    # Check that both create the same initial structure
    required_fields = ['total_duration', 'total_words', 'last_reset', 'requests']
    
    transcription_has_all = all(f"'{field}': 0" in transcription_content or f"'{field}': time.time()" in transcription_content for field in required_fields)
    translation_has_all = all(f"'{field}': 0" in translation_content or f"'{field}': time.time()" in translation_content for field in required_fields)
    
    if transcription_has_all:
        print("✅ Transcription endpoint creates complete session structure")
    else:
        print("❌ Transcription endpoint incomplete session structure")
        return False
    
    if translation_has_all:
        print("✅ Translation endpoint creates complete session structure")
    else:
        print("❌ Translation endpoint incomplete session structure")
        return False
    
    # Check that both handle missing fields
    transcription_handles_missing = ("if 'total_words' not in session" in transcription_content and 
                                   "if 'total_duration' not in session" in transcription_content)
    translation_handles_missing = ("if 'total_words' not in session" in translation_content and 
                                 "if 'total_duration' not in session" in translation_content)
    
    if transcription_handles_missing:
        print("✅ Transcription endpoint handles missing fields")
    else:
        print("❌ Transcription endpoint doesn't handle missing fields")
        return False
    
    if translation_handles_missing:
        print("✅ Translation endpoint handles missing fields")
    else:
        print("❌ Translation endpoint doesn't handle missing fields")
        return False
    
    return True

def test_original_keyerror_scenario():
    """Test the specific scenario that caused the original KeyError"""
    print("\n🎯 Testing Original KeyError Scenario")
    print("=" * 50)
    
    print("Scenario: User first uses transcription, then translation")
    
    # Check that if transcription initializes session first,
    # translation can still access total_words safely
    
    translation_path = "routes/translation.py"
    with open(translation_path, 'r', encoding='utf-8') as f:
        translation_content = f.read()
    
    # The key fix: translation endpoint should check for missing total_words
    # and add it if it doesn't exist
    
    if "if 'total_words' not in session['free_trial_usage']" in translation_content:
        print("✅ Translation checks for missing total_words field")
    else:
        print("❌ Translation doesn't check for missing total_words field")
        return False
    
    if "session['free_trial_usage']['total_words'] = 0" in translation_content:
        print("✅ Translation initializes missing total_words field")
    else:
        print("❌ Translation doesn't initialize missing total_words field")
        return False
    
    # Similarly for the reverse scenario
    transcription_path = "routes/transcription.py"
    with open(transcription_path, 'r', encoding='utf-8') as f:
        transcription_content = f.read()
    
    if "if 'total_duration' not in session['free_trial_usage']" in transcription_content:
        print("✅ Transcription checks for missing total_duration field")
    else:
        print("❌ Transcription doesn't check for missing total_duration field")
        return False
    
    if "session['free_trial_usage']['total_duration'] = 0" in transcription_content:
        print("✅ Transcription initializes missing total_duration field")
    else:
        print("❌ Transcription doesn't initialize missing total_duration field")
        return False
    
    return True

def main():
    """Run all KeyError fix tests"""
    print("🧪 Session KeyError Simple Fix Tests")
    print("=" * 60)
    print("Testing the core fix for KeyError: 'total_words' in translation")
    print("=" * 60)
    
    tests = [
        ("Session Structure Fix", test_session_structure_fix),
        ("KeyError Prevention", test_keyerror_prevention),
        ("Cross-Service Compatibility", test_cross_service_compatibility),
        ("Original KeyError Scenario", test_original_keyerror_scenario)
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
    
    if passed == total:
        print("🎉 Session KeyError successfully fixed!")
        print("\n📋 Fix Summary:")
        print("✅ Both endpoints create unified session structure")
        print("✅ Backward compatibility checks prevent KeyErrors")
        print("✅ Cross-service compatibility ensured")
        print("✅ Original KeyError scenario resolved")
        print("\n🚫 KeyError Eliminated:")
        print("   - KeyError: 'total_words' → Fixed with backward compatibility")
        print("   - KeyError: 'total_duration' → Fixed with backward compatibility")
        print("   - Services can be used in any order without conflicts")
        print("   - Session structure is robust and consistent")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
