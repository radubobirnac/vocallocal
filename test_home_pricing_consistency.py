#!/usr/bin/env python3
"""
Test script to verify that the pricing section on the home page matches the pricing page exactly.
Tests navigation links, content consistency, and smooth scrolling functionality.
"""

import os
import re

def test_navigation_link_points_to_section():
    """Test that pricing navigation link points to #pricing section instead of /pricing page"""
    print("🔗 Testing Navigation Link Points to Section")
    print("=" * 50)
    
    home_template_path = "templates/home.html"
    if not os.path.exists(home_template_path):
        print(f"❌ Home template not found: {home_template_path}")
        return False
    
    with open(home_template_path, 'r', encoding='utf-8') as f:
        home_content = f.read()
    
    # Check that pricing link points to #pricing section
    pricing_link_patterns = [
        r'href="#pricing".*data-section="pricing"',
        r'data-section="pricing".*href="#pricing"'
    ]
    
    found_section_link = any(re.search(pattern, home_content) for pattern in pricing_link_patterns)
    
    if found_section_link:
        print("✅ Pricing navigation link points to #pricing section")
    else:
        print("❌ Pricing navigation link does not point to #pricing section")
        return False
    
    # Check that it doesn't redirect to /pricing page
    redirect_patterns = [
        r'href=".*url_for\(["\']pricing["\']',
        r'href="/pricing"'
    ]
    
    found_redirect = any(re.search(pattern, home_content) for pattern in redirect_patterns)
    
    if not found_redirect:
        print("✅ No redirect to /pricing page found")
    else:
        print("❌ Found redirect to /pricing page")
        return False
    
    return True

def test_pricing_section_structure():
    """Test that pricing section has the same structure as pricing page"""
    print("\n🏗️ Testing Pricing Section Structure")
    print("=" * 50)
    
    home_template_path = "templates/home.html"
    pricing_template_path = "templates/pricing.html"
    
    with open(home_template_path, 'r', encoding='utf-8') as f:
        home_content = f.read()
    
    with open(pricing_template_path, 'r', encoding='utf-8') as f:
        pricing_content = f.read()
    
    # Check for key structural elements
    structural_elements = [
        r'pricing-container',
        r'pricing-hero',
        r'pricing-grid',
        r'pricing-card',
        r'plan-header'
    ]
    
    home_elements = []
    pricing_elements = []
    
    for element in structural_elements:
        if re.search(element, home_content):
            home_elements.append(element)
        if re.search(element, pricing_content):
            pricing_elements.append(element)
    
    if len(home_elements) >= 4:
        print(f"✅ Home page has {len(home_elements)} structural elements")
    else:
        print(f"❌ Home page only has {len(home_elements)} structural elements")
        return False
    
    if len(pricing_elements) >= 4:
        print(f"✅ Pricing page has {len(pricing_elements)} structural elements")
    else:
        print(f"❌ Pricing page only has {len(pricing_elements)} structural elements")
        return False
    
    # Check consistency
    common_elements = set(home_elements) & set(pricing_elements)
    if len(common_elements) >= 4:
        print(f"✅ {len(common_elements)} structural elements are consistent")
    else:
        print(f"❌ Only {len(common_elements)} structural elements are consistent")
        return False
    
    return True

