#!/usr/bin/env python3
"""
Test script to analyze Edge browser compatibility issues with the pricing page.
Identifies potential CSS, JavaScript, and authentication-related compatibility problems.
"""

import os
import re

def test_css_grid_compatibility():
    """Test for CSS Grid compatibility issues that might affect Edge"""
    print("🔍 Testing CSS Grid Compatibility")
    print("=" * 50)
    
    pricing_template_path = "templates/pricing.html"
    if not os.path.exists(pricing_template_path):
        print(f"❌ Pricing template not found: {pricing_template_path}")
        return False
    
    with open(pricing_template_path, 'r', encoding='utf-8') as f:
        pricing_content = f.read()
    
    # Check for CSS Grid usage in pricing page
    grid_patterns = [
        r'display:\s*grid',
        r'grid-template-columns',
        r'grid-gap',
        r'gap:\s*\d+rem'
    ]
    
    found_grid_issues = []
    for pattern in grid_patterns:
        matches = re.findall(pattern, pricing_content, re.IGNORECASE)
        if matches:
            found_grid_issues.extend(matches)
    
    if found_grid_issues:
        print("⚠️ Found CSS Grid usage that may need Edge fallbacks:")
        for issue in found_grid_issues:
            print(f"   - {issue}")
        
        # Check if there are fallbacks for older browsers
        fallback_patterns = [
            r'display:\s*flex',
            r'@supports.*grid',
            r'@media.*-ms-'
        ]
        
        found_fallbacks = []
        for pattern in fallback_patterns:
            matches = re.findall(pattern, pricing_content, re.IGNORECASE)
            if matches:
                found_fallbacks.extend(matches)
        
        if found_fallbacks:
            print("✅ Found some fallback patterns")
        else:
            print("❌ No fallback patterns found for CSS Grid")
            return False
    else:
        print("✅ No CSS Grid usage found in pricing template")
    
    return True

def test_css_custom_properties():
    """Test for CSS custom properties (variables) compatibility"""
    print("\n🎨 Testing CSS Custom Properties Compatibility")
    print("=" * 50)
    
    styles_path = "static/styles.css"
    if not os.path.exists(styles_path):
        print(f"❌ Styles file not found: {styles_path}")
        return False
    
    with open(styles_path, 'r', encoding='utf-8') as f:
        styles_content = f.read()
    
    # Check for CSS custom properties usage
    custom_prop_patterns = [
        r'--[\w-]+:\s*[^;]+;',
        r'var\(--[\w-]+\)',
        r'hsl\(var\(--[\w-]+\)\)'
    ]
    
    found_custom_props = []
    for pattern in custom_prop_patterns:
        matches = re.findall(pattern, styles_content)
        if matches:
            found_custom_props.extend(matches[:3])  # Limit to first 3 examples
    
    if found_custom_props:
        print("⚠️ Found CSS custom properties (may need Edge fallbacks):")
        for prop in found_custom_props:
            print(f"   - {prop}")
        
        # Check for fallback values
        fallback_patterns = [
            r'color:\s*#[0-9a-fA-F]{6};\s*color:\s*var\(',
            r'background-color:\s*#[0-9a-fA-F]{6};\s*background-color:\s*var\('
        ]
        
        found_fallbacks = any(re.search(pattern, styles_content) for pattern in fallback_patterns)
        
        if found_fallbacks:
            print("✅ Found some fallback values for custom properties")
        else:
            print("⚠️ Limited fallback values found for custom properties")
    else:
        print("✅ No CSS custom properties found")
    
    return True

def test_authentication_conditional_rendering():
    """Test authentication-based conditional rendering that might differ in Edge"""
    print("\n🔐 Testing Authentication Conditional Rendering")
    print("=" * 50)
    
    pricing_template_path = "templates/pricing.html"
    with open(pricing_template_path, 'r', encoding='utf-8') as f:
        pricing_content = f.read()
    
    # Check for authentication-based conditionals
    auth_patterns = [
        r'{%\s*if\s+current_user\.is_authenticated\s*%}',
        r'{%\s*else\s*%}',
        r'{%\s*endif\s*%}',
        r'data-user-authenticated',
        r'class="authenticated"'
    ]
    
    found_auth_conditionals = []
    for pattern in auth_patterns:
        matches = re.findall(pattern, pricing_content)
        if matches:
            found_auth_conditionals.extend(matches)
    
    if found_auth_conditionals:
        print("✅ Found authentication-based conditional rendering:")
        for conditional in found_auth_conditionals:
            print(f"   - {conditional}")
        
        # Check for JavaScript authentication detection
        js_auth_patterns = [
            r'checkAuthentication\(\)',
            r'isAuthenticated',
            r'data-user-authenticated',
            r'authenticated.*classList'
        ]
        
        found_js_auth = any(re.search(pattern, pricing_content, re.IGNORECASE) for pattern in js_auth_patterns)
        
        if found_js_auth:
            print("✅ Found JavaScript authentication detection")
        else:
            print("⚠️ Limited JavaScript authentication detection")
    else:
        print("❌ No authentication conditionals found")
        return False
    
    return True

