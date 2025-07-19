from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin: # Relies on is_admin property in User model
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

def require_permission(permission):
    """
    Restricts a view to users with the given permission.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # In a real app, you would check permissions from the database,
            # for example, from the UserPermission model we added.
            # For now, we will use a simple check on the user's role for demonstration.
            if not current_user.is_authenticated:
                abort(403)
            # This is a placeholder. A real implementation would query UserPermission model.
            # For simplicity, we'll assume an 'admin' role has all permissions.
            if not current_user.role == 'admin':
                 # Or check: if not current_user.has_permission(permission):
                abort(403) # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator