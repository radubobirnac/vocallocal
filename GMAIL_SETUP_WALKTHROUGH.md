# Gmail App Password Setup - Step by Step

## Why You Need This
Gmail's security policy requires App Passwords for SMTP authentication. Regular passwords are rejected with error 535.

## Prerequisites Check
1. **Gmail Account**: addankivirinchi@gmail.com ✓
2. **2-Factor Authentication**: Must be enabled (required for app passwords)

## Step-by-Step Setup

### 1. Enable 2-Factor Authentication (if not already enabled)
1. Go to: https://myaccount.google.com/security
2. Under "Signing in to Google", click **2-Step Verification**
3. Follow the setup process if not already enabled
4. **Important**: You MUST have 2FA enabled to create app passwords

### 2. Generate App Password
1. **Direct Link**: https://myaccount.google.com/apppasswords
   - Or navigate: Google Account → Security → 2-Step Verification → App passwords

2. **Select App and Device**:
   - **App**: Select "Mail"
   - **Device**: Select "Other (Custom name)"
   - **Name**: Enter "VocalLocal Email Service"

3. **Generate Password**:
   - Click **"Generate"**
   - Google will display a 16-character password like: `abcd efgh ijkl mnop`
   - **COPY THIS IMMEDIATELY** - you won't see it again

### 3. Update Your .env File
Replace your current password with the app password:

```bash
# Current (will fail):
MAIL_PASSWORD=""

# Replace with (example format):
MAIL_PASSWORD="abcd efgh ijkl mnop"
```

**Important Notes**:
- Use the app password EXACTLY as shown by Google
- Include or exclude spaces as Google displays them
- Keep the quotes around the password
- Do NOT use your regular Gmail password

### 4. Verify Configuration
Your complete email configuration should be:

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=addankivirinchi@gmail.com
MAIL_PASSWORD="your_16_character_app_password"
MAIL_DEFAULT_SENDER=addankivirinchi@gmail.com
```

## Troubleshooting

### If 2FA is not enabled:
- You cannot create app passwords without 2FA
- Enable 2FA first, then create app password

### If you can't find App Passwords option:
- Ensure 2FA is fully enabled and verified
- Wait a few minutes after enabling 2FA
- Try the direct link: https://myaccount.google.com/apppasswords

### If app password still fails:
- Double-check you copied the password correctly
- Ensure no extra spaces or characters
- Try regenerating a new app password

## Security Notes
- App passwords are account-specific and secure
- Each application should have its own app password
- You can revoke app passwords anytime from your Google Account
- App passwords work even if you change your regular Gmail password

## Testing
After updating your .env file:
1. Restart your Flask application
2. Run the test script to verify
3. Try user registration to test email sending

The 535 authentication error will be completely resolved once you use the app password.
