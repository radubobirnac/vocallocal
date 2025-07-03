# Gmail App Password Setup Guide

## Why You Need an App Password

Gmail requires **App Passwords** for SMTP authentication, not your regular account password. This is a security feature that provides dedicated passwords for applications.

## Step-by-Step Setup

### 1. Enable 2-Factor Authentication (Required)

1. Go to your Google Account: https://myaccount.google.com/
2. Click **Security** in the left sidebar
3. Under "Signing in to Google", click **2-Step Verification**
4. Follow the prompts to enable 2FA if not already enabled

### 2. Generate App Password

1. **Go to App Passwords**: https://myaccount.google.com/apppasswords
   - Or navigate: Google Account → Security → 2-Step Verification → App passwords

2. **Select App and Device**:
   - App: Select "Mail"
   - Device: Select "Other (Custom name)"
   - Enter: "VocalLocal Email Service"

3. **Generate Password**:
   - Click "Generate"
   - Google will show a 16-character password (like: `abcd efgh ijkl mnop`)
   - **Copy this password immediately** (you won't see it again)

### 3. Update Your .env File

Replace the placeholder in your `.env` file:

```bash
# Before (current - will fail)
MAIL_PASSWORD=Virinchi#19@March

# After (use your generated app password)
MAIL_PASSWORD=abcd efgh ijkl mnop
```

**Important**: 
- Use the app password exactly as shown (with or without spaces)
- Do NOT use your regular Gmail password
- Keep this password secure

### 4. Test the Configuration

After updating your `.env` file:

1. **Restart your Flask application**
2. **Test email sending**:
   ```bash
   cd vocallocal
   python test_email_functionality.py
   ```
3. **Try user registration** to test verification emails

## Troubleshooting

### Common Issues:

**"Username and Password not accepted" (535)**:
- ✅ **Fixed**: Use app password instead of regular password
- Ensure 2FA is enabled on your Gmail account
- Double-check the app password was copied correctly

**"Less secure app access"**:
- ✅ **Not needed**: App passwords work with secure apps
- This setting is deprecated and not required

**"Connection refused"**:
- Check firewall settings
- Verify SMTP settings (should be smtp.gmail.com:587)

### Alternative: OAuth2 (Advanced)

If you prefer OAuth2 instead of app passwords:
1. Set up Google Cloud Console project
2. Enable Gmail API
3. Configure OAuth2 credentials
4. Update email service to use OAuth2 flow

## Security Notes

- **App passwords are account-specific**: Each app should have its own
- **Revoke unused passwords**: Remove old app passwords you don't need
- **Monitor access**: Check your Google Account activity regularly
- **Don't share**: Keep app passwords private like regular passwords

## Quick Reference

**Gmail SMTP Settings**:
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_16_character_app_password
```

**App Password Format**: 16 characters, usually shown with spaces (e.g., `abcd efgh ijkl mnop`)

**Links**:
- Google Account Security: https://myaccount.google.com/security
- App Passwords: https://myaccount.google.com/apppasswords
- 2-Step Verification: https://myaccount.google.com/signinoptions/two-step-verification
