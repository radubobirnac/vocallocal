# VocalLocal RBAC System Guide

## Overview

The VocalLocal application implements a comprehensive Role-Based Access Control (RBAC) system that manages user permissions and AI model access based on user roles. This system ensures that users only have access to features and models appropriate for their subscription level and role.

## User Roles

### 1. Admin (`admin`)
- **Full system access**: Can access all admin routes and manage users
- **User management**: Can promote/demote users between roles
- **Unlimited model access**: Access to all AI models without restrictions
- **System analytics**: Can view system-wide analytics and usage data
- **Subscription management**: Can manage subscription plans and settings

### 2. Super User (`super_user`)
- **Premium model access**: Unlimited access to all AI models
- **No admin privileges**: Cannot access admin routes or manage users
- **Unlimited usage**: No subscription-based usage limits
- **Employee-level access**: Designed for company employees or VIP users

### 3. Normal User (`normal_user`)
- **Subscription-based access**: Access based on their subscription plan
- **Limited model access**: Only free models unless they have premium subscription
- **Usage limits**: Subject to subscription plan usage limits
- **Standard user experience**: Default role for regular customers

## Model Access Control

### Free Models (Available to all users)
- `gemini-2.0-flash-lite`
- `gemini` (legacy alias)

### Premium Models (Requires Super User role or premium subscription)
- **Transcription Models:**
  - `gpt-4o-mini-transcribe`
  - `gpt-4o-transcribe`
  - `whisper-1`

- **Translation Models:**
  - `gpt-4.1-mini`
  - `gpt-4o`
  - `gpt-4o-mini`

- **TTS Models:**
  - `gpt4o-mini`
  - `openai` (legacy alias)

- **Gemini Premium Models:**
  - `gemini-2.5-flash-preview-04-17`
  - `gemini-2.5-flash`
  - `gemini-2.5-pro-preview-03-25`
  - `gemini-2.5-pro`
  - `gemini-2.5-flash-tts`

## Implementation

### Core Components

1. **User Model (`firebase_models.py`)**
   - Role constants and validation
   - Role-based permission methods
   - User role management functions

2. **ModelAccessService (`services/model_access_service.py`)**
   - Model categorization (free vs premium)
   - Access validation logic
   - Model suggestion for denied requests

3. **RBAC Module (`rbac.py`)**
   - Route decorators for role-based access
   - Permission checking utilities
   - API-specific access control

### Route Integration

The RBAC system is integrated into all major service routes:

- **Transcription Route** (`routes/transcription.py`): Lines 66-104
- **Translation Route** (`routes/translation.py`): Lines 85-111
- **TTS Route** (`routes/tts.py`): Lines 58-80

### Access Control Flow

1. **User makes request** with specific model
2. **Route validates model access** using `ModelAccessService.validate_model_request()`
3. **If access denied:**
   - Check for suggested alternative model
   - Use suggested model or return 403 error
4. **If access granted:**
   - Proceed with requested model
5. **Log access decision** for debugging

## Usage Examples

### Checking User Role
```python
from firebase_models import User

# Get user role
role = User.get_user_role("user@example.com")

# Check specific roles
is_admin = User.is_admin("user@example.com")
is_super_user = User.is_super_user("user@example.com")
has_premium_access = User.has_premium_access("user@example.com")
```

### Validating Model Access
```python
from services.model_access_service import ModelAccessService

# Check if user can access a model
access_result = ModelAccessService.can_access_model(
    "gpt-4o-mini-transcribe", 
    "user@example.com"
)

if access_result['allowed']:
    # User can access the model
    proceed_with_model(model_name)
else:
    # Access denied
    print(f"Access denied: {access_result['reason']}")
```

### Route Protection
```python
from rbac import require_admin, require_premium_access

@bp.route('/admin/users')
@require_admin()
def admin_users():
    # Only admins can access this route
    pass

@bp.route('/premium/feature')
@require_premium_access()
def premium_feature():
    # Only admins and super users can access this route
    pass
```

## Testing

### RBAC System Test
Run the comprehensive RBAC test:
```bash
python test_rbac_system.py
```

### Integration Test
Test model access across all services:
```bash
python test_rbac_integration.py
```

## Benefits

1. **Security**: Ensures users only access authorized features
2. **Scalability**: Easy to add new roles and permissions
3. **Flexibility**: Model access can be adjusted per role
4. **Graceful Degradation**: Automatic fallback to accessible models
5. **Audit Trail**: All access decisions are logged

## Future Enhancements

1. **Subscription Integration**: Enhance normal user access based on subscription plans
2. **Dynamic Permissions**: Runtime permission updates
3. **API Rate Limiting**: Role-based rate limiting
4. **Advanced Analytics**: Role-based usage analytics
5. **Custom Roles**: User-defined roles with custom permissions

## Troubleshooting

### Common Issues

1. **User not found**: Ensure user exists in Firebase
2. **Role not set**: New users default to `normal_user` role
3. **Model access denied**: Check user role and model categorization
4. **Import errors**: Ensure all RBAC modules are properly imported

### Debug Commands

```python
# Check user role
User.get_user_role("user@example.com")

# Test model access
ModelAccessService.can_access_model("model-name", "user@example.com")

# Get user permissions
from rbac import get_user_role_info
get_user_role_info()  # For current user
```
