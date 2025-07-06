"""
Email service for VocalLocal application.
Handles email validation, sending, and templates.
"""
import re
import smtplib
import socket
import dns.resolver
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time
from config import Config

# Python 3.13 compatible email imports
try:
    # Python 3.13+ uses MIME classes with all caps
    from email.mime.text import MIMEText as MimeText
    from email.mime.multipart import MIMEMultipart as MimeMultipart
    from email.mime.base import MIMEBase as MimeBase
    from email import encoders
except ImportError:
    try:
        # Fallback for older Python versions
        from email.mime.text import MimeText
        from email.mime.multipart import MimeMultipart
        from email.mime.base import MimeBase
        from email import encoders
    except ImportError:
        # Last resort fallback
        raise ImportError("Unable to import email MIME classes. Please check your Python installation.")

# Set up logging
logger = logging.getLogger(__name__)

class EmailValidationError(Exception):
    """Custom exception for email validation errors."""
    pass

class EmailSendingError(Exception):
    """Custom exception for email sending errors."""
    pass

class EmailService:
    """Service for handling email operations."""
    
    def __init__(self):
        self.smtp_server = Config.MAIL_SERVER
        self.smtp_port = Config.MAIL_PORT
        self.use_tls = Config.MAIL_USE_TLS
        self.use_ssl = Config.MAIL_USE_SSL
        self.username = Config.MAIL_USERNAME
        self.password = Config.MAIL_PASSWORD
        self.default_sender = Config.MAIL_DEFAULT_SENDER
        
        # Email validation regex (RFC 5322 compliant with TLD requirement)
        self.email_regex = re.compile(
            r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$'
        )
    
    def validate_email_format(self, email: str) -> bool:
        """
        Validate email format using regex.
        
        Args:
            email (str): Email address to validate
            
        Returns:
            bool: True if email format is valid
        """
        if not email or not isinstance(email, str):
            return False
        
        return bool(self.email_regex.match(email.strip().lower()))
    
    def validate_email_domain(self, email: str) -> Tuple[bool, str]:
        """
        Validate email domain by checking DNS MX records.

        Note: This validates that the domain can receive emails,
        but does not verify if the specific email address exists.

        Args:
            email (str): Email address to validate

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            domain = email.split('@')[1]

            # Check if domain has MX record (preferred for email)
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                if mx_records:
                    logger.debug(f"Found {len(mx_records)} MX records for {domain}")
                    return True, ""
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                logger.debug(f"No MX records found for {domain}, checking A records")

            # Fallback: check if domain has A record (can still receive email)
            try:
                a_records = dns.resolver.resolve(domain, 'A')
                if a_records:
                    logger.debug(f"Found A records for {domain} (no MX records)")
                    return True, ""
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                return False, f"Domain '{domain}' does not exist or cannot receive emails"

        except Exception as e:
            logger.warning(f"DNS validation failed for {email}: {str(e)}")
            # If DNS check fails, assume email is valid to avoid blocking legitimate users
            return True, "DNS validation unavailable - email format appears valid"

        return False, "Domain validation failed"

    def verify_email_smtp(self, email: str, timeout: int = 10) -> Tuple[bool, str]:
        """
        Advanced email verification using SMTP connection.

        WARNING: This method actually connects to the mail server
        and may be considered intrusive. Use sparingly.

        Args:
            email (str): Email address to verify
            timeout (int): Connection timeout in seconds

        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        try:
            domain = email.split('@')[1]

            # Get MX records
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                mx_record = sorted(mx_records, key=lambda x: x.preference)[0]
                mx_host = str(mx_record.exchange).rstrip('.')
            except:
                return False, "No mail servers found for domain"

            # Connect to SMTP server
            try:
                import smtplib
                server = smtplib.SMTP(timeout=timeout)
                server.connect(mx_host, 25)
                server.helo('vocallocal.com')
                server.mail('noreply@vocallocal.com')

                # Try to verify the recipient
                code, message = server.rcpt(email)
                server.quit()

                if code == 250:
                    return True, "Email address verified via SMTP"
                elif code == 550:
                    return False, "Email address does not exist"
                else:
                    return False, f"SMTP verification inconclusive (code: {code})"

            except Exception as e:
                return False, f"SMTP connection failed: {str(e)}"

        except Exception as e:
            logger.warning(f"SMTP verification failed for {email}: {str(e)}")
            return False, f"SMTP verification error: {str(e)}"

    def validate_email(self, email: str, smtp_verify: bool = False) -> Dict[str, any]:
        """
        Simplified email validation focusing on format only.
        Domain validation removed to be more inclusive of educational and international domains.
        Security is maintained through OTP verification.

        Args:
            email (str): Email address to validate
            smtp_verify (bool): Whether to perform SMTP verification (disabled for inclusivity)

        Returns:
            Dict containing validation results with additional metadata
        """
        result = {
            'valid': False,
            'email': email.strip().lower() if email else '',
            'errors': [],
            'warnings': [],
            'validation_level': 'format_only'
        }

        # Format validation only - more inclusive approach
        if not self.validate_email_format(email):
            result['errors'].append('Please enter a valid email format (e.g., user@domain.com)')
            return result

        # Skip domain validation to be more inclusive of educational and international domains
        # Security is maintained through OTP verification process

        # Add informational message about validation level
        result['warnings'].append('Email format is valid. Verification will be done via OTP code.')

        # SMTP verification disabled for inclusivity - OTP verification provides security
        if smtp_verify:
            result['warnings'].append('SMTP verification skipped for inclusivity. OTP verification provides security.')

        result['valid'] = True
        return result
    
    def create_welcome_email(self, username: str, email: str, user_tier: str = 'free') -> MimeMultipart:
        """
        Create welcome email for new users.
        
        Args:
            username (str): User's username
            email (str): User's email address
            user_tier (str): User's subscription tier
            
        Returns:
            MimeMultipart: Email message object
        """
        msg = MimeMultipart('alternative')
        msg['Subject'] = 'Welcome to VocalLocal - Your AI-Powered Transcription Platform!'
        msg['From'] = self.default_sender
        msg['To'] = email
        
        # Define tier-specific content
        tier_info = {
            'free': {
                'limits': '60 minutes of AI transcription per month',
                'features': [
                    '✓ High-quality AI transcription',
                    '✓ Multiple language support',
                    '✓ Basic translation features',
                    '✓ Web-based interface'
                ]
            },
            'basic': {
                'limits': '280 minutes transcription, 50,000 words translation, 60 minutes TTS, 50 AI credits',
                'features': [
                    '✓ All free features',
                    '✓ Premium AI models access',
                    '✓ Text-to-speech functionality',
                    '✓ Advanced translation features',
                    '✓ Priority support'
                ]
            },
            'professional': {
                'limits': '800 minutes transcription, 160,000 words translation, 200 minutes TTS, 150 AI credits',
                'features': [
                    '✓ All basic features',
                    '✓ Highest usage limits',
                    '✓ Premium model priority',
                    '✓ Advanced AI features',
                    '✓ Priority customer support'
                ]
            }
        }
        
        current_tier = tier_info.get(user_tier, tier_info['free'])
        features_list = '\n            '.join(current_tier['features'])
        
        # HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to VocalLocal</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .features {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .cta-button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                @media only screen and (max-width: 600px) {{
                    .container {{ padding: 10px; }}
                    .header, .content {{ padding: 20px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to VocalLocal!</h1>
                    <p>Your AI-Powered Multilingual Transcription Platform</p>
                </div>
                <div class="content">
                    <h2>Hello {username}!</h2>
                    <p>Thank you for joining VocalLocal! We're excited to help you with accurate, AI-powered transcription and translation services.</p>
                    
                    <div class="features">
                        <h3>Your {user_tier.title()} Plan Includes:</h3>
                        <p><strong>Monthly Limits:</strong> {current_tier['limits']}</p>
                        <div style="margin-top: 15px;">
                            {features_list}
                        </div>
                    </div>
                    
                    <h3>Getting Started:</h3>
                    <ol>
                        <li><strong>Upload Audio:</strong> Drag and drop your audio files or record directly</li>
                        <li><strong>Choose Models:</strong> Select from our AI models for best results</li>
                        <li><strong>Get Results:</strong> Receive accurate transcriptions in seconds</li>
                        <li><strong>Translate:</strong> Convert text between 100+ languages</li>
                    </ol>
                    
                    <div style="text-align: center;">
                        <a href="https://vocallocal.com/dashboard" class="cta-button">Start Transcribing Now</a>
                    </div>
                    
                    <h3>Need Help?</h3>
                    <p>Our support team is here to help:</p>
                    <ul>
                        <li>📧 Email: support@vocallocal.com</li>
                        <li>📚 Documentation: <a href="https://vocallocal.com/docs">vocallocal.com/docs</a></li>
                        <li>💬 Live Chat: Available in your dashboard</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>© 2024 VocalLocal. All rights reserved.</p>
                    <p>This email was sent to {email}. If you didn't create this account, please ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Welcome to VocalLocal!
        
        Hello {username}!
        
        Thank you for joining VocalLocal! We're excited to help you with accurate, AI-powered transcription and translation services.
        
        Your {user_tier.title()} Plan Includes:
        Monthly Limits: {current_tier['limits']}
        
        Features:
        {chr(10).join([f'  {feature}' for feature in current_tier['features']])}
        
        Getting Started:
        1. Upload Audio: Drag and drop your audio files or record directly
        2. Choose Models: Select from our AI models for best results
        3. Get Results: Receive accurate transcriptions in seconds
        4. Translate: Convert text between 100+ languages
        
        Start transcribing now: https://vocallocal.com/dashboard
        
        Need Help?
        - Email: support@vocallocal.com
        - Documentation: https://vocallocal.com/docs
        - Live Chat: Available in your dashboard
        
        © 2024 VocalLocal. All rights reserved.
        This email was sent to {email}. If you didn't create this account, please ignore this email.
        """
        
        # Attach both versions
        msg.attach(MimeText(text_content, 'plain'))
        msg.attach(MimeText(html_content, 'html'))
        
        return msg

    def create_verification_email(self, email: str, code: str, username: str = None, verification_token: str = None) -> MimeMultipart:
        """
        Create email verification code email with optional verification link.

        Args:
            email (str): User's email address
            code (str): 6-digit verification code
            username (str): User's username (optional)
            verification_token (str): Secure token for verification link (optional)

        Returns:
            MimeMultipart: Email message object
        """
        msg = MimeMultipart('alternative')
        msg['Subject'] = 'Verify Your VocalLocal Email Address'
        msg['From'] = self.default_sender
        msg['To'] = email

        display_name = username if username else email.split('@')[0]

        # Create verification link if token is provided
        verification_link = None
        if verification_token:
            # You can customize this base URL based on your deployment
            base_url = "http://localhost:5000"  # Change this to your actual domain
            verification_link = f"{base_url}/auth/verify-email?email={email}&token={verification_token}&code={code}"

        # HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email - VocalLocal</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .email-card {{ background: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 600; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; font-size: 16px; }}
                .content {{ padding: 40px 30px; text-align: center; }}
                .verification-code {{ background: #f8f9fa; border: 2px dashed #667eea; border-radius: 8px; padding: 20px; margin: 30px 0; }}
                .code {{ font-size: 36px; font-weight: bold; color: #667eea; letter-spacing: 8px; font-family: 'Courier New', monospace; }}
                .instructions {{ background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 20px 0; text-align: left; }}
                .warning {{ background: #fff3e0; border-left: 4px solid #ff9800; padding: 15px; margin: 20px 0; text-align: left; }}
                .footer {{ background: #f8f9fa; padding: 20px 30px; text-align: center; color: #666; font-size: 14px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 500; }}
                @media only screen and (max-width: 600px) {{
                    .container {{ padding: 10px; }}
                    .header, .content, .footer {{ padding: 20px; }}
                    .code {{ font-size: 28px; letter-spacing: 4px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="email-card">
                    <div class="header">
                        <h1>🔐 Email Verification</h1>
                        <p>Secure your VocalLocal account</p>
                    </div>
                    <div class="content">
                        <h2>Hello {display_name}!</h2>
                        <p>To complete your VocalLocal registration and secure your account, please verify your email address using the code below:</p>

                        <div class="verification-code">
                            <div class="code">{code}</div>
                            <p style="margin: 10px 0 0 0; color: #666; font-size: 14px;">Enter this code in the verification popup</p>
                        </div>

                        """ + (f'''
                        <div style="margin: 30px 0; text-align: center;">
                            <a href="{verification_link}" class="button" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; display: inline-block;">
                                🔗 Verify Email Instantly
                            </a>
                            <p style="margin: 15px 0 0 0; color: #666; font-size: 14px;">
                                Click the button above to verify your email automatically, or use the code below
                            </p>
                        </div>
                        ''' if verification_link else '') + """

                        <div class="instructions">
                            """ + (f'''<h4 style="margin-top: 0;">📋 Two Ways to Verify:</h4>
                            <ol style="margin: 0; padding-left: 20px;">
                                <li><strong>Quick Option:</strong> Click the "Verify Email Instantly" button above</li>
                                <li><strong>Manual Option:</strong> Return to VocalLocal and enter the 6-digit code</li>
                            </ol>''' if verification_link else '''<h4 style="margin-top: 0;">📋 Instructions:</h4>
                            <ol style="margin: 0; padding-left: 20px;">
                                <li>Return to the VocalLocal registration page</li>
                                <li>Enter the 6-digit code above in the verification popup</li>
                                <li>Click "Verify Email" to activate your account</li>
                            </ol>''') + """
                        </div>

                        <div class="warning">
                            <h4 style="margin-top: 0;">⏰ Important:</h4>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>This code expires in <strong>10 minutes</strong></li>
                                <li>You have <strong>3 attempts</strong> to enter the correct code</li>
                                <li>If you didn't request this verification, please ignore this email</li>
                            </ul>
                        </div>

                        <p style="margin-top: 30px;">Need help? Contact our support team at <a href="mailto:support@vocallocal.com">support@vocallocal.com</a></p>
                    </div>
                    <div class="footer">
                        <p><strong>VocalLocal</strong> - AI-Powered Multilingual Transcription</p>
                        <p>This verification email was sent to {email}</p>
                        <p>© 2024 VocalLocal. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text version
        verification_link_text = f"\n\nQuick Verification Link:\n{verification_link}\n\nClick the link above to verify instantly, or use the code below." if verification_link else ""

        text_content = f"""
        VocalLocal Email Verification

        Hello {display_name}!

        To complete your VocalLocal registration, please verify your email address.
        {verification_link_text}

        Your verification code is: {code}

        Two Ways to Verify:
        1. Quick Option: Click the verification link above (if available)
        2. Manual Option: Return to VocalLocal and enter the 6-digit code

        Important:
        - This code expires in 10 minutes
        - You have 3 attempts to enter the correct code
        - If you didn't request this verification, please ignore this email

        Need help? Contact support@vocallocal.com

        VocalLocal - AI-Powered Multilingual Transcription
        This verification email was sent to {email}
        © 2024 VocalLocal. All rights reserved.
        """

        # Attach both versions
        msg.attach(MimeText(text_content, 'plain'))
        msg.attach(MimeText(html_content, 'html'))

        return msg

    def send_email(self, msg: MimeMultipart, max_retries: int = 3) -> Dict[str, any]:
        """
        Send email with retry logic and error handling.

        Args:
            msg (MimeMultipart): Email message to send
            max_retries (int): Maximum number of retry attempts

        Returns:
            Dict containing send results
        """
        result = {
            'success': False,
            'message': '',
            'attempts': 0,
            'timestamp': datetime.now().isoformat()
        }

        if not self.password:
            result['message'] = 'Email service not configured: Missing MAIL_PASSWORD'
            logger.error(result['message'])
            return result

        for attempt in range(max_retries):
            result['attempts'] = attempt + 1

            try:
                # Create SMTP connection
                if self.use_ssl:
                    server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
                else:
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                    if self.use_tls:
                        server.starttls()

                # Login and send
                server.login(self.username, self.password)
                text = msg.as_string()
                server.sendmail(msg['From'], msg['To'], text)
                server.quit()

                result['success'] = True
                result['message'] = f'Email sent successfully to {msg["To"]}'
                logger.info(result['message'])
                return result

            except smtplib.SMTPAuthenticationError as e:
                result['message'] = f'SMTP Authentication failed: {str(e)}'
                logger.error(result['message'])
                break  # Don't retry auth errors

            except smtplib.SMTPRecipientsRefused as e:
                result['message'] = f'Recipient refused: {str(e)}'
                logger.error(result['message'])
                break  # Don't retry recipient errors

            except (smtplib.SMTPException, socket.error) as e:
                result['message'] = f'SMTP error (attempt {attempt + 1}): {str(e)}'
                logger.warning(result['message'])

                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    logger.error(f'Failed to send email after {max_retries} attempts')

            except Exception as e:
                result['message'] = f'Unexpected error: {str(e)}'
                logger.error(result['message'])
                break

        return result

    def send_welcome_email(self, username: str, email: str, user_tier: str = 'free') -> Dict[str, any]:
        """
        Send welcome email to new user.

        Args:
            username (str): User's username
            email (str): User's email address
            user_tier (str): User's subscription tier

        Returns:
            Dict containing send results
        """
        try:
            # Validate email first
            validation = self.validate_email(email)
            if not validation['valid']:
                return {
                    'success': False,
                    'message': f'Invalid email address: {", ".join(validation["errors"])}',
                    'validation_errors': validation['errors']
                }

            # Create and send welcome email
            msg = self.create_welcome_email(username, email, user_tier)
            result = self.send_email(msg)

            # Log the attempt
            logger.info(f'Welcome email attempt for {email}: {result["message"]}')

            return result

        except Exception as e:
            error_msg = f'Failed to send welcome email to {email}: {str(e)}'
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'error': str(e)
            }

    def create_payment_confirmation_email(self, username: str, email: str, invoice_id: str,
                                        amount: float, currency: str, payment_date,
                                        plan_type: str, plan_name: str, billing_cycle: str) -> MimeMultipart:
        """
        Create payment confirmation email with invoice details.

        Args:
            username (str): User's username
            email (str): User's email address
            invoice_id (str): Stripe invoice ID
            amount (float): Payment amount
            currency (str): Payment currency
            payment_date (datetime): Payment date
            plan_type (str): Plan type (basic/professional)
            plan_name (str): Human-readable plan name
            billing_cycle (str): Billing cycle (monthly/annual)

        Returns:
            MimeMultipart: Email message object
        """
        msg = MimeMultipart('alternative')
        msg['Subject'] = f'Payment Confirmation - VocalLocal {plan_name}'
        msg['From'] = self.default_sender
        msg['To'] = email

        # Format payment date
        formatted_date = payment_date.strftime('%B %d, %Y at %I:%M %p UTC')

        # Define plan-specific features and limits
        plan_details = {
            'basic': {
                'monthly_limits': '280 minutes transcription, 50,000 words translation, 60 minutes TTS, 50 AI credits',
                'features': [
                    '✓ Premium AI models access',
                    '✓ Text-to-speech functionality',
                    '✓ Advanced translation features',
                    '✓ Priority support',
                    '✓ Multiple language support'
                ],
                'price': '$4.99'
            },
            'professional': {
                'monthly_limits': '800 minutes transcription, 160,000 words translation, 200 minutes TTS, 150 AI credits',
                'features': [
                    '✓ All Basic features',
                    '✓ Highest usage limits',
                    '✓ Premium model priority',
                    '✓ Advanced AI features',
                    '✓ Priority customer support',
                    '✓ Enhanced processing speed'
                ],
                'price': '$12.99'
            }
        }

        current_plan = plan_details.get(plan_type, plan_details['basic'])
        features_list = '\n                        '.join(current_plan['features'])

        # HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Payment Confirmation - VocalLocal</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .invoice-details {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745; }}
                .plan-features {{ background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .amount {{ font-size: 24px; font-weight: bold; color: #28a745; }}
                .cta-button {{ display: inline-block; background: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                .success-icon {{ font-size: 48px; color: #28a745; margin-bottom: 10px; }}
                @media only screen and (max-width: 600px) {{
                    .container {{ padding: 10px; }}
                    .header, .content {{ padding: 20px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="success-icon">✓</div>
                    <h1>Payment Confirmed!</h1>
                    <p>Thank you for your VocalLocal subscription</p>
                </div>
                <div class="content">
                    <h2>Hello {username}!</h2>
                    <p>Your payment has been successfully processed. Welcome to VocalLocal {plan_name}!</p>

                    <div class="invoice-details">
                        <h3>📄 Invoice Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Invoice ID:</strong></td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">{invoice_id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Plan:</strong></td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">{plan_name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Billing Cycle:</strong></td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">{billing_cycle.title()}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Payment Date:</strong></td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">{formatted_date}</td>
                            </tr>
                            <tr>
                                <td style="padding: 12px 0; font-size: 18px;"><strong>Amount Paid:</strong></td>
                                <td style="padding: 12px 0; text-align: right;" class="amount">{currency} {amount:.2f}</td>
                            </tr>
                        </table>
                    </div>

                    <div class="plan-features">
                        <h3>🚀 Your {plan_name} Includes:</h3>
                        <p><strong>Monthly Limits:</strong> {current_plan['monthly_limits']}</p>
                        <div style="margin-top: 15px;">
                            {features_list}
                        </div>
                    </div>

                    <h3>🎯 What's Next?</h3>
                    <ol>
                        <li><strong>Access Premium Features:</strong> All premium AI models are now available</li>
                        <li><strong>Start Transcribing:</strong> Upload audio files or record directly</li>
                        <li><strong>Explore TTS:</strong> Convert text to natural-sounding speech</li>
                        <li><strong>Advanced Translation:</strong> Use premium translation models</li>
                    </ol>

                    <div style="text-align: center;">
                        <a href="https://vocallocal.com/dashboard" class="cta-button">Access Your Dashboard</a>
                    </div>

                    <h3>📞 Need Help?</h3>
                    <p>Our support team is here to help:</p>
                    <ul>
                        <li>📧 Email: support@vocallocal.com</li>
                        <li>💬 Live Chat: Available in your dashboard</li>
                        <li>📚 Documentation: <a href="https://vocallocal.com/docs">vocallocal.com/docs</a></li>
                    </ul>

                    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin: 20px 0;">
                        <p><strong>📋 Keep This Email:</strong> This serves as your receipt and contains important billing information.</p>
                    </div>
                </div>
                <div class="footer">
                    <p>© 2024 VocalLocal. All rights reserved.</p>
                    <p>This email was sent to {email}. Questions? Contact support@vocallocal.com</p>
                    <p>Invoice ID: {invoice_id} | Next billing: {billing_cycle}</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text version
        text_content = f"""
        VocalLocal Payment Confirmation

        Hello {username}!

        Your payment has been successfully processed. Welcome to VocalLocal {plan_name}!

        INVOICE DETAILS
        ===============
        Invoice ID: {invoice_id}
        Plan: {plan_name}
        Billing Cycle: {billing_cycle.title()}
        Payment Date: {formatted_date}
        Amount Paid: {currency} {amount:.2f}

        YOUR {plan_name.upper()} INCLUDES
        ================================
        Monthly Limits: {current_plan['monthly_limits']}

        Features:
        {chr(10).join([f'  {feature}' for feature in current_plan['features']])}

        WHAT'S NEXT?
        ============
        1. Access Premium Features: All premium AI models are now available
        2. Start Transcribing: Upload audio files or record directly
        3. Explore TTS: Convert text to natural-sounding speech
        4. Advanced Translation: Use premium translation models

        Access your dashboard: https://vocallocal.com/dashboard

        NEED HELP?
        ==========
        Email: support@vocallocal.com
        Live Chat: Available in your dashboard
        Documentation: https://vocallocal.com/docs

        IMPORTANT: Keep this email as your receipt and billing record.

        © 2024 VocalLocal. All rights reserved.
        This email was sent to {email}
        Invoice ID: {invoice_id} | Next billing: {billing_cycle}
        """

        # Attach both HTML and plain text versions
        msg.attach(MimeText(text_content, 'plain'))
        msg.attach(MimeText(html_content, 'html'))

        return msg

    def send_payment_confirmation_email(self, username: str, email: str, invoice_id: str,
                                      amount: float, currency: str, payment_date,
                                      plan_type: str, plan_name: str, billing_cycle: str) -> Dict[str, any]:
        """
        Send payment confirmation email with invoice details.

        Args:
            username (str): User's username
            email (str): User's email address
            invoice_id (str): Stripe invoice ID
            amount (float): Payment amount
            currency (str): Payment currency
            payment_date (datetime): Payment date
            plan_type (str): Plan type (basic/professional)
            plan_name (str): Human-readable plan name
            billing_cycle (str): Billing cycle (monthly/annual)

        Returns:
            Dict containing send results
        """
        try:
            # Validate email first
            validation = self.validate_email(email)
            if not validation['valid']:
                return {
                    'success': False,
                    'message': f'Invalid email address: {", ".join(validation["errors"])}',
                    'validation_errors': validation['errors']
                }

            # Create and send payment confirmation email
            msg = self.create_payment_confirmation_email(
                username, email, invoice_id, amount, currency,
                payment_date, plan_type, plan_name, billing_cycle
            )
            result = self.send_email(msg)

            # Log the attempt
            logger.info(f'Payment confirmation email attempt for {email}, invoice {invoice_id}: {result["message"]}')

            return result

        except Exception as e:
            error_msg = f'Failed to send payment confirmation email to {email}: {str(e)}'
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'error': str(e)
            }

# Global email service instance
email_service = EmailService()
