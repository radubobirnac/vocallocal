"""
Room cleanup service for automatic maintenance of conversation rooms
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from models.firebase_models import ConversationRoom, ConversationMessage

# Configure logging
logger = logging.getLogger(__name__)

class RoomCleanupService:
    """Service for managing automatic room cleanup"""
    
    def __init__(self, cleanup_interval_minutes=10, inactive_threshold_minutes=5):
        self.cleanup_interval_minutes = cleanup_interval_minutes
        self.inactive_threshold_minutes = inactive_threshold_minutes
        self.cleanup_thread = None
        self.running = False
    
    def start(self):
        """Start the cleanup service"""
        if self.running:
            logger.warning("Room cleanup service is already running")
            return
        
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        logger.info(f"Room cleanup service started (interval: {self.cleanup_interval_minutes} min, threshold: {self.inactive_threshold_minutes} min)")
    
    def stop(self):
        """Stop the cleanup service"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        logger.info("Room cleanup service stopped")
    
    def _cleanup_loop(self):
        """Main cleanup loop"""
        while self.running:
            try:
                self.cleanup_inactive_rooms()
                # Sleep for the specified interval
                time.sleep(self.cleanup_interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                # Sleep for a shorter time on error to retry sooner
                time.sleep(60)
    
    def cleanup_inactive_rooms(self):
        """Clean up inactive rooms"""
        try:
            cleaned_count = ConversationRoom.cleanup_inactive_rooms(self.inactive_threshold_minutes)
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} inactive rooms")
            return cleaned_count
        except Exception as e:
            logger.error(f"Error during room cleanup: {str(e)}")
            return 0
    
    def cleanup_old_messages(self, days_old=7):
        """Clean up old conversation messages (optional)"""
        try:
            # This would require additional implementation in ConversationMessage model
            # For now, we'll just log that this feature is available
            logger.info(f"Message cleanup for messages older than {days_old} days is not yet implemented")
            return 0
        except Exception as e:
            logger.error(f"Error during message cleanup: {str(e)}")
            return 0
    
    def get_room_statistics(self):
        """Get statistics about current rooms"""
        try:
            # This would require additional queries to Firebase
            # For now, return basic info
            stats = {
                'cleanup_interval_minutes': self.cleanup_interval_minutes,
                'inactive_threshold_minutes': self.inactive_threshold_minutes,
                'service_running': self.running,
                'last_cleanup': datetime.now().isoformat()
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting room statistics: {str(e)}")
            return {}

# Global instance
room_cleanup_service = RoomCleanupService()

def start_room_cleanup_service():
    """Start the global room cleanup service"""
    room_cleanup_service.start()

def stop_room_cleanup_service():
    """Stop the global room cleanup service"""
    room_cleanup_service.stop()

def get_room_cleanup_stats():
    """Get room cleanup statistics"""
    return room_cleanup_service.get_room_statistics()

# Auto-start the service when the module is imported
# This ensures cleanup runs automatically when the app starts
def initialize_cleanup_service():
    """Initialize the cleanup service with app context"""
    try:
        start_room_cleanup_service()
        logger.info("Room cleanup service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize room cleanup service: {str(e)}")

# Call initialization when module is imported
# initialize_cleanup_service()  # Commented out for now - will be called from app.py
