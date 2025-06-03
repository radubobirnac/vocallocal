# DigitalOcean Deployment - Quick Commands

## 🚀 **Essential Commands for DigitalOcean Console**

### **Step 1: Create OAuth Credentials**
```bash
cat > Oauth.json << 'EOF'
{
  "web": {
    "client_id": "251369708830-a60ai4q3v5uut6hasvttkfca8mueqqr7.apps.googleusercontent.com",
    "project_id": "vocal-local-e1e70",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "REPLACE_WITH_YOUR_CLIENT_SECRET",
    "redirect_uris": [
      "https://YOUR_APP_NAME.ondigitalocean.app/auth/callback"
    ],
    "javascript_origins": [
      "https://YOUR_APP_NAME.ondigitalocean.app"
    ]
  }
}
EOF
```

### **Step 2: Create Firebase Credentials**
```bash
cat > firebase-credentials.json << 'EOF'
{
  "type": "service_account",
  "project_id": "vocal-local-e1e70",
  "private_key_id": "REPLACE_WITH_YOUR_PRIVATE_KEY_ID",
  "private_key": "-----BEGIN PRIVATE KEY-----\nREPLACE_WITH_YOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@vocal-local-e1e70.iam.gserviceaccount.com",
  "client_id": "REPLACE_WITH_YOUR_CLIENT_ID",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40vocal-local-e1e70.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
EOF
```

### **Step 3: Verify Files**
```bash
# Check files exist
ls -la *.json

# Verify JSON format
python -m json.tool Oauth.json
python -m json.tool firebase-credentials.json
```

### **Step 4: Test Application**
```bash
# Test Firebase connection
python -c "import firebase_config; firebase_config.initialize_firebase(); print('✅ Firebase working')"

# Check app status
ps aux | grep python
```

## 📋 **Environment Variables for DigitalOcean**

Set these in **Settings** → **Environment Variables**:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=generate_random_32_character_string
FIREBASE_DATABASE_URL=https://vocal-local-e1e70-default-rtdb.firebaseio.com
FIREBASE_STORAGE_BUCKET=vocal-local-e1e70.appspot.com

# Optional
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_CLIENT_ID=251369708830-a60ai4q3v5uut6hasvttkfca8mueqqr7.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://YOUR_APP_NAME.ondigitalocean.app/auth/callback
```

## 🔧 **App Configuration**

### Build Settings:
- **Build Command**: `pip install -r requirements.txt`
- **Run Command**: `python app.py`
- **Port**: `5001`
- **Source Directory**: `/vocallocal` (if app is in subdirectory)

### Google OAuth Setup:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Add redirect URI: `https://YOUR_APP_NAME.ondigitalocean.app/auth/callback`
3. Add JavaScript origin: `https://YOUR_APP_NAME.ondigitalocean.app`

## 🚨 **Troubleshooting Commands**

```bash
# If app won't start
tail -f /var/log/app.log

# If credentials are missing
ls -la *.json

# If Firebase fails
python test_firebase_fix.py

# Recreate credentials (if lost after restart)
# Run the cat commands from Step 1 and 2 again
```

## ⚡ **Quick Deployment Checklist**

1. ✅ Push code to GitHub
2. ✅ Create DigitalOcean app from GitHub repo
3. ✅ Set environment variables in DigitalOcean dashboard
4. ✅ Deploy app
5. ✅ Access console and create credential files
6. ✅ Update Google OAuth redirect URIs
7. ✅ Test the application

## 🎯 **Your App URL**
`https://YOUR_APP_NAME.ondigitalocean.app`

Replace `YOUR_APP_NAME` with your actual DigitalOcean app name!
