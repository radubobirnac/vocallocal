"""
History Service for VocalLocal

Provides improved data retrieval for transcriptions and translations
with better error handling, sorting, and pagination.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# Try different import paths for Firebase models
try:
    from firebase_models import Transcription, Translation
except ImportError:
    try:
        from models.firebase_models import Transcription, Translation
    except ImportError:
        try:
            from vocallocal.models.firebase_models import Transcription, Translation
        except ImportError:
            # Create fallback classes if imports fail
            class Transcription:
                @staticmethod
                def get_ref(path):
                    class RefObj:
                        @staticmethod
                        def get():
                            return {}
                        @staticmethod
                        def order_by_child(field):
                            return RefObj()
                        @staticmethod
                        def limit_to_last(limit):
                            return RefObj()
                        @staticmethod
                        def limit_to_first(limit):
                            return RefObj()
                    return RefObj()

            class Translation:
                @staticmethod
                def get_ref(path):
                    class RefObj:
                        @staticmethod
                        def get():
                            return {}
                        @staticmethod
                        def order_by_child(field):
                            return RefObj()
                        @staticmethod
                        def limit_to_last(limit):
                            return RefObj()
                        @staticmethod
                        def limit_to_first(limit):
                            return RefObj()
                    return RefObj()

logger = logging.getLogger(__name__)

class HistoryService:
    """Service for managing user history data with improved error handling."""

    @staticmethod
    def get_user_transcriptions(user_email: str, limit: int = 100, sort_desc: bool = True) -> Dict[str, Any]:
        """
        Get user transcriptions with improved error handling and sorting.

        Args:
            user_email: User's email address
            limit: Maximum number of items to retrieve
            sort_desc: Sort in descending order (newest first)

        Returns:
            Dictionary of transcriptions with metadata
        """
        user_id = user_email.replace('.', ',')
        transcriptions = {}
        error_info = None

        try:
            # First attempt: Try with Firebase ordering (requires index)
            logger.info(f"Attempting to fetch transcriptions with ordering for user: {user_email}")

            if sort_desc:
                transcriptions = Transcription.get_ref(f'transcriptions/{user_id}').order_by_child('timestamp').limit_to_last(limit).get()
            else:
                transcriptions = Transcription.get_ref(f'transcriptions/{user_id}').order_by_child('timestamp').limit_to_first(limit).get()

            if transcriptions:
                logger.info(f"Successfully fetched {len(transcriptions)} transcriptions with ordering")
                return {
                    'data': transcriptions,
                    'sorted': True,
                    'method': 'firebase_ordered',
                    'count': len(transcriptions)
                }

        except Exception as e:
            error_info = str(e)
            logger.warning(f"Firebase ordering failed: {error_info}")

            # Check if it's an indexing error
            if "index not defined" in error_info.lower() or "indexon" in error_info.lower():
                logger.warning("Indexing error detected - falling back to manual sorting")

        try:
            # Second attempt: Fetch all data without ordering and sort manually
            logger.info("Attempting to fetch transcriptions without ordering")
            transcriptions = Transcription.get_ref(f'transcriptions/{user_id}').get()

            if transcriptions:
                # Convert to list for sorting
                transcription_list = []
                for key, item in transcriptions.items():
                    item['_key'] = key
                    transcription_list.append(item)

                # Sort by timestamp
                transcription_list.sort(
                    key=lambda x: HistoryService._parse_timestamp(x.get('timestamp', '')),
                    reverse=sort_desc
                )

                # Convert back to dictionary and limit results
                sorted_transcriptions = {}
                for i, item in enumerate(transcription_list[:limit]):
                    key = item.pop('_key')
                    sorted_transcriptions[key] = item

                logger.info(f"Successfully fetched and sorted {len(sorted_transcriptions)} transcriptions manually")
                return {
                    'data': sorted_transcriptions,
                    'sorted': True,
                    'method': 'manual_sorted',
                    'count': len(sorted_transcriptions),
                    'total_available': len(transcription_list)
                }
            else:
                logger.info("No transcriptions found for user")
                return {
                    'data': {},
                    'sorted': True,
                    'method': 'empty',
                    'count': 0
                }

        except Exception as e2:
            logger.error(f"Failed to fetch transcriptions without ordering: {str(e2)}")
            return {
                'data': {},
                'sorted': False,
                'method': 'failed',
                'count': 0,
                'error': str(e2),
                'original_error': error_info
            }

    @staticmethod
    def get_user_translations(user_email: str, limit: int = 100, sort_desc: bool = True) -> Dict[str, Any]:
        """
        Get user translations with improved error handling and sorting.

        Args:
            user_email: User's email address
            limit: Maximum number of items to retrieve
            sort_desc: Sort in descending order (newest first)

        Returns:
            Dictionary of translations with metadata
        """
        user_id = user_email.replace('.', ',')
        translations = {}
        error_info = None

        try:
            # First attempt: Try with Firebase ordering (requires index)
            logger.info(f"Attempting to fetch translations with ordering for user: {user_email}")

            if sort_desc:
                translations = Translation.get_ref(f'translations/{user_id}').order_by_child('timestamp').limit_to_last(limit).get()
            else:
                translations = Translation.get_ref(f'translations/{user_id}').order_by_child('timestamp').limit_to_first(limit).get()

            if translations:
                logger.info(f"Successfully fetched {len(translations)} translations with ordering")
                return {
                    'data': translations,
                    'sorted': True,
                    'method': 'firebase_ordered',
                    'count': len(translations)
                }

        except Exception as e:
            error_info = str(e)
            logger.warning(f"Firebase ordering failed: {error_info}")

        try:
            # Second attempt: Fetch all data without ordering and sort manually
            logger.info("Attempting to fetch translations without ordering")
            translations = Translation.get_ref(f'translations/{user_id}').get()

            if translations:
                # Convert to list for sorting
                translation_list = []
                for key, item in translations.items():
                    item['_key'] = key
                    translation_list.append(item)

                # Sort by timestamp
                translation_list.sort(
                    key=lambda x: HistoryService._parse_timestamp(x.get('timestamp', '')),
                    reverse=sort_desc
                )

                # Convert back to dictionary and limit results
                sorted_translations = {}
                for i, item in enumerate(translation_list[:limit]):
                    key = item.pop('_key')
                    sorted_translations[key] = item

                logger.info(f"Successfully fetched and sorted {len(sorted_translations)} translations manually")
                return {
                    'data': sorted_translations,
                    'sorted': True,
                    'method': 'manual_sorted',
                    'count': len(sorted_translations),
                    'total_available': len(translation_list)
                }
            else:
                logger.info("No translations found for user")
                return {
                    'data': {},
                    'sorted': True,
                    'method': 'empty',
                    'count': 0
                }

        except Exception as e2:
            logger.error(f"Failed to fetch translations without ordering: {str(e2)}")
            return {
                'data': {},
                'sorted': False,
                'method': 'failed',
                'count': 0,
                'error': str(e2),
                'original_error': error_info
            }

    @staticmethod
    def get_combined_history(user_email: str, limit: int = 100, sort_desc: bool = True) -> Dict[str, Any]:
        """
        Get combined transcriptions and translations history.

        Args:
            user_email: User's email address
            limit: Maximum number of items to retrieve total
            sort_desc: Sort in descending order (newest first)

        Returns:
            Combined and sorted history data
        """
        # Get transcriptions and translations
        transcriptions_result = HistoryService.get_user_transcriptions(user_email, limit, sort_desc)
        translations_result = HistoryService.get_user_translations(user_email, limit, sort_desc)

        # Combine data
        combined_items = []

        # Add transcriptions
        for key, item in transcriptions_result['data'].items():
            combined_items.append({
                'id': key,
                'type': 'transcription',
                'data': item,
                'timestamp': item.get('timestamp', ''),
                'parsed_timestamp': HistoryService._parse_timestamp(item.get('timestamp', ''))
            })

        # Add translations
        for key, item in translations_result['data'].items():
            combined_items.append({
                'id': key,
                'type': 'translation',
                'data': item,
                'timestamp': item.get('timestamp', ''),
                'parsed_timestamp': HistoryService._parse_timestamp(item.get('timestamp', ''))
            })

        # Sort combined items
        combined_items.sort(key=lambda x: x['parsed_timestamp'], reverse=sort_desc)

        # Limit results
        limited_items = combined_items[:limit]

        return {
            'items': limited_items,
            'transcriptions_count': transcriptions_result['count'],
            'translations_count': translations_result['count'],
            'total_count': len(limited_items),
            'total_available': len(combined_items),
            'transcriptions_method': transcriptions_result['method'],
            'translations_method': translations_result['method'],
            'sorted': True
        }

    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> datetime:
        """
        Parse timestamp string to datetime object.

        Args:
            timestamp_str: ISO format timestamp string

        Returns:
            datetime object, or epoch if parsing fails
        """
        if not timestamp_str:
            return datetime.fromtimestamp(0)

        try:
            # Try ISO format first
            if 'T' in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                # Try other common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S']:
                    try:
                        return datetime.strptime(timestamp_str, fmt)
                    except ValueError:
                        continue

            # If all else fails, try to parse as float (Unix timestamp)
            return datetime.fromtimestamp(float(timestamp_str))

        except (ValueError, TypeError):
            logger.warning(f"Failed to parse timestamp: {timestamp_str}")
            return datetime.fromtimestamp(0)
