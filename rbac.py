"""
Role-Based Access Control (RBAC) module for VocalLocal.

This module provides decorators and utilities for implementing role-based access control
throughout the VocalLocal application.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, jsonify, request
from flask_login import current_user, login_required
from models.firebase_models import User


class RolePermissions:
    """Define permissions for each role."""
    
    # Admin permissions (highest level)
    ADMIN_PERMISSIONS = {
        'access_admin_routes': True,
        'manage_users': True,
        'promote_users': True,
        'view_all_data': True,
        'access_premium_models': True,
        'unlimited_usage': True,
        'manage_subscription_plans': True,
        'view_system_analytics': True
    }
    
    # Super User permissions (employee level)
    SUPER_USER_PERMISSIONS = {
        'access_admin_routes': False,
        'manage_users': False,
        'promote_users': False,
        'view_all_data': False,
        'access_premium_models': True,
        'unlimited_usage': True,
        'manage_subscription_plans': False,
        'view_system_analytics': False
    }
    
    # Normal User permissions (subscription-based)
    NORMAL_USER_PERMISSIONS = {
        'access_admin_routes': False,
        'manage_users': False,
        'promote_users': False,
        'view_all_data': False,
        'access_premium_models': False,  # Based on subscription
        'unlimited_usage': False,  # Based on subscription
        'manage_subscription_plans': False,
        'view_system_analytics': False
    }
    
    @staticmethod
    def get_permissions(role):
        """Get permissions for a specific role."""
        if role == User.ROLE_ADMIN:
            return RolePermissions.ADMIN_PERMISSIONS
        elif role == User.ROLE_SUPER_USER:
            return RolePermissions.SUPER_USER_PERMISSIONS
        elif role == User.ROLE_NORMAL_USER:
            return RolePermissions.NORMAL_USER_PERMISSIONS
        else:
            return RolePermissions.NORMAL_USER_PERMISSIONS  # Default to normal user


def require_role(required_role):
    """
    Decorator to require a specific role for accessing a route.
    
    Args:
        required_role (str): The role required to access the route
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            user_role = getattr(current_user, 'role', User.ROLE_NORMAL_USER)
            
            if user_role != required_role:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin():
    """Decorator to require admin role."""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            user_role = getattr(current_user, 'role', User.ROLE_NORMAL_USER)
            
            if user_role != User.ROLE_ADMIN:
                flash('Admin access required.', 'danger')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin_or_special_auth():
    """
    Decorator to require either admin role OR the special admin authentication.
    This maintains backward compatibility with the existing 'Radu'/'Fasteasy' system.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check for special admin authentication (existing system)
            if session.get('special_admin_auth') == True:
                return f(*args, **kwargs)
            
            # Check for admin role (new RBAC system)
            if current_user.is_authenticated:
                user_role = getattr(current_user, 'role', User.ROLE_NORMAL_USER)
                if user_role == User.ROLE_ADMIN:
                    return f(*args, **kwargs)
            
            # Neither special auth nor admin role - redirect to admin login
            return redirect(url_for('admin.users'))
        return decorated_function
    return decorator


def require_premium_access():
    """Decorator to require premium access (admin or super user)."""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            user_role = getattr(current_user, 'role', User.ROLE_NORMAL_USER)
            
            if user_role not in [User.ROLE_ADMIN, User.ROLE_SUPER_USER]:
                flash('Premium access required.', 'danger')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_permission(permission_name):
    """
    Check if the current user has a specific permission.
    
    Args:
        permission_name (str): The name of the permission to check
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    if not current_user.is_authenticated:
        return False
    
    user_role = getattr(current_user, 'role', User.ROLE_NORMAL_USER)
    permissions = RolePermissions.get_permissions(user_role)
    
    return permissions.get(permission_name, False)


def check_model_access(model_name):
    """
    Check if the current user can access a specific AI model.
    
    Args:
        model_name (str): The name of the model to check access for
        
    Returns:
        bool: True if user can access the model, False otherwise
    """
    if not current_user.is_authenticated:
        return False
    
    user_role = getattr(current_user, 'role', User.ROLE_NORMAL_USER)
    
    # Admin and Super Users have access to all models
    if user_role in [User.ROLE_ADMIN, User.ROLE_SUPER_USER]:
        return True
    
    # Normal users are restricted to Flash 2.5 models unless they have a subscription
    # This will be integrated with the existing subscription system
    if model_name in ['gemini-2.5-flash-preview', 'gemini-2.5-flash']:
        return True
    
    # For other models, check subscription (this will be handled by existing subscription logic)
    return False


def api_require_role(required_role):
    """
    Decorator for API endpoints that require a specific role.
    Returns JSON error responses instead of redirects.
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_role = getattr(current_user, 'role', User.ROLE_NORMAL_USER)
            
            if user_role != required_role:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_require_admin():
    """API decorator to require admin role."""
    return api_require_role(User.ROLE_ADMIN)


def api_require_premium_access():
    """API decorator to require premium access (admin or super user)."""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_role = getattr(current_user, 'role', User.ROLE_NORMAL_USER)
            
            if user_role not in [User.ROLE_ADMIN, User.ROLE_SUPER_USER]:
                return jsonify({'error': 'Premium access required'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_user_role_info():
    """
    Get comprehensive role information for the current user.
    
    Returns:
        dict: User role information including permissions
    """
    if not current_user.is_authenticated:
        return {
            'role': None,
            'permissions': {},
            'has_premium_access': False,
            'has_admin_privileges': False
        }
    
    user_role = getattr(current_user, 'role', User.ROLE_NORMAL_USER)
    permissions = RolePermissions.get_permissions(user_role)
    
    return {
        'role': user_role,
        'permissions': permissions,
        'has_premium_access': user_role in [User.ROLE_ADMIN, User.ROLE_SUPER_USER],
        'has_admin_privileges': user_role == User.ROLE_ADMIN
    }
