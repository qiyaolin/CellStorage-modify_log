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
