# Email Functionality Setup Guide

This guide explains how to configure and use the email functionality in VocalLocal.

## Features Implemented

✅ **Email Validation**
- Real-time email format validation using regex
- DNS/MX record validation to check if domain exists
- Frontend validation with visual feedback
- Backend validation during registration

✅ **Welcome Emails**
- Automatic welcome email after successful registration
- Mobile-friendly HTML templates
- Tier-specific content (free, basic, professional)
- Fallback plain text version

✅ **Email Service**
- SMTP configuration with Gmail support
- Retry logic with exponential backoff
- Comprehensive error handling and logging
- Email sending status tracking

## Environment Variables Setup

Add these variables to your `.env` file:

```bash
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=
MAIL_PASSWORD=your_gmail_app_password_here
MAIL_DEFAULT_SENDER=
```

## Gmail App Password Setup

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and generate password
   - Use this 16-character password as `MAIL_PASSWORD`

⚠️ **Important**: Never use your regular Gmail password. Always use an app password.

## Testing Email Functionality

### 1. Run Test Script
```bash
cd vocallocal
python test_email_functionality.py
```

### 2. Test API Endpoints
```bash
# Test email configuration
curl http://localhost:5001/api/test-email-config

# Test email validation
curl -X POST http://localhost:5001/api/validate-email \
  -H "Content-Type: application/json" \
  -d '{"email": "test@gmail.com"}'

# Test welcome email (replace with real email)
curl -X POST http://localhost:5001/api/send-welcome-email \
  -H "Content-Type: application/json" \
  -d '{"username": "TestUser", "email": "your-email@gmail.com", "user_tier": "free"}'
```

### 3. Test Registration Flow
1. Go to `/auth/register`
2. Enter email address and watch real-time validation
3. Complete registration
4. Check email for welcome message

## Email Validation Features

### Understanding Email Validation Levels

**Level 1: Format Validation**
- Checks email format using RFC 5322 compliant regex
- Validates structure (user@domain.com)
- Instant feedback, no network requests

**Level 2: Domain Validation (Default)**
- Checks if domain has MX records (mail servers)
- Verifies domain can receive emails
- Does NOT verify if specific email address exists
- Examples:
  - ✅ `user@gmail.com` - Valid (gmail.com has mail servers)
  - ✅ `nonexistent@gmail.com` - Valid (domain can receive email)
  - ❌ `user@fakedomain123.com` - Invalid (domain doesn't exist)

**Level 3: SMTP Verification (Optional)**
- Actually connects to mail server
- Attempts to verify specific email address
- Slower and potentially intrusive
- May be blocked by some mail servers

### Frontend Validation
- **Real-time feedback** as user types
- **Visual indicators** (green checkmark, red X)
- **Loading states** during validation
- **Clear error messages** with helpful suggestions
- **Informational warnings** about validation limitations

### Backend Validation
- **Format validation** using RFC 5322 compliant regex
- **DNS/MX record validation** verifies domain can receive emails
- **Optional SMTP verification** for thorough checking
- **Graceful fallback** if validation service fails
- **Detailed error messages** with context

## Welcome Email Content

The welcome email includes:
- **Personalized greeting** with username
- **Tier-specific features** and limits
- **Getting started guide** with steps
- **Support contact information**
- **Mobile-friendly design** with responsive layout
- **Dark mode support** for email clients

## Error Handling

### Email Validation Errors
- Invalid format → "Please enter a valid email format (e.g., user@domain.com)"
- Domain doesn't exist → "Domain 'example.com' does not exist or cannot receive emails"
- Service unavailable → "Unable to validate email. Please try again."
- SMTP verification failed → "Email verification failed: [specific reason]"

### Important Notes About Email Validation

**Why "virinchi@gmail.com" Shows as Valid:**
- The validation correctly identifies that gmail.com can receive emails
- It does NOT verify if the user "virinchi" actually exists
- This is standard behavior for email validation systems
- To verify actual email existence, you would need:
  - Email verification links (recommended)
  - SMTP verification (optional, may be blocked)
  - Third-party email verification services

**Best Practices:**
- Use domain validation for registration (current implementation)
- Send verification emails to confirm ownership
- Consider SMTP verification only for critical flows
- Provide clear messaging about validation limitations

### Email Sending Errors
- Authentication failed → Check MAIL_PASSWORD
- Recipient refused → Email address may be invalid
- SMTP errors → Retry with exponential backoff
- Service unavailable → Graceful degradation

## Integration Points

### Registration Flow
1. User enters email → Real-time validation
2. Form submission → Backend validation
3. User creation → Welcome email sent
4. Success message → Includes email status

### OAuth Registration
- OAuth users bypass email validation (already verified)
- Welcome emails still sent for OAuth registrations
- Email validation only for manual registration

## Monitoring and Logging

### Email Service Logs
```python
logger.info(f'Welcome email sent successfully to {email}')
logger.warning(f'Welcome email failed for {email}: {error}')
logger.error(f'Email validation failed: {error}')
```

### Metrics to Monitor
- Email validation success rate
- Welcome email delivery rate
- DNS validation performance
- SMTP connection failures

## Troubleshooting

### Common Issues

**Email validation not working**
- Check internet connection for DNS queries
- Verify dnspython package is installed
- Check browser console for JavaScript errors

**Welcome emails not sending**
- Verify MAIL_PASSWORD is set correctly
- Check Gmail app password is valid
- Ensure 2FA is enabled on Gmail account
- Check SMTP server connectivity

**Frontend validation not appearing**
- Verify email-validation.js is loaded
- Check browser console for errors
- Ensure CSS styles are applied

### Debug Commands
```bash
# Test DNS resolution
nslookup gmail.com

# Test SMTP connection
telnet smtp.gmail.com 587

# Check environment variables
echo $MAIL_PASSWORD

# Test email service import
python -c "from services.email_service import email_service; print('OK')"
```

## Security Considerations

- **App passwords** instead of regular passwords
- **Environment variables** for sensitive data
- **Input validation** to prevent email injection
- **Rate limiting** on validation endpoints
- **Logging without sensitive data** (no passwords/emails in logs)

## Future Enhancements

- Email verification links for account activation
- Password reset emails
- Email templates for different languages
- Email analytics and tracking
- Bulk email capabilities for announcements
