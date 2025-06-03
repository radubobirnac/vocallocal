# Environment Variables Configuration Guide

This guide explains how to configure VocalLocal with secure environment variables instead of committing credential files to version control.

## Overview

VocalLocal now supports secure environment variable configuration for:
- **Firebase credentials** (`FIREBASE_CREDENTIALS_JSON`)
- **Google OAuth credentials** (`GOOGLE_OAUTH_CREDENTIALS_JSON`)

This approach improves security by keeping sensitive credentials out of the codebase while maintaining full functionality.

## Environment Variables

### Firebase Configuration

#### Primary (Recommended)
```bash
# Complete Firebase service account JSON as a single line
FIREBASE_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project-id",...}
```

#### Legacy Support
```bash
# Still supported for backward compatibility
FIREBASE_CREDENTIALS={"type":"service_account","project_id":"your-project-id",...}
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
```

#### Database Configuration
```bash
FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

### Google OAuth Configuration

#### Primary (Recommended)
```bash
# Complete OAuth JSON as a single line
GOOGLE_OAUTH_CREDENTIALS_JSON={"web":{"client_id":"your_client_id",...}}
```

#### Legacy Support
```bash
# Still supported for backward compatibility
OAUTH_CREDENTIALS={"web":{"client_id":"your_client_id",...}}
```

#### Individual Fields (Legacy)
```bash
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=https://localhost:5001/auth/callback
```

## Setup Instructions

### Step 1: Convert JSON Files to Environment Variables

Run the conversion script to generate environment variables from your JSON files:

```bash
cd vocallocal
python convert_json_to_env.py
```

This script will:
1. Read your `Oauth.json` and `firebase-credentials.json` files
2. Convert them to single-line JSON strings
3. Display the environment variable format
4. Provide security guidance

### Step 2: Set Environment Variables

#### For Local Development

Create a `.env` file in the `vocallocal` directory:

```bash
# Copy from .env.example
cp .env.example .env

# Add the generated environment variables to .env
# Example:
GOOGLE_OAUTH_CREDENTIALS_JSON={"web":{"client_id":"251369708830-...","project_id":"vocal-local-e1e70",...}}
FIREBASE_CREDENTIALS_JSON={"type":"service_account","project_id":"vocal-local-e1e70",...}}
```

#### For Production Deployment

Set environment variables in your deployment platform:

**Render:**
1. Go to your service dashboard
2. Navigate to Environment tab
3. Add the environment variables

**DigitalOcean App Platform:**
1. Go to your app settings
2. Navigate to Environment Variables
3. Add the variables

**Heroku:**
```bash
heroku config:set GOOGLE_OAUTH_CREDENTIALS_JSON='{"web":{"client_id":"..."}}'
heroku config:set FIREBASE_CREDENTIALS_JSON='{"type":"service_account",...}'
```

## Fallback Behavior

The application uses a priority system for credential loading:

### Firebase Credentials (in order)
1. `FIREBASE_CREDENTIALS_JSON` environment variable
2. `FIREBASE_CREDENTIALS` environment variable (legacy)
3. `FIREBASE_CREDENTIALS_PATH` file path
4. Application Default Credentials

### OAuth Credentials (in order)
1. `GOOGLE_OAUTH_CREDENTIALS_JSON` environment variable
2. `OAUTH_CREDENTIALS` environment variable (legacy)
3. `Oauth.json` file in various locations
4. Individual environment variables (`GOOGLE_CLIENT_ID`, etc.)

## Security Best Practices

### ✅ Do
- Use environment variables for production deployments
- Keep JSON credential files in `.gitignore`
- Use your deployment platform's secure environment variable storage
- Regularly rotate credentials
- Use the conversion script to generate proper format

### ❌ Don't
- Commit credential files to version control
- Share environment variable values publicly
- Store credentials in plain text files in production
- Use the same credentials across multiple environments

## File Structure

```
vocallocal/
├── .env.example              # Template with all environment variables
├── .gitignore               # Excludes credential files
├── convert_json_to_env.py   # Conversion utility script
├── Oauth.json              # Local OAuth credentials (gitignored)
├── firebase-credentials.json # Local Firebase credentials (gitignored)
└── ...
```

## Troubleshooting

### Common Issues

1. **JSON Parsing Errors**
   - Ensure JSON is properly escaped
   - Use the conversion script to generate correct format
   - Check for missing quotes or brackets

2. **Authentication Failures**
   - Verify environment variables are set correctly
   - Check application logs for specific error messages
   - Ensure credentials have proper permissions

3. **Fallback to File-based Credentials**
   - Check if environment variables are properly set
   - Verify JSON format is correct
   - Review application startup logs

### Debug Commands

```bash
# Check if environment variables are set
echo $GOOGLE_OAUTH_CREDENTIALS_JSON
echo $FIREBASE_CREDENTIALS_JSON

# Test credential conversion
python convert_json_to_env.py

# Check application logs for authentication status
python app.py
```

## Migration from File-based Credentials

If you're migrating from file-based credentials:

1. **Backup your existing files**
2. **Run the conversion script** to generate environment variables
3. **Set environment variables** in your deployment platform
4. **Test the application** to ensure authentication works
5. **Remove credential files** from version control (they're already in .gitignore)

The application maintains backward compatibility, so you can migrate gradually.

## Support

For issues with environment variable configuration:
1. Check the application logs for specific error messages
2. Verify JSON format using the conversion script
3. Ensure all required environment variables are set
4. Review the fallback behavior section above
