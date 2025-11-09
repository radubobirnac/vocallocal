"""
Password Reset Service
Handles password reset functionality including token generation, validation, and email sending.
"""

import secrets
import hashlib
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import request

from models.firebase_models import User
from services.email_service import email_service

logger = logging.getLogger(__name__)

class PasswordResetService:
    """Service for handling password reset operations."""
    
    def __init__(self):
        self.token_expiry_minutes = 30  # Reset tokens expire in 30 minutes
        self.max_attempts = 3  # Maximum reset attempts per email per hour
        self.rate_limit_window = 3600  # 1 hour in seconds

    def get_base_url(self) -> str:
        """
        Get the base URL for the application.

        Returns one of five specific base URLs:
        1. https://vocallocal.com (production)
        2. https://vocallocal-l5et5.ondigitalocean.app (production DigitalOcean)
        3. https://test-vocallocal-x9n74.ondigitalocean.app (test DigitalOcean)
        4. https://vocallocal.net (production)
        5. http://localhost:5001 (development)

        Returns:
            str: Base URL for the application
        """
        # 1. Check for explicit base URL in environment variables
        base_url = os.environ.get('VOCALLOCAL_BASE_URL')
        if base_url:
            return base_url.rstrip('/')

        # 2. Check for DigitalOcean App Platform URL
        app_url = os.environ.get('APP_URL')
        if app_url:
            return app_url.rstrip('/')

        # 3. Try to get URL from Flask request context
        try:
            from flask import has_request_context
            if has_request_context() and request:
                url_root = request.url_root.rstrip('/')
                # Map known domains to your specific URLs
                if 'vocallocal-l5et5.ondigitalocean.app' in url_root:
                    return 'https://vocallocal-l5et5.ondigitalocean.app'
                elif 'test-vocallocal-x9n74.ondigitalocean.app' in url_root:
                    return 'https://test-vocallocal-x9n74.ondigitalocean.app'
                elif 'vocallocal.net' in url_root:
                    return 'https://vocallocal.net'
                elif 'vocallocal.com' in url_root:
                    return 'https://vocallocal.com'
                elif 'localhost' in url_root:
                    return 'http://localhost:5001'
                else:
                    return url_root
        except (RuntimeError, ImportError):
            pass

        # 4. Default to localhost for development
        return 'http://localhost:5001'

    def generate_reset_token(self, email: str) -> str:
        """
        Generate a secure password reset token.
        
        Args:
            email (str): User's email address
            
        Returns:
            str: Secure reset token
        """
        # Generate a cryptographically secure random token
        random_bytes = secrets.token_bytes(32)
        timestamp = str(int(datetime.now().timestamp()))
        
        # Combine email, timestamp, and random bytes for uniqueness
        token_data = f"{email}:{timestamp}:{random_bytes.hex()}"
        
        # Create SHA-256 hash of the token data
        token_hash = hashlib.sha256(token_data.encode()).hexdigest()
        
        return token_hash
    
    def store_reset_token(self, email: str, token: str) -> bool:
        """
        Store password reset token in database.
        
        Args:
            email (str): User's email address
            token (str): Reset token
            
        Returns:
            bool: True if stored successfully
        """
        try:
            user_id = email.replace('.', ',')
            expiry_time = datetime.now() + timedelta(minutes=self.token_expiry_minutes)
            
            reset_data = {
                'token': token,
                'email': email,
                'created_at': datetime.now().isoformat(),
                'expires_at': expiry_time.isoformat(),
                'used': False,
                'attempts': 0
            }
            
            # Store in Firebase under password_resets collection
            User.get_ref('password_resets').child(user_id).set(reset_data)
            
            logger.info(f"Password reset token stored for {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store reset token for {email}: {str(e)}")
            return False
    
    def validate_reset_token(self, email: str, token: str) -> Tuple[bool, str]:
        """
        Validate password reset token.
        
        Args:
            email (str): User's email address
            token (str): Reset token to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            user_id = email.replace('.', ',')
            reset_data = User.get_ref('password_resets').child(user_id).get()
            
            if not reset_data:
                return False, "No password reset request found for this email"
            
            stored_token = reset_data.get('token')
            if not stored_token:
                return False, "Invalid reset token"
            
            # Check if token matches
            if stored_token != token:
                return False, "Invalid reset token"
            
            # Check if token has been used
            if reset_data.get('used', False):
                return False, "Reset token has already been used"
            
            # Check if token has expired
            expires_at = datetime.fromisoformat(reset_data.get('expires_at'))
            if datetime.now() > expires_at:
                return False, "Reset token has expired"
            
            return True, "Token is valid"
            
        except Exception as e:
            logger.error(f"Error validating reset token for {email}: {str(e)}")
            return False, "Error validating reset token"
    
    def mark_token_used(self, email: str, token: str) -> bool:
        """
        Mark reset token as used.
        
        Args:
            email (str): User's email address
            token (str): Reset token
            
        Returns:
            bool: True if marked successfully
        """
        try:
            user_id = email.replace('.', ',')
            User.get_ref('password_resets').child(user_id).update({
                'used': True,
                'used_at': datetime.now().isoformat()
            })
            
            logger.info(f"Reset token marked as used for {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark token as used for {email}: {str(e)}")
            return False
    
    def check_rate_limit(self, email: str) -> Tuple[bool, str]:
        """
        Check if user has exceeded rate limit for password reset requests.
        
        Args:
            email (str): User's email address
            
        Returns:
            Tuple[bool, str]: (is_allowed, error_message)
        """
        try:
            user_id = email.replace('.', ',')
            
            # Get recent reset attempts
            attempts_ref = User.get_ref('password_reset_attempts').child(user_id)
            attempts_data = attempts_ref.get() or {}
            
            # Clean up old attempts (older than rate limit window)
            current_time = datetime.now()
            recent_attempts = []
            
            for attempt_id, attempt_data in attempts_data.items():
                attempt_time = datetime.fromisoformat(attempt_data.get('timestamp'))
                if (current_time - attempt_time).total_seconds() < self.rate_limit_window:
                    recent_attempts.append(attempt_data)
            
            # Check if exceeded max attempts
            if len(recent_attempts) >= self.max_attempts:
                return False, f"Too many password reset attempts. Please wait 1 hour before trying again."
            
            return True, "Rate limit check passed"
            
        except Exception as e:
            logger.error(f"Error checking rate limit for {email}: {str(e)}")
            return True, "Rate limit check skipped due to error"
    
    def log_reset_attempt(self, email: str) -> bool:
        """
        Log password reset attempt for rate limiting.
        
        Args:
            email (str): User's email address
            
        Returns:
            bool: True if logged successfully
        """
        try:
            user_id = email.replace('.', ',')
            attempt_id = secrets.token_hex(8)
            
            attempt_data = {
                'email': email,
                'timestamp': datetime.now().isoformat(),
                'ip_address': 'unknown'  # Could be enhanced to capture real IP
            }
            
            User.get_ref('password_reset_attempts').child(user_id).child(attempt_id).set(attempt_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log reset attempt for {email}: {str(e)}")
            return False
    
    def create_reset_email(self, email: str, token: str, username: str = None) -> MIMEMultipart:
        """
        Create password reset email.

        Args:
            email (str): User's email address
            token (str): Reset token
            username (str): User's username (optional)

        Returns:
            MIMEMultipart: Email message object
        """
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Reset Your VocalLocal Password'
        msg['From'] = email_service.default_sender
        msg['To'] = email

        display_name = username if username else email.split('@')[0]

        # Create reset link with dynamic base URL
        base_url = self.get_base_url()
        reset_link = f"{base_url}/auth/reset-password?email={email}&token={token}"
        
        # HTML version
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 0; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 30px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #666; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                    <p>VocalLocal - AI-Powered Transcription</p>
                </div>
                
                <div class="content">
                    <h2>Hello {display_name}!</h2>
                    
                    <p>We received a request to reset your VocalLocal password. If you made this request, click the button below to set a new password:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset My Password</a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace;">{reset_link}</p>
                    
                    <div class="warning">
                        <strong>⚠️ Important Security Information:</strong>
                        <ul>
                            <li>This link expires in 30 minutes</li>
                            <li>If you didn't request this reset, please ignore this email</li>
                            <li>Never share this link with anyone</li>
                            <li>VocalLocal will never ask for your password via email</li>
                        </ul>
                    </div>
                    
                    <p>If you're having trouble with the button above, copy and paste the URL into your web browser.</p>
                    
                    <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                </div>
                
                <div class="footer">
                    <p>This email was sent by VocalLocal</p>
                    <p>If you have questions, contact us at support@vocallocal.com</p>
                    <p>&copy; 2024 VocalLocal. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        VocalLocal Password Reset
        
        Hello {display_name}!
        
        We received a request to reset your VocalLocal password.
        
        To reset your password, click this link:
        {reset_link}
        
        Important:
        - This link expires in 30 minutes
        - If you didn't request this reset, please ignore this email
        - Never share this link with anyone
        
        If you didn't request a password reset, you can safely ignore this email.
        Your password will remain unchanged.
        
        Need help? Contact support@vocallocal.com
        
        VocalLocal Team
        """
        
        # Attach both versions
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        return msg
    
    def send_reset_email(self, email: str, username: str = None) -> Dict[str, any]:
        """
        Send password reset email to user.
        
        Args:
            email (str): User's email address
            username (str): User's username (optional)
            
        Returns:
            Dict containing send results
        """
        try:
            # Check if user exists
            user_data = User.get_by_email(email)
            if not user_data:
                # Don't reveal if email exists or not for security
                return {
                    'success': True,
                    'message': 'If an account with this email exists, you will receive a password reset link shortly.'
                }
            
            # Check rate limit
            rate_limit_ok, rate_limit_msg = self.check_rate_limit(email)
            if not rate_limit_ok:
                return {
                    'success': False,
                    'message': rate_limit_msg
                }
            
            # Generate and store reset token
            token = self.generate_reset_token(email)
            if not self.store_reset_token(email, token):
                return {
                    'success': False,
                    'message': 'Failed to generate reset token. Please try again.'
                }
            
            # Log the attempt
            self.log_reset_attempt(email)
            
            # Create and send email
            username = username or user_data.get('username')
            msg = self.create_reset_email(email, token, username)
            result = email_service.send_email(msg)
            
            if result['success']:
                logger.info(f"Password reset email sent to {email}")
                return {
                    'success': True,
                    'message': 'If an account with this email exists, you will receive a password reset link shortly.'
                }
            else:
                logger.error(f"Failed to send reset email to {email}: {result['message']}")
                return {
                    'success': False,
                    'message': 'Failed to send reset email. Please try again later.'
                }
                
        except Exception as e:
            logger.error(f"Error sending reset email to {email}: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred. Please try again later.'
            }

# Global password reset service instance
password_reset_service = PasswordResetService()
