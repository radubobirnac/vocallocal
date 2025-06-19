#!/usr/bin/env python3
"""
Stripe Setup Testing Script for VocalLocal
Tests Stripe API connectivity, products, and webhook configuration
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_stripe_installation():
    """Test if Stripe library is installed"""
    try:
        import stripe
        print("✅ Stripe library installed successfully")

        # Try different ways to get version
        try:
            version = stripe.__version__
        except AttributeError:
            try:
                version = stripe._version
            except AttributeError:
                version = "Unknown (but installed)"

        print(f"   Version: {version}")
        return True
    except ImportError:
        print("❌ Stripe library not installed")
        print("   Run: pip install stripe>=7.0.0")
        return False

def test_api_keys():
    """Test Stripe API keys configuration"""
    print("\n🔑 Testing API Keys...")
    
    # Check environment variables
    publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
    secret_key = os.getenv('STRIPE_SECRET_KEY')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    if not publishable_key:
        print("❌ STRIPE_PUBLISHABLE_KEY not found in environment")
        return False
    
    if not secret_key:
        print("❌ STRIPE_SECRET_KEY not found in environment")
        return False
        
    if not webhook_secret:
        print("⚠️  STRIPE_WEBHOOK_SECRET not found (needed for webhooks)")
    
    # Validate key formats
    if publishable_key.startswith('pk_test_'):
        print("✅ Using test publishable key")
    elif publishable_key.startswith('pk_live_'):
        print("⚠️  Using LIVE publishable key - be careful!")
    else:
        print("❌ Invalid publishable key format")
        return False
        
    if secret_key.startswith('sk_test_'):
        print("✅ Using test secret key")
    elif secret_key.startswith('sk_live_'):
        print("⚠️  Using LIVE secret key - be careful!")
    else:
        print("❌ Invalid secret key format")
        return False
    
    return True

def test_stripe_api_connectivity():
    """Test actual connection to Stripe API"""
    print("\n🌐 Testing Stripe API Connectivity...")
    
    try:
        import stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        # Test API call
        account = stripe.Account.retrieve()
        print(f"✅ Connected to Stripe successfully")
        print(f"   Account ID: {account.id}")
        print(f"   Country: {account.country}")
        print(f"   Email: {account.email}")
        print(f"   Charges enabled: {account.charges_enabled}")
        print(f"   Payouts enabled: {account.payouts_enabled}")
        
        return True
        
    except stripe.error.AuthenticationError:
        print("❌ Authentication failed - check your secret key")
        return False
    except Exception as e:
        print(f"❌ API connection failed: {str(e)}")
        return False

def test_products_and_prices():
    """Test if products and prices are configured"""
    print("\n💰 Testing Products and Prices...")
    
    try:
        import stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        # List products
        products = stripe.Product.list(limit=10)
        print(f"✅ Found {len(products.data)} products")
        
        vocallocal_products = []
        for product in products.data:
            if 'vocallocal' in product.name.lower() or 'vocal local' in product.name.lower():
                vocallocal_products.append(product)
                print(f"   📦 {product.name} (ID: {product.id})")
        
        if not vocallocal_products:
            print("⚠️  No VocalLocal products found")
            print("   You need to create products for Basic and Professional plans")
            return False
        
        # List prices for VocalLocal products
        print("\n💵 Checking Prices...")
        for product in vocallocal_products:
            prices = stripe.Price.list(product=product.id)
            print(f"   Product: {product.name}")
            for price in prices.data:
                amount = price.unit_amount / 100 if price.unit_amount else 0
                currency = price.currency.upper()
                interval = price.recurring.interval if price.recurring else 'one-time'
                print(f"     💲 {amount} {currency}/{interval} (ID: {price.id})")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to retrieve products: {str(e)}")
        return False

def test_webhook_endpoint_url():
    """Test webhook endpoint URL configuration"""
    print("\n🔗 Testing Webhook Configuration...")
    
    # Check if webhook URL is accessible
    webhook_url = input("Enter your webhook URL (e.g., https://yourdomain.com/payment/webhook): ").strip()
    
    if not webhook_url:
        print("⚠️  No webhook URL provided - you'll need this for production")
        return False
    
    try:
        import requests
        
        # Test if URL is accessible (expect 405 Method Not Allowed for GET)
        response = requests.get(webhook_url, timeout=10)
        
        if response.status_code == 405:
            print("✅ Webhook endpoint is accessible (returns 405 for GET as expected)")
            return True
        elif response.status_code == 404:
            print("❌ Webhook endpoint returns 404 - endpoint not implemented yet")
            return False
        else:
            print(f"⚠️  Webhook endpoint returns {response.status_code} - may need investigation")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach webhook URL: {str(e)}")
        return False

def generate_test_environment_template():
    """Generate a template for environment variables"""
    print("\n📝 Environment Variables Template:")
    print("=" * 50)
    print("""
# Add these to your .env file or environment variables:

# Stripe Test Keys (get from https://dashboard.stripe.com/test/apikeys)
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Product Price IDs (get after creating products)
STRIPE_BASIC_PRICE_ID=price_your_basic_price_id
STRIPE_PROFESSIONAL_PRICE_ID=price_your_professional_price_id

# Webhook Configuration
STRIPE_WEBHOOK_ENDPOINT_SECRET=whsec_your_endpoint_secret
    """)

def main():
    """Run all pre-implementation tests"""
    print("🚀 VocalLocal Stripe Setup Testing")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Stripe installation
    if test_stripe_installation():
        tests_passed += 1
    
    # Test 2: API keys
    if test_api_keys():
        tests_passed += 1
    
    # Test 3: API connectivity
    if test_stripe_api_connectivity():
        tests_passed += 1
    
    # Test 4: Products and prices
    if test_products_and_prices():
        tests_passed += 1
    
    # Test 5: Webhook URL
    if test_webhook_endpoint_url():
        tests_passed += 1
    
    # Summary
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Ready to implement payment integration.")
    elif tests_passed >= 3:
        print("⚠️  Most tests passed. Address the issues above before proceeding.")
    else:
        print("❌ Multiple issues found. Please fix configuration before implementing.")
    
    # Generate template
    generate_test_environment_template()

if __name__ == "__main__":
    main()
