"""
Main routes for VocalLocal
"""
from flask import Blueprint, render_template, redirect, url_for, send_from_directory, current_app
from flask_login import current_user, login_required

# Create a blueprint for the main routes
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Main index route - handles both authenticated and non-authenticated users."""
    if current_user.is_authenticated:
        # User is logged in, show the main application
        return render_template('index.html')
    else:
        # User is not logged in, redirect to login page
        return redirect(url_for('auth_routes.login'))

@bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('profile.html', user=current_user)

@bp.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('static', path)
