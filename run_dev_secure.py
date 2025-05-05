import os
import webbrowser
from threading import Timer
from app import app

# Create ssl directory if it doesn't exist
os.makedirs('ssl', exist_ok=True)

def open_browser():
    webbrowser.open_new('https://localhost:5000/')

if __name__ == '__main__':
    # Check if certificates exist, if not, suggest running generate_dev_certs.py
    if not (os.path.exists('ssl/cert.pem') and os.path.exists('ssl/key.pem')):
        print("SSL certificates not found. Please run generate_dev_certs.py first.")
        exit(1)
    
    # Open browser after a short delay
    Timer(1.5, open_browser).start()
    
    app.run(
        host='0.0.0.0',
        port=5000,
        ssl_context=('ssl/cert.pem', 'ssl/key.pem'),
        debug=True
    )

