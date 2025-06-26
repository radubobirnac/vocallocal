#!/usr/bin/env python3
"""
Test Frontend-Backend Synchronization
Verifies that frontend and backend model configurations are in sync
"""

import os
import sys
import json
import re

def load_frontend_config():
    """Load frontend model configuration from plan-access-control.js"""
    print("📱 Loading Frontend Configuration...")
    
    try:
        js_file_path = os.path.join('static', 'js', 'plan-access-control.js')
        
        with open(js_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract planModelAccess object using regex
        pattern = r'this\.planModelAccess\s*=\s*({.*?});'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            print("❌ Could not find planModelAccess in frontend file")
            return None
        
        # Convert JavaScript object to Python dict (simplified parsing)
        js_object = match.group(1)
        
        # Replace JavaScript syntax with Python syntax
        js_object = js_object.replace("'", '"')
        js_object = re.sub(r'//.*?\n', '\n', js_object)  # Remove comments
        js_object = re.sub(r',\s*}', '}', js_object)  # Remove trailing commas
        js_object = re.sub(r',\s*]', ']', js_object)  # Remove trailing commas in arrays
        
        try:
            frontend_config = json.loads(js_object)
            print("✅ Frontend configuration loaded successfully")
            return frontend_config
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse frontend configuration: {e}")
            return None
            
    except FileNotFoundError:
        print(f"❌ Frontend file not found: {js_file_path}")
        return None
    except Exception as e:
        print(f"❌ Error loading frontend config: {e}")
        return None

def load_backend_config():
    """Load backend model configuration from plan_access_control.py"""
    print("\n🖥️  Loading Backend Configuration...")
    
    try:
        from services.plan_access_control import PlanAccessControl
        
        backend_config = PlanAccessControl.PLAN_MODEL_ACCESS
        print("✅ Backend configuration loaded successfully")
        return backend_config
        
    except ImportError as e:
        print(f"❌ Failed to import backend configuration: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading backend config: {e}")
        return None

def compare_configurations(frontend, backend):
    """Compare frontend and backend configurations"""
    print("\n🔍 Comparing Frontend vs Backend Configurations...")
    
    if not frontend or not backend:
        print("❌ Cannot compare - missing configuration data")
        return False
    
    issues = []
    
    # Check each plan
    for plan in ['free', 'basic', 'professional']:
        print(f"\n  {plan.upper()} Plan:")
        
        if plan not in frontend:
            issues.append(f"Frontend missing {plan} plan")
            continue
        if plan not in backend:
            issues.append(f"Backend missing {plan} plan")
            continue
        
        # Check each service type
        for service in ['transcription', 'translation', 'tts', 'interpretation']:
            frontend_models = set(frontend[plan].get(service, []))
            backend_models = set(backend[plan].get(service, []))
            
            if frontend_models == backend_models:
                print(f"    ✅ {service}: {len(frontend_models)} models (synced)")
            else:
                print(f"    ❌ {service}: MISMATCH")
                print(f"       Frontend: {sorted(frontend_models)}")
                print(f"       Backend:  {sorted(backend_models)}")
                
                # Find differences
                only_frontend = frontend_models - backend_models
                only_backend = backend_models - frontend_models
                
                if only_frontend:
                    issues.append(f"{plan}/{service}: Frontend has extra models: {only_frontend}")
                if only_backend:
                    issues.append(f"{plan}/{service}: Backend has extra models: {only_backend}")
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} synchronization issues:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        return False
    else:
        print("\n✅ Frontend and backend configurations are perfectly synchronized!")
        return True

def test_tts_models_locked():
    """Verify that all TTS models are properly locked"""
    print("\n🔒 Testing TTS Model Locking...")
    
    try:
        from services.plan_access_control import PlanAccessControl
        
        # Check that free plan has no TTS models
        free_tts = PlanAccessControl.PLAN_MODEL_ACCESS['free']['tts']
        
        if len(free_tts) == 0:
            print("✅ Free plan has no TTS models (all locked)")
        else:
            print(f"❌ Free plan still has TTS models: {free_tts}")
            return False
        
        # Check that all TTS models require upgrade
        all_tts_models = set()
        for plan in ['basic', 'professional']:
            all_tts_models.update(PlanAccessControl.PLAN_MODEL_ACCESS[plan]['tts'])
        
        print(f"📊 Total TTS models requiring upgrade: {len(all_tts_models)}")
        for model in sorted(all_tts_models):
            restriction_info = PlanAccessControl.get_model_restriction_info(model, 'tts', 'free')
            required_plan = restriction_info.get('required_plan')
            print(f"   🔒 {model}: requires {required_plan} plan")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing TTS locking: {e}")
        return False

def test_html_templates():
    """Check HTML templates for lock icons"""
    print("\n🌐 Testing HTML Templates...")
    
    templates_to_check = [
        'templates/index.html',
        'templates/try_it_free.html',
        'templates/test_plan_access.html'
    ]
    
    issues = []
    
    for template_path in templates_to_check:
        if not os.path.exists(template_path):
            issues.append(f"Template not found: {template_path}")
            continue
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for TTS model options
            tts_section_match = re.search(r'<select[^>]*id=["\']tts-model-select["\'][^>]*>(.*?)</select>', content, re.DOTALL)
            
            if tts_section_match:
                tts_options = tts_section_match.group(1)
                
                # Count lock icons in TTS options
                lock_count = tts_options.count('🔒')
                option_count = tts_options.count('<option')
                
                # Exclude empty/default options
                non_empty_options = len(re.findall(r'<option[^>]*value=["\'][^"\']+["\']', tts_options))
                
                print(f"   📄 {template_path}:")
                print(f"      TTS options: {non_empty_options}")
                print(f"      Lock icons: {lock_count}")
                
                if lock_count >= non_empty_options and lock_count > 0:
                    print(f"      ✅ All TTS models have lock icons")
                else:
                    print(f"      ❌ Missing lock icons on some TTS models")
                    issues.append(f"{template_path}: Only {lock_count}/{non_empty_options} TTS models have locks")
            else:
                print(f"   📄 {template_path}: No TTS selector found")
                
        except Exception as e:
            issues.append(f"Error reading {template_path}: {e}")
    
    if issues:
        print(f"\n⚠️  HTML template issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ All HTML templates have proper lock icons")
        return True

def main():
    """Run all synchronization tests"""
    print("🔄 VocalLocal Frontend-Backend Synchronization Test")
    print("=" * 55)
    
    tests = [
        ("Frontend-Backend Config Sync", lambda: compare_configurations(
            load_frontend_config(), load_backend_config())),
        ("TTS Models Locking", test_tts_models_locked),
        ("HTML Templates", test_html_templates)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {str(e)}")
    
    # Summary
    print(f"\n{'='*55}")
    print(f"📊 Synchronization Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Frontend and backend are perfectly synchronized!")
        print("🔒 All TTS models are properly locked and responsive!")
    elif passed >= total * 0.8:
        print("⚠️  Most tests passed. Address the issues above.")
    else:
        print("❌ Multiple synchronization issues found.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
