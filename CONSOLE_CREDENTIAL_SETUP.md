# Console-Based Credential Setup Guide

This guide shows you how to create credential files directly on your deployment server using simple console commands. This is the **recommended approach** for VocalLocal deployment - it's simple, secure, and works on all platforms.

## Why Console-Based Setup?

✅ **Simple**: Just copy-paste your JSON content  
✅ **Secure**: Files exist only on the server, never in version control  
✅ **Universal**: Works on any platform (Render, Heroku, DigitalOcean, VPS)  
✅ **Familiar**: Uses standard console commands that most developers know  
✅ **No Code Changes**: Uses existing file-based credential system  

## Required Credential Files

You need to create two files on your deployment server:

1. **`Oauth.json`** - Google OAuth credentials
2. **`firebase-credentials.json`** - Firebase service account credentials

## Platform-Specific Instructions

### 🚀 Render

1. **Access Console**:
   - Go to your service dashboard on Render
   - Click on the **"Shell"** tab
   - This opens a terminal in your deployed application

2. **Create OAuth Credentials**:
   ```bash
   cat > Oauth.json << 'EOF'
   {
     "web": {
       "client_id": "your-client-id-here",
       "project_id": "your-project-id",
       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
       "token_uri": "https://oauth2.googleapis.com/token",
       "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
       "client_secret": "your-client-secret-here",
       "redirect_uris": [
         "https://your-app.onrender.com/auth/callback"
       ],
       "javascript_origins": [
         "https://your-app.onrender.com"
       ]
     }
   }
   EOF
   ```

3. **Create Firebase Credentials**:
   ```bash
   cat > firebase-credentials.json << 'EOF'
   {
     "type": "service_account",
     "project_id": "your-project-id",
     "private_key_id": "your-private-key-id",
     "private_key": "-----BEGIN PRIVATE KEY-----\nyour-private-key-content\n-----END PRIVATE KEY-----\n",
     "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
     "client_id": "your-client-id",
     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
     "token_uri": "https://oauth2.googleapis.com/token",
     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
     "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com",
     "universe_domain": "googleapis.com"
   }
   EOF
   ```

### 🌊 DigitalOcean App Platform

1. **Access Console**:
   - Go to your app in DigitalOcean
   - Navigate to the **Console** tab
   - Open a terminal session

2. **Navigate to App Directory**:
   ```bash
   cd /workspace
   # or wherever your app is deployed
   ```

3. **Create credential files** using the same `cat` commands as shown above

### 🟣 Heroku

1. **Access Console**:
   ```bash
   # Use Heroku CLI to access your app's console
   heroku run bash -a your-app-name
   ```

2. **Create credential files** using the same `cat` commands as shown above

### 🖥️ VPS/Server

1. **SSH into your server**:
   ```bash
   ssh user@your-server.com
   ```

2. **Navigate to your app directory**:
   ```bash
   cd /path/to/your/vocallocal/app
   ```

3. **Create credential files** using the same `cat` commands as shown above

## Alternative Method: Using Text Editors

If you prefer using a text editor instead of `cat` commands:

### Using nano:
```bash
# Create OAuth file
nano Oauth.json
# Paste your JSON content, then press Ctrl+X, Y, Enter to save

# Create Firebase file
nano firebase-credentials.json
# Paste your JSON content, then press Ctrl+X, Y, Enter to save
```

### Using vim:
```bash
# Create OAuth file
vim Oauth.json
# Press 'i' to enter insert mode, paste content, press Esc, type ':wq' to save

# Create Firebase file
vim firebase-credentials.json
# Press 'i' to enter insert mode, paste content, press Esc, type ':wq' to save
```

## Getting Your Credential Content

### Google OAuth Credentials (`Oauth.json`)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project
3. Navigate to **APIs & Services** > **Credentials**
4. Find your OAuth 2.0 Client ID
5. Click the download button to get the JSON file
6. Copy the content and paste it when creating `Oauth.json`

### Firebase Credentials (`firebase-credentials.json`)

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. Go to **Project Settings** > **Service Accounts**
4. Click **"Generate new private key"**
5. Download the JSON file
6. Copy the content and paste it when creating `firebase-credentials.json`

## Verification

After creating the files, verify they exist and are valid:

```bash
# Check if files exist
ls -la *.json

# Verify JSON format (optional)
python -m json.tool Oauth.json
python -m json.tool firebase-credentials.json
```

## Security Notes

🔒 **Security Best Practices**:
- Files are created directly on the server, never in version control
- Credential files are already in `.gitignore`
- Only authorized personnel should have server access
- Regularly rotate credentials for security
- Use platform-specific secret management when available

## Troubleshooting

### File Not Found Errors
- Make sure you're in the correct directory
- Check file permissions: `chmod 644 *.json`
- Verify the application can read the files

### JSON Format Errors
- Use the verification commands above to check JSON syntax
- Make sure there are no extra characters or line breaks
- Copy the exact JSON content from your downloaded files

### Permission Issues
- Ensure the application user can read the files
- Check file ownership: `chown app-user:app-group *.json`

## What Happens Next?

Once you create these files:

1. **VocalLocal automatically detects them** on startup
2. **Authentication works immediately** - no restart needed on most platforms
3. **Google OAuth login** becomes available
4. **Firebase features** (user data, history) work correctly

The application checks for credential files in this order:
1. App root directory (where you create them)
2. `/etc/secrets/` (platform secret mounts)
3. `/app/` (Heroku-style deployments)
4. User home directory

## Need Help?

If you encounter issues:
1. Check the application logs for specific error messages
2. Verify your JSON files are valid using the verification commands
3. Ensure your OAuth redirect URIs match your deployment URL
4. Make sure your Firebase project is properly configured

This console-based approach is the simplest and most reliable way to set up credentials for VocalLocal!
