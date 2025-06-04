# In app/main/__init__.py
from flask import Blueprint

bp = Blueprint('main', __name__)

# Import routes at the end to avoid circular dependencies
from app.main import routes