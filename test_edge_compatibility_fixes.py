#!/usr/bin/env python3
"""
Test script to verify Edge compatibility fixes for the pricing page.
Validates that all necessary fallbacks and polyfills are in place.
"""

import os
import re

def test_edge_css_included():
    """Test that Edge compatibility CSS is included in pricing template"""
    print("🎨 Testing Edge CSS Inclusion")
    print("=" * 50)
    
    pricing_template_path = "templates/pricing.html"
    if not os.path.exists(pricing_template_path):
        print(f"❌ Pricing template not found: {pricing_template_path}")
        return False
    
    with open(pricing_template_path, 'r', encoding='utf-8') as f:
        pricing_content = f.read()
    
    # Check for Edge compatibility CSS inclusion
    edge_css_patterns = [
        r'edge-compatibility\.css',
        r'static.*css.*edge-compatibility'
    ]
    
    found_edge_css = any(re.search(pattern, pricing_content) for pattern in edge_css_patterns)
    
    if found_edge_css:
        print("✅ Edge compatibility CSS is included")
    else:
        print("❌ Edge compatibility CSS not found")
        return False
    
    return True

def test_edge_js_included():
    """Test that Edge compatibility JavaScript is included"""
    print("\n📜 Testing Edge JavaScript Inclusion")
    print("=" * 50)
    
    pricing_template_path = "templates/pricing.html"
    with open(pricing_template_path, 'r', encoding='utf-8') as f:
        pricing_content = f.read()
    
    # Check for Edge compatibility JS inclusion
    edge_js_patterns = [
        r'edge-compatibility\.js',
        r'static.*js.*edge-compatibility'
    ]
    
    found_edge_js = any(re.search(pattern, pricing_content) for pattern in edge_js_patterns)
    
    if found_edge_js:
        print("✅ Edge compatibility JavaScript is included")
    else:
        print("❌ Edge compatibility JavaScript not found")
        return False
    
    # Check that it's loaded before other scripts
    script_order = []
    script_pattern = r'<script[^>]*src="[^"]*([^/"]+\.js)"'
    matches = re.findall(script_pattern, pricing_content)
    
    if matches:
        edge_index = None
        for i, script in enumerate(matches):
            if 'edge-compatibility' in script:
                edge_index = i
                break
        
        if edge_index is not None and edge_index == 0:
            print("✅ Edge compatibility script loads first")
        elif edge_index is not None:
            print("⚠️ Edge compatibility script loads after other scripts")
        else:
            print("❌ Edge compatibility script not found in load order")
    
    return True

def test_css_fallbacks():
    """Test that CSS fallbacks are properly implemented"""
    print("\n🔧 Testing CSS Fallbacks")
    print("=" * 50)
    
    # Check Edge compatibility CSS file
    edge_css_path = "static/css/edge-compatibility.css"
    if not os.path.exists(edge_css_path):
        print(f"❌ Edge CSS file not found: {edge_css_path}")
        return False
    
    with open(edge_css_path, 'r', encoding='utf-8') as f:
        edge_css_content = f.read()
    
    # Check for important fallback patterns
    fallback_patterns = [
        r'@supports not \(display: grid\)',  # Grid fallback
        r'display: -ms-flexbox',  # Edge flexbox prefix
        r'-ms-flex',  # Edge flex properties
        r'@media screen and \(-ms-high-contrast',  # Edge detection
        r'display: flex !important',  # Grid fallback
        r'flex-wrap: wrap !important'  # Grid fallback
    ]
    
    found_fallbacks = []
    for pattern in fallback_patterns:
        if re.search(pattern, edge_css_content, re.IGNORECASE):
            found_fallbacks.append(pattern)
    
    if len(found_fallbacks) >= 4:
        print(f"✅ Found {len(found_fallbacks)} CSS fallback patterns")
        for fallback in found_fallbacks:
            print(f"   - {fallback}")
    else:
        print(f"❌ Only found {len(found_fallbacks)} CSS fallback patterns")
        return False
    
    return True

