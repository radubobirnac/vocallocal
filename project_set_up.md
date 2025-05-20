# VocalLocal Project Setup Guide

This guide provides step-by-step instructions for setting up the VocalLocal project on your local machine.

## Latest Updates (20/05/2023)

- Implemented Google OAuth authentication for user login
- Added manual username/password authentication with secure practices
- Created a new home page as landing page for non-authenticated users
- Added About Us section with project information
- Implemented Transcript History feature under History dropdown
- Unified transcription and translation history with search and filtering capabilities
- Improved navigation with dedicated History dropdown menu
- Enhanced UI with consistent styling across pages

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

Firebase is required for user authentication, transcript history, and data storage:

1. Create a Firebase project at [firebase.google.com](https://firebase.google.com)
2. Generate a service account key from Project Settings > Service Accounts
3. Save the JSON file as `firebase-credentials.json` in the project root
4. Set up the following in your Firebase database:
   - Create a collection for `users` to store user information
   - Create a collection for `transcripts` to store transcription and translation history
   - Add an index on the `timestamp` field for the `transcripts` collection with the rule `.indexOn`: `timestamp` to enable sorting and querying

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
- Only accessible to users with username 'Radu' and password 'Fasteasy'
- View and manage registered users

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
- Check that the Firebase database rules include the index on the `timestamp` field
- Ensure the Firebase collections are properly set up

### Port Already in Use

If the port is already in use:
- Change the port number in the command: `python app.py --port 5002`
- Or kill the process using the port and try again

## Deployment

For deployment to Render, refer to the main README.md file.