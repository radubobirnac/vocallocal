# Deploying VocalLocal to Render

This guide covers how to deploy the VocalLocal application to Render.com.

## Prerequisites

- A Render.com account
- Your project code in a Git repository (GitHub, GitLab, etc.)
- Your API keys and configuration values

## Deployment Steps

### 1. Create a New Web Service

1. Log in to your Render dashboard: https://dashboard.render.com/
2. Click on "New +" and select "Web Service"
3. Connect your Git repository
   - Select the repository containing your VocalLocal code
   - If needed, configure access to private repositories

### 2. Configure the Web Service

Fill in the following details:

- **Name**: `vocallocal` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Choose the region closest to your users
- **Branch**: `main` (or your deployment branch)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

### 3. Add Environment Variables

Add the following environment variables under the "Environment" section:

```
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_secret_key
PYTHON_VERSION=3.9
```

Add any other required environment variables from your `.env` file.

### 4. Configure Advanced Options

Under "Advanced" settings:

1. **Auto-Deploy**: Set to "Yes" for automatic deployments when you push to your repository
2. **Health Check Path**: `/health` (if you have a health check endpoint)

### 5. Add Persistent Disk (Optional)

If your application needs to store files:

1. Enable the persistent disk option
2. Set an appropriate disk size (start with 1GB)
3. Set the mount path to `/data`

### 6. Configure Caching

To enable caching for faster builds:

1. In the "Build" section, check "Enable Build Cache"
2. Add the following directories to cache:
   - `.pip-cache`
   - `venv`

### 7. Deploy the Service

Click "Create Web Service" to start the deployment process.

### 8. Upload Firebase and OAuth Credentials

After deployment, you need to add your credential files:

1. Go to your web service in the Render dashboard
2. Navigate to the "Shell" tab
3. Upload your credential files:

```bash
# Create directories if needed
mkdir -p config

# Create and edit the Firebase credentials file
cat > firebase-credentials.json << 'EOL'
{
  "type": "service_account",
  "project_id": "your-project-id",
  ...rest of your Firebase credentials...
}
EOL

# Create and edit the OAuth credentials file
cat > oauth.json << 'EOL'
{
  "web": {
    "client_id": "your-client-id",
    ...rest of your OAuth credentials...
  }
}
EOL
```

### 9. Update OAuth Redirect URIs

Update your Google OAuth redirect URIs to include your Render domain:

1. Go to the Google Cloud Console
2. Navigate to your OAuth 2.0 Client IDs
3. Add your Render domain to the authorized redirect URIs:
   - `https://your-app-name.onrender.com/auth/callback`

### 10. Verify Deployment

1. Once deployment is complete, click on the generated URL to access your application
2. Check the logs for any errors
3. Test the main functionality to ensure everything works correctly

## Redeployment

To redeploy your application:

1. Push changes to your connected Git repository (auto-deploy will trigger)
2. Or manually trigger a deploy from the Render dashboard:
   - Go to your web service
   - Click "Manual Deploy" > "Deploy latest commit"

## Troubleshooting

### Build Failures

If your build fails:
- Check the build logs for specific errors
- Verify your `requirements.txt` file is correct
- Ensure your Python version is compatible

### Runtime Errors

If your application crashes after deployment:
- Check the logs in the Render dashboard
- Verify all environment variables are set correctly
- Ensure credential files are properly uploaded

### SSL/HTTPS Issues

Render automatically provides SSL certificates, but if you have hardcoded HTTP URLs:
- Update any hardcoded URLs to use HTTPS
- Update OAuth redirect URIs to use your Render domain

## Optimizing Performance

- Enable prewarming to reduce cold starts
- Configure auto-scaling if needed (on paid plans)
- Use the persistent disk for file storage instead of ephemeral storage