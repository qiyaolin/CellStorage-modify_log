from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    """Main dashboard showing both subproject options"""
    return render_template('dashboard.html')