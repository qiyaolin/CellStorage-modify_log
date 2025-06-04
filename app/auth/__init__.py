# In app/auth/__init__.py
from flask import Blueprint

bp = Blueprint('auth', __name__)

# Import routes at the end to avoid circular dependencies
from app.auth import routes