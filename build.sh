#!/usr/bin/env bash
# Install system dependencies for PyAudio
apt-get update
apt-get install -y portaudio19-dev python3-pyaudio

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories if they don't exist
mkdir -p transcripts logs
touch transcripts/.gitkeep logs/.gitkeep 