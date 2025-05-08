"""Authentication module for VocalLocal."""
import os
from functools import wraps
from flask import Blueprint, redirect, url_for, session, request, flash, render_template
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from firebase_models import User, UserActivity

# Initialize login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

# Initialize OAuth
oauth = OAuth()

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Google OAuth instance
google = None

@login_manager.user_loader
def load_user(user_id):
    """Load user from Firebase by email."""
    user_data = User.get_by_email(user_id)
    if not user_data:
        return None

    # Create user object compatible with Flask-Login
    class UserObject:
        def __init__(self, email, data):
            self.id = email
            self.email = email
            self.username = data.get('username')
            self.is_admin = data.get('is_admin', False)
            self.password_hash = data.get('password_hash')

        def is_authenticated(self):
            return True

        def is_active(self):
            return True

        def is_anonymous(self):
            return False

        def get_id(self):
            return self.id

        def check_password(self, password):
            if not self.password_hash:
                return False
            return check_password_hash(self.password_hash, password)

    return UserObject(user_id, user_data)

def init_app(app):
    """Initialize authentication with the Flask app."""
    global google

    # Initialize login manager
    login_manager.init_app(app)

    # Initialize OAuth
    oauth.init_app(app)

    # Register blueprint
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Configure Google OAuth
    try:
        # Try to load OAuth credentials from Oauth.json file
        oauth_file_path = os.path.join(os.path.dirname(__file__), 'Oauth.json')
        if os.path.exists(oauth_file_path):
            import json
            with open(oauth_file_path, 'r') as f:
                oauth_data = json.load(f)

            if 'web' in oauth_data:
                web_config = oauth_data['web']
                client_id = web_config.get('client_id')
                client_secret = web_config.get('client_secret')
                redirect_uris = web_config.get('redirect_uris', [])

                if client_id and client_secret:
                    # Register the OAuth provider
                    oauth.register(
                        name='google',
                        client_id=client_id,
                        client_secret=client_secret,
                        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                        client_kwargs={'scope': 'openid email profile'},
                    )
                    google = oauth.google
                    app.logger.info("Google OAuth configured successfully from Oauth.json")

                    # Log the redirect URIs for debugging
                    app.logger.info(f"Configured redirect URIs: {redirect_uris}")
                else:
                    app.logger.warning("Invalid OAuth.json: missing client_id or client_secret")
            else:
                app.logger.warning("Invalid OAuth.json format: missing 'web' key")
        else:
            # Fall back to environment variables
            google_client_id = os.getenv('GOOGLE_CLIENT_ID')
            google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

            if google_client_id and google_client_secret:
                oauth.register(
                    name='google',
                    client_id=google_client_id,
                    client_secret=google_client_secret,
                    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                    client_kwargs={'scope': 'openid email profile'},
                )
                google = oauth.google
                app.logger.info("Google OAuth configured successfully from environment variables")
            else:
                app.logger.warning("Google OAuth not configured: missing client ID or secret")
    except Exception as e:
        app.logger.error(f"Error configuring Google OAuth: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())

    # Create admin user if it doesn't exist
    with app.app_context():
        try:
            admin_username = os.getenv('ADMIN_USERNAME', 'admin')
            admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
            admin_password = os.getenv('ADMIN_PASSWORD')

            if admin_password:
                try:
                    # Check if admin exists - with error handling
                    try:
                        admin_user = User.get_by_email(admin_email)
                    except Exception as e:
                        app.logger.error(f"Error checking for admin user: {str(e)}")
                        admin_user = None

                    if not admin_user:
                        try:
                            # Create admin user in Firebase
                            password_hash = generate_password_hash(admin_password)
                            User.create(
                                username=admin_username,
                                email=admin_email,
                                password_hash=password_hash,
                                is_admin=True
                            )
                            app.logger.info(f"Created admin user: {admin_username}")
                        except Exception as create_error:
                            app.logger.error(f"Error creating admin user: {str(create_error)}")
                except Exception as e:
                    app.logger.error(f"Error checking/creating admin user: {str(e)}")
                    # Continue with app initialization even if admin user creation fails
                    import traceback
                    app.logger.error(traceback.format_exc())
        except Exception as e:
            app.logger.error(f"Error in auth initialization: {str(e)}")
            # Continue with app initialization even if there's an error
            import traceback
            app.logger.error(traceback.format_exc())

# Routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login route."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False) == 'on'

        # Check if username is actually an email
        if '@' in username:
            email = username
        else:
            # Try to find user by username
            users = User.get_all_users()
            email = None
            for user in users:
                if user.get('username') == username:
                    email = user.get('email')
                    break

            if not email:
                flash('Invalid username or password', 'danger')
                return render_template('login.html')

        user_data = User.get_by_email(email)

        if user_data and check_password_hash(user_data.get('password_hash', ''), password):
            # Create user object
            class UserObject:
                def __init__(self, email, data):
                    self.id = email
                    self.email = email
                    self.username = data.get('username')
                    self.is_admin = data.get('is_admin', False)
                    self._data = data  # Store the full user data

                def is_authenticated(self):
                    return True

                def is_active(self):
                    return True

                def is_anonymous(self):
                    return False

                def get_id(self):
                    return self.id

                def check_password(self, password):
                    """Check if the provided password matches the stored hash."""
                    password_hash = self._data.get('password_hash', '')
                    return check_password_hash(password_hash, password)

            user = UserObject(email, user_data)
            login_user(user, remember=remember)

            # Log activity
            UserActivity.log(
                user_email=email,
                activity_type='login',
                details='Manual login'
            )

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))

        flash('Invalid email or password', 'danger')

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register route."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate input
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')

        # Check if email already exists
        if User.get_by_email(email):
            flash('Email already exists', 'danger')
            return render_template('register.html')

        # Create new user
        password_hash = generate_password_hash(password)
        User.create(
            username=username,
            email=email,
            password_hash=password_hash
        )

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout route."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/google')
@auth_bp.route('/auth/google')  # Add this route to match potential OAuth.json redirect URI
def google_login():
    """Google OAuth login route."""
    try:
        # Make sure Google OAuth is configured
        if not google:
            flash("Google OAuth is not configured properly. Please contact the administrator.", "danger")
            return redirect(url_for('auth.login'))

        # Try to get redirect URI from OAuth.json
        oauth_file_path = os.path.join(os.path.dirname(__file__), 'Oauth.json')
        redirect_uri = None

        if os.path.exists(oauth_file_path):
            try:
                import json
                with open(oauth_file_path, 'r') as f:
                    oauth_data = json.load(f)

                if 'web' in oauth_data and 'redirect_uris' in oauth_data['web']:
                    # Find the callback URI that matches our route
                    for uri in oauth_data['web']['redirect_uris']:
                        if '/auth/callback' in uri:
                            redirect_uri = uri
                            break
            except Exception as json_error:
                print(f"Error reading OAuth.json: {str(json_error)}")

        # If we couldn't get a redirect URI from the file, try environment or build dynamically
        if not redirect_uri:
            redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')

        if not redirect_uri:
            # Build the URI dynamically as a last resort
            redirect_uri = url_for('auth.google_callback', _external=True)

        print(f"Google OAuth redirect URI: {redirect_uri}")
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        flash(f"Error with Google login: {str(e)}", "danger")
        print(f"Google OAuth error: {str(e)}")
        return redirect(url_for('auth.login'))

