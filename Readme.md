# VocalLocal Project Setup Guide

This guide provides step-by-step instructions for setting up the VocalLocal project on your local machine.

## Latest Updates

### Bug Fixes and Stability Improvements (25/05/2025)

- 🔧 **Fixed Firebase Storage Bucket Error**: Resolved "Storage bucket name not specified" error by adding proper storage bucket configuration
- 🔧 **Improved Import System**: Implemented robust import system with comprehensive fallback mechanisms for Transcription/Translation models
- 🔧 **Enhanced Error Handling**: Added comprehensive error handling throughout the application with graceful degradation
- 🔧 **Fixed Navigation Issues**: Resolved broken functionality when navigating between different dropdowns and sections
- 🔧 **Added Fallback Services**: Application now continues to work even when Firebase services are partially unavailable
- 🔧 **Improved Dashboard Stability**: Dashboard now handles Firebase initialization errors gracefully
- 🔧 **Better Environment Configuration**: Added FIREBASE_STORAGE_BUCKET to environment configuration

### Cache Busting Implementation (26/05/2025)

- 🚀 **Comprehensive Cache Busting System**: Implemented automatic cache-busting for all static assets (CSS, JavaScript files)
- 🚀 **Version-Based URLs**: Static files now include version parameters based on file modification time
- 🚀 **Service Worker Integration**: Added service worker for intelligent caching strategies and update notifications
- 🚀 **HTTP Cache Headers**: Proper cache control headers for different file types and scenarios
- 🚀 **Browser Compatibility**: Meta tags and headers to prevent cache-related functionality issues
- 🚀 **Automatic Updates**: Users receive notifications when new versions are available
- 🚀 **Security Headers**: Added comprehensive security headers for better protection
- 🚀 **Debug Tools**: Built-in cache management tools for developers and troubleshooting

### Previous Updates (20/05/2023)

- Implemented Google OAuth authentication for user login
- Added manual username/password authentication with secure practices
- Created a new home page as landing page for non-authenticated users
- Added About Us section with project information
- Implemented Transcript History feature under History dropdown
- Unified transcription and translation history with search and filtering capabilities
- Improved navigation with dedicated History dropdown menu
- Enhanced UI with consistent styling across pages
- **NEW**: Implemented Monthly Usage Reset System compatible with Firebase free plan
- **NEW**: Added admin interface for usage monitoring and manual reset triggers
- **NEW**: Automatic client-side usage reset with data archiving
- **NEW**: External cron service support for automated monthly resets

## Prerequisites

- Python 3.8 or higher
- Git
- OpenAI API key
- Google Gemini API key (optional)
- Firebase project (required for user authentication and data storage)
- Google OAuth credentials (required for Google Sign-In)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/radubobirnac/vocallocal.git
cd vocallocal
```

### 2. Create and Activate Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env
```

Edit the `.env` file and add your API keys and configuration:

```
# Required
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com

# Required for Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=https://localhost:5001/auth/callback

# Optional
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Set Up SSL Certificates (for HTTPS)

Generate self-signed certificates for local development:

```bash
python generate_dev_certs.py
```

This will create SSL certificates in the `ssl` directory.

### 6. Configure Firebase (Required)

Firebase is required for user authentication, transcript history, data storage, and usage tracking:

1. Create a Firebase project at [firebase.google.com](https://firebase.google.com)
2. Generate a service account key from Project Settings > Service Accounts
3. Save the JSON file as `firebase-credentials.json` in the project root
4. Set up the following in your Firebase database:
   - Create a collection for `users` to store user information
   - Create collections for `transcripts`, `transcriptions`, and `translations` to store user data
   - Add indexes on the `timestamp` field for these collections with the following rules:
     ```json
     "transcripts": {
       ".indexOn": ["timestamp", "user_email"]
     },
     "transcriptions": {
       ".indexOn": ["timestamp", "user_email"],
       "$userId": {
         ".indexOn": "timestamp"
       }
     },
     "translations": {
       ".indexOn": ["timestamp", "user_email"],
       "$userId": {
         ".indexOn": "timestamp"
       }
     }
     ```
   - These indexes are required for sorting and querying data by timestamp

5. **Usage Tracking Setup** (Firebase Free Plan Compatible):

   VocalLocal includes comprehensive usage tracking that works with Firebase's free plan:

   - ✅ **No Cloud Functions Required** - Uses Python services and direct database operations
   - ✅ **Atomic Transactions** - Ensures data consistency
   - ✅ **Real-time Updates** - Updates both currentPeriod and totalUsage counters
   - ✅ **Free Plan Compatible** - Uses only Realtime Database features

   The usage tracking is automatically available once Firebase is configured. See `USAGE_TRACKING_FREE_PLAN.md` for detailed usage instructions.

### 7. Configure Google OAuth (Required for OAuth Login)

To enable Google Sign-In (recommended authentication method):

1. Create OAuth credentials in the [Google Cloud Console](https://console.cloud.google.com)
2. Set the authorized redirect URI to `https://localhost:5001/auth/callback`
3. Save the client ID and secret in your `.env` file
4. Alternatively, save your OAuth credentials in an `OAuth.json` file in the project root

