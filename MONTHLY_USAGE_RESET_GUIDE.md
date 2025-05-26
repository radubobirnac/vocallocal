# Monthly Usage Reset System for VocalLocal

This document describes the monthly usage reset system implemented for the VocalLocal application, designed to work within Firebase's free Spark plan limitations.

## Overview

The monthly usage reset system automatically resets all users' monthly usage counters (transcription minutes, translation words, TTS minutes, AI credits) and archives the previous month's usage data. This system is designed to work without Firebase's paid cron job features.

## System Components

### 1. Firebase Cloud Functions

#### `resetMonthlyUsage`
- **Type**: Callable function (admin only)
- **Purpose**: Resets all users' monthly usage and archives data
- **Features**:
  - Resets currentPeriod usage counters to zero
  - Archives previous month's data to `usage/history/{YYYY-MM}/`
  - Updates resetDate for each user to next month's first day
  - Uses UTC timezone for consistency
  - Provides detailed reporting of processed users

#### `resetMonthlyUsageHTTP`
- **Type**: HTTP trigger
- **Purpose**: Allows external cron services to trigger reset
- **Security**: Requires secret token authentication
- **Usage**: Compatible with free external cron services

#### `getUsageStatistics`
- **Type**: Callable function (admin only)
- **Purpose**: Returns current usage statistics across all users
- **Data**: User counts, usage totals, plan distribution, reset status

#### `checkAndResetUsage`
- **Type**: Callable function
- **Purpose**: Checks if users need reset and optionally triggers it
- **Features**: Can handle individual user resets or admin-triggered full resets

### 2. Admin Interface

#### Usage Reset Management Page
- **URL**: `/admin/usage-reset`
- **Access**: Requires special admin credentials (username: 'Radu', password: 'Fasteasy')
- **Features**:
  - Real-time usage statistics display
  - Manual reset trigger with force option
  - Reset status checking
  - User-friendly dashboard with visual feedback

#### Admin API Endpoints
- `GET /admin/api/usage-statistics` - Get current usage statistics
- `POST /admin/api/reset-monthly-usage` - Trigger manual reset
- `GET /admin/api/check-reset-status` - Check if users need reset

### 3. Client-Side Auto-Reset

#### Automatic Reset Check
- **Trigger**: User login and usage tracking operations
- **Logic**: Checks if current time > user's resetDate
- **Fallback**: Local reset if Cloud Function fails
- **Archiving**: Preserves usage data before reset

## Implementation Details

### Database Structure

```
/users/{userId}/
  usage/
    currentPeriod/
      transcriptionMinutes: number
      translationWords: number
      ttsMinutes: number
      aiCredits: number
      resetDate: number (timestamp)

    totalUsage/
      transcriptionMinutes: number
      translationWords: number
      ttsMinutes: number
      aiCredits: number

    lastResetAt: number (timestamp)

/usage/history/{YYYY-MM}/{userId}/
  transcriptionMinutes: number
  translationWords: number
  ttsMinutes: number
  aiCredits: number
  resetDate: number
  archivedAt: number
  planType: string
```

### Reset Logic

1. **Check Reset Date**: Compare current time with user's resetDate
2. **Archive Data**: Save current usage to history collection
3. **Reset Counters**: Set all currentPeriod usage to zero
4. **Update Reset Date**: Calculate and set next month's reset date
5. **Log Activity**: Record reset action for audit trail

### Timezone Handling

- **Standard**: UTC timezone for all calculations
- **Reset Date**: First day of next month at 00:00:00 UTC
- **Consistency**: Ensures global users reset at same time

## Usage Scenarios

### 1. Manual Admin Reset

```javascript
// Admin triggers reset via web interface
POST /admin/api/reset-monthly-usage
{
  "forceReset": false  // Optional: ignore reset dates
}
```

### 2. External Cron Service

```bash
# Monthly cron job (1st day of month at 00:00 UTC)
curl -X POST https://your-firebase-project.cloudfunctions.net/resetMonthlyUsageHTTP \
  -H "x-reset-token: vocallocal-reset-2024" \
  -H "Content-Type: application/json" \
  -d '{"forceReset": false}'
```