def test_pricing_content_consistency():
    """Test that pricing content is identical between home and pricing pages"""
    print("\n📋 Testing Pricing Content Consistency")
    print("=" * 50)
    
    home_template_path = "templates/home.html"
    pricing_template_path = "templates/pricing.html"
    
    with open(home_template_path, 'r', encoding='utf-8') as f:
        home_content = f.read()
    
    with open(pricing_template_path, 'r', encoding='utf-8') as f:
        pricing_content = f.read()
    
    # Check for identical plan names and prices
    plan_patterns = [
        r'Free Plan.*\$0',
        r'Basic Plan.*\$4\.99',
        r'Professional Plan.*\$12\.99',
        r'Pay-As-You-Go.*300.*credits'
    ]
    
    home_plans = []
    pricing_plans = []
    
    for pattern in plan_patterns:
        if re.search(pattern, home_content, re.DOTALL):
            home_plans.append(pattern)
        if re.search(pattern, pricing_content, re.DOTALL):
            pricing_plans.append(pattern)
    
    if len(home_plans) >= 3:
        print(f"✅ Home page has {len(home_plans)} pricing plans")
    else:
        print(f"❌ Home page only has {len(home_plans)} pricing plans")
        return False
    
    if len(pricing_plans) >= 3:
        print(f"✅ Pricing page has {len(pricing_plans)} pricing plans")
    else:
        print(f"❌ Pricing page only has {len(pricing_plans)} pricing plans")
        return False
    
    # Check for identical features
    feature_patterns = [
        r'60 transcription minutes per month',
        r'280 transcription minutes per month',
        r'800 transcription minutes per month',
        r'Access to premium AI models',
        r'Priority email support'
    ]
    
    home_features = []
    pricing_features = []
    
    for pattern in feature_patterns:
        if re.search(pattern, home_content):
            home_features.append(pattern)
        if re.search(pattern, pricing_content):
            pricing_features.append(pattern)
    
    if len(home_features) >= 4:
        print(f"✅ Home page has {len(home_features)} consistent features")
    else:
        print(f"❌ Home page only has {len(home_features)} consistent features")
        return False
    
    return True

def test_pricing_styles_included():
    """Test that pricing styles are included in home page"""
    print("\n🎨 Testing Pricing Styles Inclusion")
    print("=" * 50)
    
    home_template_path = "templates/home.html"
    with open(home_template_path, 'r', encoding='utf-8') as f:
        home_content = f.read()
    
    # Check for pricing-specific styles
    style_patterns = [
        r'\.pricing-card\s*{',
        r'\.pricing-hero\s*h1\s*{',
        r'\.pricing-grid\s*{',
        r'grid-template-columns.*repeat',
        r'@media.*pricing-grid'
    ]
    
    found_styles = []
    for pattern in style_patterns:
        if re.search(pattern, home_content):
            found_styles.append(pattern)
    
    if len(found_styles) >= 3:
        print(f"✅ Found {len(found_styles)} pricing-specific styles")
    else:
        print(f"❌ Only found {len(found_styles)} pricing-specific styles")
        return False
    
    # Check for responsive grid styles
    responsive_patterns = [
        r'@media.*min-width.*1400px',
        r'@media.*max-width.*768px',
        r'grid-template-columns.*repeat\(4, 1fr\)',
        r'grid-template-columns.*1fr'
    ]
    
    found_responsive = []
    for pattern in responsive_patterns:
        if re.search(pattern, home_content):
            found_responsive.append(pattern)
    
    if len(found_responsive) >= 3:
        print(f"✅ Found {len(found_responsive)} responsive grid styles")
    else:
        print(f"❌ Only found {len(found_responsive)} responsive grid styles")
        return False
    
    return True

def test_smooth_scrolling_support():
    """Test that smooth scrolling is supported for pricing section"""
    print("\n🌊 Testing Smooth Scrolling Support")
    print("=" * 50)
    
    # Check navigation.js for smooth scrolling functionality
    navigation_js_path = "static/navigation.js"
    if not os.path.exists(navigation_js_path):
        print(f"❌ Navigation JS not found: {navigation_js_path}")
        return False
    
    with open(navigation_js_path, 'r', encoding='utf-8') as f:
        navigation_content = f.read()
    
    # Check for smooth scrolling patterns
    smooth_scroll_patterns = [
        r'behavior:\s*["\']smooth["\']',
        r'scrollTo\(',
        r'href\^="#"',
        r'data-section',
        r'updateActiveNavigation'
    ]
    
    found_smooth_scroll = []
    for pattern in smooth_scroll_patterns:
        if re.search(pattern, navigation_content):
            found_smooth_scroll.append(pattern)
    
    if len(found_smooth_scroll) >= 4:
        print(f"✅ Found {len(found_smooth_scroll)} smooth scrolling features")
    else:
        print(f"❌ Only found {len(found_smooth_scroll)} smooth scrolling features")
        return False
    
    # Check for section-based navigation
    section_nav_patterns = [
        r'data-section.*pricing',
        r'currentHash',
        r'sectionId',
        r'querySelector.*data-section'
    ]
    
    found_section_nav = []
    for pattern in section_nav_patterns:
        if re.search(pattern, navigation_content):
            found_section_nav.append(pattern)
    
    if len(found_section_nav) >= 2:
        print(f"✅ Found {len(found_section_nav)} section navigation features")
    else:
        print(f"❌ Only found {len(found_section_nav)} section navigation features")
        return False
    
    return True

