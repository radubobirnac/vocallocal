"""Authentication module for VocalLocal."""
import os
import json
import logging
from functools import wraps
from flask import Blueprint, redirect, url_for, session, request, flash, render_template, jsonify, current_app
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from firebase_models import User, UserActivity
from services.password_reset_service import password_reset_service

# Set up logging
logger = logging.getLogger(__name__)

# Initialize login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

# Initialize OAuth
oauth = OAuth()

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

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
            self.role = data.get('role', 'normal_user')  # Add role support
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

        def has_role(self, role):
            """Check if user has a specific role."""
            return self.role == role

        def has_admin_privileges(self):
            """Check if user has admin privileges."""
            return self.role == 'admin'

        def has_premium_access(self):
            """Check if user has premium access (admin or super user)."""
            return self.role in ['admin', 'super_user']

    return UserObject(user_id, user_data)

def init_app(app):
    """Initialize authentication with the Flask app."""
    global google

    # Initialize login manager
    login_manager.init_app(app)

    # Initialize OAuth
    oauth.init_app(app)

    # Add session activity tracker for mobile UX
    @app.before_request
    def track_user_activity():
        """Track user activity to extend session for active users."""
        if current_user.is_authenticated:
            from datetime import datetime, timedelta

            # Check if we need to extend the session
            last_activity = session.get('last_activity')
            now = datetime.now()

            if last_activity:
                last_activity_time = datetime.fromisoformat(last_activity)
                # If user has been active within the last hour, extend session
                if now - last_activity_time < timedelta(hours=1):
                    session.permanent = True

            # Update last activity timestamp
            session['last_activity'] = now.isoformat()

    # Register blueprint
    app.register_blueprint(auth_bp)

    # Configure Google OAuth
    try:
        # Method 1: Try OAuth credential files in common locations
        oauth_file_paths = [
            "Oauth.json",  # App root (local development)
            os.path.join(os.path.dirname(__file__), 'Oauth.json'),  # Relative to auth module
            "/etc/secrets/Oauth.json",  # Deployment platforms (Render, etc.)
            "/etc/secrets/oauth-json",  # Alternative naming
            "/app/Oauth.json",  # Heroku-style deployment
            os.path.expanduser("~/Oauth.json")  # User home directory
        ]

        oauth_file_path = None
        for path in oauth_file_paths:
            if os.path.exists(path):
                oauth_file_path = path
                app.logger.info(f"Found OAuth credentials at: {path}")
                break

        if oauth_file_path:
            try:
                with open(oauth_file_path, 'r') as f:
                    oauth_data = json.load(f)

                if 'web' in oauth_data:
                    web_config = oauth_data['web']
                    client_id = web_config.get('client_id')
                    client_secret = web_config.get('client_secret')
                    auth_uri = web_config.get('auth_uri', 'https://accounts.google.com/o/oauth2/auth')
                    token_uri = web_config.get('token_uri', 'https://oauth2.googleapis.com/token')

                    app.logger.info(f"Using OAuth client ID from file: {client_id[:5]}...{client_id[-5:] if client_id else 'None'}")

                    if client_id and client_secret:
                        # Register the OAuth provider with credentials from file
                        oauth.register(
                            name='google',
                            client_id=client_id,
                            client_secret=client_secret,
                            authorize_url=auth_uri,
                            authorize_params=None,
                            access_token_url=token_uri,
                            access_token_params=None,
                            refresh_token_url=token_uri,
                            redirect_uri=None,
                            client_kwargs={
                                'scope': 'openid email profile',
                                'token_endpoint_auth_method': 'client_secret_post'
                            },
                            jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
                        )
                        google = oauth.google
                        app.logger.info("Google OAuth configured successfully from credential file")
                        return  # Exit early if successful
            except Exception as e:
                app.logger.error(f"Error loading OAuth credentials from {oauth_file_path}: {str(e)}")

        # Method 2: Try environment variables (for advanced users)
        oauth_json_str = os.getenv('GOOGLE_OAUTH_CREDENTIALS_JSON') or os.getenv('OAUTH_CREDENTIALS')
        if oauth_json_str:
            try:
                app.logger.info("Found OAuth credentials in environment variable")
                oauth_data = json.loads(oauth_json_str)

                if 'web' in oauth_data:
                    web_config = oauth_data['web']
                    client_id = web_config.get('client_id')
                    client_secret = web_config.get('client_secret')
                    auth_uri = web_config.get('auth_uri', 'https://accounts.google.com/o/oauth2/auth')
                    token_uri = web_config.get('token_uri', 'https://oauth2.googleapis.com/token')

                    if client_id and client_secret:
                        oauth.register(
                            name='google',
                            client_id=client_id,
                            client_secret=client_secret,
                            authorize_url=auth_uri,
                            authorize_params={
                                'prompt': 'select_account',
                                'access_type': 'offline'
                            },
                            access_token_url=token_uri,
                            access_token_params=None,
                            refresh_token_url=token_uri,
                            redirect_uri=None,
                            client_kwargs={
                                'scope': 'openid email profile',
                                'token_endpoint_auth_method': 'client_secret_post'
                            },
                            jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
                        )
                        google = oauth.google
                        app.logger.info("Google OAuth configured successfully from environment variable")
                        return  # Exit early if successful
            except Exception as e:
                app.logger.error(f"Error parsing OAuth environment variable: {str(e)}")

        # Method 3: Fall back to individual environment variables
        app.logger.info("OAuth.json not found or invalid, using individual environment variables")
        google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

        app.logger.info(f"Using OAuth client ID from env: {google_client_id[:5]}...{google_client_id[-5:] if google_client_id else 'None'}")

        if google_client_id and google_client_secret:
            # Register the OAuth provider with credentials from environment
            oauth.register(
                name='google',
                client_id=google_client_id,
                client_secret=google_client_secret,
                authorize_url='https://accounts.google.com/o/oauth2/auth',
                authorize_params={
                    'prompt': 'select_account',
                    'access_type': 'offline'
                },
                access_token_url='https://oauth2.googleapis.com/token',
                access_token_params=None,
                refresh_token_url='https://oauth2.googleapis.com/token',
                redirect_uri=None,
                client_kwargs={
                    'scope': 'openid email profile',
                    'token_endpoint_auth_method': 'client_secret_post'
                },
                jwks_uri='https://www.googleapis.com/oauth2/v3/certs',  # Add JWKS URI
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

                    # Determine role - check role field first, then fallback to is_admin
                    role = data.get('role')
                    if role and role in ['admin', 'super_user', 'normal_user']:
                        self.role = role
                    elif data.get('is_admin', False):
                        self.role = 'admin'
                    else:
                        self.role = 'normal_user'

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

                def has_role(self, role):
                    """Check if user has a specific role."""
                    return self.role == role

                def has_admin_privileges(self):
                    """Check if user has admin privileges."""
                    return self.role == 'admin'

                def has_premium_access(self):
                    """Check if user has premium access (admin or super user)."""
                    return self.role in ['admin', 'super_user']

                def is_super_user(self):
                    """Check if user is a super user."""
                    return self.role == 'super_user'

                def is_normal_user(self):
                    """Check if user is a normal user."""
                    return self.role == 'normal_user'

            user = UserObject(email, user_data)
            # Always use remember=True for 7-day session persistence
            # This provides better mobile UX by keeping users logged in
            login_user(user, remember=True, duration=current_app.config.get('REMEMBER_COOKIE_DURATION'))

            # Make session permanent for better mobile experience
            session.permanent = True

            # Log activity
            UserActivity.log(
                user_email=email,
                activity_type='login',
                details='Manual login with 7-day persistence'
            )

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))

        flash('Invalid email or password', 'danger')

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register route with email validation and welcome email."""
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

        # Enhanced email validation
        try:
            from services.email_service import email_service
            email_validation = email_service.validate_email(email)

            if not email_validation['valid']:
                error_msg = 'Invalid email address'
                if email_validation.get('errors'):
                    error_msg = email_validation['errors'][0]
                flash(error_msg, 'danger')
                return render_template('register.html')
        except Exception as e:
            logger.warning(f'Email validation failed: {str(e)}')
            # Continue with basic validation if service fails
            if '@' not in email or '.' not in email.split('@')[1]:
                flash('Please enter a valid email address', 'danger')
                return render_template('register.html')

        # Check if email already exists
        if User.get_by_email(email):
            flash('Email already exists', 'danger')
            return render_template('register.html')

        try:
            # DO NOT create user yet - only create after email verification
            # Store registration data in session for verification process
            password_hash = generate_password_hash(password)

            # Send verification code first
            try:
                from services.email_verification_service import email_verification_service
                verification_result = email_verification_service.send_verification_code(email, username)

                if verification_result['success']:
                    logger.info(f'Verification email sent successfully to {email}')

                    # Store registration data in session for verification process
                    session['pending_registration'] = {
                        'email': email,
                        'username': username,
                        'password_hash': password_hash,
                        'next': request.args.get('next')
                    }

                    # Ensure session is saved
                    session.permanent = True

                    # Debug logging
                    logger.info(f'Registration data stored in session for {email}')
                    logger.info(f'Session keys after storage: {list(session.keys())}')

                    # Redirect to verification page
                    return redirect(url_for('auth.verify_email'))
                else:
                    logger.error(f'Failed to send verification email to {email}: {verification_result["message"]}')
                    flash('Failed to send verification email. Please try again or contact support.', 'danger')
                    return render_template('register.html')

            except Exception as e:
                logger.error(f'Error sending verification email to {email}: {str(e)}')
                flash('Failed to send verification email. Please try again or contact support.', 'danger')
                return render_template('register.html')

        except Exception as e:
            logger.error(f'User creation failed: {str(e)}')
            flash('Registration failed. Please try again.', 'danger')
            return render_template('register.html')

    return render_template('register.html')

@auth_bp.route('/verify-email')
def verify_email():
    """Email verification page with support for direct links."""
    # Check for direct link parameters
    email_param = request.args.get('email')
    token_param = request.args.get('token')
    code_param = request.args.get('code')

    # If direct link parameters are provided, handle token verification
    if email_param and token_param and code_param:
        logger.info(f"Direct verification link accessed for email: {email_param}")

        try:
            from services.email_verification_service import email_verification_service

            # Verify the token
            if email_verification_service.verify_token(email_param, token_param, code_param):
                logger.info(f"Valid verification token for {email_param}")

                # Set up session data for this verification
                session['pending_verification'] = {
                    'email': email_param,
                    'username': email_param.split('@')[0],  # Default username
                    'auto_verify': True,
                    'code': code_param
                }
                session.permanent = True

                # Render verification page with pre-filled data and auto-verification option
                return render_template('verify_email.html',
                                     email=email_param,
                                     username=email_param.split('@')[0],
                                     auto_verify=True,
                                     verification_code=code_param)
            else:
                logger.warning(f"Invalid verification token for {email_param}")
                flash('Invalid or expired verification link. Please try again.', 'danger')
                return redirect(url_for('auth.register'))

        except Exception as e:
            logger.error(f"Error processing verification link: {str(e)}")
            flash('Error processing verification link. Please try manual verification.', 'warning')

    # Check if there's pending verification data (check both possible keys)
    pending_data = session.get('pending_registration') or session.get('pending_verification')

    # Debug logging
    logger.info(f"Verify email page accessed. Session keys: {list(session.keys())}")
    if pending_data:
        logger.info(f"Found pending data for email: {pending_data.get('email')}")
    else:
        logger.warning("No pending verification data found in session")

    if not pending_data:
        flash('No pending email verification found. Please register again.', 'warning')
        return redirect(url_for('auth.register'))

    return render_template('verify_email.html',
                         email=pending_data.get('email'),
                         username=pending_data.get('username'),
                         auto_verify=pending_data.get('auto_verify', False),
                         verification_code=pending_data.get('code'))

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout route."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/google')
def google_login():
    """Google OAuth login route."""
    try:
        # Store the next parameter in session before redirecting to Google
        next_page = request.args.get('next')
        if next_page:
            session['next'] = next_page

        # Make sure Google OAuth is configured
        if not google:
            flash("Google OAuth is not configured properly. Please contact the administrator.", "danger")
            return redirect(url_for('auth.login'))

        # Get the current host from the request
        host = request.host_url.rstrip('/')

        # Determine the appropriate redirect URI based on the host
        if 'ondigitalocean.app' in host:
            if 'vocallocal-l5et5.ondigitalocean.app' in host:
                redirect_uri = "https://vocallocal-l5et5.ondigitalocean.app/auth/callback"
            elif 'test-vocallocal-x9n74.ondigitalocean.app' in host:
                redirect_uri = "https://test-vocallocal-x9n74.ondigitalocean.app/auth/callback"
            else:
                # Fallback for any other DigitalOcean domain
                redirect_uri = f"{host}/auth/callback"
        elif 'onrender.com' in host:
            redirect_uri = f"{host}/auth/callback"
        else:
            # Local development
            redirect_uri = url_for('auth.google_callback', _external=True)

        print(f"Using redirect URI: {redirect_uri}")

        # Use the specific redirect URI with account selection prompt
        return google.authorize_redirect(
            redirect_uri,
            prompt='select_account',
            access_type='offline'
        )
    except Exception as e:
        flash(f"Error with Google login: {str(e)}", "danger")
        print(f"Google OAuth error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return redirect(url_for('auth.login'))

@auth_bp.route('/callback')
def google_callback():
    """Google OAuth callback route."""
    try:
        print("Google callback route called")
        print(f"Request args: {request.args}")

        # Get token without ID token validation
        print("Attempting to authorize access token...")
        token = None
        try:
            # Try to get the token with ID token validation
            token = google.authorize_access_token()
        except Exception as token_error:
            print(f"Error with standard token authorization: {str(token_error)}")
            # Fall back to manual token fetching without ID token validation
            try:
                code = request.args.get('code')
                if not code:
                    raise ValueError("No authorization code received")

                # Manually exchange the code for a token
                token_endpoint = 'https://oauth2.googleapis.com/token'

                # Determine the appropriate redirect URI based on the host
                host = request.host_url.rstrip('/')
                if 'ondigitalocean.app' in host:
                    redirect_uri = f"{host}/auth/callback"
                elif 'onrender.com' in host:
                    redirect_uri = f"{host}/auth/callback"
                else:
                    # Local development
                    redirect_uri = url_for('auth.google_callback', _external=True)

                token_data = {
                    'code': code,
                    'client_id': google.client_id,
                    'client_secret': google.client_secret,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code'
                }

                import requests
                token_response = requests.post(token_endpoint, data=token_data)
                token_response.raise_for_status()
                token = token_response.json()
                print(f"Manually obtained token: {token}")
            except Exception as manual_error:
                print(f"Error with manual token fetching: {str(manual_error)}")
                raise

        if not token:
            raise ValueError("Failed to obtain access token")

        print(f"Token received: {token}")

        # Get user info - use the full URL for the userinfo endpoint
        print("Fetching user info...")
        access_token = token.get('access_token')
        if not access_token:
            raise ValueError("No access token in response")

        # Use requests directly to get user info
        import requests
        headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers)
        userinfo_response.raise_for_status()
        user_info = userinfo_response.json()

        print(f"Google OAuth callback received. User info: {user_info.get('email')}")

        # Check if user exists in Firebase
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')

        if not email:
            flash("Could not get email from Google. Please try again.", "danger")
            return redirect(url_for('auth.login'))

        # Get or create user
        user = User.get_or_create(email, name, picture)

        # Log the user in with 7-day persistence for better mobile UX
        login_user(user, remember=True, duration=current_app.config.get('REMEMBER_COOKIE_DURATION'))

        # Make session permanent for better mobile experience
        session.permanent = True

        # Log user activity
        UserActivity.log(email, 'login', {'method': 'google', 'persistence': '7-day'})

        # Check for next parameter in session or URL args for redirect after login
        next_page = session.get('next') or request.args.get('next')
        if next_page:
            # Clear the next parameter from session
            session.pop('next', None)
            return redirect(next_page)

        # Default redirect to home page
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Error during Google authentication: {str(e)}", "danger")
        print(f"Google OAuth callback error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return redirect(url_for('auth.login'))

def _handle_google_callback():
    """Handle Google OAuth callback for direct calls from app.py's root_auth_callback route."""
    try:
        print("Google callback handler called directly")
        print(f"Request args: {request.args}")

        # Get token without ID token validation
        print("Attempting to authorize access token...")
        token = None
        try:
            # Try to get the token with ID token validation
            token = google.authorize_access_token()
        except Exception as token_error:
            print(f"Error with standard token authorization: {str(token_error)}")
            # Fall back to manual token fetching without ID token validation
            try:
                code = request.args.get('code')
                if not code:
                    raise ValueError("No authorization code received")

                # Manually exchange the code for a token
                token_endpoint = 'https://oauth2.googleapis.com/token'

                # Determine the appropriate redirect URI based on the host
                host = request.host_url.rstrip('/')
                if 'ondigitalocean.app' in host:
                    redirect_uri = f"{host}/auth/callback"
                elif 'onrender.com' in host:
                    redirect_uri = f"{host}/auth/callback"
                else:
                    # Local development
                    redirect_uri = url_for('auth.google_callback', _external=True)

                token_data = {
                    'code': code,
                    'client_id': google.client_id,
                    'client_secret': google.client_secret,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code'
                }

                import requests
                token_response = requests.post(token_endpoint, data=token_data)
                token_response.raise_for_status()
                token = token_response.json()
                print(f"Manually obtained token: {token}")
            except Exception as manual_error:
                print(f"Error with manual token fetching: {str(manual_error)}")
                raise

        if not token:
            raise ValueError("Failed to obtain access token")

        print(f"Token received: {token}")

        # Get user info - use the full URL for the userinfo endpoint
        print("Fetching user info...")
        access_token = token.get('access_token')
        if not access_token:
            raise ValueError("No access token in response")

        # Use requests directly to get user info
        import requests
        headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers)
        userinfo_response.raise_for_status()
        user_info = userinfo_response.json()

        print(f"Google OAuth callback received. User info: {user_info.get('email')}")

        # Check if user exists in Firebase
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')

        if not email:
            flash("Could not get email from Google. Please try again.", "danger")
            return redirect(url_for('auth.login'))

        # Get or create user
        user = User.get_or_create(email, name, picture)

        # Log the user in with 7-day persistence for better mobile UX
        login_user(user, remember=True, duration=current_app.config.get('REMEMBER_COOKIE_DURATION'))

        # Make session permanent for better mobile experience
        session.permanent = True

        # Log user activity
        UserActivity.log(email, 'login', {'method': 'google', 'persistence': '7-day'})

        # Check for next parameter in session or URL args for redirect after login
        next_page = session.get('next') or request.args.get('next')
        if next_page:
            # Clear the next parameter from session
            session.pop('next', None)
            return redirect(next_page)

        # Default redirect to home page
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Error during Google authentication: {str(e)}", "danger")
        print(f"Google OAuth callback error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile route."""
    transcriptions = {}
    translations = {}

    try:
        # Try with normal email
        transcriptions = Transcription.get_by_user(current_user.email, limit=20)
    except Exception as e:
        print(f"Error fetching with normal email: {str(e)}")
        try:
            # Try with comma-formatted email
            email_with_comma = current_user.email.replace('.', ',')
            transcriptions = Transcription.get_by_user(email_with_comma, limit=20)
        except Exception as e2:
            print(f"Error fetching with comma email: {str(e2)}")
            transcriptions = {}

    try:
        # Fetch user's translation history
        translations = User.get_ref(f'translations/{current_user.email.replace(".", ",")}').order_by_child('timestamp').limit_to_last(20).get()
    except Exception as e:
        print(f"Error fetching translations: {str(e)}")
        # Try to fetch without ordering if index is not defined
        try:
            translations = User.get_ref(f'translations/{current_user.email.replace(".", ",")}').get()
        except Exception as e2:
            print(f"Error fetching translations without ordering: {str(e2)}")

    return render_template('profile.html',
                          user=current_user,
                          transcriptions=transcriptions if transcriptions else {},
                          translations=translations if translations else {})

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

@auth_bp.route('/debug')
def oauth_debug():
    """Debug route to check OAuth configuration."""
    debug_info = {
        "google_configured": google is not None,
        "client_id": google.client_id if google else None,
        "redirect_uris_in_code": [
            url_for('auth.google_callback', _external=True),
            "https://vocallocal-l5et5.ondigitalocean.app/auth/callback",
            "https://test-vocallocal-x9n74.ondigitalocean.app/auth/callback",
            "https://vocallocal.onrender.com/auth/callback"
        ],
        "current_host": request.host_url,
        "is_secure": request.is_secure
    }
    return jsonify(debug_info)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password route - request password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        # Validate email format
        if not email:
            flash('Please enter your email address', 'danger')
            return render_template('forgot_password.html')

        if '@' not in email:
            flash('Please enter a valid email address', 'danger')
            return render_template('forgot_password.html')

        try:
            # Send reset email (service handles all validation and security)
            result = password_reset_service.send_reset_email(email)

            if result['success']:
                flash(result['message'], 'success')
                # Always redirect to login page after successful request
                return redirect(url_for('auth.login'))
            else:
                flash(result['message'], 'danger')
                return render_template('forgot_password.html')

        except Exception as e:
            logger.error(f"Error in forgot password for {email}: {str(e)}")
            flash('An error occurred. Please try again later.', 'danger')
            return render_template('forgot_password.html')

    return render_template('forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password route - set new password with token."""
    email = request.args.get('email') or request.form.get('email')
    token = request.args.get('token') or request.form.get('token')

    if not email or not token:
        flash('Invalid reset link. Please request a new password reset.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Validate passwords
        if not new_password or not confirm_password:
            flash('Please fill in all fields', 'danger')
            return render_template('reset_password.html', email=email, token=token)

        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('reset_password.html', email=email, token=token)

        if len(new_password) < 6:
            flash('Password must be at least 6 characters long', 'danger')
            return render_template('reset_password.html', email=email, token=token)

        try:
            # Validate token
            is_valid, error_msg = password_reset_service.validate_reset_token(email, token)
            if not is_valid:
                flash(error_msg, 'danger')
                return redirect(url_for('auth.forgot_password'))

            # Update password
            user_id = email.replace('.', ',')
            password_hash = generate_password_hash(new_password)
            User.get_ref('users').child(user_id).update({
                'password_hash': password_hash
            })

            # Mark token as used
            password_reset_service.mark_token_used(email, token)

            # Log activity
            UserActivity.log(
                user_email=email,
                activity_type='password_reset',
                details='Password reset via email link'
            )

            flash('Password reset successfully! You can now log in with your new password.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            logger.error(f"Error resetting password for {email}: {str(e)}")
            flash('An error occurred while resetting your password. Please try again.', 'danger')
            return render_template('reset_password.html', email=email, token=token)

    # GET request - validate token and show form
    try:
        is_valid, error_msg = password_reset_service.validate_reset_token(email, token)
        if not is_valid:
            flash(error_msg, 'danger')
            return redirect(url_for('auth.forgot_password'))

        return render_template('reset_password.html', email=email, token=token)

    except Exception as e:
        logger.error(f"Error validating reset token for {email}: {str(e)}")
        flash('Invalid reset link. Please request a new password reset.', 'danger')
        return redirect(url_for('auth.forgot_password'))
