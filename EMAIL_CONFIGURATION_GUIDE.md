# Email Configuration Guide

## Quick Fix for Current Issue

The error "Email service not configured: Missing MAIL_PASSWORD" occurs because the `MAIL_PASSWORD` environment variable is not set in your `.env` file.

### Immediate Solution

1. **Generate Gmail App Password**:
   - Go to your Google Account settings
   - Navigate to Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
   - Copy the 16-character password

2. **Update your `.env` file**:
   Replace `your_gmail_app_password_here` with your actual Gmail app password:
   ```bash
   MAIL_PASSWORD=your_actual_16_character_app_password
   ```

3. **Restart your application** for the changes to take effect.

## Complete Email Configuration

Your `.env` file now includes these email settings:

```bash
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=virinchiaddanki@gmail.com
MAIL_PASSWORD=your_gmail_app_password_here
MAIL_DEFAULT_SENDER=virinchiaddanki@gmail.com
```

## Gmail App Password Setup Steps

1. **Enable 2-Factor Authentication** (required for app passwords)
2. **Generate App Password**:
   - Visit: https://myaccount.google.com/security
   - Click "2-Step Verification"
   - Scroll down to "App passwords"
   - Select "Mail" as the app
   - Generate and copy the password

3. **Security Notes**:
   - App passwords are 16 characters with no spaces
   - Use this password, not your regular Gmail password
   - Keep this password secure and don't share it

## Testing Email Configuration

Run the test script to verify your email setup:

```bash
cd vocallocal
python test_email_functionality.py
```

This will show:
- ✓ Email service configuration status
- ✓ SMTP connection test
- ✓ Email sending test (optional)

## Troubleshooting

### Common Issues:

1. **"SMTP Authentication failed"**:
   - Verify 2FA is enabled on Gmail
   - Double-check the app password
   - Ensure you're using the app password, not regular password

2. **"Connection refused"**:
   - Check firewall settings
   - Verify SMTP server and port settings

3. **"Email service not configured"**:
   - Ensure MAIL_PASSWORD is set in .env
   - Restart the application after changes

### Alternative Email Providers:

If you prefer not to use Gmail, you can configure other providers:

**Outlook/Hotmail:**
```bash
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@outlook.com
MAIL_PASSWORD=your_password
```

**Yahoo:**
```bash
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@yahoo.com
MAIL_PASSWORD=your_app_password
```

## Production Deployment

For production environments:
1. Use environment variables instead of .env files
2. Store credentials securely (e.g., DigitalOcean App Platform environment variables)
3. Consider using dedicated email services like SendGrid or AWS SES for better deliverability

## Email Verification Flow

Once configured, the email verification system will:
1. Generate 6-digit verification codes
2. Send verification emails to new users
3. Validate codes within 10-minute expiration
4. Allow up to 3 verification attempts
5. Provide resend functionality with cooldown
