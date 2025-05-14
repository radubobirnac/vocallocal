@echo off
echo ===================================================
echo VocalLocal HTTPS Server Launcher
echo ===================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Check if app.py exists
if not exist app.py (
    echo ERROR: app.py not found in the current directory.
    echo Please run this batch file from the VocalLocal root directory.
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking required packages...
python -c "try: import flask, openai, pyopenssl; print('All required packages found.'); except ImportError as e: print(f'Missing package: {str(e)}'); exit(1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Some required packages may be missing.
    echo You might need to run: pip install flask openai pyopenssl
    echo.
    echo Press any key to continue anyway or Ctrl+C to cancel...
    pause >nul
)

REM Check if SSL certificates exist
if not exist ssl\cert.pem (
    echo SSL certificates not found. Generating new certificates...
    
    REM Check if generate_dev_certs.py exists
    if not exist generate_dev_certs.py (
        echo ERROR: generate_dev_certs.py not found.
        echo Creating a simple certificate generator...
        
        echo from OpenSSL import crypto > generate_dev_certs.py
        echo import os >> generate_dev_certs.py
        echo. >> generate_dev_certs.py
        echo # Create ssl directory if it doesn't exist >> generate_dev_certs.py
        echo os.makedirs('ssl', exist_ok=True) >> generate_dev_certs.py
        echo. >> generate_dev_certs.py
        echo # Generate a key pair >> generate_dev_certs.py
        echo key = crypto.PKey() >> generate_dev_certs.py
        echo key.generate_key(crypto.TYPE_RSA, 2048) >> generate_dev_certs.py
        echo. >> generate_dev_certs.py
        echo # Create a self-signed cert >> generate_dev_certs.py
        echo cert = crypto.X509() >> generate_dev_certs.py
        echo cert.get_subject().CN = "localhost" >> generate_dev_certs.py
        echo cert.set_serial_number(1000) >> generate_dev_certs.py
        echo cert.gmtime_adj_notBefore(0) >> generate_dev_certs.py
        echo cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for a year >> generate_dev_certs.py
        echo cert.set_issuer(cert.get_subject()) >> generate_dev_certs.py
        echo cert.set_pubkey(key) >> generate_dev_certs.py
        echo cert.sign(key, 'sha256') >> generate_dev_certs.py
        echo. >> generate_dev_certs.py
        echo # Write to disk >> generate_dev_certs.py
        echo with open("ssl/cert.pem", "wb") as f: >> generate_dev_certs.py
        echo     f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert)) >> generate_dev_certs.py
        echo with open("ssl/key.pem", "wb") as f: >> generate_dev_certs.py
        echo     f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key)) >> generate_dev_certs.py
        echo. >> generate_dev_certs.py
        echo print("Self-signed certificates generated in ssl/ directory") >> generate_dev_certs.py
    )
    
    python generate_dev_certs.py
    if %errorlevel% neq 0 (
        echo ERROR: Failed to generate SSL certificates.
        echo Please run 'python generate_dev_certs.py' manually.
        pause
        exit /b 1
    )
)

echo.
echo ===================================================
echo Starting VocalLocal secure server on port 5001...
echo ===================================================
echo.
echo Server will be available at: https://localhost:5001
echo.
echo NOTE: Your browser may show a security warning because
echo       the certificate is self-signed. This is normal.
echo       Click "Advanced" and then "Proceed" to continue.
echo.
echo Press Ctrl+C to stop the server
echo ===================================================
echo.

REM Start the server with HTTPS on port 5001
python app.py --port 5001 --secure --open-browser

REM Keep the window open if there's an error
if %errorlevel% neq 0 (
    echo.
    echo ===================================================
    echo Server stopped with an error (code: %errorlevel%).
    echo ===================================================
    pause
)
