#!/usr/bin/env python3
"""
Stripe Products Setup Script for VocalLocal
Creates products and prices for Basic and Professional plans
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_stripe_products():
    """Create VocalLocal products and prices in Stripe"""
    
    try:
        import stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        if not stripe.api_key:
            print("❌ STRIPE_SECRET_KEY not found in environment variables")
            return False
        
        print("🚀 Setting up VocalLocal products in Stripe...")
        
        # Product configurations
        products_config = [
            {
                'name': 'VocalLocal Basic Plan',
                'description': '280 transcription minutes, 50K translation words, 60 TTS minutes, 50 AI credits',
                'price': 499,  # $4.99 in cents
                'plan_type': 'basic'
            },
            {
                'name': 'VocalLocal Professional Plan', 
                'description': '800 transcription minutes, 160K translation words, 200 TTS minutes, 150 AI credits',
                'price': 1299,  # $12.99 in cents
                'plan_type': 'professional'
            }
        ]
        
        created_products = []
        
        for config in products_config:
            print(f"\n📦 Creating product: {config['name']}")
            
            # Create product
            product = stripe.Product.create(
                name=config['name'],
                description=config['description'],
                metadata={
                    'plan_type': config['plan_type'],
                    'app': 'vocallocal'
                }
            )
            
            print(f"   ✅ Product created: {product.id}")
            
            # Create monthly price
            price = stripe.Price.create(
                product=product.id,
                unit_amount=config['price'],
                currency='usd',
                recurring={'interval': 'month'},
                metadata={
                    'plan_type': config['plan_type'],
                    'app': 'vocallocal'
                }
            )
            
            print(f"   ✅ Price created: {price.id} (${config['price']/100}/month)")
            
            created_products.append({
                'plan_type': config['plan_type'],
                'product_id': product.id,
                'price_id': price.id,
                'amount': config['price']
            })
        
        # Display environment variables to add
        print("\n🔧 Add these environment variables:")
        print("=" * 50)
        
        for product in created_products:
            env_var = f"STRIPE_{product['plan_type'].upper()}_PRICE_ID"
            print(f"{env_var}={product['price_id']}")
        
        print("\n📋 Product Summary:")
        print("=" * 30)
        for product in created_products:
            print(f"Plan: {product['plan_type'].title()}")
            print(f"  Product ID: {product['product_id']}")
            print(f"  Price ID: {product['price_id']}")
            print(f"  Amount: ${product['amount']/100}/month")
            print()
        
        return True
        
    except stripe.error.AuthenticationError:
        print("❌ Stripe authentication failed. Check your secret key.")
        return False
    except Exception as e:
        print(f"❌ Error creating products: {str(e)}")
        return False

def list_existing_products():
    """List existing products to avoid duplicates"""
    
    try:
        import stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        print("📋 Existing Stripe Products:")
        print("=" * 30)
        
        products = stripe.Product.list(limit=20)
        
        vocallocal_products = []
        for product in products.data:
            if 'vocallocal' in product.name.lower() or 'vocal local' in product.name.lower():
                vocallocal_products.append(product)
        
        if not vocallocal_products:
            print("No VocalLocal products found.")
            return []
        
        for product in vocallocal_products:
            print(f"\n📦 {product.name}")
            print(f"   ID: {product.id}")
            print(f"   Description: {product.description}")
            
            # List prices for this product
            prices = stripe.Price.list(product=product.id)
            for price in prices.data:
                amount = price.unit_amount / 100 if price.unit_amount else 0
                currency = price.currency.upper()
                interval = price.recurring.interval if price.recurring else 'one-time'
                print(f"   💲 {amount} {currency}/{interval} (Price ID: {price.id})")
        
        return vocallocal_products
        
    except Exception as e:
        print(f"❌ Error listing products: {str(e)}")
        return []

def setup_webhook_endpoint():
    """Guide for setting up webhook endpoint"""
    
    print("\n🔗 Webhook Endpoint Setup Guide:")
    print("=" * 35)
    print("""
1. Go to Stripe Dashboard: https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Enter your endpoint URL: https://yourdomain.com/payment/webhook
4. Select these events:
   ✅ checkout.session.completed
   ✅ customer.subscription.created
   ✅ customer.subscription.updated
   ✅ customer.subscription.deleted
   ✅ invoice.payment_succeeded
   ✅ invoice.payment_failed
   ✅ customer.created

5. Copy the webhook signing secret (starts with whsec_)
6. Add to environment: STRIPE_WEBHOOK_SECRET=whsec_your_secret

For local testing, use Stripe CLI:
   stripe listen --forward-to localhost:5001/payment/webhook
    """)

def main():
    """Main setup function"""
    
    print("🚀 VocalLocal Stripe Products Setup")
    print("=" * 40)
    
    # Check if Stripe is installed
    try:
        import stripe
    except ImportError:
        print("❌ Stripe library not installed")
        print("   Run: pip install stripe>=7.0.0")
        return
    
    # Check API key
    if not os.getenv('STRIPE_SECRET_KEY'):
        print("❌ STRIPE_SECRET_KEY not found in environment variables")
        print("   Add your Stripe secret key to .env file")
        return
    
    # List existing products first
    existing_products = list_existing_products()
    
    if existing_products:
        print(f"\n⚠️  Found {len(existing_products)} existing VocalLocal products.")
        choice = input("Do you want to create new products anyway? (y/N): ").strip().lower()
        if choice != 'y':
            print("Skipping product creation.")
            setup_webhook_endpoint()
            return
    
    # Create products
    if setup_stripe_products():
        print("\n🎉 Products created successfully!")
        setup_webhook_endpoint()
    else:
        print("\n❌ Failed to create products.")

if __name__ == "__main__":
    main()
