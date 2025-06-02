#!/usr/bin/env python3
"""
VocalLocal DigitalOcean Deployment Helper
Automatically configures OAuth and environment variables
"""

import requests
import json
import os
from urllib.parse import urlencode

class DigitalOceanDeployer:
    def __init__(self, app_url):
        self.app_url = app_url.rstrip('/')
        self.oauth_urls = {
            'redirect_uris': [
                f"{self.app_url}/auth/callback",
                f"{self.app_url}/auth/google/callback"
            ],
            'javascript_origins': [self.app_url]
        }
    
    def print_oauth_config(self):
        """Print OAuth configuration for manual setup"""
        print("🔧 GOOGLE OAUTH CONFIGURATION")
        print("=" * 50)
        print("\n📍 Go to: https://console.cloud.google.com/apis/credentials")
        print("📍 Select project: vocal-local-e1e70")
        print("📍 Click on 'Radu' OAuth client")
        print("\n✅ ADD THESE REDIRECT URIs:")
        for uri in self.oauth_urls['redirect_uris']:
            print(f"   {uri}")
        
        print("\n✅ ADD THESE JAVASCRIPT ORIGINS:")
        for origin in self.oauth_urls['javascript_origins']:
            print(f"   {origin}")
        
        print("\n💾 Click SAVE and wait 5 minutes")
    
    def print_env_vars(self):
        """Print corrected environment variables"""
        print("\n🔧 DIGITALOCEAN ENVIRONMENT VARIABLE FIX")
        print("=" * 50)
        print("\n❌ CHANGE THIS VARIABLE NAME:")
        print("   FROM: FIREBASE_CREDENTIALS_JSON")
        print("   TO:   FIREBASE_CREDENTIALS")
        print("   (Keep the same JSON value)")
        
        print("\n✅ OR ADD THIS NEW VARIABLE:")
        print("FIREBASE_CREDENTIALS={\"type\":\"service_account\",\"project_id\":\"vocal-local-e1e70\",\"private_key_id\":\"98a96a0f6dc2c3e7900912b92742b2b180ee742e\",\"private_key\":\"-----BEGIN PRIVATE KEY-----\\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDj+FAM4vpdVgvI\\n5yyvbxJe7x+n/12aDBkqg/n9r+Hl8DJqiqgdA8YIr1AZScLM06yjSCAKAa7/o4F/\\n3lk3Tnnf1C1NI0+8RnITaKGPX5S8mLtpD+zsie6Tu38BzoVD3iDVyIN49v7KY9b9\\n4mAzZGIaCI7wSqqOdNg8+11bsC5Jo3+TSS1vvt4zQKFThc+x7ahnMA6RSkEdYNMh\\nU6JA8zEWYDD3NQAz2PdCzwH4w6YbQyzgcB5gbkwLraw5IxkGgWlQvHTLpv5tWf+m\\nOwl+/njfRLubdxMAfKMdUZKaJ7frJO0pUhv+S3ma56oMDM9v4jGfDsBpxAabC4UD\\nSFJZ2XqJAgMBAAECggEAEUJMQC+CdCTGq2D6GHWMouCQaVn7WoVqNdZsS50gWXXK\\nAVgqQlkV6fQo2KNFktd/MVTtbQiD2NGGhTlekIH51tzjyZxf5eGA8zB3k8jRFEat\\nYJa+sYk/RVK7erXpj7HuUzUVJAgyEb1Fim7UKOvjg/RMKwvCFhspQFOo9Z803+jy\\n6wyskHlBgcJSbNvmHJQk1EVEbZ1Y6Yikb/a6VEdN01gbPeyeJIEhhdHXTfr1oAJI\\nHrB9TpLrcDA2RK5tynStlK+it/omkuKaSUd9kB/xUn3vL1imUaIFcKUFlZ0eDi6Z\\ndcA+v2Y9UzgZIRbOpN2ctPg3N5Btzs29irAFbNcIQQKBgQD8iRWeEesnfSglvfWa\\nduS9443zfqwgkXyKd2ZxLvSkhJ0OJuT1jivYXMaVBMmpRxEyLaRy5yZ6izxaoSEp\\nE121b3ZFmjjA+Ku8AG4vVpNQifwa2ISPXkXJXogrDv4kU5RJVCh5M9JYl0RPOyDN\\nMc23I5RuturwcxEnaGsIkxu3QQKBgQDnGPP+jFtFMwgB9o9aBrJk8xANktUZ7c/J\\n8ENAaCjDHJJn1AdDEUqYw7CdngX3IRCv0JSG207FMmv3xu/VwgI/SVasl2J17P5V\\nF9u1Al9ox6im4w+8HDijx7pLW9alhosRFP7jgRJyon/sLZxnSMrT7sRAxgpmSsbp\\nvk6/mLT5SQKBgQDuL4nRJktqWnSkbG+bOepzY44+jEpjCXWyz/0yYbxi86WCdJLd\\nPDQEhTTT1skxvRLuBfimW3iCepL5VCKHsHlhKHkgGt7Ou3yW/LzwLzMQ8qRy2abl\\n5l/iFyRNoH15287v/s2Ry5vo7PuD01wTzZae1pMofaRIF++lAKp7Uu0AQQKBgGxg\\n0HTNQDSIxTWeewYeY+Vh9GJZPSVm2O78hZ2b+5ndOXAGCM3UOya/h4GzzVpjoF7D\\ntBQ2n49toSLXojyeOs2RSFuyt1NOpAIqwkt\\nsqacZt2sWP+AmVc3RFQaQHO+/omJj6VESX28KSqkhDqjxwRMXFIJuE3Z7DJ9ZpWY\\nGYNL19wEf2zuQ/tz+yW2Wl3G\\n-----END PRIVATE KEY-----\\n\",\"client_email\":\"firebase-adminsdk-fbsvc@vocal-local-e1e70.iam.gserviceaccount.com\",\"client_id\":\"103578034737972704669\",\"auth_uri\":\"https://accounts.google.com/o/oauth2/auth\",\"token_uri\":\"https://oauth2.googleapis.com/token\",\"auth_provider_x509_cert_url\":\"https://www.googleapis.com/oauth2/v1/certs\",\"client_x509_cert_url\":\"https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40vocal-local-e1e70.iam.gserviceaccount.com\",\"universe_domain\":\"googleapis.com\"}")
    
    def test_deployment(self):
        """Test if the deployment is working"""
        print(f"\n🧪 TESTING DEPLOYMENT")
        print("=" * 50)
        try:
            response = requests.get(f"{self.app_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ App is responding!")
            else:
                print(f"⚠️  App responded with status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ App is not responding: {e}")
        
        print(f"\n🔗 Test your app at: {self.app_url}")
        print(f"🔗 Try OAuth login: {self.app_url}/login")

def main():
    print("🚀 VOCALLOCAL DIGITALOCEAN DEPLOYMENT HELPER")
    print("=" * 60)
    
    app_url = "https://vocallocal-l5et5.ondigitalocean.app"
    deployer = DigitalOceanDeployer(app_url)
    
    print(f"📱 Configuring for: {app_url}")
    
    deployer.print_env_vars()
    deployer.print_oauth_config()
    deployer.test_deployment()
    
    print("\n🎉 DEPLOYMENT COMPLETE!")
    print("Wait 5 minutes after making OAuth changes, then test your app!")

if __name__ == "__main__":
    main()