### 3. Automatic Client-Side Reset

```python
# Triggered during user operations
from services.user_account_service import UserAccountService

# This automatically checks and resets if needed
UserAccountService.track_usage(user_id, "transcriptionMinutes", 5.0)
```

## Free Plan Compatibility

### Firebase Spark Plan Limitations
- ❌ No Firebase Functions Scheduler (requires Blaze plan)
- ❌ No Cloud Tasks (requires Blaze plan)
- ✅ HTTP triggers (available on free plan)
- ✅ Callable functions (available on free plan)
- ✅ Realtime Database (available on free plan)

### Alternative Scheduling Solutions

1. **External Free Cron Services**:
   - cron-job.org (free tier)
   - EasyCron (free tier)
   - GitHub Actions (free for public repos)

2. **Client-Side Triggers**:
   - User login checks
   - Usage tracking operations
   - Admin manual triggers

3. **Webhook Services**:
   - Zapier (free tier)
   - IFTTT (free tier)
   - Microsoft Power Automate (free tier)

## Security Considerations

### Admin Authentication
- Special admin credentials required for manual triggers
- Session-based authentication for admin interface
- Activity logging for audit trail

### HTTP Trigger Security
- Secret token authentication
- Request method validation (POST only)
- Rate limiting through Firebase quotas

### Data Protection
- Usage data archived before reset
- Atomic operations to prevent data loss
- Error handling and rollback capabilities

## Monitoring and Maintenance

### Admin Dashboard Features
- Real-time usage statistics
- User count and plan distribution
- Reset status monitoring
- Error reporting and logging

### Logging and Debugging
- Cloud Function logs in Firebase Console
- Admin activity tracking in database
- Error details for troubleshooting

### Performance Considerations
- Batch operations for multiple users
- Efficient database queries
- Minimal function execution time

## Setup Instructions

### 1. Deploy Firebase Functions
```bash
cd firebase-functions
firebase deploy --only functions
```

### 2. Configure External Cron (Optional)
```bash
# Example cron job for 1st day of month at 00:00 UTC
0 0 1 * * curl -X POST https://your-project.cloudfunctions.net/resetMonthlyUsageHTTP \
  -H "x-reset-token: vocallocal-reset-2024" \
  -d '{"forceReset": false}'
```

### 3. Set Firebase Configuration (Optional)
```bash
# Set custom reset token
firebase functions:config:set reset.token="your-custom-token"
```

### 4. Test the System
1. Access admin interface: `/admin/usage-reset`
2. Check usage statistics
3. Test manual reset with force option
4. Verify data archiving

## Troubleshooting

### Common Issues

1. **Reset Not Triggering**
   - Check user resetDate values
   - Verify admin authentication
   - Review Cloud Function logs

2. **Data Not Archiving**
   - Check Firebase database permissions
   - Verify archive path structure
   - Review error logs

3. **External Cron Failing**
   - Verify HTTP trigger URL
   - Check authentication token
   - Review cron service logs

### Error Recovery

1. **Partial Reset Failure**
   - Use force reset option
   - Check individual user data
   - Manual data correction if needed

2. **Archive Data Loss**
   - Check usage/history collection
   - Restore from backup if available
   - Implement additional monitoring

## Future Enhancements

### Potential Improvements
- Email notifications for reset completion
- Usage trend analysis and reporting
- Automated backup before reset
- Custom reset schedules per user
- Integration with billing systems

### Scalability Considerations
- Batch processing for large user bases
- Distributed reset operations
- Performance monitoring and optimization
- Database indexing improvements

## Support and Maintenance

For issues or questions regarding the monthly usage reset system:

1. Check Firebase Console logs
2. Review admin dashboard for errors
3. Verify database structure and permissions
4. Test with manual reset first
5. Contact system administrator if needed

---

**Note**: This system is designed to work within Firebase's free plan limitations while providing robust monthly usage reset functionality. Regular monitoring and maintenance are recommended to ensure optimal performance.
