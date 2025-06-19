"""
VocalLocal Configuration Module
"""
import os
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Application configuration
class Config:
    # Basic Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

    # Upload settings
    UPLOAD_FOLDER = tempfile.gettempdir()
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'm4a', 'mp4', 'webm'}
    # Note: We don't set MAX_CONTENT_LENGTH to allow larger files
    # API-specific limits are handled in the service layer:
    # - OpenAI API: 25MB limit (automatically switches to Gemini for larger files)
    # - Gemini API: 200MB limit (files larger than this should be split)

    # API keys and services
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    # Stripe payment configuration
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

    # Feature flags
    GEMINI_AVAILABLE = True  # Will be updated at runtime
    METRICS_AVAILABLE = True  # Will be updated at runtime

    # Server settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5001))

    @staticmethod
    def allowed_file(filename):
        """Check if a filename has an allowed extension"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
