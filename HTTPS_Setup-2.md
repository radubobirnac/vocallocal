# HTTPS Setup Guide for VocalLocal

This guide explains how to set up HTTPS for both local development and Render deployment.

## Local Development with HTTPS

1. Install required packages:
   ```
   pip install pyopenssl requests
   ```

2. Generate self-signed certificates:
   ```
   python generate_dev_certs.py
   ```

3. Run the secure development server:
   ```
   python run_dev_secure.py
   ```

4. Your browser will open automatically to https://localhost:5000
   - You'll see a security warning because the certificate is self-signed
   - Click "Advanced" and then "Proceed to localhost (unsafe)" to continue
   - This warning is normal in development and won't appear in production

## Testing HTTPS Redirects

To verify that HTTP requests are properly redirected to HTTPS:

```
python test_https.py
```

You can also test your Render deployment:

```
python test_https.py https://vocallocal-kcbv.onrender.com
```

## Render Deployment

When deploying to Render:

1. Render automatically provides HTTPS for your site
2. The app.py modifications ensure HTTP requests redirect to HTTPS
3. The security headers in render.yaml provide additional protection

Your site will be accessible at https://vocallocal-kcbv.onrender.com and any HTTP requests will automatically redirect to HTTPS.