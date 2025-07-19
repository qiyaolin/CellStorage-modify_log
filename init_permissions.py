#!/usr/bin/env python3
"""
Initialize default permissions for users in the system.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.shared.permissions import PermissionManager
from app.cell_storage.models import User

def init_permissions():
    """Initialize default permissions for existing users"""
    app = create_app()
    
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("No users found in the system.")
            return
        
        print(f"Found {len(users)} users. Initializing permissions...")
        
        for user in users:
            print(f"\nProcessing user: {user.username}")
            
            # Get current permissions
            current_perms = PermissionManager.get_user_permissions(user.id)
            
            if not current_perms:
                # Check if user is admin (you may need to adjust this check)
                if hasattr(user, 'is_admin') and user.is_admin:
                    print(f"  - Granting admin permissions to {user.username}")
                    PermissionManager.grant_permission_group(user.id, 'admin', user.id)
                elif user.username == 'admin':  # Default admin username
                    print(f"  - Granting admin permissions to {user.username}")
                    PermissionManager.grant_permission_group(user.id, 'admin', user.id)
                else:
                    # Grant user-level permissions by default
                    print(f"  - Granting user permissions to {user.username}")
                    PermissionManager.grant_permission_group(user.id, 'user', user.id)
            else:
                print(f"  - User {user.username} already has {len(current_perms)} permissions")
        
        print("\nPermission initialization completed!")
        
        # Show summary
        print("\n=== Permission Summary ===")
        for user in users:
            perms = PermissionManager.get_user_permissions(user.id)
            print(f"{user.username}: {len(perms)} permissions")

if __name__ == "__main__":
    init_permissions()