## Running the Application

### Start with HTTPS (Recommended)

```bash
python run_dev_secure.py
```

This will start the server with HTTPS on port 5000.

### Start with HTTP

```bash
python app.py --port 5001
```

Or use the provided batch file:

```bash
start_server.bat
```

## Accessing the Application

- HTTPS: https://localhost:5000
- HTTP: http://localhost:5001

When using HTTPS with self-signed certificates, your browser will show a security warning. Click "Advanced" and then "Proceed" to continue.

## Application Features

### Authentication

- **Google OAuth Login**: Sign in with your Google account
- **Username/Password Authentication**: Register and login with username and password
- **Secure Authentication**: Password hashing and secure session management

### Home Page

- Landing page for non-authenticated users
- Information about the application
- Navigation to login/register

### About Us

- Information about the VocalLocal project
- Project goals and features

### Transcription and Translation

- Record audio for transcription
- Translate transcribed text to multiple languages
- Save transcriptions and translations to your account

### History

- View your transcript history
- Search and filter through past transcriptions and translations
- Unified view of all your content

### Admin Features

- Admin panel at `/admin/users` route
- View and manage registered users
- **Monthly Usage Reset Management** at `/admin/usage-reset` route
  - Real-time usage statistics across all users
  - Manual monthly usage reset with force option
  - Usage history archiving and monitoring
  - Compatible with Firebase free plan (no paid features required)

### Monthly Usage Reset System

VocalLocal includes a comprehensive monthly usage reset system designed to work within Firebase's free plan limitations:

- **Automatic Reset**: Users' monthly usage counters reset automatically when their reset date is reached
- **Data Archiving**: Previous month's usage data is archived to `usage/history/{YYYY-MM}/` before reset
- **Admin Control**: Manual reset triggers available through admin interface
- **External Scheduling**: HTTP trigger support for external free cron services
- **Client-Side Fallback**: Automatic reset checking during user operations
- **Free Plan Compatible**: No Firebase paid features required (no Cloud Scheduler/Tasks)

For detailed setup and usage instructions, see `MONTHLY_USAGE_RESET_GUIDE.md`.

## Troubleshooting

### SSL Certificate Issues

If you encounter SSL certificate issues:
- Regenerate certificates using `python generate_dev_certs.py`
- Make sure the certificates are in the correct directory
- Try using HTTP instead for local development

### API Key Issues

If transcription or translation fails:
- Verify your OpenAI API key is correct and has sufficient credits
- Check the console logs for specific error messages

### Authentication Issues

If Google OAuth login fails:
- Verify your Google OAuth credentials are correct
- Check that the redirect URI matches exactly what's configured in Google Cloud Console
- Ensure your Firebase project is properly configured for authentication

### Firebase Issues

If transcript history or user authentication isn't working:
- Verify your Firebase credentials are correct
- Check that the Firebase database rules include the indexes on the `timestamp` field for all collections
- If you see errors like `Index not defined, add ".indexOn": "timestamp", for path "/transcriptions/user@example,com"`, you need to update your Firebase security rules with the proper indexes
- Follow the detailed instructions in the `firebase-functions/SETUP-GUIDE.md` file for setting up Firebase security rules
- Ensure the Firebase collections are properly set up

### Port Already in Use

If the port is already in use:
- Change the port number in the command: `python app.py --port 5002`
- Or kill the process using the port and try again

### Cache Issues

If users are experiencing functionality problems due to cached files:
- The cache busting system should automatically handle this
- Users can manually clear cache using browser settings
- For debugging, use browser console commands:
  - `cacheControls.checkCacheStatus()` - View cache contents
  - `cacheControls.clearCache()` - Clear all caches
  - `cacheControls.forceUpdate()` - Force service worker update
- Check if service worker is registered: `navigator.serviceWorker.getRegistrations()`
- For detailed troubleshooting, see `CACHE_BUSTING_GUIDE.md`

## Deployment

For deployment to Render, refer to the main README.md file.