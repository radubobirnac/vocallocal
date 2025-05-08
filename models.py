"""
Database models for VocalLocal application.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(db.Model, UserMixin):
    """User model for authentication."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # OAuth related fields
    oauth_provider = db.Column(db.String(20), nullable=True)  # 'google', 'github', etc.
    oauth_id = db.Column(db.String(100), nullable=True, index=True)
    
    def __init__(self, username, email, password=None, is_admin=False, 
                 oauth_provider=None, oauth_id=None):
        self.username = username
        self.email = email
        self.is_admin = is_admin
        self.oauth_provider = oauth_provider
        self.oauth_id = oauth_id
        
        # Only set password if provided (for OAuth users, password might be None)
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against stored hash."""
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'oauth_provider': self.oauth_provider
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class UserActivity(db.Model):
    """Model to track user activity."""
    
    __tablename__ = 'user_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # 'transcription', 'translation', etc.
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('activities', lazy=True))
    
    def __repr__(self):
        return f'<UserActivity {self.activity_type} by User {self.user_id}>'
