"""
Socket.IO configuration and initialization for VocalLocal real-time communication
"""

import os
from flask_socketio import SocketIO
from flask import request
from flask_login import current_user
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SocketIO instance
socketio = None

def init_socketio(app):
    """Initialize Socket.IO with the Flask app"""
    global socketio

    # Configure Socket.IO with appropriate settings
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",  # Configure based on your deployment needs
        async_mode='threading',    # Use threading for better compatibility
        logger=True,
        engineio_logger=True,
        ping_timeout=60,
        ping_interval=25
    )

    # Register Socket.IO event handlers
    from socketio_handlers import register_socketio_handlers
    register_socketio_handlers(socketio)

    # Register connection handlers
    register_connection_handlers(socketio)

    logger.info("Socket.IO initialized successfully")
    return socketio

def get_socketio():
    """Get the Socket.IO instance"""
    return socketio

def register_connection_handlers(socketio_instance):
    """Register connection event handlers after Socket.IO is initialized"""

    @socketio_instance.event
    def connect(auth):
        """Handle client connection"""
        if not current_user.is_authenticated:
            logger.warning(f"Unauthorized connection attempt from {request.sid}")
            return False

        logger.info(f"User {current_user.email} connected with session ID: {request.sid}")
        return True

    @socketio_instance.event
    def disconnect():
        """Handle client disconnection"""
        if current_user.is_authenticated:
            logger.info(f"User {current_user.email} disconnected from session ID: {request.sid}")
        else:
            logger.info(f"Anonymous user disconnected from session ID: {request.sid}")
