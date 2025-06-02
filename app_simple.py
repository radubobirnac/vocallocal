"""
VocalLocal Web Service - Simplified Version for Debugging
This is a minimal version to test what's working
"""
import os
import sys
from flask import Flask, render_template, redirect, url_for, jsonify, flash
from config import Config

# Initialize Flask application
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = Config.SECRET_KEY

# Configure upload settings
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER

print("🚀 Starting VocalLocal (Simple Version)")

# Initialize Firebase with error handling
try:
    from firebase_config import initialize_firebase
    initialize_firebase()
    print("✅ Firebase initialized successfully")
except Exception as e:
    print(f"⚠️  Firebase initialization failed: {e}")
    print("Application will continue with limited functionality")

# Initialize authentication with error handling
try:
    import auth
    auth.init_app(app)
    print("✅ Authentication initialized successfully")
except Exception as e:
    print(f"⚠️  Authentication initialization failed: {e}")

# Define routes directly in this file (no blueprints for now)
@app.route('/')
def index():
    """Main index route."""
    try:
        from flask_login import current_user
        if current_user.is_authenticated:
            return render_template('index.html')
        else:
            return render_template('home.html')
    except Exception as e:
        print(f"Error in index route: {e}")
        return f"<h1>VocalLocal</h1><p>App is running but there's an issue: {e}</p>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route - direct implementation."""
    try:
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        return render_template('login.html')
    except Exception as e:
        print(f"Error in login route: {e}")
        return f"<h1>Login</h1><p>Login page error: {e}</p><a href='/'>Back to Home</a>"

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy', 
        'service': 'VocalLocal',
        'version': 'simple',
        'routes_working': True
    })

@app.route('/api/health')
def api_health_check():
    """API health check endpoint."""
    return jsonify({
        'status': 'healthy', 
        'api': 'VocalLocal API',
        'version': 'simple'
    })

@app.route('/pricing')
def pricing():
    """Pricing page."""
    try:
        return render_template('pricing.html')
    except Exception as e:
        print(f"Error in pricing route: {e}")
        return f"<h1>Pricing</h1><p>Pricing page error: {e}</p><a href='/'>Back to Home</a>"

@app.route('/transcribe')
def transcribe():
    """Transcribe page."""
    try:
        return render_template('transcribe.html')
    except Exception as e:
        print(f"Error in transcribe route: {e}")
        return f"<h1>Transcribe</h1><p>Transcribe page error: {e}</p><a href='/'>Back to Home</a>"

@app.route('/translate')
def translate():
    """Translate page."""
    try:
        return render_template('translate.html')
    except Exception as e:
        print(f"Error in translate route: {e}")
        return f"<h1>Translate</h1><p>Translate page error: {e}</p><a href='/'>Back to Home</a>"

@app.route('/try-it-free')
def try_it_free():
    """Try it free page."""
    try:
        return render_template('try_it_free.html')
    except Exception as e:
        print(f"Error in try_it_free route: {e}")
        return f"<h1>Try It Free</h1><p>Try it free page error: {e}</p><a href='/'>Back to Home</a>"

# Google OAuth routes
@app.route('/auth/google')
def google_login():
    """Google OAuth login."""
    try:
        from auth import google_login as auth_google_login
        return auth_google_login()
    except Exception as e:
        print(f"Error in google_login route: {e}")
        return f"<h1>OAuth Error</h1><p>Google login error: {e}</p><a href='/'>Back to Home</a>"

@app.route('/auth/callback')
def auth_callback():
    """OAuth callback."""
    try:
        from auth import _handle_google_callback
        return _handle_google_callback()
    except Exception as e:
        print(f"Error in auth_callback route: {e}")
        flash("Error during authentication. Please try again.", "danger")
        return redirect(url_for('login'))

@app.route('/debug-routes')
def debug_routes():
    """Debug route to show all available routes."""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': str(rule)
        })
    
    html = "<h1>VocalLocal Routes Debug</h1>"
    html += f"<p>Total routes: {len(routes)}</p>"
    html += "<ul>"
    for route in sorted(routes, key=lambda x: x['rule']):
        html += f"<li><strong>{route['rule']}</strong> → {route['endpoint']} ({', '.join(route['methods'])})</li>"
    html += "</ul>"
    html += "<p><a href='/'>Back to Home</a></p>"
    
    return html

@app.route('/debug-test')
def debug_test():
    """Simple debug test."""
    return """
    <html>
        <head><title>VocalLocal Debug Test (Simple Version)</title></head>
        <body>
            <h1>🎉 SUCCESS! VocalLocal Simple Version is Working!</h1>
            <p>This is the simplified version for debugging.</p>
            <h2>Test Routes:</h2>
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/login">Login</a></li>
                <li><a href="/health">Health Check</a></li>
                <li><a href="/api/health">API Health Check</a></li>
                <li><a href="/pricing">Pricing</a></li>
                <li><a href="/transcribe">Transcribe</a></li>
                <li><a href="/translate">Translate</a></li>
                <li><a href="/try-it-free">Try It Free</a></li>
                <li><a href="/auth/google">Google OAuth</a></li>
                <li><a href="/debug-routes">Debug Routes List</a></li>
            </ul>
        </body>
    </html>
    """

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return f"""
    <html>
        <head><title>404 - Page Not Found</title></head>
        <body>
            <h1>404 - Page Not Found</h1>
            <p>The requested page was not found.</p>
            <p><a href="/debug-routes">View all available routes</a></p>
            <p><a href="/">Back to Home</a></p>
        </body>
    </html>
    """, 404

@app.errorhandler(500)
def internal_error(error):
    return f"""
    <html>
        <head><title>500 - Internal Server Error</title></head>
        <body>
            <h1>500 - Internal Server Error</h1>
            <p>Something went wrong: {error}</p>
            <p><a href="/">Back to Home</a></p>
        </body>
    </html>
    """, 500

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='VocalLocal Web Service (Simple)')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    print(f"🚀 Starting VocalLocal Simple on http://localhost:{args.port}")
    print("📋 Available routes will be listed at /debug-routes")
    
    app.run(debug=args.debug, host=args.host, port=args.port)
