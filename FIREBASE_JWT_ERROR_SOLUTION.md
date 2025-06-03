# Firebase JWT Signature Error - Complete Solution

## 🚨 Problem Identified

Your Firebase service account credentials are causing an "Invalid JWT Signature" error. This is a common issue that occurs when:

- The service account key is outdated or corrupted
- The service account lacks proper permissions
- There are clock synchronization issues

## ✅ **SOLUTION: Regenerate Firebase Service Account Key**

### Step 1: Delete Current Service Account Key

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project: **vocal-local-e1e70**
3. Click the gear icon ⚙️ → **Project Settings**
4. Go to **Service Accounts** tab
5. Find your current service account: `firebase-adminsdk-fbsvc@vocal-local-e1e70.iam.gserviceaccount.com`
6. **Delete the existing private key** (if any are listed)

### Step 2: Generate New Service Account Key

1. In the same **Service Accounts** tab
2. Click **"Generate new private key"**
3. Click **"Generate key"** in the confirmation dialog
4. A new JSON file will be downloaded
5. **Save this file as `firebase-credentials.json`** in your project directory

### Step 3: Verify Service Account Permissions

Make sure your service account has these roles in Google Cloud Console:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select project: **vocal-local-e1e70**
3. Navigate to **IAM & Admin** → **IAM**
4. Find your service account: `firebase-adminsdk-fbsvc@vocal-local-e1e70.iam.gserviceaccount.com`
5. Ensure it has these roles:
   - ✅ **Firebase Admin SDK Administrator Service Agent**
   - ✅ **Firebase Realtime Database Admin**
   - ✅ **Firebase Authentication Admin**

### Step 4: Replace Your Credentials File

```bash
# Backup your current file (optional)
cp firebase-credentials.json firebase-credentials.json.old

# Replace with the newly downloaded file
# Copy the new JSON content to firebase-credentials.json
```

### Step 5: Test the Fix

Run the diagnostic script again:

```bash
python fix_firebase_jwt_error.py
```

You should see:
```
✅ Firebase initialization successful
✅ Database write test successful
✅ Test cleanup successful
```

## 🔧 Alternative Solution: Use Environment Variables

If file-based credentials continue to have issues, you can use environment variables:

### Option A: Complete JSON in Environment Variable

1. **Convert your new credentials to environment variable**:
   ```bash
   python convert_json_to_env.py
   ```

2. **Set the environment variable**:
   ```bash
   # In your .env file
   FIREBASE_CREDENTIALS_JSON={"type":"service_account","project_id":"vocal-local-e1e70",...}
   ```

### Option B: Use Application Default Credentials

1. **Install Google Cloud SDK**
2. **Authenticate with your Google account**:
   ```bash
   gcloud auth application-default login
   ```
3. **Remove the credentials file** (let it use ADC)

## 🚀 Quick Fix Commands

If you want to quickly test with a fresh service account:

```bash
# 1. Download new service account key from Firebase Console
# 2. Replace the file
cp /path/to/downloaded/key.json firebase-credentials.json

# 3. Test immediately
python fix_firebase_jwt_error.py

# 4. If successful, test the full application
python app.py
```

## 🔍 Verification Steps

After implementing the solution:

1. **Test Firebase Connection**:
   ```bash
   python -c "import firebase_config; firebase_config.initialize_firebase(); print('✅ Firebase working')"
   ```

2. **Test Google OAuth Login**:
   - Start the application: `python app.py`
   - Go to: `http://localhost:5001`
   - Try Google OAuth login
   - Should work without JWT signature errors

3. **Check Application Logs**:
   - Look for successful Firebase initialization messages
   - No more "Invalid JWT Signature" errors

## 🛡️ Security Notes

- **Never commit** the new `firebase-credentials.json` to version control
- **Keep the file secure** - it provides admin access to your Firebase project
- **Rotate keys regularly** for better security
- **Use environment variables** in production deployments

## 📞 If Issues Persist

If you still get JWT signature errors after regenerating the key:

1. **Check system time synchronization**:
   ```bash
   # Windows
   w32tm /resync
   
   # Linux/Mac
   sudo ntpdate -s time.nist.gov
   ```

2. **Verify Firebase project settings**:
   - Ensure the project ID matches: `vocal-local-e1e70`
   - Check that Realtime Database is enabled
   - Verify Authentication is enabled

3. **Try a completely new service account**:
   - Create a new service account in Google Cloud Console
   - Assign the same permissions
   - Generate a new key

## 🎯 Expected Result

After following these steps:

- ✅ Google OAuth login will work without errors
- ✅ User data will be saved to Firebase
- ✅ Transcription history will be stored properly
- ✅ No more "Invalid JWT Signature" errors

The most common cause is an outdated service account key, so regenerating it should resolve the issue immediately.
