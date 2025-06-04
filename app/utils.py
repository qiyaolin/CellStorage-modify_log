from datetime import datetime
import json
from . import db
from .models import AuditLog

def log_audit(user_id, action, target_type=None, target_id=None, details=None, **extra):
    """Create an ``AuditLog`` entry.

    ``details`` may be a string or dictionary. Any additional keyword
    arguments are captured into the details payload for convenience so
    callers won't accidentally pass unexpected parameters.
    """

    if extra:
        if isinstance(details, dict):
            extra.update(details)
        elif details is not None:
            extra["details"] = details
        details = json.dumps(extra)
    elif isinstance(details, dict):
        details = json.dumps(details)

    log = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.session.add(log)
    db.session.commit()


def clear_database_except_admin():
    """Delete all records except users with the admin role."""
    from app.models import (
        User,
        CellLine,
        Tower,
        Drawer,
        Box,
        CryoVial,
        VialBatch,
        AuditLog,
    )

    # Delete dependent tables first to satisfy foreign key constraints
    for model in (
        CryoVial,
        VialBatch,
        Box,
        Drawer,
        Tower,
        CellLine,
        AuditLog,
    ):
        db.session.query(model).delete()
    db.session.query(User).filter(User.role != 'admin').delete()
    db.session.commit()