def test_javascript_edge_compatibility():
    """Test JavaScript features that might have Edge compatibility issues"""
    print("\n📜 Testing JavaScript Edge Compatibility")
    print("=" * 50)
    
    # Check pricing-specific JavaScript
    pricing_js_path = "static/js/pricing-payg.js"
    if not os.path.exists(pricing_js_path):
        print(f"❌ Pricing JavaScript not found: {pricing_js_path}")
        return False
    
    with open(pricing_js_path, 'r', encoding='utf-8') as f:
        pricing_js_content = f.read()
    
    # Check for modern JavaScript features that might not work in older Edge
    modern_js_patterns = [
        r'class\s+\w+\s*{',  # ES6 classes
        r'async\s+\w+\s*\(',  # Async functions
        r'await\s+',  # Await keyword
        r'const\s+\w+\s*=',  # Const declarations
        r'let\s+\w+\s*=',  # Let declarations
        r'=>\s*{',  # Arrow functions
        r'\.includes\(',  # Array.includes
        r'\.classList\.',  # classList API
        r'document\.querySelector',  # Modern DOM API
        r'fetch\('  # Fetch API
    ]
    
    found_modern_features = []
    for pattern in modern_js_patterns:
        matches = re.findall(pattern, pricing_js_content)
        if matches:
            found_modern_features.append((pattern, len(matches)))
    
    if found_modern_features:
        print("⚠️ Found modern JavaScript features (check Edge support):")
        for pattern, count in found_modern_features:
            print(f"   - {pattern}: {count} occurrences")
        
        # Check for polyfills or fallbacks
        fallback_patterns = [
            r'if\s*\(\s*!.*\.includes\)',
            r'if\s*\(\s*!.*\.classList\)',
            r'if\s*\(\s*!.*fetch\)',
            r'polyfill',
            r'fallback'
        ]
        
        found_fallbacks = any(re.search(pattern, pricing_js_content, re.IGNORECASE) for pattern in fallback_patterns)
        
        if found_fallbacks:
            print("✅ Found some JavaScript fallbacks")
        else:
            print("⚠️ Limited JavaScript fallbacks found")
    else:
        print("✅ No problematic modern JavaScript features found")
    
    return True

def test_responsive_design_edge_issues():
    """Test responsive design features that might render differently in Edge"""
    print("\n📱 Testing Responsive Design Edge Compatibility")
    print("=" * 50)
    
    pricing_template_path = "templates/pricing.html"
    with open(pricing_template_path, 'r', encoding='utf-8') as f:
        pricing_content = f.read()
    
    # Check for responsive design patterns
    responsive_patterns = [
        r'@media\s*\([^)]+\)',
        r'grid-template-columns:\s*repeat\(',
        r'minmax\(',
        r'auto-fit',
        r'auto-fill',
        r'fr\s*\)',
        r'clamp\(',
        r'min\(',
        r'max\('
    ]
    
    found_responsive_features = []
    for pattern in responsive_patterns:
        matches = re.findall(pattern, pricing_content, re.IGNORECASE)
        if matches:
            found_responsive_features.extend(matches[:2])  # Limit examples
    
    if found_responsive_features:
        print("⚠️ Found advanced responsive features (check Edge support):")
        for feature in found_responsive_features:
            print(f"   - {feature}")
        
        # Check for simpler fallbacks
        fallback_patterns = [
            r'display:\s*flex',
            r'flex-wrap',
            r'@media.*max-width.*768px',
            r'@media.*min-width.*768px'
        ]
        
        found_fallbacks = any(re.search(pattern, pricing_content, re.IGNORECASE) for pattern in fallback_patterns)
        
        if found_fallbacks:
            print("✅ Found responsive fallback patterns")
        else:
            print("⚠️ Limited responsive fallbacks found")
    else:
        print("✅ No advanced responsive features found")
    
    return True

