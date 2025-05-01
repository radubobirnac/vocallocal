#!/bin/bash

# Print debugging information
echo "Starting deployment script..."
echo "Python version:"
python --version
echo "Pip version:"
pip --version

# Ensure Google packages are installed
echo "Installing Google Generative AI package..."
pip install google-generativeai>=0.8.5 --verbose
echo "Installing Google API dependencies..."
pip install google-api-core google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib googleapis-common-protos protobuf --verbose

# Verify installation
echo "Checking installed packages:"
pip list | grep google

# Check environment variables (without revealing values)
echo "Checking environment variables:"
if [ -n "$OPENAI_API_KEY" ]; then
  echo "OPENAI_API_KEY is set"
else
  echo "OPENAI_API_KEY is NOT set"
fi

if [ -n "$GEMINI_API_KEY" ]; then
  echo "GEMINI_API_KEY is set"
else
  echo "GEMINI_API_KEY is NOT set"
fi

# Start the application
echo "Starting Gunicorn server..."
gunicorn app:app
