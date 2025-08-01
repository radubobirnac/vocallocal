"""Authentication module for VocalLocal."""
import os
import json
from functools import wraps
from flask import Blueprint, redirect, url_for, session, request, flash, render_template, jsonify
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
        # Method 1: Try GOOGLE_OAUTH_CREDENTIALS_JSON environment variable (JSON string)
        oauth_json_str = os.getenv('GOOGLE_OAUTH_CREDENTIALS_JSON')
        if oauth_json_str:
            app.logger.info("Found OAuth credentials in GOOGLE_OAUTH_CREDENTIALS_JSON environment variable")
            try:
                oauth_data = json.loads(oauth_json_str)

                if 'web' in oauth_data:
                    web_config = oauth_data['web']
                    client_id = web_config.get('client_id')
                    client_secret = web_config.get('client_secret')
                    auth_uri = web_config.get('auth_uri', 'https://accounts.google.com/o/oauth2/auth')
                    token_uri = web_config.get('token_uri', 'https://oauth2.googleapis.com/token')

                    app.logger.info(f"Using OAuth client ID from env var: {client_id[:5]}...{client_id[-5:] if client_id else 'None'}")

                    if client_id and client_secret:
                        # Register the OAuth provider with credentials from environment variable
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
                            jwks_uri='https://www.googleapis.com/oauth2/v3/certs',  # Add JWKS URI
                        )
                        google = oauth.google
                        app.logger.info("Google OAuth configured successfully from GOOGLE_OAUTH_CREDENTIALS_JSON environment variable")
                        return  # Exit early if successful
            except Exception as e:
                app.logger.error(f"Error parsing GOOGLE_OAUTH_CREDENTIALS_JSON environment variable: {str(e)}")
                # Continue to other methods if this fails

        # Method 2: Try to load credentials from OAuth.json file
        oauth_file_path = None
        possible_oauth_paths = [
            os.path.join(os.path.dirname(__file__), 'Oauth.json'),  # Local file
            "/etc/secrets/Oauth.json",  # Render secret file
            "/etc/secrets/oauth-json"   # Render secret file (no extension)
        ]

        for path in possible_oauth_paths:
            if os.path.exists(path):
                oauth_file_path = path
                app.logger.info(f"Found OAuth.json at: {path}")
                break

        if oauth_file_path:
            import json
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
                        jwks_uri='https://www.googleapis.com/oauth2/v3/certs',  # Add JWKS URI
                    )
                    google = oauth.google
                    app.logger.info("Google OAuth configured successfully from OAuth.json")
                    return  # Exit early if successful

        # Fall back to environment variables
        app.logger.info("OAuth.json not found or invalid, using environment variables")
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
        return redirect(url_for('main.index'))

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
            return redirect(url_for('main.index'))

        flash('Invalid email or password', 'danger')

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

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
    return redirect(url_for('main.index'))

@auth_bp.route('/google')
def google_login():
    """Google OAuth login route."""
    try:
        # Make sure Google OAuth is configured
        if not google:
            flash("Google OAuth is not configured properly. Please contact the administrator.", "danger")
            return redirect(url_for('auth.login'))

        # Get the current host from the request
        host = request.host_url.rstrip('/')

        # If we're on a cloud platform, use the specific domain
        if 'onrender.com' in host:
            if 'vocallocal.onrender.com' in host:
                redirect_uri = "https://vocallocal.onrender.com/auth/callback"
            elif 'vocallocal-aj6b.onrender.com' in host:
                redirect_uri = "https://vocallocal-aj6b.onrender.com/auth/callback"
            else:
                # Fallback for any other Render domain
                redirect_uri = f"{host}/auth/callback"
        elif 'ondigitalocean.app' in host:
            if 'vocallocal-l5et5.ondigitalocean.app' in host:
                redirect_uri = "https://vocallocal-l5et5.ondigitalocean.app/auth/callback"
            elif 'test-vocallocal-x9n74.ondigitalocean.app' in host:
                redirect_uri = "https://test-vocallocal-x9n74.ondigitalocean.app/auth/callback"
            else:
                # Fallback for any other DigitalOcean domain
                redirect_uri = f"{host}/auth/callback"
        else:
            # Local development
            redirect_uri = url_for('auth.google_callback', _external=True)

        print(f"Using redirect URI: {redirect_uri}")

        # Use the specific redirect URI
        return google.authorize_redirect(redirect_uri)
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
                if 'onrender.com' in host:
                    if 'vocallocal.onrender.com' in host:
                        redirect_uri = "https://vocallocal.onrender.com/auth/callback"
                    elif 'vocallocal-aj6b.onrender.com' in host:
                        redirect_uri = "https://vocallocal-aj6b.onrender.com/auth/callback"
                    else:
                        redirect_uri = f"{host}/auth/callback"
                elif 'ondigitalocean.app' in host:
                    if 'vocallocal-l5et5.ondigitalocean.app' in host:
                        redirect_uri = "https://vocallocal-l5et5.ondigitalocean.app/auth/callback"
                    elif 'test-vocallocal-x9n74.ondigitalocean.app' in host:
                        redirect_uri = "https://test-vocallocal-x9n74.ondigitalocean.app/auth/callback"
                    else:
                        # Fallback for any other DigitalOcean domain
                        redirect_uri = f"{host}/auth/callback"
                else:
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

        # Log the user in
        login_user(user)

        # Log user activity
        UserActivity.log(email, 'login', {'method': 'google'})

        # Redirect to home page
        return redirect(url_for('main.index'))
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
                if 'onrender.com' in host:
                    if 'vocallocal.onrender.com' in host:
                        redirect_uri = "https://vocallocal.onrender.com/auth/callback"
                    elif 'vocallocal-aj6b.onrender.com' in host:
                        redirect_uri = "https://vocallocal-aj6b.onrender.com/auth/callback"
                    else:
                        # Fallback for any other Render domain
                        redirect_uri = f"{host}/auth/callback"
                elif 'ondigitalocean.app' in host:
                    if 'vocallocal-l5et5.ondigitalocean.app' in host:
                        redirect_uri = "https://vocallocal-l5et5.ondigitalocean.app/auth/callback"
                    elif 'test-vocallocal-x9n74.ondigitalocean.app' in host:
                        redirect_uri = "https://test-vocallocal-x9n74.ondigitalocean.app/auth/callback"
                    else:
                        # Fallback for any other DigitalOcean domain
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

        # Log the user in
        login_user(user)

        # Log user activity
        UserActivity.log(email, 'login', {'method': 'google'})

        # Redirect to home page
        return redirect(url_for('main.index'))
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
        # Fetch user's transcription history
        transcriptions = User.get_ref(f'transcriptions/{current_user.email.replace(".", ",")}').order_by_child('timestamp').limit_to_last(20).get()
    except Exception as e:
        print(f"Error fetching transcriptions: {str(e)}")
        # Try to fetch without ordering if index is not defined
        try:
            transcriptions = User.get_ref(f'transcriptions/{current_user.email.replace(".", ",")}').get()
        except Exception as e2:
            print(f"Error fetching transcriptions without ordering: {str(e2)}")

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
            "https://vocallocal.onrender.com/auth/callback",
            "https://vocallocal-aj6b.onrender.com/auth/callback",
            "https://vocallocal-l5et5.ondigitalocean.app/auth/callback",
            "https://test-vocallocal-x9n74.ondigitalocean.app/auth/callback"
        ],
        "current_host": request.host_url,
        "is_secure": request.is_secure
    }
    return jsonify(debug_info)
