from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from . import bp
from .. import db
from ..shared.permissions import PermissionManager, require_permission
from ..shared.decorators import admin_required
from ..cell_storage.models import User
from ..inventory.models import UserPermission


@bp.route('/permissions')
@login_required
@require_permission('admin.permission_management')
def permissions():
    """Permission management interface"""
    users = User.query.all()
    
    # Get user permissions
    user_permissions = {}
    for user in users:
        user_permissions[user.id] = PermissionManager.get_user_permissions(user.id)
    
    # Categorize permissions for template
    permissions = PermissionManager.PERMISSIONS
    
    inventory_permissions = [k for k in permissions.keys() if k.startswith('inventory.')]
    location_permissions = [k for k in permissions.keys() if k.startswith('location.')]
    supplier_permissions = [k for k in permissions.keys() if k.startswith('supplier.')]
    order_permissions = [k for k in permissions.keys() if k.startswith('order.')]
    admin_permissions = [k for k in permissions.keys() if k.startswith('admin.')]
    data_permissions = [k for k in permissions.keys() if k.startswith('data.')]
    
    return render_template('admin/permissions.html',
                         users=users,
                         user_permissions=user_permissions,
                         permission_descriptions=permissions,
                         inventory_permissions=inventory_permissions,
                         location_permissions=location_permissions,
                         supplier_permissions=supplier_permissions,
                         order_permissions=order_permissions,
                         admin_permissions=admin_permissions,
                         data_permissions=data_permissions)


@bp.route('/users/<int:user_id>/permissions')
@login_required
@require_permission('admin.permission_management')
def user_permissions_detail(user_id):
    """Detailed permission editing for a specific user"""
    user = User.query.get_or_404(user_id)
    
    # Get current permissions with details
    permissions = db.session.query(UserPermission).filter(
        UserPermission.user_id == user_id,
        UserPermission.is_active == True
    ).all()
    
    # Group permissions by category
    permission_categories = {}
    for perm in permissions:
        category = perm.permission.split('.')[0]
        if category not in permission_categories:
            permission_categories[category] = []
        permission_categories[category].append(perm)
    
    return render_template('admin/user_permissions_detail.html',
                         user=user,
                         permissions=permissions,
                         permission_categories=permission_categories,
                         all_permissions=PermissionManager.PERMISSIONS,
                         permission_groups=PermissionManager.PERMISSION_GROUPS,
                         current_time=datetime.now())


# API Endpoints

@bp.route('/api/users/<int:user_id>/permissions')
@login_required
@require_permission('admin.permission_management')
def api_get_user_permissions(user_id):
    """Get user permissions via API"""
    permissions = PermissionManager.get_user_permissions(user_id)
    
    # Get permission details
    permission_details = []
    for perm_obj in db.session.query(UserPermission).filter(
        UserPermission.user_id == user_id,
        UserPermission.is_active == True
    ).all():
        permission_details.append({
            'permission': perm_obj.permission,
            'granted_at': perm_obj.granted_at.isoformat() if perm_obj.granted_at else None,
            'expires_at': perm_obj.expires_at.isoformat() if perm_obj.expires_at else None,
            'granted_by': perm_obj.granted_by.username if perm_obj.granted_by else None,
            'resource_type': perm_obj.resource_type,
            'resource_id': perm_obj.resource_id
        })
    
    return jsonify({
        'permissions': permissions,
        'details': permission_details
    })


