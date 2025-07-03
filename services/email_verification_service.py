"""
Email verification service for VocalLocal application.
Handles verification code generation, storage, and validation.
"""
import random
import string
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from firebase_config import initialize_firebase
from services.email_service import email_service

# Set up logging
logger = logging.getLogger(__name__)

class EmailVerificationService:
    """Service for handling email verification with 6-digit codes."""
    
    def __init__(self):
        self.db_ref = initialize_firebase()
        self.code_length = 6
        self.code_expiry_minutes = 10
        self.max_attempts = 3
        self.resend_cooldown_minutes = 1
    
    def generate_verification_code(self) -> str:
        """
        Generate a 6-digit verification code.
        
        Returns:
            str: 6-digit numeric code
        """
        return ''.join(random.choices(string.digits, k=self.code_length))
    
    def store_verification_code(self, email: str, code: str) -> Dict[str, any]:
        """
        Store verification code in Firebase with expiration.
        
        Args:
            email (str): Email address
            code (str): Verification code
            
        Returns:
            Dict containing storage result
        """
        try:
            # Create verification record
            verification_data = {
                'code': code,
                'email': email.lower().strip(),
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(minutes=self.code_expiry_minutes)).isoformat(),
                'attempts': 0,
                'verified': False,
                'resend_count': 0
            }
            
            # Store in Firebase under email_verifications/{email_hash}
            email_key = email.lower().strip().replace('.', '_').replace('@', '_at_')
            self.db_ref.child('email_verifications').child(email_key).set(verification_data)
            
            logger.info(f'Verification code stored for {email}')
            
            return {
                'success': True,
                'message': 'Verification code stored successfully',
                'expires_at': verification_data['expires_at']
            }
            
        except Exception as e:
            logger.error(f'Failed to store verification code for {email}: {str(e)}')
            return {
                'success': False,
                'message': f'Failed to store verification code: {str(e)}'
            }
    
    def get_verification_data(self, email: str) -> Optional[Dict]:
        """
        Retrieve verification data for an email.
        
        Args:
            email (str): Email address
            
        Returns:
            Dict or None: Verification data if exists
        """
        try:
            email_key = email.lower().strip().replace('.', '_').replace('@', '_at_')
            verification_data = self.db_ref.child('email_verifications').child(email_key).get()
            
            if verification_data:
                return verification_data
            return None
            
        except Exception as e:
            logger.error(f'Failed to retrieve verification data for {email}: {str(e)}')
            return None
    
    def is_code_expired(self, verification_data: Dict) -> bool:
        """
        Check if verification code has expired.
        
        Args:
            verification_data (Dict): Verification data from database
            
        Returns:
            bool: True if expired
        """
        try:
            expires_at = datetime.fromisoformat(verification_data['expires_at'])
            return datetime.now() > expires_at
        except:
            return True
    
    def can_resend_code(self, email: str) -> Tuple[bool, str]:
        """
        Check if user can request a new verification code.
        
        Args:
            email (str): Email address
            
        Returns:
            Tuple[bool, str]: (can_resend, message)
        """
        verification_data = self.get_verification_data(email)
        
        if not verification_data:
            return True, "No previous verification found"
        
        # Check if already verified
        if verification_data.get('verified', False):
            return False, "Email already verified"
        
        # Check resend cooldown
        try:
            created_at = datetime.fromisoformat(verification_data['created_at'])
            cooldown_end = created_at + timedelta(minutes=self.resend_cooldown_minutes)
            
            if datetime.now() < cooldown_end:
                remaining_seconds = int((cooldown_end - datetime.now()).total_seconds())
                return False, f"Please wait {remaining_seconds} seconds before requesting a new code"
        except:
            pass
        
        # Check resend limit (max 5 resends per hour)
        resend_count = verification_data.get('resend_count', 0)
        if resend_count >= 5:
            return False, "Too many verification attempts. Please try again later."
        
        return True, "Can resend verification code"
    
    def send_verification_code(self, email: str, username: str = None) -> Dict[str, any]:
        """
        Generate and send verification code via email.
        
        Args:
            email (str): Email address
            username (str): Username for personalization
            
        Returns:
            Dict containing send result
        """
        try:
            # Check if can resend
            can_resend, message = self.can_resend_code(email)
            if not can_resend:
                return {
                    'success': False,
                    'message': message,
                    'error_type': 'rate_limit'
                }
            
            # Generate new code
            code = self.generate_verification_code()
            
            # Store code
            store_result = self.store_verification_code(email, code)
            if not store_result['success']:
                return store_result
            
            # Update resend count
            verification_data = self.get_verification_data(email)
            if verification_data:
                resend_count = verification_data.get('resend_count', 0) + 1
                email_key = email.lower().strip().replace('.', '_').replace('@', '_at_')
                self.db_ref.child('email_verifications').child(email_key).child('resend_count').set(resend_count)
            
            # Send email
            email_result = self.send_verification_email(email, code, username)
            
            if email_result['success']:
                return {
                    'success': True,
                    'message': 'Verification code sent successfully',
                    'expires_in_minutes': self.code_expiry_minutes
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to send verification email: {email_result["message"]}',
                    'error_type': 'email_send_failed'
                }
                
        except Exception as e:
            logger.error(f'Failed to send verification code to {email}: {str(e)}')
            return {
                'success': False,
                'message': f'Verification system error: {str(e)}',
                'error_type': 'system_error'
            }
    
    def verify_code(self, email: str, submitted_code: str) -> Dict[str, any]:
        """
        Verify submitted code against stored code.
        
        Args:
            email (str): Email address
            submitted_code (str): Code submitted by user
            
        Returns:
            Dict containing verification result
        """
        try:
            # Get verification data
            verification_data = self.get_verification_data(email)
            
            if not verification_data:
                return {
                    'success': False,
                    'message': 'No verification code found. Please request a new code.',
                    'error_type': 'no_code'
                }
            
            # Check if already verified
            if verification_data.get('verified', False):
                return {
                    'success': True,
                    'message': 'Email already verified',
                    'already_verified': True
                }
            
            # Check if expired
            if self.is_code_expired(verification_data):
                return {
                    'success': False,
                    'message': 'Verification code has expired. Please request a new code.',
                    'error_type': 'expired'
                }
            
            # Check attempt limit
            attempts = verification_data.get('attempts', 0)
            if attempts >= self.max_attempts:
                return {
                    'success': False,
                    'message': 'Too many failed attempts. Please request a new code.',
                    'error_type': 'too_many_attempts'
                }
            
            # Verify code
            stored_code = verification_data.get('code', '')
            if submitted_code.strip() == stored_code:
                # Mark as verified
                email_key = email.lower().strip().replace('.', '_').replace('@', '_at_')
                self.db_ref.child('email_verifications').child(email_key).update({
                    'verified': True,
                    'verified_at': datetime.now().isoformat()
                })
                
                logger.info(f'Email verification successful for {email}')
                
                return {
                    'success': True,
                    'message': 'Email verified successfully!',
                    'verified': True
                }
            else:
                # Increment attempts
                new_attempts = attempts + 1
                email_key = email.lower().strip().replace('.', '_').replace('@', '_at_')
                self.db_ref.child('email_verifications').child(email_key).child('attempts').set(new_attempts)
                
                remaining_attempts = self.max_attempts - new_attempts
                
                return {
                    'success': False,
                    'message': f'Invalid verification code. {remaining_attempts} attempts remaining.',
                    'error_type': 'invalid_code',
                    'remaining_attempts': remaining_attempts
                }
                
        except Exception as e:
            logger.error(f'Failed to verify code for {email}: {str(e)}')
            return {
                'success': False,
                'message': f'Verification system error: {str(e)}',
                'error_type': 'system_error'
            }
    
    def is_email_verified(self, email: str) -> bool:
        """
        Check if email has been verified.
        
        Args:
            email (str): Email address
            
        Returns:
            bool: True if verified
        """
        verification_data = self.get_verification_data(email)
        if verification_data:
            return verification_data.get('verified', False)
        return False
    
    def send_verification_email(self, email: str, code: str, username: str = None) -> Dict[str, any]:
        """
        Send verification code email.
        
        Args:
            email (str): Email address
            code (str): Verification code
            username (str): Username for personalization
            
        Returns:
            Dict containing send result
        """
        try:
            # Create verification email
            msg = email_service.create_verification_email(email, code, username)
            
            # Send email
            result = email_service.send_email(msg)
            
            return result
            
        except Exception as e:
            logger.error(f'Failed to send verification email to {email}: {str(e)}')
            return {
                'success': False,
                'message': f'Failed to send verification email: {str(e)}'
            }

# Global email verification service instance
email_verification_service = EmailVerificationService()