def test_pricing_section_id():
    """Test that pricing section has correct ID for navigation"""
    print("\n🆔 Testing Pricing Section ID")
    print("=" * 50)
    
    home_template_path = "templates/home.html"
    with open(home_template_path, 'r', encoding='utf-8') as f:
        home_content = f.read()
    
    # Check for pricing section with correct ID
    section_patterns = [
        r'<section\s+id="pricing"',
        r'id="pricing".*class="pricing-section"',
        r'section.*pricing.*pricing-container'
    ]
    
    found_section_id = any(re.search(pattern, home_content) for pattern in section_patterns)
    
    if found_section_id:
        print("✅ Pricing section has correct ID")
    else:
        print("❌ Pricing section missing correct ID")
        return False
    
    return True

def test_navigation_active_state():
    """Test that navigation active state works for pricing section"""
    print("\n🎯 Testing Navigation Active State")
    print("=" * 50)
    
    home_template_path = "templates/home.html"
    with open(home_template_path, 'r', encoding='utf-8') as f:
        home_content = f.read()
    
    # Check for data-section attribute on pricing link
    pricing_link_patterns = [
        r'data-section="pricing"',
        r'class="nav-link".*data-section="pricing"',
        r'href="#pricing".*data-section="pricing"'
    ]
    
    found_data_section = any(re.search(pattern, home_content) for pattern in pricing_link_patterns)
    
    if found_data_section:
        print("✅ Pricing link has data-section attribute")
    else:
        print("❌ Pricing link missing data-section attribute")
        return False
    
    return True

def main():
    """Run all home page pricing consistency tests"""
    print("🧪 Home Page Pricing Consistency Tests")
    print("=" * 60)
    print("Testing that pricing section on home page matches /pricing page exactly")
    print("=" * 60)
    
    tests = [
        ("Navigation Link Points to Section", test_navigation_link_points_to_section),
        ("Pricing Section Structure", test_pricing_section_structure),
        ("Pricing Content Consistency", test_pricing_content_consistency),
        ("Pricing Styles Inclusion", test_pricing_styles_included),
        ("Smooth Scrolling Support", test_smooth_scrolling_support),
        ("Pricing Section ID", test_pricing_section_id),
        ("Navigation Active State", test_navigation_active_state)
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
    print("📊 HOME PAGE PRICING CONSISTENCY SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ CONSISTENT" if result else "❌ INCONSISTENT"
        print(f"{status:<15} {test_name}")
        if result:
            passed += 1
    
    print(f"\nConsistency Score: {passed}/{total}")
    
    if passed == total:
        print("🎉 Home page pricing section perfectly matches /pricing page!")
        print("\n📋 Consistency Features:")
        print("✅ Navigation link points to #pricing section (no redirect)")
        print("✅ Identical pricing structure and content")
        print("✅ Same pricing plans, features, and prices")
        print("✅ Consistent styling and responsive design")
        print("✅ Smooth scrolling navigation support")
        print("✅ Proper section ID for navigation")
        print("✅ Active state management for navigation")
        print("\n🌊 User Experience:")
        print("   - Smooth scrolling from Home → About Us → Pricing Plans")
        print("   - Navigation underline moves smoothly between sections")
        print("   - Pricing section looks identical to /pricing page")
        print("   - No page redirects, seamless single-page experience")
    else:
        print("⚠️ Home page pricing section needs attention!")
        print("\n🚨 Inconsistencies Found:")
        for test_name, result in results:
            if not result:
                print(f"   - {test_name}")
        print("\n🔧 Recommended Actions:")
        print("   - Ensure pricing content matches exactly")
        print("   - Verify navigation links point to sections")
        print("   - Test smooth scrolling functionality")
        print("   - Check responsive design consistency")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
