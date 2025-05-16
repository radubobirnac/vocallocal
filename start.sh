#!/bin/bash

# Print debugging information
echo "Starting deployment script..."
echo "Python version:"
python --version
echo "Pip version:"
pip --version

# Install Google packages directly into the site-packages directory
echo "Installing Google packages directly..."
python -m pip install --target=/opt/render/project/src/.venv/lib/python3.11/site-packages google-generativeai>=0.8.5
python -m pip install --target=/opt/render/project/src/.venv/lib/python3.11/site-packages google-api-core google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib googleapis-common-protos protobuf

# Verify installation
echo "Checking installed packages:"
pip list | grep google

# Check Python path
echo "Python path:"
python -c "import sys; print('\n'.join(sys.path))"

# Try to import the google package
echo "Trying to import google package..."
python -c "
try:
    import google
    print(f'Successfully imported google package: {google.__file__}')
    try:
        import google.generativeai
        print(f'Successfully imported google.generativeai package: {google.generativeai.__file__}')
    except ImportError as e:
        print(f'Failed to import google.generativeai: {e}')
except ImportError as e:
    print(f'Failed to import google package: {e}')
"

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

# Install pydub for audio chunking
echo "Installing pydub for audio chunking..."
python -m pip install --target=/opt/render/project/src/.venv/lib/python3.11/site-packages pydub

# Check if FFmpeg is installed
echo "Checking for FFmpeg..."
if command -v ffmpeg &> /dev/null; then
  echo "FFmpeg is available"
else
  echo "FFmpeg is not available. Installing..."
  apt-get update && apt-get install -y ffmpeg
fi

# Start the application with our custom Gunicorn configuration
echo "Starting Gunicorn server with memory optimization..."
gunicorn app:app --config gunicorn_config.py