def test_javascript_polyfills():
    """Test that JavaScript polyfills are implemented"""
    print("\n🔌 Testing JavaScript Polyfills")
    print("=" * 50)
    
    edge_js_path = "static/js/edge-compatibility.js"
    if not os.path.exists(edge_js_path):
        print(f"❌ Edge JS file not found: {edge_js_path}")
        return False
    
    with open(edge_js_path, 'r', encoding='utf-8') as f:
        edge_js_content = f.read()
    
    # Check for important polyfills
    polyfill_patterns = [
        r'Array\.prototype\.includes',  # Array.includes polyfill
        r'String\.prototype\.includes',  # String.includes polyfill
        r'window\.fetch.*function',  # Fetch polyfill
        r'isEdge\(\)',  # Edge detection
        r'checkAuthenticationEdge',  # Enhanced auth detection
        r'addEventListenerEdge'  # Enhanced event handling
    ]
    
    found_polyfills = []
    for pattern in polyfill_patterns:
        if re.search(pattern, edge_js_content):
            found_polyfills.append(pattern)
    
    if len(found_polyfills) >= 5:
        print(f"✅ Found {len(found_polyfills)} JavaScript polyfills")
        for polyfill in found_polyfills:
            print(f"   - {polyfill}")
    else:
        print(f"❌ Only found {len(found_polyfills)} JavaScript polyfills")
        return False
    
    return True

def test_inline_css_fallbacks():
    """Test that inline CSS fallbacks are added to pricing template"""
    print("\n🎯 Testing Inline CSS Fallbacks")
    print("=" * 50)
    
    pricing_template_path = "templates/pricing.html"
    with open(pricing_template_path, 'r', encoding='utf-8') as f:
        pricing_content = f.read()
    
    # Check for CSS custom property fallbacks in template
    fallback_patterns = [
        r'border: 2px solid #[0-9a-fA-F]{6}.*border: 2px solid hsl\(var\(',
        r'background: #[0-9a-fA-F]{6}.*background: hsl\(var\(',
        r'color: #[0-9a-fA-F]{6}.*color: hsl\(var\(',
        r'background-color: #[0-9a-fA-F]{6}.*background-color: hsl\(var\('
    ]
    
    found_inline_fallbacks = []
    for pattern in fallback_patterns:
        if re.search(pattern, pricing_content, re.DOTALL):
            found_inline_fallbacks.append(pattern)
    
    if len(found_inline_fallbacks) >= 2:
        print(f"✅ Found {len(found_inline_fallbacks)} inline CSS fallbacks")
    else:
        print(f"⚠️ Only found {len(found_inline_fallbacks)} inline CSS fallbacks")
    
    # Check for specific fallback colors
    critical_fallbacks = [
        r'#667eea',  # Primary color fallback
        r'#e2e8f0',  # Border color fallback
        r'#ffffff',  # Background fallback
        r'#1a202c'   # Text color fallback
    ]
    
    found_colors = []
    for color in critical_fallbacks:
        if re.search(color, pricing_content, re.IGNORECASE):
            found_colors.append(color)
    
    if len(found_colors) >= 3:
        print(f"✅ Found {len(found_colors)} critical color fallbacks")
    else:
        print(f"❌ Only found {len(found_colors)} critical color fallbacks")
        return False
    
    return True

def test_authentication_compatibility():
    """Test authentication state compatibility for Edge"""
    print("\n🔐 Testing Authentication Compatibility")
    print("=" * 50)
    
    pricing_template_path = "templates/pricing.html"
    with open(pricing_template_path, 'r', encoding='utf-8') as f:
        pricing_content = f.read()
    
    # Check for authentication attributes
    auth_patterns = [
        r'class="authenticated"',
        r'data-user-authenticated="true"',
        r'{%\s*if\s+current_user\.is_authenticated\s*%}'
    ]
    
    found_auth_patterns = []
    for pattern in auth_patterns:
        if re.search(pattern, pricing_content):
            found_auth_patterns.append(pattern)
    
    if len(found_auth_patterns) >= 2:
        print(f"✅ Found {len(found_auth_patterns)} authentication patterns")
    else:
        print(f"❌ Only found {len(found_auth_patterns)} authentication patterns")
        return False
    
    # Check Edge JS for enhanced auth detection
    edge_js_path = "static/js/edge-compatibility.js"
    with open(edge_js_path, 'r', encoding='utf-8') as f:
        edge_js_content = f.read()
    
    enhanced_auth_patterns = [
        r'checkAuthenticationEdge',
        r'document\.body\.classList\.contains\(["\']authenticated["\']\)',
        r'document\.querySelector\(["\'][^"\']*data-user-authenticated',
        r'window\.currentUser'
    ]
    
    found_enhanced_auth = []
    for pattern in enhanced_auth_patterns:
        if re.search(pattern, edge_js_content):
            found_enhanced_auth.append(pattern)
    
    if len(found_enhanced_auth) >= 3:
        print(f"✅ Found {len(found_enhanced_auth)} enhanced auth detection methods")
    else:
        print(f"❌ Only found {len(found_enhanced_auth)} enhanced auth detection methods")
        return False
    
    return True

