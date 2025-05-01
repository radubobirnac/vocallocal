#!/bin/bash

# This script runs after the build process on Render

echo "Running postbuild script..."
echo "Python version:"
python --version
echo "Pip version:"
pip --version

# Explicitly install Google packages
echo "Explicitly installing Google packages..."
pip install google-generativeai>=0.8.5 --verbose
pip install google-api-core google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib googleapis-common-protos protobuf --verbose

# Verify installation
echo "Checking installed packages:"
pip list | grep google

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

echo "Postbuild script completed."
