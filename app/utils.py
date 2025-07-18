from datetime import datetime
import json
from . import db
from .models import AuditLog, AppConfig, VialBatch

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
    """Delete all records except users with the admin role.

    The deletion order respects foreign key constraints so we remove
    dependent records before their parents."""

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

    # Remove dependent records first to avoid foreign key violations
    for model in (
        AuditLog,
        CryoVial,
        VialBatch,
        Box,
        Drawer,
        Tower,
        CellLine,
    ):
        db.session.query(model).delete()

    db.session.query(User).filter(User.role != 'admin').delete()
    db.session.commit()


def get_batch_counter():
    """Return current batch counter as int, initializing if missing."""
    setting = AppConfig.query.filter_by(key='batch_counter').first()
    if not setting:
        # initialize based on current max batch id
        max_id = db.session.query(db.func.max(VialBatch.id)).scalar() or 0
        setting = AppConfig(key='batch_counter', value=str(max_id + 1))
        db.session.add(setting)
        db.session.commit()
    try:
        return int(setting.value)
    except (ValueError, TypeError):
        return 1


def set_batch_counter(value):
    setting = AppConfig.query.filter_by(key='batch_counter').first()
    if not setting:
        setting = AppConfig(key='batch_counter')
        db.session.add(setting)
    setting.value = str(int(value))
    db.session.commit()


def get_next_batch_id(auto_commit=True):
    """Retrieve and increment the batch counter atomically."""
    setting = AppConfig.query.filter_by(key='batch_counter').with_for_update().first()
    if not setting:
        max_id = db.session.query(db.func.max(VialBatch.id)).scalar() or 0
        setting = AppConfig(key='batch_counter', value=str(max_id + 1))
        db.session.add(setting)
    current = int(setting.value)
    setting.value = str(current + 1)
    if auto_commit:
        db.session.commit()
    return current
