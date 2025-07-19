"""
Fine-grained permissions system for inventory management.
Provides decorators and functions for controlling access to resources.
"""

from functools import wraps
from flask import abort, request, current_app
from flask_login import current_user
from ..inventory.models import UserPermission
from ..cell_storage.models import User


class PermissionManager:
    """Central permission management class"""
    
    # Define available permissions
    PERMISSIONS = {
        # Inventory permissions
        'inventory.view': 'View inventory items',
        'inventory.create': 'Create new inventory items',
        'inventory.edit': 'Edit inventory items',
        'inventory.delete': 'Delete inventory items',
        'inventory.use': 'Record usage of inventory items',
        'inventory.adjust_quantity': 'Adjust item quantities',
        'inventory.manage_types': 'Manage inventory types',
        
        # Location permissions
        'location.view': 'View locations',
        'location.create': 'Create new locations',
        'location.edit': 'Edit locations',
        'location.delete': 'Delete locations',
        'location.manage_capacity': 'Manage location capacity',
        
        # Supplier permissions
        'supplier.view': 'View suppliers',
        'supplier.create': 'Create new suppliers',
        'supplier.edit': 'Edit suppliers',
        'supplier.delete': 'Delete suppliers',
        'supplier.manage_contacts': 'Manage supplier contacts',
        
        # Order permissions
        'order.view': 'View orders',
        'order.create': 'Create purchase orders',
        'order.edit': 'Edit orders',
        'order.approve': 'Approve orders',
        'order.receive': 'Receive orders',
        'order.cancel': 'Cancel orders',
        
        # Admin permissions
        'admin.user_management': 'Manage users',
        'admin.permission_management': 'Manage permissions',
        'admin.system_config': 'System configuration',
        'admin.audit_logs': 'View audit logs',
        'admin.reports': 'Generate reports',
        'admin.bulk_operations': 'Bulk operations',
        
        # Data permissions
        'data.export': 'Export data',
        'data.import': 'Import data',
        'data.backup': 'Create backups',
        'data.restore': 'Restore from backups'
    }
    
    # Permission groups for easier assignment
    PERMISSION_GROUPS = {
        'viewer': [
            'inventory.view', 'location.view', 'supplier.view', 'order.view'
        ],
        'user': [
            'inventory.view', 'inventory.create', 'inventory.edit', 'inventory.use',
            'location.view', 'supplier.view', 'order.view', 'order.create',
            'data.export'
        ],
        'manager': [
            'inventory.view', 'inventory.create', 'inventory.edit', 'inventory.use',
            'inventory.adjust_quantity', 'location.view', 'location.create', 
            'location.edit', 'supplier.view', 'supplier.create', 'supplier.edit',
            'order.view', 'order.create', 'order.edit', 'order.approve',
            'data.export', 'data.import'
        ],
        'admin': list(PERMISSIONS.keys())  # All permissions
    }
    
    @classmethod
    def get_user_permissions(cls, user_id):
        """Get all permissions for a user"""
        from .. import db
        
        permissions = db.session.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.is_active == True
        ).all()
        
        # Check for expired permissions
        from datetime import datetime
        active_permissions = []
        for perm in permissions:
            if perm.expires_at is None or perm.expires_at > datetime.utcnow():
                active_permissions.append(perm.permission)
        
        return active_permissions
    
    @classmethod
    def has_permission(cls, user_id, permission, resource_type=None, resource_id=None):
        """Check if user has a specific permission"""
        from .. import db
        from datetime import datetime
        
        # Admin users have all permissions
        user = User.query.get(user_id)
        if user and hasattr(user, 'is_admin') and user.is_admin:
            return True
        
        # Check specific permission
        query = db.session.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.permission == permission,
            UserPermission.is_active == True
        )
        
        # Add resource-specific filters if provided
        if resource_type:
            query = query.filter(UserPermission.resource_type == resource_type)
        if resource_id:
            query = query.filter(UserPermission.resource_id == resource_id)
        
        perm = query.first()
        
        if not perm:
            return False
        
        # Check expiration
        if perm.expires_at and perm.expires_at <= datetime.utcnow():
            return False
        
        return True
    
    @classmethod
    def grant_permission(cls, user_id, permission, granted_by_user_id, 
                        resource_type=None, resource_id=None, expires_at=None):
        """Grant a permission to a user"""
        from .. import db
        from datetime import datetime
        
        # Check if permission already exists
        existing = db.session.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.permission == permission,
            UserPermission.resource_type == resource_type,
            UserPermission.resource_id == resource_id
        ).first()
        
        if existing:
            # Update existing permission
            existing.is_active = True
            existing.granted_by_user_id = granted_by_user_id
            existing.granted_at = datetime.utcnow()
            existing.expires_at = expires_at
        else:
            # Create new permission
            perm = UserPermission(
                user_id=user_id,
                permission=permission,
                resource_type=resource_type,
                resource_id=resource_id,
                granted_by_user_id=granted_by_user_id,
                expires_at=expires_at
            )
            db.session.add(perm)
        
        db.session.commit()
    
    @classmethod
    def revoke_permission(cls, user_id, permission, resource_type=None, resource_id=None):
        """Revoke a permission from a user"""
        from .. import db
        
        query = db.session.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.permission == permission
        )
        
        if resource_type:
            query = query.filter(UserPermission.resource_type == resource_type)
        if resource_id:
            query = query.filter(UserPermission.resource_id == resource_id)
        
        perm = query.first()
        if perm:
            perm.is_active = False
            db.session.commit()
    
    @classmethod
    def grant_permission_group(cls, user_id, group_name, granted_by_user_id):
        """Grant all permissions in a group to a user"""
        if group_name not in cls.PERMISSION_GROUPS:
            raise ValueError(f"Unknown permission group: {group_name}")
        
        for permission in cls.PERMISSION_GROUPS[group_name]:
            cls.grant_permission(user_id, permission, granted_by_user_id)


def require_permission(permission, resource_type=None, resource_id_param=None):
    """
    Decorator to require a specific permission for a view function.
    
    Args:
        permission: The required permission string
        resource_type: Optional resource type for resource-specific permissions
        resource_id_param: Parameter name that contains the resource ID
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Get resource ID from request if specified
            resource_id = None
            if resource_id_param:
                resource_id = kwargs.get(resource_id_param) or request.args.get(resource_id_param)
            
            # Check permission
            if not PermissionManager.has_permission(
                current_user.id, 
                permission, 
                resource_type, 
                resource_id
            ):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def has_permission(permission, resource_type=None, resource_id=None):
    """
    Template function to check permissions in Jinja2 templates.
    """
    if not current_user.is_authenticated:
        return False
    
    return PermissionManager.has_permission(
        current_user.id, 
        permission, 
        resource_type, 
        resource_id
    )


def get_user_permissions(user_id=None):
    """
    Get permissions for current user or specified user.
    """
    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id
    
    if not user_id:
        return []
    
    return PermissionManager.get_user_permissions(user_id)


# Permission checking functions for common operations
def can_view_inventory():
    return has_permission('inventory.view')

def can_edit_inventory():
    return has_permission('inventory.edit')

def can_manage_locations():
    return has_permission('location.edit')

def can_manage_suppliers():
    return has_permission('supplier.edit')

def can_approve_orders():
    return has_permission('order.approve')

def is_admin():
    return has_permission('admin.user_management')