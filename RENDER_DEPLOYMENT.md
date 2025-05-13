# Deploying VocalLocal to Render

This guide provides instructions for deploying the VocalLocal application to Render.

## Files for Render Deployment

The following files have been created specifically for Render deployment:

1. `app_render.py` - A simplified version of the main application file with direct route handling
2. `auth_render.py` - A fixed version of the authentication module
3. `routes/main_render.py` - A simplified version of the main routes

## Deployment Steps

### 1. Prepare Your Files

1. Rename the files to replace the existing ones:
   ```bash
   copy app_render.py app.py
   copy auth_render.py auth.py
   copy routes\main_render.py routes\main.py
   ```

2. Commit the changes to your GitHub repository:
   ```bash
   git add .
   git commit -m "Fix routing for Render deployment"
   git push origin main
   ```

### 2. Deploy to Render

1. Log in to your Render account
2. Connect to your GitHub repository if you haven't already
3. Create a new Web Service:
   - Select your repository
   - Name: `vocallocal` (or your preferred name)
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

### 3. Configure Environment Variables

Add the following environment variables in the Render dashboard:

- `GOOGLE_CLIENT_ID`: Your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth client secret
- `SECRET_KEY`: A secure random string for Flask sessions
- `ADMIN_USERNAME`: Admin username (default: admin)
- `ADMIN_EMAIL`: Admin email (default: admin@example.com)
- `ADMIN_PASSWORD`: Admin password

### 4. Add Secrets (if needed)

If you have Firebase credentials or OAuth.json, add them as secrets:

1. Go to the "Secrets" tab in your Render dashboard
2. Add a new secret file:
   - Mount Path: `/etc/secrets/firebase-credentials`
   - Contents: Your Firebase credentials JSON

### 5. Deploy and Test

1. Click "Create Web Service" to deploy
2. Wait for the deployment to complete
3. Test the application by visiting the provided URL

## Troubleshooting

### Common Issues

1. **BuildError: Could not build url for endpoint 'main.index'**
   - This error occurs when the blueprint registration is not working correctly
   - Solution: Use the provided `app_render.py` which includes a root-level index route

2. **Google OAuth Callback Issues**
   - If Google OAuth callbacks fail, check the redirect URIs in your Google Cloud Console
   - Make sure they match the URLs in your Render deployment

3. **Firebase Connection Issues**
   - Verify that your Firebase credentials are correctly mounted as secrets
   - Check the logs for any Firebase initialization errors

### Checking Logs

To diagnose issues, check the logs in the Render dashboard:

1. Go to your Web Service in the Render dashboard
2. Click on the "Logs" tab
3. Look for error messages, especially Python tracebacks

## Important Notes

1. The `app_render.py` file includes a root-level index route to avoid blueprint routing issues
2. Authentication redirects use `url_for('index')` instead of `url_for('main.index')`
3. The application uses environment variables for configuration instead of local files

## Reverting to Local Development

If you need to revert to the original files for local development:

```bash
git checkout -- app.py auth.py routes/main.py
```

This will restore the original files from your Git repository.