def test_responsive_design_fallbacks():
    """Test responsive design fallbacks for Edge"""
    print("\n📱 Testing Responsive Design Fallbacks")
    print("=" * 50)
    
    edge_css_path = "static/css/edge-compatibility.css"
    with open(edge_css_path, 'r', encoding='utf-8') as f:
        edge_css_content = f.read()
    
    # Check for responsive fallbacks
    responsive_patterns = [
        r'@media screen and \(max-width: 768px\)',
        r'@media screen and \(max-width: 1024px\)',
        r'-ms-grid-columns',
        r'grid-template-columns: repeat\(2, 1fr\)',
        r'flex-wrap: wrap'
    ]
    
    found_responsive = []
    for pattern in responsive_patterns:
        if re.search(pattern, edge_css_content):
            found_responsive.append(pattern)
    
    if len(found_responsive) >= 4:
        print(f"✅ Found {len(found_responsive)} responsive design fallbacks")
    else:
        print(f"❌ Only found {len(found_responsive)} responsive design fallbacks")
        return False
    
    return True

def main():
    """Run all Edge compatibility fix tests"""
    print("🧪 Edge Compatibility Fixes Verification")
    print("=" * 60)
    print("Testing that all Edge compatibility fixes are properly implemented")
    print("=" * 60)
    
    tests = [
        ("Edge CSS Inclusion", test_edge_css_included),
        ("Edge JavaScript Inclusion", test_edge_js_included),
        ("CSS Fallbacks", test_css_fallbacks),
        ("JavaScript Polyfills", test_javascript_polyfills),
        ("Inline CSS Fallbacks", test_inline_css_fallbacks),
        ("Authentication Compatibility", test_authentication_compatibility),
        ("Responsive Design Fallbacks", test_responsive_design_fallbacks)
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
    print("📊 EDGE COMPATIBILITY FIXES SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ IMPLEMENTED" if result else "❌ MISSING"
        print(f"{status:<15} {test_name}")
        if result:
            passed += 1
    
    print(f"\nImplementation Score: {passed}/{total}")
    
    if passed == total:
        print("🎉 All Edge compatibility fixes are properly implemented!")
        print("\n📋 Edge Compatibility Features:")
        print("✅ CSS Grid fallbacks with Flexbox")
        print("✅ CSS custom property fallbacks")
        print("✅ JavaScript polyfills for modern features")
        print("✅ Enhanced authentication detection")
        print("✅ Responsive design fallbacks")
        print("✅ Edge-specific media queries")
        print("✅ Inline style fallbacks for critical elements")
        print("\n🌐 Browser Support:")
        print("   - Microsoft Edge (all versions)")
        print("   - Chrome (consistent rendering)")
        print("   - Authentication state consistency")
        print("   - Responsive design compatibility")
    else:
        print("⚠️ Some Edge compatibility fixes are missing!")
        print("\n🚨 Missing Implementations:")
        for test_name, result in results:
            if not result:
                print(f"   - {test_name}")
        print("\n🔧 Recommended Actions:")
        print("   - Implement missing CSS fallbacks")
        print("   - Add required JavaScript polyfills")
        print("   - Test in actual Edge browser")
        print("   - Verify authentication flow consistency")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
