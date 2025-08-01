from flask import Blueprint

bp = Blueprint('system_admin', __name__, url_prefix='/admin')

from . import routes