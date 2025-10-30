# Flask-Admin Interface Backup - Original Configuration
# This file contains the original Flask-Admin configuration before GAE fixes
# Use this for reference or rollback if needed

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView, expose
from flask_admin.actions import action
from flask import flash, redirect, url_for
from flask_login import current_user
from sqlalchemy import text

class OriginalBaseModelView(ModelView):
    """Original Base ModelView without GAE compatibility fixes"""
    page_size = 100

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access admin panel', 'warning')
            return redirect(url_for('auth.login'))
        else:
            flash('Admin access required', 'error')
            return redirect(url_for('cell_storage.index'))

def init_admin_original(app):
    """Original Flask-Admin initialization - for rollback reference"""
    from app import db

    # Original configuration with template_mode
    admin = Admin(
        app,
        name='Cell Storage Admin',
        template_mode='bootstrap3',
        index_view=CustomAdminIndexView(name='首页', url='/flask-admin')
    )

    # Model registrations would go here...
    return admin

# Notes for rollback:
# 1. Replace BaseModelView with OriginalBaseModelView
# 2. Use init_admin_original instead of init_admin
# 3. Remove error handling if causing issues
# 4. Revert app.yaml handlers section