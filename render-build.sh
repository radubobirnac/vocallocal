#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install FFmpeg
echo "Installing FFmpeg..."
apt-get update
apt-get install -y ffmpeg

# Verify FFmpeg installation
ffmpeg -version

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Print success message
echo "Build completed successfully!"
