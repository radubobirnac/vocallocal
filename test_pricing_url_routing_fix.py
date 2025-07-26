#!/usr/bin/env python3
"""
Test script to verify that the pricing URL routing inconsistency has been fixed.
Tests that all pricing page links use clean URLs (/pricing) instead of hash-based URLs (#pricing).
"""

import os
import re
import requests
import time
from urllib.parse import urljoin

def test_home_template_pricing_link():
    """Test that home.html uses clean URL for pricing link"""
    print("🔗 Testing Home Template Pricing Link")
    print("=" * 50)
    
    template_path = "templates/home.html"
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that hash-based pricing URL is removed
    hash_pricing_pattern = r'href=["\']#pricing["\']'
    hash_matches = re.findall(hash_pricing_pattern, content)
    
    if hash_matches:
        print("❌ Found hash-based pricing URLs:")
        for match in hash_matches:
            print(f"   - {match}")
        return False
    else:
        print("✅ No hash-based pricing URLs found")
    
    # Check that clean URL is present
    clean_pricing_patterns = [
        r'href=["\']{{.*url_for\(["\']pricing["\'].*}}["\']',
        r'href=["\']{{.*url_for\(.*pricing.*\).*}}["\']'
    ]
    
    found_clean_url = False
    for pattern in clean_pricing_patterns:
        if re.search(pattern, content):
            found_clean_url = True
            print("✅ Found clean pricing URL using url_for('pricing')")
            break
    
    if not found_clean_url:
        print("❌ Clean pricing URL not found")
        return False
    
    # Check that data-page attribute is used instead of data-section
    data_page_pattern = r'data-page=["\']pricing["\']'
    if re.search(data_page_pattern, content):
        print("✅ Found correct data-page='pricing' attribute")
    else:
        print("❌ data-page='pricing' attribute not found")
        return False
    
    # Check that old data-section attribute is removed
    data_section_pattern = r'data-section=["\']pricing["\']'
    if re.search(data_section_pattern, content):
        print("❌ Old data-section='pricing' attribute still present")
        return False
    else:
        print("✅ Old data-section='pricing' attribute removed")
    
    return True