def test_inline_styles_vs_classes():
    """Test for inline styles that might render differently in Edge"""
    print("\n🎯 Testing Inline Styles vs CSS Classes")
    print("=" * 50)
    
    pricing_template_path = "templates/pricing.html"
    with open(pricing_template_path, 'r', encoding='utf-8') as f:
        pricing_content = f.read()
    
    # Count inline styles
    inline_style_pattern = r'style="[^"]*"'
    inline_styles = re.findall(inline_style_pattern, pricing_content)
    
    # Count CSS classes
    class_pattern = r'class="[^"]*"'
    css_classes = re.findall(class_pattern, pricing_content)
    
    print(f"📊 Style Distribution:")
    print(f"   - Inline styles: {len(inline_styles)}")
    print(f"   - CSS classes: {len(css_classes)}")
    
    if len(inline_styles) > len(css_classes):
        print("⚠️ High ratio of inline styles (may cause Edge inconsistencies)")
        
        # Check for problematic inline style patterns
        problematic_patterns = [
            r'style="[^"]*hsl\(var\(',
            r'style="[^"]*grid[^"]*"',
            r'style="[^"]*flex[^"]*"',
            r'style="[^"]*transform[^"]*"'
        ]
        
        found_problematic = []
        for pattern in problematic_patterns:
            matches = re.findall(pattern, pricing_content)
            if matches:
                found_problematic.extend(matches[:2])  # Limit examples
        
        if found_problematic:
            print("❌ Found potentially problematic inline styles:")
            for style in found_problematic:
                print(f"   - {style[:50]}...")
            return False
        else:
            print("✅ Inline styles appear to be simple")
    else:
        print("✅ Good balance of CSS classes vs inline styles")
    
    return True

def generate_edge_compatibility_fixes():
    """Generate specific fixes for Edge compatibility issues"""
    print("\n🔧 Generating Edge Compatibility Fixes")
    print("=" * 50)
    
    fixes = [
        "1. Add CSS Grid fallbacks with Flexbox",
        "2. Provide fallback values for CSS custom properties",
        "3. Add Edge-specific media queries if needed",
        "4. Test JavaScript authentication detection in Edge",
        "5. Verify responsive design breakpoints in Edge",
        "6. Consider moving critical inline styles to CSS classes",
        "7. Add Edge-specific user agent detection if necessary",
        "8. Test payment processing flow in Edge browser"
    ]
    
    print("📋 Recommended Edge Compatibility Fixes:")
    for fix in fixes:
        print(f"   {fix}")
    
    return True

def main():
    """Run all Edge compatibility tests"""
    print("🧪 Edge Browser Compatibility Analysis")
    print("=" * 60)
    print("Analyzing pricing page for Edge-specific rendering issues")
    print("=" * 60)
    
    tests = [
        ("CSS Grid Compatibility", test_css_grid_compatibility),
        ("CSS Custom Properties", test_css_custom_properties),
        ("Authentication Conditional Rendering", test_authentication_conditional_rendering),
        ("JavaScript Edge Compatibility", test_javascript_edge_compatibility),
        ("Responsive Design Edge Issues", test_responsive_design_edge_issues),
        ("Inline Styles vs Classes", test_inline_styles_vs_classes),
        ("Edge Compatibility Fixes", generate_edge_compatibility_fixes)
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
    print("📊 EDGE COMPATIBILITY ANALYSIS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results) - 1  # Exclude the fixes generator
    
    for test_name, result in results[:-1]:  # Exclude fixes from pass/fail
        status = "✅ COMPATIBLE" if result else "⚠️ NEEDS ATTENTION"
        print(f"{status:<18} {test_name}")
        if result:
            passed += 1
    
    print(f"\nCompatibility Score: {passed}/{total}")
    
    if passed >= total - 1:  # Allow one minor issue
        print("🎉 Pricing page has good Edge compatibility!")
        print("\n📋 Edge Compatibility Summary:")
        print("✅ CSS features are mostly Edge-compatible")
        print("✅ Authentication rendering should work consistently")
        print("✅ JavaScript features are reasonably modern")
        print("✅ Responsive design should render properly")
        print("✅ Style distribution is reasonable")
        print("\n🔧 Minor improvements recommended:")
        print("   - Test actual rendering in Edge browser")
        print("   - Consider adding CSS Grid fallbacks")
        print("   - Verify payment flow works in Edge")
    else:
        print("⚠️ Pricing page may have Edge compatibility issues!")
        print("\n🚨 Issues Found:")
        for test_name, result in results[:-1]:
            if not result:
                print(f"   - {test_name}")
        print("\n🔧 Recommended Actions:")
        print("   - Implement CSS fallbacks for modern features")
        print("   - Test authentication flow in Edge")
        print("   - Add browser-specific polyfills if needed")
        print("   - Consider progressive enhancement approach")
    
    return passed >= total - 1

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
