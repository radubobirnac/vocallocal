#!/bin/bash

# Print debugging information
echo "Starting build script..."
echo "Python version:"
python --version
echo "Pip version:"
pip --version

# Update pip
echo "Updating pip..."
pip install --upgrade pip

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y portaudio19-dev python3-pyaudio

# Install Python dependencies
echo "Installing Python dependencies from requirements-render.txt..."
pip install -r requirements-render.txt

# Explicitly install Google packages
echo "Explicitly installing Google packages..."
pip install google-generativeai>=0.8.5
pip install google-api-core google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib googleapis-common-protos protobuf

# Verify installation
echo "Checking installed packages:"
pip list | grep google

echo "Build script completed successfully."