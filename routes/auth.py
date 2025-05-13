"""
Authentication routes for VocalLocal
"""
import traceback
from flask import Blueprint, redirect, url_for, flash

# Create a blueprint for the auth routes with a unique name
bp = Blueprint('auth_routes', __name__, url_prefix='/auth')

@bp.route('/google')
def google_login():
    """Redirect to the auth blueprint's Google login route."""
    # Import the login handler function from auth module
    from auth import google_login as auth_google_login
    return auth_google_login()

@bp.route('/callback')
def auth_callback():
    """Handle the Google OAuth callback directly."""
    try:
        # Import the callback handler function
        from auth import _handle_google_callback

        # Call the handler function directly
        return _handle_google_callback()
    except Exception as e:
        print(f"Error in auth_callback: {str(e)}")
        print(traceback.format_exc())
        flash("Error during authentication. Please try again.", "danger")
        return redirect(url_for('auth_routes.login'))
