from datetime import datetime
from . import db
from .models import AuditLog


def log_audit(user_id, action, target_type=None, target_id=None, details=None):
    """Create an AuditLog entry."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.session.add(log)
    db.session.commit()
