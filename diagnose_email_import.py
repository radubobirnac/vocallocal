#!/usr/bin/env python3
"""
Diagnostic script to identify email import issues in VocalLocal.
"""

import sys
import os

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

print("\n=== Testing Standard Library Email Imports ===")

# Test basic email imports
try:
    import email
    print("✓ email module imported successfully")
    print(f"  email module location: {email.__file__}")
except ImportError as e:
    print(f"✗ Failed to import email module: {e}")

try:
    from email import mime
    print("✓ email.mime imported successfully")
    print(f"  email.mime location: {mime.__file__}")
except ImportError as e:
    print(f"✗ Failed to import email.mime: {e}")

try:
    from email.mime import text
    print("✓ email.mime.text imported successfully")
    print(f"  email.mime.text location: {text.__file__}")
except ImportError as e:
    print(f"✗ Failed to import email.mime.text: {e}")

try:
    from email.mime.text import MimeText
    print("✓ MimeText imported successfully")
    print(f"  MimeText class: {MimeText}")
except ImportError as e:
    print(f"✗ Failed to import MimeText: {e}")

try:
    from email.mime.multipart import MimeMultipart
    print("✓ MimeMultipart imported successfully")
except ImportError as e:
    print(f"✗ Failed to import MimeMultipart: {e}")

try:
    from email.mime.base import MimeBase
    print("✓ MimeBase imported successfully")
except ImportError as e:
    print(f"✗ Failed to import MimeBase: {e}")

try:
    from email import encoders
    print("✓ email.encoders imported successfully")
except ImportError as e:
    print(f"✗ Failed to import email.encoders: {e}")

print("\n=== Testing Other Required Imports ===")

try:
    import smtplib
    print("✓ smtplib imported successfully")
except ImportError as e:
    print(f"✗ Failed to import smtplib: {e}")

try:
    import dns.resolver
    print("✓ dns.resolver imported successfully")
except ImportError as e:
    print(f"✗ Failed to import dns.resolver: {e}")
    print("  Install with: pip install dnspython")

print("\n=== Testing Email Service Import ===")

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from services.email_service import EmailService
    print("✓ EmailService class imported successfully")
except ImportError as e:
    print(f"✗ Failed to import EmailService: {e}")
    print(f"  Error details: {type(e).__name__}: {e}")

try:
    from services.email_service import email_service
    print("✓ email_service instance imported successfully")
except ImportError as e:
    print(f"✗ Failed to import email_service instance: {e}")

print("\n=== Testing Config Import ===")

try:
    from config import Config
    print("✓ Config imported successfully")
    print(f"  MAIL_SERVER: {getattr(Config, 'MAIL_SERVER', 'Not set')}")
    print(f"  MAIL_PORT: {getattr(Config, 'MAIL_PORT', 'Not set')}")
    print(f"  MAIL_USERNAME: {getattr(Config, 'MAIL_USERNAME', 'Not set')}")
    print(f"  MAIL_PASSWORD configured: {bool(getattr(Config, 'MAIL_PASSWORD', None))}")
except ImportError as e:
    print(f"✗ Failed to import Config: {e}")

print("\n=== Checking for Conflicting Files ===")

# Check for any email.py files that might conflict
for root, dirs, files in os.walk('.'):
    for file in files:
        if file == 'email.py':
            print(f"⚠️  Found potential conflicting file: {os.path.join(root, file)}")

print("\n=== Testing Simple Email Creation ===")

try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    
    # Create a simple test email
    msg = MimeMultipart()
    msg['Subject'] = 'Test Email'
    msg['From'] = 'test@example.com'
    msg['To'] = 'recipient@example.com'
    
    text_part = MimeText('This is a test email', 'plain')
    msg.attach(text_part)
    
    print("✓ Successfully created test email message")
    print(f"  Message type: {type(msg)}")
    print(f"  Subject: {msg['Subject']}")
    
except Exception as e:
    print(f"✗ Failed to create test email: {e}")

print("\n=== Recommendations ===")
print("If MimeText import fails:")
print("1. Check Python installation integrity")
print("2. Reinstall Python if necessary")
print("3. Check for conflicting email.py files in project")
print("4. Try importing in a fresh Python environment")
print("5. Check if running in virtual environment with correct packages")
