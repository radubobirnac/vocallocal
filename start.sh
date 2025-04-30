#!/bin/bash

# Ensure Google packages are installed
pip install google-generativeai>=0.8.5
pip install google-api-core google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib googleapis-common-protos protobuf

# Start the application
gunicorn app:app
