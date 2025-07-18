# In app/__init__.py
from flask import Flask
import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
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

    with app.app_context():
        from app.utils import get_batch_counter
        db.create_all()
        try:
            db.session.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_plain VARCHAR(128);"
            ))
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Ensure batch counter config exists
        get_batch_counter()

    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .main import bp as main_bp # Keep commented for now
    app.register_blueprint(main_bp)

    from app import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    # ADD THIS CONTEXT PROCESSOR
    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.utcnow().year}

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