# These routes handle the Google OAuth callback
@auth_bp.route('/google/callback')
def google_callback():
    """Google OAuth callback route."""
    return _handle_google_callback()

@auth_bp.route('/auth/callback')  # This matches the URI in OAuth.json
def auth_callback():
    """Alternative Google OAuth callback route."""
    return _handle_google_callback()

# Make this function accessible from outside the module
def _handle_google_callback():
    """Google OAuth callback route."""
    # Make sure Google OAuth is configured
    if not google:
        flash("Google OAuth is not configured properly. Please contact the administrator.", "danger")
        return redirect(url_for('auth.login'))

    # Get token and user info from Google
    try:
        token = google.authorize_access_token()
        # Use the full URL for userinfo endpoint
        userinfo_endpoint = 'https://www.googleapis.com/oauth2/v2/userinfo'
        resp = google.get(userinfo_endpoint)
        user_info = resp.json()
        print(f"Google user info received: {user_info.get('email')}")
    except Exception as oauth_error:
        print(f"Google OAuth error: {str(oauth_error)}")
        import traceback
        print(traceback.format_exc())
        flash("Error authenticating with Google. Please try again or use email login.", "danger")
        return redirect(url_for('auth.login'))

    # Check if user exists
    try:
        user_data = User.get_by_oauth('google', user_info['id'])
    except Exception as db_error:
        print(f"Database error checking OAuth user: {str(db_error)}")
        flash("Error accessing user database. Please try again later.", "danger")
        return redirect(url_for('auth.login'))

    if not user_data:
        # Check if email already exists
        existing_user = User.get_by_email(user_info['email'])
        if existing_user:
            # Update existing user with OAuth info
            User.update_oauth(
                email=user_info['email'],
                oauth_provider='google',
                oauth_id=user_info['id']
            )
            user_data = existing_user
        else:
            # Create new user
            User.create(
                username=user_info['email'].split('@')[0],  # Use part before @ as username
                email=user_info['email'],
                oauth_provider='google',
                oauth_id=user_info['id']
            )
            user_data = User.get_by_email(user_info['email'])

    # Create user object
    class UserObject:
        def __init__(self, email, data):
            self.id = email
            self.email = email
            self.username = data.get('username')
            self.is_admin = data.get('is_admin', False)
            self._data = data  # Store the full user data

        def is_authenticated(self):
            return True

        def is_active(self):
            return True

        def is_anonymous(self):
            return False

        def get_id(self):
            return self.id

        def check_password(self, password):
            """Check if the provided password matches the stored hash."""
            password_hash = self._data.get('password_hash', '')
            return check_password_hash(password_hash, password)

    user = UserObject(user_data.get('email'), user_data)
    login_user(user)

    # Log activity
    UserActivity.log(
        user_email=user_data.get('email'),
        activity_type='login',
        details='Google OAuth login'
    )

    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile route."""
    return render_template('profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change password route."""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('auth.profile'))

    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('auth.profile'))

    try:
        # Update password in Firebase
        user_id = current_user.email.replace('.', ',')
        password_hash = generate_password_hash(new_password)
        User.get_ref('users').child(user_id).update({
            'password_hash': password_hash
        })

        flash('Password changed successfully', 'success')
    except Exception as e:
        flash(f'Error changing password: {str(e)}', 'danger')

    return redirect(url_for('auth.profile'))



