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
        
        # Email validation regex (RFC 5322 compliant)
        self.email_regex = re.compile(
            r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
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
        Comprehensive email validation.

        Args:
            email (str): Email address to validate
            smtp_verify (bool): Whether to perform SMTP verification (slower, more thorough)

        Returns:
            Dict containing validation results with additional metadata
        """
        result = {
            'valid': False,
            'email': email.strip().lower() if email else '',
            'errors': [],
            'warnings': [],
            'validation_level': 'format_and_domain'
        }

        # Format validation
        if not self.validate_email_format(email):
            result['errors'].append('Please enter a valid email format (e.g., user@domain.com)')
            return result

        # Domain validation
        domain_valid, domain_error = self.validate_email_domain(email)
        if not domain_valid:
            result['errors'].append(domain_error)
            return result

        # Add informational message about validation level
        result['warnings'].append('Email format and domain are valid. Note: This does not verify if the specific email address exists.')

        # Optional SMTP verification
        if smtp_verify:
            result['validation_level'] = 'format_domain_and_smtp'
            smtp_valid, smtp_message = self.verify_email_smtp(email)

            if not smtp_valid:
                result['errors'].append(f"Email verification failed: {smtp_message}")
                result['warnings'].append('The email format and domain are valid, but the specific address may not exist.')
                # Still mark as valid for domain-level validation
                result['valid'] = True
                return result
            else:
                result['warnings'] = [smtp_message]

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

    def create_verification_email(self, email: str, code: str, username: str = None) -> MimeMultipart:
        """
        Create email verification code email.

        Args:
            email (str): User's email address
            code (str): 6-digit verification code
            username (str): User's username (optional)

        Returns:
            MimeMultipart: Email message object
        """
        msg = MimeMultipart('alternative')
        msg['Subject'] = 'Verify Your VocalLocal Email Address'
        msg['From'] = self.default_sender
        msg['To'] = email

        display_name = username if username else email.split('@')[0]

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

                        <div class="instructions">
                            <h4 style="margin-top: 0;">📋 Instructions:</h4>
                            <ol style="margin: 0; padding-left: 20px;">
                                <li>Return to the VocalLocal registration page</li>
                                <li>Enter the 6-digit code above in the verification popup</li>
                                <li>Click "Verify Email" to activate your account</li>
                            </ol>
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
        text_content = f"""
        VocalLocal Email Verification

        Hello {display_name}!

        To complete your VocalLocal registration, please verify your email address.

        Your verification code is: {code}

        Instructions:
        1. Return to the VocalLocal registration page
        2. Enter the 6-digit code above in the verification popup
        3. Click "Verify Email" to activate your account

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

# Global email service instance
email_service = EmailService()
