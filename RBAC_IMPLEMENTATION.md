# Role-Based Access Control (RBAC) Implementation

## Overview

This document describes the comprehensive Role-Based Access Control (RBAC) system implemented for the VocalLocal application. The system provides three distinct user roles with specific permissions and access levels.

## Role Hierarchy

### 1. Admin Role (Highest Privilege)
- **Full system access** including administrative features
- **Can access admin routes** like `/admin/users`, `/usage-tracks`, etc.
- **Can promote users** to Super User status
- **Can access all AI models** (Flash 2.0, premium models, etc.)
- **Can view all user data** and system analytics
- **Unlimited usage** of all features
- **Can manage subscription plans** and system settings

### 2. Super User Role (Employee Access)
- **Full access to all AI models** and transcription/translation functionality
- **Can use basic mode, bilingual mode**, and all premium features
- **Unlimited usage** of core application features
- **CANNOT access administrative routes** (`/admin/users`, `/usage-tracks`, etc.)
- **CANNOT promote other users** or manage user roles
- **No subscription limits** but restricted from admin panel

### 3. Normal User Role (Standard Users)
- **Current user permissions** based on subscription plan (Free/Basic/Professional)
- **Plan-based restrictions** on models and usage limits
- **Limited to Flash 2.0 models** unless they have a premium subscription
- **No administrative access**
- **Subject to usage tracking** and monthly limits

## Implementation Components

### 1. Database Schema Updates

#### User Model (`models/firebase_models.py`)
- Added `role` field to user database schema
- Added role constants: `ROLE_ADMIN`, `ROLE_SUPER_USER`, `ROLE_NORMAL_USER`
- Added role management methods:
  - `update_user_role(email, new_role)`
  - `get_user_role(email)`
  - `is_admin(email)`, `is_super_user(email)`, `is_normal_user(email)`
  - `has_admin_privileges(email)`, `has_premium_access(email)`

#### Firebase Security Rules
- Added role validation in user profile section
- Added `userRoles` collection for role management
- Updated admin access rules to include role-based permissions

### 2. RBAC Module (`rbac.py`)

#### Permission System
- `RolePermissions` class defining permissions for each role
- Permission checking functions:
  - `check_permission(permission_name)`
  - `check_model_access(model_name)`
  - `get_user_role_info()`

#### Decorators
- `@require_role(required_role)` - Require specific role
- `@require_admin()` - Require admin role
- `@require_admin_or_special_auth()` - Backward compatibility with existing system
- `@require_premium_access()` - Require admin or super user
- API versions: `@api_require_admin()`, `@api_require_premium_access()`

### 3. Model Access Service (`services/model_access_service.py`)

#### Model Categories
- **Free Models**: `gemini-2.0-flash-lite`
- **Premium Models**: `gpt-4o-mini-transcribe`, `gpt-4o-transcribe`, `gemini-2.5-flash-preview-04-17`, `gpt-4.1-mini`, `gemini-2.5-flash`, `gemini-2.5-flash-tts`, `gpt4o-mini`, `openai`

#### Access Control Functions
- `can_access_model(model_name, user_email)` - Check model access
- `get_available_models(user_email)` - Get accessible models
- `validate_model_request(model_name, user_email)` - Validate model requests
- `get_model_restrictions_info(user_email)` - Get comprehensive restrictions

### 4. Admin Interface Updates

#### Admin Users Page (`templates/admin_users.html`)
- Added role column to user table
- Added "Change Role" button for each user
- Role management modal with dropdown selection
- Real-time role updates via AJAX
- Visual role indicators with color-coded badges

#### Admin Routes (`routes/admin.py`)
- Added role management API endpoints:
  - `PUT /admin/api/users/<user_email>/role` - Update user role
  - `GET /admin/api/users/<user_email>/role` - Get user role
- Backward compatibility with existing admin authentication
- Role change logging and activity tracking

## Usage Examples

### 1. Checking User Permissions

```python
from rbac import check_permission, check_model_access

# Check if user can access admin features
if check_permission('access_admin_routes'):
    # Show admin menu
    pass

# Check if user can access a specific model
if check_model_access('gpt-4o'):
    # Allow model selection
    pass
```

### 2. Using Decorators

```python
from rbac import require_admin, require_premium_access

@require_admin()
def admin_only_route():
    # Only admins can access this
    pass

@require_premium_access()
def premium_feature():
    # Admins and Super Users can access this
    pass
```

### 3. Model Access Validation

```python
from services.model_access_service import ModelAccessService

# Check if user can access a model
access_info = ModelAccessService.can_access_model('gpt-4o', user_email)
if access_info['allowed']:
    # Proceed with model request
    pass
else:
    # Show upgrade prompt or suggest alternative
    suggested_model = access_info.get('suggested_model')
```

### 4. Role Management

```python
from models.firebase_models import User

# Promote user to Super User
User.update_user_role('user@example.com', User.ROLE_SUPER_USER)

# Check user role
role = User.get_user_role('user@example.com')
if role == User.ROLE_ADMIN:
    # User is admin
    pass
```

## Migration and Backward Compatibility

### Existing Users
- All existing users default to `normal_user` role
- Existing `is_admin` flag is preserved for backward compatibility
- Users with `is_admin=True` are automatically assigned `admin` role

### Existing Admin System
- The hardcoded 'Radu'/'Fasteasy' admin authentication is preserved
- New role-based admin access works alongside existing system
- `@require_admin_or_special_auth()` decorator provides seamless transition

### API Compatibility
- All existing API endpoints continue to work
- New role-based restrictions are additive, not breaking
- Subscription-based access for normal users remains unchanged

## Security Considerations

### Role Assignment
- Only admins can promote users to Super User or Admin roles
- Users cannot promote themselves
- Role changes are logged in user activities

### Model Access
- Model access is validated at both frontend and backend
- API-level enforcement prevents unauthorized model usage
- Graceful degradation with suggested alternatives

### Firebase Security
- Database rules enforce role-based access at the data level
- Admin-only collections are protected
- User data isolation is maintained

## Future Enhancements

### Planned Features
- **Coupon Users**: Special role for promotional access
- **Organization Roles**: Team-based permissions
- **Time-limited Roles**: Temporary access grants
- **Custom Permissions**: Fine-grained permission sets

### Integration Points
- **Stripe Payment Integration**: Role-based subscription management
- **Usage Analytics**: Role-based reporting and insights
- **Audit Logging**: Comprehensive role change tracking

## Testing

### Role Assignment Testing
1. Create test users with different roles
2. Verify role-specific access restrictions
3. Test role promotion/demotion workflows
4. Validate backward compatibility

### Model Access Testing
1. Test model access for each role
2. Verify subscription integration for normal users
3. Test API-level model restrictions
4. Validate error handling and fallbacks

### Admin Interface Testing
1. Test role management modal functionality
2. Verify real-time role updates
3. Test permission-based UI elements
4. Validate admin authentication flows

## Deployment Notes

### Database Migration
- No database migration required
- New fields are added with default values
- Existing data remains intact

### Configuration
- No additional configuration required
- RBAC system is enabled by default
- Backward compatibility is automatic

### Monitoring
- Monitor role change activities
- Track model access patterns
- Watch for permission-related errors
- Validate subscription integration
