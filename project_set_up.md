# VocalLocal Project Setup Guide

This guide provides step-by-step instructions for setting up the VocalLocal project on your local machine.

## Prerequisites

- Python 3.8 or higher
- Git
- OpenAI API key
- Google Gemini API key (optional)
- Firebase project (optional, for user authentication and data storage)
- Google OAuth credentials (optional, for Google Sign-In)

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

# Optional
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here
FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=https://localhost:5001/auth/callback
```

### 5. Set Up SSL Certificates (for HTTPS)

Generate self-signed certificates for local development:

```bash
python generate_dev_certs.py
```

This will create SSL certificates in the `ssl` directory.

### 6. Configure Firebase (Optional)

If you want to use Firebase for authentication and data storage:

1. Create a Firebase project at [firebase.google.com](https://firebase.google.com)
2. Generate a service account key from Project Settings > Service Accounts
3. Save the JSON file as `firebase-credentials.json` in the project root

### 7. Configure Google OAuth (Optional)

If you want to enable Google Sign-In:

1. Create OAuth credentials in the [Google Cloud Console](https://console.cloud.google.com)
2. Set the authorized redirect URI to `https://localhost:5001/auth/callback`
3. Save the client ID and secret in your `.env` file

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

### Port Already in Use

If the port is already in use:
- Change the port number in the command: `python app.py --port 5002`
- Or kill the process using the port and try again

## Deployment

For deployment to Render, refer to the main README.md file.