@bp.route('/api/users/<int:user_id>/permissions/<permission>', methods=['POST'])
@login_required
@require_permission('admin.permission_management')
def api_grant_permission(user_id, permission):
    """Grant a permission to a user"""
    data = request.get_json() or {}
    
    try:
        # Parse expiration date if provided
        expires_at = None
        if data.get('expires_at'):
            expires_at = datetime.fromisoformat(data['expires_at'])
        
        PermissionManager.grant_permission(
            user_id=user_id,
            permission=permission,
            granted_by_user_id=current_user.id,
            resource_type=data.get('resource_type'),
            resource_id=data.get('resource_id'),
            expires_at=expires_at
        )
        
        return jsonify({'success': True, 'message': 'Permission granted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/api/users/<int:user_id>/permissions/<permission>', methods=['DELETE'])
@login_required
@require_permission('admin.permission_management')
def api_revoke_permission(user_id, permission):
    """Revoke a permission from a user"""
    data = request.get_json() or {}
    
    try:
        PermissionManager.revoke_permission(
            user_id=user_id,
            permission=permission,
            resource_type=data.get('resource_type'),
            resource_id=data.get('resource_id')
        )
        
        return jsonify({'success': True, 'message': 'Permission revoked successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/api/users/<int:user_id>/permission-groups/<group_name>', methods=['POST'])
@login_required
@require_permission('admin.permission_management')
def api_assign_permission_group(user_id, group_name):
    """Assign a permission group to a user"""
    try:
        # First revoke all existing permissions
        existing_permissions = db.session.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.is_active == True
        ).all()
        
        for perm in existing_permissions:
            perm.is_active = False
        
        # Grant new permission group
        PermissionManager.grant_permission_group(
            user_id=user_id,
            group_name=group_name,
            granted_by_user_id=current_user.id
        )
        
        return jsonify({'success': True, 'message': f'{group_name} permissions assigned successfully'})
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/users', methods=['POST'])
@login_required
@require_permission('admin.user_management')
def api_create_user():
    """Create a new user"""
    data = request.get_json()
    
    try:
        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data.get('email')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Assign initial permission group
        if data.get('permission_group'):
            PermissionManager.grant_permission_group(
                user_id=user.id,
                group_name=data['permission_group'],
                granted_by_user_id=current_user.id
            )
        
        return jsonify({
            'success': True, 
            'message': 'User created successfully',
            'user_id': user.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@require_permission('admin.user_management')
def api_delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Cannot delete the current user
        if user.id == current_user.id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        # Deactivate all permissions
        permissions = db.session.query(UserPermission).filter_by(user_id=user_id).all()
        for perm in permissions:
            perm.is_active = False
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/permissions')
@login_required
@require_permission('admin.permission_management')
def api_list_permissions():
    """List all available permissions"""
    return jsonify({
        'permissions': PermissionManager.PERMISSIONS,
        'groups': PermissionManager.PERMISSION_GROUPS
    })


@bp.route('/api/permissions/audit')
@login_required
@require_permission('admin.audit_logs')
def api_permission_audit():
    """Get permission audit log"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    user_id = request.args.get('user_id', type=int)
    
    query = db.session.query(UserPermission)
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    permissions = query.order_by(UserPermission.granted_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    result = {
        'permissions': [{
            'id': perm.id,
            'user_id': perm.user_id,
            'username': perm.user.username if perm.user else 'Unknown',
            'permission': perm.permission,
            'granted_at': perm.granted_at.isoformat() if perm.granted_at else None,
            'granted_by': perm.granted_by.username if perm.granted_by else 'System',
            'expires_at': perm.expires_at.isoformat() if perm.expires_at else None,
            'is_active': perm.is_active,
            'resource_type': perm.resource_type,
            'resource_id': perm.resource_id
        } for perm in permissions.items],
        'pagination': {
            'page': permissions.page,
            'pages': permissions.pages,
            'per_page': permissions.per_page,
            'total': permissions.total,
            'has_next': permissions.has_next,
            'has_prev': permissions.has_prev
        }
    }
    
    return jsonify(result)


@bp.route('/audit/permissions')
@login_required
@require_permission('admin.audit_logs')
def permission_audit():
    """Permission audit page"""
    return render_template('admin/permission_audit.html')


# Dashboard for admin overview
@bp.route('/')
@login_required
@require_permission('admin.user_management')
def admin_dashboard():
    """Admin dashboard"""
    # Get statistics
    total_users = User.query.count()
    active_permissions = UserPermission.query.filter_by(is_active=True).count()
    recent_permissions = UserPermission.query.order_by(
        UserPermission.granted_at.desc()
    ).limit(10).all()
    
    # Permission distribution
    permission_stats = {}
    for group_name, permissions in PermissionManager.PERMISSION_GROUPS.items():
        count = 0
        for user in User.query.all():
            user_perms = PermissionManager.get_user_permissions(user.id)
            if all(perm in user_perms for perm in permissions):
                count += 1
        permission_stats[group_name] = count
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_permissions=active_permissions,
                         recent_permissions=recent_permissions,
                         permission_stats=permission_stats)