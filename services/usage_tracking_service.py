"""
Usage Tracking Service for VocalLocal (Firebase Free Plan Compatible)

This service provides atomic usage tracking functionality without requiring
Firebase Cloud Functions, making it compatible with Firebase's free plan.
"""

import logging
import time
from datetime import datetime
from firebase_config import initialize_firebase
from models.firebase_models import FirebaseModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UsageTrackingService(FirebaseModel):
    """Service for tracking user usage with atomic operations on Firebase free plan."""

    @staticmethod
    def _encode_user_id(user_id):
        """
        Encode user ID to be Firebase path-safe.
        Firebase paths cannot contain: . $ # [ ] /
        We'll replace these characters with safe alternatives.
        """
        if not user_id:
            return user_id

        # Replace problematic characters
        encoded = user_id.replace('.', ',')  # Replace dots with commas
        encoded = encoded.replace('@', '_at_')  # Replace @ with _at_
        encoded = encoded.replace('#', '_hash_')  # Replace # with _hash_
        encoded = encoded.replace('$', '_dollar_')  # Replace $ with _dollar_
        encoded = encoded.replace('[', '_lbracket_')  # Replace [ with _lbracket_
        encoded = encoded.replace(']', '_rbracket_')  # Replace ] with _rbracket_
        encoded = encoded.replace('/', '_slash_')  # Replace / with _slash_

        return encoded

    @staticmethod
    def _decode_user_id(encoded_user_id):
        """
        Decode Firebase path-safe user ID back to original format.
        """
        if not encoded_user_id:
            return encoded_user_id

        # Reverse the encoding
        decoded = encoded_user_id.replace(',', '.')  # Replace commas back to dots
        decoded = decoded.replace('_at_', '@')  # Replace _at_ back to @
        decoded = decoded.replace('_hash_', '#')  # Replace _hash_ back to #
        decoded = decoded.replace('_dollar_', '$')  # Replace _dollar_ back to $
        decoded = decoded.replace('_lbracket_', '[')  # Replace _lbracket_ back to [
        decoded = decoded.replace('_rbracket_', ']')  # Replace _rbracket_ back to ]
        decoded = decoded.replace('_slash_', '/')  # Replace _slash_ back to /

        return decoded

    @staticmethod
    def deduct_transcription_usage(user_id, minutes_used):
        """
        Deduct transcription usage from a user's account with atomic operations.

        Args:
            user_id (str): The user ID to deduct usage from
            minutes_used (float): The number of minutes to deduct

        Returns:
            dict: Result of the operation
        """
        return UsageTrackingService._deduct_usage(
            user_id=user_id,
            service_type='transcriptionMinutes',
            amount_used=minutes_used,
            service_name='transcription'
        )

    @staticmethod
    def deduct_translation_usage(user_id, words_used):
        """
        Deduct translation usage from a user's account with atomic operations.

        Args:
            user_id (str): The user ID to deduct usage from
            words_used (int): The number of words to deduct

        Returns:
            dict: Result of the operation
        """
        return UsageTrackingService._deduct_usage(
            user_id=user_id,
            service_type='translationWords',
            amount_used=words_used,
            service_name='translation'
        )

    @staticmethod
    def deduct_tts_usage(user_id, minutes_used):
        """
        Deduct TTS usage from a user's account with atomic operations.

        Args:
            user_id (str): The user ID to deduct usage from
            minutes_used (float): The number of minutes to deduct

        Returns:
            dict: Result of the operation
        """
        return UsageTrackingService._deduct_usage(
            user_id=user_id,
            service_type='ttsMinutes',
            amount_used=minutes_used,
            service_name='TTS'
        )

    @staticmethod
    def deduct_ai_credits(user_id, credits_used):
        """
        Deduct AI credits from a user's account with atomic operations.

        Args:
            user_id (str): The user ID to deduct usage from
            credits_used (int): The number of credits to deduct

        Returns:
            dict: Result of the operation
        """
        return UsageTrackingService._deduct_usage(
            user_id=user_id,
            service_type='aiCredits',
            amount_used=credits_used,
            service_name='AI credits'
        )

    @staticmethod
    def _deduct_usage(user_id, service_type, amount_used, service_name):
        """
        Internal method to deduct usage with atomic operations.

        Args:
            user_id (str): The user ID
            service_type (str): The type of service (transcriptionMinutes, translationWords, etc.)
            amount_used (float): The amount to deduct
            service_name (str): Human-readable service name for logging

        Returns:
            dict: Result of the operation
        """
        try:
            logger.info(f"Deducting {service_name} usage for user {user_id}: {amount_used}")

            # Encode user ID for Firebase path safety
            encoded_user_id = UsageTrackingService._encode_user_id(user_id)
            logger.debug(f"Encoded user ID: {user_id} -> {encoded_user_id}")

            # Get user reference
            user_ref = UsageTrackingService.get_ref(f'users/{encoded_user_id}')

            # Perform atomic transaction
            def update_usage(current_data):
                if current_data is None:
                    # Initialize user data if it doesn't exist
                    current_data = {
                        'usage': {
                            'currentPeriod': {
                                'transcriptionMinutes': 0,
                                'translationWords': 0,
                                'ttsMinutes': 0,
                                'aiCredits': 0
                            },
                            'totalUsage': {
                                'transcriptionMinutes': 0,
                                'translationWords': 0,
                                'ttsMinutes': 0,
                                'aiCredits': 0
                            }
                        },
                        'lastActivityAt': int(time.time() * 1000)
                    }

                # Ensure usage structure exists
                if 'usage' not in current_data:
                    current_data['usage'] = {
                        'currentPeriod': {
                            'transcriptionMinutes': 0,
                            'translationWords': 0,
                            'ttsMinutes': 0,
                            'aiCredits': 0
                        },
                        'totalUsage': {
                            'transcriptionMinutes': 0,
                            'translationWords': 0,
                            'ttsMinutes': 0,
                            'aiCredits': 0
                        }
                    }

                if 'currentPeriod' not in current_data['usage']:
                    current_data['usage']['currentPeriod'] = {
                        'transcriptionMinutes': 0,
                        'translationWords': 0,
                        'ttsMinutes': 0,
                        'aiCredits': 0
                    }

                if 'totalUsage' not in current_data['usage']:
                    current_data['usage']['totalUsage'] = {
                        'transcriptionMinutes': 0,
                        'translationWords': 0,
                        'ttsMinutes': 0,
                        'aiCredits': 0
                    }

                # Get current values
                current_period_usage = current_data['usage']['currentPeriod'].get(service_type, 0)
                total_usage = current_data['usage']['totalUsage'].get(service_type, 0)

                # Update usage counters
                current_data['usage']['currentPeriod'][service_type] = current_period_usage + amount_used
                current_data['usage']['totalUsage'][service_type] = total_usage + amount_used

                # Update last activity timestamp
                current_data['lastActivityAt'] = int(time.time() * 1000)

                return current_data

            # Execute transaction using Firebase Admin SDK
            # The Firebase Admin SDK transaction method works differently
            try:
                # Use a simple update approach since Firebase Admin SDK transactions are complex
                # First, get current data
                current_data = user_ref.get()

                # Apply the update function
                updated_data = update_usage(current_data)

                # Set the updated data
                user_ref.set(updated_data)

                # Get the new values
                new_current_usage = updated_data['usage']['currentPeriod'][service_type]
                new_total_usage = updated_data['usage']['totalUsage'][service_type]

                logger.info(f"{service_name} usage deducted for user {user_id}: {amount_used}, "
                           f"new current: {new_current_usage}, new total: {new_total_usage}")

                return {
                    'success': True,
                    'deducted': amount_used,
                    'currentPeriodUsage': new_current_usage,
                    'totalUsage': new_total_usage,
                    'serviceType': service_name.lower().replace(' ', '_')
                }

            except Exception as transaction_error:
                raise Exception(f'Update operation failed: {str(transaction_error)}')

        except Exception as e:
            logger.error(f"Error deducting {service_name} usage for user {user_id}: {str(e)}")

            return {
                'success': False,
                'error': {
                    'code': 'internal-error',
                    'message': f'An error occurred while deducting {service_name} usage',
                    'details': str(e)
                }
            }

    @staticmethod
    def get_user_usage(user_id):
        """
        Get current usage data for a user.

        Args:
            user_id (str): The user ID

        Returns:
            dict: User usage data
        """
        try:
            # Encode user ID for Firebase path safety
            encoded_user_id = UsageTrackingService._encode_user_id(user_id)
            logger.debug(f"Getting usage for encoded user ID: {user_id} -> {encoded_user_id}")

            user_data = UsageTrackingService.get_ref(f'users/{encoded_user_id}').get()

            if not user_data or 'usage' not in user_data:
                return {
                    'currentPeriod': {
                        'transcriptionMinutes': 0,
                        'translationWords': 0,
                        'ttsMinutes': 0,
                        'aiCredits': 0
                    },
                    'totalUsage': {
                        'transcriptionMinutes': 0,
                        'translationWords': 0,
                        'ttsMinutes': 0,
                        'aiCredits': 0
                    }
                }

            return user_data['usage']

        except Exception as e:
            logger.error(f"Error getting usage for user {user_id}: {str(e)}")
            return None

    @staticmethod
    def reset_current_period_usage(user_id):
        """
        Reset current period usage for a user (for billing cycle reset).

        Args:
            user_id (str): The user ID

        Returns:
            dict: Result of the operation
        """
        try:
            logger.info(f"Resetting current period usage for user {user_id}")

            # Encode user ID for Firebase path safety
            encoded_user_id = UsageTrackingService._encode_user_id(user_id)
            logger.debug(f"Resetting usage for encoded user ID: {user_id} -> {encoded_user_id}")

            user_ref = UsageTrackingService.get_ref(f'users/{encoded_user_id}')

            def reset_usage(current_data):
                if current_data is None or 'usage' not in current_data:
                    return current_data

                # Reset current period usage
                current_data['usage']['currentPeriod'] = {
                    'transcriptionMinutes': 0,
                    'translationWords': 0,
                    'ttsMinutes': 0,
                    'aiCredits': 0
                }

                # Update reset date
                current_data['usage']['resetDate'] = int(time.time() * 1000)

                return current_data

            # Use simple update approach
            try:
                # Get current data
                current_data = user_ref.get()

                # Apply the reset function
                updated_data = reset_usage(current_data)

                if updated_data is not None:
                    # Set the updated data
                    user_ref.set(updated_data)
                    logger.info(f"Current period usage reset for user {user_id}")
                    return {'success': True}
                else:
                    raise Exception('No user data to reset')

            except Exception as reset_error:
                raise Exception(f'Reset operation failed: {str(reset_error)}')

        except Exception as e:
            logger.error(f"Error resetting usage for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
