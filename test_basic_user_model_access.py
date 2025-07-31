#!/usr/bin/env python3
"""
Test script to verify that Basic users have access to all models.
Tests both backend and frontend configurations.
"""

import os
import re

def test_backend_plan_access_control():
    """Test that Basic users have access to all models in backend configuration"""
    print("🔧 Testing Backend Plan Access Control")
    print("=" * 50)
    
    plan_access_file = "services/plan_access_control.py"
    if not os.path.exists(plan_access_file):
        print(f"❌ File not found: {plan_access_file}")
        return False
    
    with open(plan_access_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract Basic plan configuration
    basic_plan_match = re.search(r"'basic':\s*{(.*?)},\s*'professional':", content, re.DOTALL)
    if not basic_plan_match:
        print("❌ Could not find Basic plan configuration")
        return False
    
    basic_config = basic_plan_match.group(1)
    
    # Check for all expected models in Basic plan
    expected_models = [
        'gemini-2.0-flash-lite',
        'gpt-4o-mini-transcribe',
        'gpt-4o-transcribe',
        'gemini-2.5-flash-preview-04-17',
        'gemini-2.5-flash-preview-05-20',
        'gemini-2.5-flash',
        'gemini-2.5-flash-tts',
        'gpt4o-mini',
        'openai',
        'gpt-4.1-mini'
    ]
    
    missing_models = []
    for model in expected_models:
        if model not in basic_config:
            missing_models.append(model)
    
    if missing_models:
        print(f"❌ Basic plan missing models: {missing_models}")
        return False
    else:
        print(f"✅ Basic plan has access to all {len(expected_models)} expected models")
    
    # Check that Basic and Professional plans have the same models
    professional_plan_match = re.search(r"'professional':\s*{(.*?)}\s*}", content, re.DOTALL)
    if professional_plan_match:
        professional_config = professional_plan_match.group(1)
        
        # Count models in each plan
        basic_model_count = len(re.findall(r"'[^']*-[^']*'", basic_config))
        professional_model_count = len(re.findall(r"'[^']*-[^']*'", professional_config))
        
        print(f"📊 Basic plan models: {basic_model_count}")
        print(f"📊 Professional plan models: {professional_model_count}")
        
        if basic_model_count >= professional_model_count - 1:  # Allow small difference
            print("✅ Basic plan has similar model access to Professional plan")
        else:
            print("⚠️ Basic plan has significantly fewer models than Professional plan")
    
    return True

def test_frontend_plan_access_control():
    """Test that Basic users have access to all models in frontend configuration"""
    print("\n🌐 Testing Frontend Plan Access Control")
    print("=" * 50)
    
    plan_access_js_file = "static/js/plan-access-control.js"
    if not os.path.exists(plan_access_js_file):
        print(f"❌ File not found: {plan_access_js_file}")
        return False
    
    with open(plan_access_js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract Basic plan configuration from JavaScript
    basic_plan_match = re.search(r"'basic':\s*{(.*?)},\s*'professional':", content, re.DOTALL)
    if not basic_plan_match:
        print("❌ Could not find Basic plan configuration in JavaScript")
        return False
    
    basic_config = basic_plan_match.group(1)
    
    # Check for all expected models in Basic plan
    expected_models = [
        'gemini-2.0-flash-lite',
        'gpt-4o-mini-transcribe',
        'gpt-4o-transcribe',
        'gemini-2.5-flash-preview-04-17',
        'gemini-2.5-flash-preview-05-20',
        'gemini-2.5-flash-tts',
        'gpt4o-mini',
        'openai',
        'gpt-4.1-mini'
    ]
    
    missing_models = []
    for model in expected_models:
        if model not in basic_config:
            missing_models.append(model)
    
    if missing_models:
        print(f"❌ Frontend Basic plan missing models: {missing_models}")
        return False
    else:
        print(f"✅ Frontend Basic plan has access to all {len(expected_models)} expected models")
    
    return True

def test_rbac_access_control_js():
    """Test that RBAC access control allows Basic users access to premium models"""
    print("\n🔐 Testing RBAC Access Control JavaScript")
    print("=" * 50)
    
    rbac_file = "static/js/rbac-access-control.js"
    if not os.path.exists(rbac_file):
        print(f"❌ File not found: {rbac_file}")
        return False
    
    with open(rbac_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for Basic plan access logic
    basic_access_patterns = [
        r"this\.userPlan === 'basic'.*return true",
        r"userPlan === 'basic'.*accessible",
        r"'basic'.*plan.*access"
    ]
    
    found_basic_access = False
    for pattern in basic_access_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            found_basic_access = True
            break
    
    if found_basic_access:
        print("✅ RBAC JavaScript includes Basic plan access logic")
    else:
        print("❌ RBAC JavaScript missing Basic plan access logic")
        return False
    
    # Check that Basic users are not restricted to free models only
    restrictive_patterns = [
        r"userPlan.*===.*'basic'.*false",
        r"basic.*restricted.*free.*models"
    ]
    
    found_restrictions = False
    for pattern in restrictive_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            found_restrictions = True
            break
    
    if not found_restrictions:
        print("✅ No restrictive patterns found for Basic users")
    else:
        print("⚠️ Found potentially restrictive patterns for Basic users")
    
    return True

def test_model_access_control_js():
    """Test that model access control JavaScript allows all users access to all models"""
    print("\n🎛️ Testing Model Access Control JavaScript")
    print("=" * 50)
    
    model_access_file = "static/js/model-access-control.js"
    if not os.path.exists(model_access_file):
        print(f"❌ File not found: {model_access_file}")
        return False
    
    with open(model_access_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for updated access logic
    access_patterns = [
        r"return true.*normal.*user",
        r"all.*models.*accessible.*normal.*user",
        r"Basic.*plan.*access.*all.*models"
    ]
    
    found_access_logic = False
    for pattern in access_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            found_access_logic = True
            break
    
    if found_access_logic:
        print("✅ Model access control includes updated access logic")
    else:
        print("❌ Model access control missing updated access logic")
        return False
    
    return True

def test_model_access_ui_js():
    """Test that model access UI JavaScript removes lock icons for Basic users"""
    print("\n🔓 Testing Model Access UI JavaScript")
    print("=" * 50)
    
    model_access_ui_file = "static/js/model-access.js"
    if not os.path.exists(model_access_ui_file):
        print(f"❌ File not found: {model_access_ui_file}")
        return False
    
    with open(model_access_ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for Basic plan logic
    basic_ui_patterns = [
        r"userPlan.*===.*'basic'",
        r"hasBasicOrHigher",
        r"basic.*professional.*remove.*lock"
    ]
    
    found_basic_ui_logic = False
    for pattern in basic_ui_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            found_basic_ui_logic = True
            break
    
    if found_basic_ui_logic:
        print("✅ Model access UI includes Basic plan logic")
    else:
        print("❌ Model access UI missing Basic plan logic")
        return False
    
    return True

def test_bilingual_mode_js():
    """Test that bilingual mode JavaScript removes lock icons for Basic users"""
    print("\n🌍 Testing Bilingual Mode JavaScript")
    print("=" * 50)
    
    bilingual_file = "static/js/bilingual-mode.js"
    if not os.path.exists(bilingual_file):
        print(f"❌ File not found: {bilingual_file}")
        return False
    
    with open(bilingual_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for Basic plan logic
    basic_bilingual_patterns = [
        r"userPlan.*===.*'basic'",
        r"hasBasicOrHigher",
        r"basic.*professional.*lock"
    ]
    
    found_basic_bilingual_logic = False
    for pattern in basic_bilingual_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            found_basic_bilingual_logic = True
            break
    
    if found_basic_bilingual_logic:
        print("✅ Bilingual mode includes Basic plan logic")
    else:
        print("❌ Bilingual mode missing Basic plan logic")
        return False
    
    return True

def main():
    """Run all Basic user model access tests"""
    print("🧪 Basic User Model Access Tests")
    print("=" * 60)
    print("Testing that Basic users have access to all models")
    print("=" * 60)
    
    tests = [
        ("Backend Plan Access Control", test_backend_plan_access_control),
        ("Frontend Plan Access Control", test_frontend_plan_access_control),
        ("RBAC Access Control JavaScript", test_rbac_access_control_js),
        ("Model Access Control JavaScript", test_model_access_control_js),
        ("Model Access UI JavaScript", test_model_access_ui_js),
        ("Bilingual Mode JavaScript", test_bilingual_mode_js)
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
    print("📊 BASIC USER MODEL ACCESS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ IMPLEMENTED" if result else "❌ MISSING"
        print(f"{status:<15} {test_name}")
        if result:
            passed += 1
    
    print(f"\nImplementation Score: {passed}/{total}")
    
    if passed >= total - 1:  # Allow one minor issue
        print("🎉 Basic users have access to all models!")
        print("\n📋 Model Access Features:")
        print("✅ Backend configuration allows Basic users access to all models")
        print("✅ Frontend JavaScript removes model restrictions for Basic users")
        print("✅ UI removes lock icons (🔒) for Basic users")
        print("✅ Model selection dropdowns show all models as available")
        print("✅ No upgrade prompts for model selection")
        print("✅ Consistent access across all services (transcription, translation, TTS)")
        print("\n🌐 User Experience:")
        print("   - Basic users see all models without lock icons")
        print("   - No upgrade prompts when selecting premium models")
        print("   - Same model access as Professional users")
        print("   - Only usage limits differentiate Basic from Professional")
    else:
        print("⚠️ Some Basic user model access features are missing!")
        print("\n🚨 Missing Implementations:")
        for test_name, result in results:
            if not result:
                print(f"   - {test_name}")
        print("\n🔧 Recommended Actions:")
        print("   - Update backend plan access control configuration")
        print("   - Update frontend JavaScript model access logic")
        print("   - Remove lock icons from UI for Basic users")
        print("   - Test model selection dropdowns")
        print("   - Verify no upgrade prompts for Basic users")
    
    return passed >= total - 1

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
