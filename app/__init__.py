# In app/__init__.py
from flask import Flask
import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, CSRFError
from sqlalchemy import text
from config import Config
from datetime import datetime  # 确保导入 datetime

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Please login first"
login_manager.login_message_category = "info"
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # CSRF 错误处理
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        from flask import render_template, request, current_app
        current_app.logger.warning(f'CSRF Error: {e.description} on {request.url}')
        return render_template('errors/csrf_error.html', reason=e.description), 400

    with app.app_context():
        from app.shared.utils import get_batch_counter
        db.create_all()
        try:
            # Add password_plain column to users table
            db.session.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_plain VARCHAR(128);"
            ))
            
            # Add batch_id column to print_jobs table if it exists
            db.session.execute(text(
                "ALTER TABLE print_jobs ADD COLUMN IF NOT EXISTS batch_id INTEGER;"
            ))
            
            # Add foreign key constraint if it doesn't exist
            db.session.execute(text("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE constraint_name = 'fk_print_jobs_batch_id'
                    ) THEN
                        ALTER TABLE print_jobs 
                        ADD CONSTRAINT fk_print_jobs_batch_id 
                        FOREIGN KEY (batch_id) REFERENCES vial_batches(id);
                    END IF;
                END $$;
            """))
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Log the error but don't stop app startup
            print(f"Database migration warning: {e}")

        # Ensure batch counter config exists
        get_batch_counter()

    # Register blueprints
    from .shared.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .main_routes import bp as main_bp
    app.register_blueprint(main_bp)

    from .cell_storage.main import bp as cell_storage_bp
    app.register_blueprint(cell_storage_bp, url_prefix='/cell-storage')

    from .inventory import routes as inventory_routes
    app.register_blueprint(inventory_routes.bp, url_prefix='/inventory')
    
    # Register API blueprints
    from .api.printing import printing_api
    app.register_blueprint(printing_api)
    
    # Disable CSRF protection for printing API endpoints
    csrf.exempt(printing_api)
    
    # Initialize Flask-Admin first
    from .admin_interface import init_admin
    init_admin(app)

    # Register the original admin blueprint with a different prefix
    from .admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/system-admin')

    # Import models from both subprojects
    from app.cell_storage import models as cell_models
    from app.inventory import models as inventory_models

    @login_manager.user_loader
    def load_user(user_id):
        return cell_models.User.query.get(int(user_id))

    # ADD THIS CONTEXT PROCESSOR
    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.utcnow().year}
    
    # Add permission functions to template context
    @app.context_processor
    def inject_permission_functions():
        from .shared.permissions import (has_permission, get_user_permissions, 
                                       can_view_inventory, can_edit_inventory,
                                       can_manage_locations, can_manage_suppliers,
                                       can_approve_orders, is_admin)
        return {
            'has_permission': has_permission,
            'get_user_permissions': get_user_permissions,
            'can_view_inventory': can_view_inventory,
            'can_edit_inventory': can_edit_inventory,
            'can_manage_locations': can_manage_locations,
            'can_manage_suppliers': can_manage_suppliers,
            'can_approve_orders': can_approve_orders,
            'is_admin': is_admin
        }

    @app.template_filter('from_json')
    def from_json_filter(value):
        """Convert a JSON string to a Python object."""
        try:
            return json.loads(value) if value else None
        except Exception:
            return None

    @app.template_filter('default_if_none')
    def default_if_none_filter(value, default=''):
        """Return default value if the value is None, empty string, or 'None'."""
        if value is None or value == '' or str(value) == 'None':
            return default
        return value

    return app