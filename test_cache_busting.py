#!/usr/bin/env python3
"""
Test script for cache busting implementation
"""

import os
import sys
import time
import requests
from urllib.parse import urlparse, parse_qs

def test_cache_busting():
    """Test the cache busting implementation."""
    
    # Configuration
    BASE_URL = "http://localhost:5001"
    TEST_FILES = [
        "/static/styles.css",
        "/static/script.js",
        "/static/auth.js",
        "/static/common.js"
    ]
    
    print("🧪 Testing Cache Busting Implementation")
    print("=" * 50)
    
    # Test 1: Check if versioned URLs are generated
    print("\n1. Testing versioned URL generation...")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            content = response.text
            
            # Check for versioned URLs in HTML
            versioned_found = 0
            for test_file in TEST_FILES:
                if f"{test_file}?v=" in content:
                    versioned_found += 1
                    print(f"   ✅ Found versioned URL for {test_file}")
                else:
                    print(f"   ❌ No versioned URL found for {test_file}")
            
            if versioned_found == len(TEST_FILES):
                print("   🎉 All static files have versioned URLs!")
            else:
                print(f"   ⚠️  Only {versioned_found}/{len(TEST_FILES)} files have versioned URLs")
        else:
            print(f"   ❌ Failed to fetch homepage: {response.status_code}")
    
    except requests.RequestException as e:
        print(f"   ❌ Error fetching homepage: {e}")
    
    # Test 2: Check cache headers for versioned files
    print("\n2. Testing cache headers for versioned files...")
    
    for test_file in TEST_FILES:
        try:
            # Add a version parameter
            versioned_url = f"{BASE_URL}{test_file}?v={int(time.time())}"
            response = requests.head(versioned_url)
            
            if response.status_code == 200:
                cache_control = response.headers.get('Cache-Control', '')
                expires = response.headers.get('Expires', '')
                
                if 'max-age=31536000' in cache_control and 'immutable' in cache_control:
                    print(f"   ✅ {test_file}: Correct long-term cache headers")
                else:
                    print(f"   ❌ {test_file}: Incorrect cache headers: {cache_control}")
            else:
                print(f"   ❌ {test_file}: File not found ({response.status_code})")
        
        except requests.RequestException as e:
            print(f"   ❌ {test_file}: Error - {e}")
    
    # Test 3: Check cache headers for non-versioned files
    print("\n3. Testing cache headers for non-versioned files...")
    
    for test_file in TEST_FILES:
        try:
            response = requests.head(f"{BASE_URL}{test_file}")
            
            if response.status_code == 200:
                cache_control = response.headers.get('Cache-Control', '')
                
                if 'max-age=3600' in cache_control:
                    print(f"   ✅ {test_file}: Correct short-term cache headers")
                else:
                    print(f"   ❌ {test_file}: Incorrect cache headers: {cache_control}")
            else:
                print(f"   ❌ {test_file}: File not found ({response.status_code})")
        
        except requests.RequestException as e:
            print(f"   ❌ {test_file}: Error - {e}")
    
    # Test 4: Check HTML page cache headers
    print("\n4. Testing HTML page cache headers...")
    
    html_pages = ["/", "/auth/login", "/auth/register"]
    
    for page in html_pages:
        try:
            response = requests.head(f"{BASE_URL}{page}")
            
            if response.status_code in [200, 302]:  # 302 for redirects
                cache_control = response.headers.get('Cache-Control', '')
                pragma = response.headers.get('Pragma', '')
                
                if 'no-cache' in cache_control and 'no-store' in cache_control:
                    print(f"   ✅ {page}: Correct no-cache headers")
                else:
                    print(f"   ❌ {page}: Incorrect cache headers: {cache_control}")
            else:
                print(f"   ❌ {page}: Unexpected status ({response.status_code})")
        
        except requests.RequestException as e:
            print(f"   ❌ {page}: Error - {e}")
    
    # Test 5: Check service worker availability
    print("\n5. Testing service worker availability...")
    
    try:
        response = requests.get(f"{BASE_URL}/static/sw.js")
        
        if response.status_code == 200:
            content = response.text
            if 'Service Worker for VocalLocal' in content:
                print("   ✅ Service worker is available and contains expected content")
            else:
                print("   ❌ Service worker found but content is unexpected")
        else:
            print(f"   ❌ Service worker not found ({response.status_code})")
    
    except requests.RequestException as e:
        print(f"   ❌ Service worker error: {e}")
    
    # Test 6: Check cache manager availability
    print("\n6. Testing cache manager availability...")
    
    try:
        response = requests.get(f"{BASE_URL}/static/cache-manager.js")
        
        if response.status_code == 200:
            content = response.text
            if 'Cache Manager for VocalLocal' in content:
                print("   ✅ Cache manager is available and contains expected content")
            else:
                print("   ❌ Cache manager found but content is unexpected")
        else:
            print(f"   ❌ Cache manager not found ({response.status_code})")
    
    except requests.RequestException as e:
        print(f"   ❌ Cache manager error: {e}")
    
    # Test 7: Check security headers
    print("\n7. Testing security headers...")
    
    try:
        response = requests.head(f"{BASE_URL}/static/styles.css")
        
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
        }
        
        for header, expected_value in security_headers.items():
            actual_value = response.headers.get(header, '')
            if expected_value in actual_value:
                print(f"   ✅ {header}: {actual_value}")
            else:
                print(f"   ❌ {header}: Expected '{expected_value}', got '{actual_value}'")
    
    except requests.RequestException as e:
        print(f"   ❌ Security headers test error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Cache busting tests completed!")
    print("\nIf any tests failed, check the implementation and server configuration.")
    print("For debugging, use browser console commands:")
    print("  - cacheControls.checkCacheStatus()")
    print("  - cacheControls.clearCache()")
    print("  - cacheControls.forceUpdate()")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Allow custom base URL
        BASE_URL = sys.argv[1]
    
    test_cache_busting()
