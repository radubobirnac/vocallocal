@echo off
echo Starting VocalLocal secure server on port 5001...

REM Check if SSL certificates exist
if not exist ssl\cert.pem (
    echo SSL certificates not found. Generating new certificates...
    python generate_dev_certs.py
    if errorlevel 1 (
        echo Failed to generate SSL certificates.
        echo Please run 'python generate_dev_certs.py' manually.
        pause
        exit /b 1
    )
)

REM Start the server with HTTPS on port 5001
echo Starting secure server at https://localhost:5001
python app.py --port 5001 --secure --open-browser

REM Keep the window open if there's an error
if errorlevel 1 (
    echo Server stopped with an error.
    pause
)
