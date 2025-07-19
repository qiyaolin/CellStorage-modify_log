# In app/main/__init__.py
from flask import Blueprint

bp = Blueprint('cell_storage', __name__)

# Import routes at the end to avoid circular dependencies
from . import routes