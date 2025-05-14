
# VocalLocal Setup Guide

This guide will help you set up the VocalLocal application with HTTPS and Google OAuth authentication.

## Prerequisites

- Python 3.8 or higher
- Git
- Google Cloud account (for OAuth)
- Firebase account (for database)

## 🔧 Step 1: Initial Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/radubobirnac/vocallocal.git
   cd vocallocal
   ```

2. Create and activate a virtual environment:

   **On Linux/macOS:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   **On Windows:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file to add your API keys and other required settings.

## 🔒 Step 2: HTTPS Certificate Setup

1. Generate self-signed certificates:
   ```bash
   python generate_dev_certs.py
   ```

2. Run the secure development server:
   ```bash
   python run_dev_secure.py
   ```

3. Your browser should open automatically to https://localhost:5000
   - You'll see a security warning (normal for self-signed certificates)
   - Click "Advanced" and then "Proceed to localhost (unsafe)"

## 🔑 Step 3: Google OAuth Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Go to APIs & Services > Credentials
4. Create an OAuth 2.0 Client ID

5. Add these JavaScript origins:
   - http://localhost:5000
   - https://localhost:5000

6. Add these redirect URIs:
   - http://localhost:5000/auth/callback
   - https://localhost:5000/auth/callback

7. Download the OAuth credentials JSON file
8. Save the file as `Oauth.json` in the project root directory

## 🔥 Step 4: Firebase Config Setup

1. Create a Firebase project at [firebase.google.com](https://firebase.google.com)
2. Generate a service account key from Project Settings > Service Accounts
3. Save the JSON file as `firebase-credentials.json` in the project root
4. Update your `.env` file with the Firebase database URL:
   ```
   FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com
   FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
   ```

## ✅ Running the Application

1. Run with HTTPS:
   ```bash
   python run_dev_secure.py
   ```

2. Or run with standard HTTP:
   ```bash
   python app.py
   ```

## ⚠️ Important Notes

- Do not commit the `Oauth.json` or `firebase-credentials.json` files to version control
- Add them to your `.gitignore` file
- For production deployment, use proper SSL certificates and secure environment variables