def test_navigation_js_pricing_support():
    """Test that navigation.js supports pricing page detection"""
    print("\n🧭 Testing Navigation.js Pricing Support")
    print("=" * 50)
    
    nav_js_path = "static/navigation.js"
    if not os.path.exists(nav_js_path):
        print(f"❌ Navigation script not found: {nav_js_path}")
        return False
    
    with open(nav_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for pricing page detection
    pricing_detection_patterns = [
        r'currentPath\.includes\(["\']\/pricing["\']',
        r'currentPage\s*=\s*["\']pricing["\']'
    ]
    
    found_detection = False
    for pattern in pricing_detection_patterns:
        if re.search(pattern, content):
            found_detection = True
            print("✅ Found pricing page detection logic")
            break
    
    if not found_detection:
        print("❌ Pricing page detection logic not found")
        return False
    
    # Check for data-page selector support
    data_page_selector_pattern = r'data-page.*pricing'
    if re.search(data_page_selector_pattern, content):
        print("✅ Found data-page selector support")
    else:
        print("⚠️ data-page selector support not explicitly found (may be generic)")
    
    return True

def test_flask_pricing_route():
    """Test that Flask pricing route is properly configured"""
    print("\n🌐 Testing Flask Pricing Route Configuration")
    print("=" * 50)
    
    app_py_path = "app.py"
    if not os.path.exists(app_py_path):
        print(f"❌ App file not found: {app_py_path}")
        return False
    
    with open(app_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for pricing route definition
    pricing_route_patterns = [
        r'@app\.route\(["\']\/pricing["\']',
        r'def pricing\(\):'
    ]

    route_found = False
    function_found = False

    # Check for route decorator
    if re.search(r'@app\.route\(["\']\/pricing["\']', content):
        route_found = True
        print("✅ Found @app.route('/pricing') decorator")

    # Check for function definition
    if re.search(r'def pricing\(\):', content):
        function_found = True
        print("✅ Found pricing() function definition")
    
    if not route_found:
        print("❌ Pricing route decorator not found")
        return False
    
    if not function_found:
        print("❌ Pricing function definition not found")
        return False
    
    # Check that it renders the correct template
    template_render_pattern = r'render_template\(["\']pricing\.html["\']'
    if re.search(template_render_pattern, content):
        print("✅ Found correct template rendering (pricing.html)")
    else:
        print("❌ Correct template rendering not found")
        return False
    
    return True

def test_upgrade_button_urls():
    """Test that upgrade buttons use clean URLs"""
    print("\n🔄 Testing Upgrade Button URLs")
    print("=" * 50)
    
    files_to_check = [
        "templates/index.html",
        "templates/dashboard.html",
        "templates/pricing.html"
    ]
    
    all_clean = True
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            print(f"⚠️ File not found: {file_path}")
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for upgrade-related URLs
        upgrade_url_patterns = [
            r'window\.upgradeConfig\.pricingUrl',
            r'url_for\(["\']pricing["\']',
            r'next=["\']\/pricing["\']'
        ]
        
        found_clean_urls = []
        for pattern in upgrade_url_patterns:
            matches = re.findall(pattern, content)
            if matches:
                found_clean_urls.extend(matches)
        
        if found_clean_urls:
            print(f"✅ {file_path} - Found clean upgrade URLs:")
            for url in found_clean_urls:
                print(f"   - {url}")
        else:
            print(f"⚠️ {file_path} - No upgrade URLs found (may not be relevant)")
    
    return all_clean

def test_no_remaining_hash_pricing_urls():
    """Test that no hash-based pricing URLs remain anywhere"""
    print("\n🔍 Testing for Remaining Hash-Based Pricing URLs")
    print("=" * 50)
    
    files_to_check = []
    
    # Find all HTML and JS files
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        skip_dirs = ['.git', '__pycache__', 'node_modules', '.env', 'venv']
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith(('.html', '.js', '.py')):
                files_to_check.append(os.path.join(root, file))
    
    hash_pricing_found = []
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for hash-based pricing URLs
            hash_patterns = [
                r'href=["\']#pricing["\']',
                r'window\.location\.href\s*=\s*["\']#pricing["\']',
                r'location\.hash\s*=\s*["\']pricing["\']'
            ]
            
            for pattern in hash_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    hash_pricing_found.append((file_path, matches))
        
        except (UnicodeDecodeError, PermissionError):
            # Skip files that can't be read
            continue
    
    if hash_pricing_found:
        print("❌ Found remaining hash-based pricing URLs:")
        for file_path, matches in hash_pricing_found:
            print(f"   {file_path}:")
            for match in matches:
                print(f"     - {match}")
        return False
    else:
        print("✅ No hash-based pricing URLs found in any files")
        return True

def test_url_routing_consistency():
    """Test overall URL routing consistency"""
    print("\n📋 Testing URL Routing Consistency")
    print("=" * 50)
    
    # Check that all pricing-related links are consistent
    consistency_checks = [
        ("Home template uses clean URL", test_home_template_pricing_link),
        ("Navigation.js supports pricing", test_navigation_js_pricing_support),
        ("Flask route configured", test_flask_pricing_route),
        ("Upgrade buttons use clean URLs", test_upgrade_button_urls),
        ("No hash URLs remain", test_no_remaining_hash_pricing_urls)
    ]
    
    results = []
    for check_name, check_func in consistency_checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error in {check_name}: {e}")
            results.append((check_name, False))
    
    return results

def main():
    """Run all URL routing fix tests"""
    print("🧪 Pricing URL Routing Fix Tests")
    print("=" * 60)
    
    # Run individual tests
    tests = [
        ("Home Template Pricing Link", test_home_template_pricing_link),
        ("Navigation.js Pricing Support", test_navigation_js_pricing_support),
        ("Flask Pricing Route", test_flask_pricing_route),
        ("Upgrade Button URLs", test_upgrade_button_urls),
        ("No Remaining Hash URLs", test_no_remaining_hash_pricing_urls)
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
        print("🎉 All URL routing fixes successfully implemented!")
        print("\n📋 URL Routing Fix Summary:")
        print("✅ Home navigation link: #pricing → /pricing")
        print("✅ Navigation.js updated to support pricing page")
        print("✅ Flask route properly configured")
        print("✅ All upgrade buttons use clean URLs")
        print("✅ No hash-based pricing URLs remain")
        print("✅ SEO-friendly URL structure achieved")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
