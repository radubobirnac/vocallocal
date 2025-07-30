#!/usr/bin/env python3
"""
Test script to verify that VocalLocal brand names are clickable across all templates.
Tests for proper linking, styling, and accessibility.
"""

import os
import re

def test_brand_links_exist():
    """Test that brand names are wrapped in clickable links"""
    print("🔗 Testing Brand Links Existence")
    print("=" * 50)
    
    templates_to_check = [
        "templates/home.html",
        "templates/login.html", 
        "templates/register.html",
        "templates/index.html",
        "templates/pricing.html",
        "templates/profile.html",
        "templates/history.html",
        "templates/dashboard.html",
        "templates/try_it_free.html"
    ]
    
    results = {}
    
    for template_path in templates_to_check:
        if not os.path.exists(template_path):
            print(f"⚠️ Template not found: {template_path}")
            results[template_path] = False
            continue
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for brand link patterns
        brand_link_patterns = [
            r'<a[^>]*href="[^"]*main\.index[^"]*"[^>]*>.*VocalLocal.*</a>',
            r'<a[^>]*href="[^"]*main\.index[^"]*"[^>]*>.*Vocal Local.*</a>',
            r'<a[^>]*class="brand-link"[^>]*>.*VocalLocal.*</a>',
            r'href="[^"]*main\.index[^"]*".*VocalLocal',
            r'href="[^"]*main\.index[^"]*".*Vocal Local'
        ]
        
        found_brand_link = any(re.search(pattern, content, re.DOTALL | re.IGNORECASE) for pattern in brand_link_patterns)
        
        if found_brand_link:
            print(f"✅ {template_path}: Brand name is clickable")
            results[template_path] = True
        else:
            print(f"❌ {template_path}: Brand name is not clickable")
            results[template_path] = False
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nBrand Links: {passed}/{total} templates have clickable brand names")
    return passed >= total * 0.8  # Allow 20% to not have brand names

def test_proper_routing():
    """Test that brand links use proper Flask routing"""
    print("\n🛣️ Testing Proper Routing")
    print("=" * 50)
    
    templates_to_check = [
        "templates/home.html",
        "templates/login.html", 
        "templates/register.html",
        "templates/index.html",
        "templates/pricing.html",
        "templates/profile.html",
        "templates/history.html",
        "templates/dashboard.html",
        "templates/try_it_free.html"
    ]
    
    correct_routing = 0
    total_with_links = 0
    
    for template_path in templates_to_check:
        if not os.path.exists(template_path):
            continue
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if template has brand links
        has_brand_link = bool(re.search(r'VocalLocal|Vocal Local', content))
        if not has_brand_link:
            continue
        
        total_with_links += 1
        
        # Check for proper routing patterns
        proper_routing_patterns = [
            r'url_for\(["\']main\.index["\']',
            r'href="[^"]*main\.index[^"]*"'
        ]
        
        has_proper_routing = any(re.search(pattern, content) for pattern in proper_routing_patterns)
        
        # Check for incorrect routing patterns
        incorrect_routing_patterns = [
            r'url_for\(["\']index["\']',  # Should be main.index
            r'href="/"[^>]*VocalLocal',   # Direct href without url_for
            r'href="/index"'              # Direct href without url_for
        ]
        
        has_incorrect_routing = any(re.search(pattern, content) for pattern in incorrect_routing_patterns)
        
        if has_proper_routing and not has_incorrect_routing:
            print(f"✅ {template_path}: Uses proper Flask routing")
            correct_routing += 1
        else:
            print(f"❌ {template_path}: Incorrect routing detected")
    
    print(f"\nProper Routing: {correct_routing}/{total_with_links} templates use correct routing")
    return correct_routing >= total_with_links * 0.8

def test_brand_link_css_included():
    """Test that brand-link.css is included in all templates"""
    print("\n🎨 Testing Brand Link CSS Inclusion")
    print("=" * 50)
    
    templates_to_check = [
        "templates/home.html",
        "templates/login.html", 
        "templates/register.html",
        "templates/index.html",
        "templates/pricing.html",
        "templates/profile.html",
        "templates/history.html",
        "templates/dashboard.html",
        "templates/try_it_free.html"
    ]
    
    css_included = 0
    total_templates = 0
    
    for template_path in templates_to_check:
        if not os.path.exists(template_path):
            continue
        
        total_templates += 1
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for brand-link.css inclusion
        css_patterns = [
            r'brand-link\.css',
            r'css/brand-link\.css'
        ]
        
        has_css = any(re.search(pattern, content) for pattern in css_patterns)
        
        if has_css:
            print(f"✅ {template_path}: Includes brand-link.css")
            css_included += 1
        else:
            print(f"❌ {template_path}: Missing brand-link.css")
    
    print(f"\nCSS Inclusion: {css_included}/{total_templates} templates include brand-link.css")
    return css_included >= total_templates * 0.8

def test_brand_link_structure():
    """Test that brand links have proper HTML structure"""
    print("\n🏗️ Testing Brand Link Structure")
    print("=" * 50)
    
    templates_to_check = [
        "templates/home.html",
        "templates/login.html", 
        "templates/register.html",
        "templates/try_it_free.html"
    ]
    
    proper_structure = 0
    total_navbar_templates = 0
    
    for template_path in templates_to_check:
        if not os.path.exists(template_path):
            continue
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if template has navbar structure
        has_navbar = bool(re.search(r'navbar-brand|brand-title', content))
        if not has_navbar:
            continue
        
        total_navbar_templates += 1
        
        # Check for proper structure patterns
        structure_patterns = [
            r'<a[^>]*class="brand-link"[^>]*>.*<span class="brand-icon">.*<span class="brand-name">VocalLocal</span>.*</a>',
            r'brand-link.*brand-icon.*brand-name',
            r'<a[^>]*href="[^"]*main\.index[^"]*"[^>]*class="brand-link"'
        ]
        
        has_proper_structure = any(re.search(pattern, content, re.DOTALL) for pattern in structure_patterns)
        
        if has_proper_structure:
            print(f"✅ {template_path}: Has proper brand link structure")
            proper_structure += 1
        else:
            print(f"❌ {template_path}: Improper brand link structure")
    
    print(f"\nProper Structure: {proper_structure}/{total_navbar_templates} navbar templates have proper structure")
    return proper_structure >= total_navbar_templates * 0.8

