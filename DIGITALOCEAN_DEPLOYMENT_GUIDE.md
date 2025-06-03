# DigitalOcean App Platform Deployment Guide

## 🚀 Complete Step-by-Step Deployment Instructions

### Prerequisites
- ✅ GitHub repository with VocalLocal code
- ✅ DigitalOcean account
- ✅ Firebase project setup
- ✅ Google OAuth credentials
- ✅ API keys (OpenAI, Gemini)

---

## 📋 **STEP 1: Prepare Your Repository**

### 1.1 Ensure Clean Repository
```bash
# Make sure no credential files are committed
git status
git add .
git commit -m "Prepare for DigitalOcean deployment"
git push origin main
```

### 1.2 Verify .gitignore Protection
Your credential files should already be protected:
- ✅ `firebase-credentials.json`
- ✅ `Oauth.json`
- ✅ `.env`

---

## 🌊 **STEP 2: Create DigitalOcean App**

### 2.1 Create New App
1. Go to [DigitalOcean Cloud](https://cloud.digitalocean.com)
2. Click **"Create"** → **"Apps"**
3. Choose **"GitHub"** as source
4. Select your VocalLocal repository
5. Choose branch: **main**
6. Auto-deploy: **Enabled** ✅

### 2.2 Configure Build Settings
- **Source Directory**: `/vocallocal` (if your app is in a subdirectory)
- **Build Command**: `pip install -r requirements.txt`
- **Run Command**: `python app.py`
- **Port**: `5001`

### 2.3 Choose Plan
- **Basic Plan**: $5/month (recommended for testing)
- **Professional Plan**: $12/month (for production)

---

## ⚙️ **STEP 3: Configure Environment Variables**

### 3.1 Set Required Environment Variables
In DigitalOcean App Platform dashboard:

1. Go to **Settings** → **Environment Variables**
2. Add these variables:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here_generate_random_string

# Firebase Configuration
FIREBASE_DATABASE_URL=https://vocal-local-e1e70-default-rtdb.firebaseio.com
FIREBASE_STORAGE_BUCKET=vocal-local-e1e70.appspot.com

# Optional API Keys
GEMINI_API_KEY=your_gemini_api_key_here

# Google OAuth (Individual - Optional, we'll use file-based)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://your-app-name.ondigitalocean.app/auth/callback
```

### 3.2 Generate SECRET_KEY
```python
# Run this locally to generate a secret key
import secrets
print(secrets.token_hex(32))
# Copy the output to SECRET_KEY environment variable
```

---

## 🚀 **STEP 4: Deploy the App**

### 4.1 Initial Deployment
1. Click **"Create Resources"**
2. Wait for deployment (5-10 minutes)
3. Note your app URL: `https://your-app-name.ondigitalocean.app`

### 4.2 Check Deployment Status
- ✅ Build should complete successfully
- ✅ App should start (may show errors about missing credentials - this is normal)

---

## 🔐 **STEP 5: Create Credential Files via Console**

### 5.1 Access DigitalOcean Console
1. In your app dashboard, go to **"Console"** tab
2. Click **"Create Console"**
3. This opens a terminal in your deployed app

### 5.2 Create OAuth Credentials File
```bash
# In the DigitalOcean console, run:
cat > Oauth.json << 'EOF'
{
  "web": {
    "client_id": "your-google-client-id-here",
    "project_id": "vocal-local-e1e70",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-google-client-secret-here",
    "redirect_uris": [
      "https://your-app-name.ondigitalocean.app/auth/callback"
    ],
    "javascript_origins": [
      "https://your-app-name.ondigitalocean.app"
    ]
  }
}
EOF
```

### 5.3 Create Firebase Credentials File
```bash
# In the DigitalOcean console, run:
cat > firebase-credentials.json << 'EOF'
{
  "type": "service_account",
  "project_id": "vocal-local-e1e70",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nyour-private-key-content-here\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@vocal-local-e1e70.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40vocal-local-e1e70.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
EOF
```

### 5.4 Verify Files Created
```bash
# Check files exist
ls -la *.json

# Verify JSON format
python -m json.tool Oauth.json
python -m json.tool firebase-credentials.json
```

---

## 🔧 **STEP 6: Update Google OAuth Settings**

### 6.1 Update OAuth Redirect URIs
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **APIs & Services** → **Credentials**
3. Find your OAuth 2.0 Client ID
4. Add these URIs:
   ```
   https://your-app-name.ondigitalocean.app/auth/callback
   ```
5. Add JavaScript origins:
   ```
   https://your-app-name.ondigitalocean.app
   ```

---

## ✅ **STEP 7: Test Deployment**

### 7.1 Restart App (if needed)
- In DigitalOcean dashboard, click **"Actions"** → **"Force Rebuild and Deploy"**

### 7.2 Test Application
1. Visit: `https://your-app-name.ondigitalocean.app`
2. Test Google OAuth login
3. Test transcription features
4. Verify user data is saved

### 7.3 Check Logs
- In DigitalOcean dashboard, go to **"Runtime Logs"**
- Look for successful Firebase initialization
- No "Invalid JWT Signature" errors

---

## 🛠️ **STEP 8: Troubleshooting Commands**

### 8.1 If App Won't Start
```bash
# In DigitalOcean console:
# Check if files exist
ls -la

# Check app logs
tail -f /var/log/app.log

# Test Firebase connection
python -c "import firebase_config; firebase_config.initialize_firebase(); print('Firebase OK')"
```

### 8.2 If OAuth Fails
```bash
# Verify OAuth file
cat Oauth.json

# Check redirect URI matches
echo "Current app URL: https://your-app-name.ondigitalocean.app"
```

### 8.3 If Credentials Are Lost
```bash
# Files may be lost on app restart - recreate them:
# Run the cat commands from Step 5.2 and 5.3 again
```

---

## 📋 **STEP 9: Production Checklist**

### 9.1 Security
- ✅ Credential files not in version control
- ✅ Environment variables set securely
- ✅ HTTPS enabled (automatic on DigitalOcean)
- ✅ API keys secured

### 9.2 Performance
- ✅ Choose appropriate plan size
- ✅ Monitor resource usage
- ✅ Set up alerts

### 9.3 Monitoring
- ✅ Check runtime logs regularly
- ✅ Monitor error rates
- ✅ Set up uptime monitoring

---

## 🚨 **Important Notes**

### Credential File Persistence
⚠️ **Important**: Files created via console may be lost during app restarts/rebuilds. For production:

1. **Option A**: Use environment variables instead:
   ```bash
   # Set these in DigitalOcean environment variables:
   GOOGLE_OAUTH_CREDENTIALS_JSON={"web":{"client_id":"...","client_secret":"..."}}
   FIREBASE_CREDENTIALS_JSON={"type":"service_account","project_id":"vocal-local-e1e70",...}
   ```

2. **Option B**: Use DigitalOcean Spaces for file storage
3. **Option C**: Recreate files after each deployment

### Custom Domain (Optional)
1. Add your domain in DigitalOcean dashboard
2. Update OAuth redirect URIs to use your domain
3. Update environment variables

---

## 🎯 **Expected Result**

After following these steps:
- ✅ VocalLocal running on DigitalOcean
- ✅ Google OAuth login working
- ✅ Firebase data storage working
- ✅ All transcription features functional
- ✅ Secure credential management

Your app will be available at: `https://your-app-name.ondigitalocean.app`

## 📞 **Need Help?**

If you encounter issues:
1. Check DigitalOcean runtime logs
2. Use the console to verify credential files
3. Test individual components using the troubleshooting commands
4. Refer to `FIREBASE_JWT_ERROR_SOLUTION.md` for Firebase issues