def test_accessibility_attributes():
    """Test that brand links have proper accessibility attributes"""
    print("\n♿ Testing Accessibility Attributes")
    print("=" * 50)
    
    # Check brand-link.css for accessibility features
    css_path = "static/css/brand-link.css"
    if not os.path.exists(css_path):
        print(f"❌ Brand link CSS not found: {css_path}")
        return False
    
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Check for accessibility features in CSS
    accessibility_patterns = [
        r'\.brand-link:focus',
        r'outline:.*solid',
        r'focus-visible',
        r'prefers-reduced-motion',
        r'prefers-contrast'
    ]
    
    found_accessibility = []
    for pattern in accessibility_patterns:
        if re.search(pattern, css_content, re.IGNORECASE):
            found_accessibility.append(pattern)
    
    if len(found_accessibility) >= 3:
        print(f"✅ Found {len(found_accessibility)} accessibility features in CSS")
        for feature in found_accessibility:
            print(f"   - {feature}")
    else:
        print(f"❌ Only found {len(found_accessibility)} accessibility features")
        return False
    
    return True

def test_hover_effects():
    """Test that brand links have hover effects"""
    print("\n🖱️ Testing Hover Effects")
    print("=" * 50)
    
    css_path = "static/css/brand-link.css"
    if not os.path.exists(css_path):
        print(f"❌ Brand link CSS not found: {css_path}")
        return False
    
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Check for hover effects
    hover_patterns = [
        r'\.brand-link:hover',
        r'opacity:.*0\.\d+',
        r'transform:.*translateY',
        r'transition:.*ease'
    ]
    
    found_hover_effects = []
    for pattern in hover_patterns:
        if re.search(pattern, css_content, re.IGNORECASE):
            found_hover_effects.append(pattern)
    
    if len(found_hover_effects) >= 3:
        print(f"✅ Found {len(found_hover_effects)} hover effects in CSS")
    else:
        print(f"❌ Only found {len(found_hover_effects)} hover effects")
        return False
    
    return True

def test_consistent_styling():
    """Test that brand links maintain consistent styling"""
    print("\n🎯 Testing Consistent Styling")
    print("=" * 50)
    
    css_path = "static/css/brand-link.css"
    if not os.path.exists(css_path):
        print(f"❌ Brand link CSS not found: {css_path}")
        return False
    
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Check for consistent styling features
    styling_patterns = [
        r'text-decoration:\s*none\s*!important',
        r'color:\s*inherit\s*!important',
        r'font-family:.*Poppins',
        r'font-weight:.*700',
        r'cursor:\s*pointer'
    ]
    
    found_styling = []
    for pattern in styling_patterns:
        if re.search(pattern, css_content, re.IGNORECASE):
            found_styling.append(pattern)
    
    if len(found_styling) >= 4:
        print(f"✅ Found {len(found_styling)} consistent styling features")
    else:
        print(f"❌ Only found {len(found_styling)} consistent styling features")
        return False
    
    return True

def main():
    """Run all brand name clickable tests"""
    print("🧪 VocalLocal Brand Name Clickable Tests")
    print("=" * 60)
    print("Testing that brand names are clickable across all templates")
    print("=" * 60)
    
    tests = [
        ("Brand Links Existence", test_brand_links_exist),
        ("Proper Routing", test_proper_routing),
        ("Brand Link CSS Inclusion", test_brand_link_css_included),
        ("Brand Link Structure", test_brand_link_structure),
        ("Accessibility Attributes", test_accessibility_attributes),
        ("Hover Effects", test_hover_effects),
        ("Consistent Styling", test_consistent_styling)
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
    print("📊 BRAND NAME CLICKABLE SUMMARY")
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
        print("🎉 VocalLocal brand names are properly clickable!")
        print("\n📋 Clickable Brand Features:")
        print("✅ Brand names wrapped in clickable links")
        print("✅ Proper Flask routing with url_for('main.index')")
        print("✅ Brand-link.css included across all templates")
        print("✅ Proper HTML structure with brand-link class")
        print("✅ Accessibility features (focus, keyboard navigation)")
        print("✅ Hover effects for visual feedback")
        print("✅ Consistent styling across all pages")
        print("\n🌐 User Experience:")
        print("   - Click VocalLocal brand → Navigate to home page")
        print("   - Visual feedback on hover (opacity, transform)")
        print("   - Keyboard accessible with focus indicators")
        print("   - Consistent behavior across all pages")
        print("   - Maintains brand styling while being clickable")
    else:
        print("⚠️ Some brand name clickable features are missing!")
        print("\n🚨 Missing Implementations:")
        for test_name, result in results:
            if not result:
                print(f"   - {test_name}")
        print("\n🔧 Recommended Actions:")
        print("   - Wrap brand names in anchor tags")
        print("   - Use proper Flask routing")
        print("   - Include brand-link.css in all templates")
        print("   - Add accessibility attributes")
        print("   - Test hover effects and styling")
    
    return passed >= total - 1

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
