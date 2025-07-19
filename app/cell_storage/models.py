from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .. import db  # Import db object from app package's __init__.py
import json


# We will initialize LoginManager in app/__init__.py and set user_loader
# from . import login_manager # This line is not needed now, user_loader is set in __init__.py

# flask_login UserMixin provides default implementation for user session management
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    # email = db.Column(db.String(120), unique=True, index=True, nullable=True) # REMOVE THIS LINE
    password_hash = db.Column(db.String(256))
    password_plain = db.Column(db.String(128))  # store plain password for admin view
    role = db.Column(db.String(64), default='user', nullable=False)  # e.g., 'user', 'admin'. Make role non-nullable.

    # Relationships remain largely the same, they are not directly tied to email
    cell_lines_created = db.relationship('CellLine', backref='creator', lazy='dynamic',
                                         foreign_keys='CellLine.created_by_user_id')
    vials_frozen = db.relationship('CryoVial', backref='freezer_operator', lazy='dynamic',
                                   foreign_keys='CryoVial.frozen_by_user_id')
    audit_logs = db.relationship('AuditLog', backref='user_performing_action', lazy='dynamic',
                                 foreign_keys='AuditLog.user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.password_plain = password

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    # Helper property for admin checks (optional but convenient)
    @property
    def is_admin(self):
        return self.role == 'admin'


class CellLine(db.Model):
    __tablename__ = 'cell_lines'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, index=True, nullable=False)
    source = db.Column(db.String(128))  # e.g., ATCC, Gift
    species = db.Column(db.String(64))  # e.g., Human, Mouse
    original_passage = db.Column(db.String(64))  # Can be number or range, so use string
    culture_medium = db.Column(db.String(255))
    antibiotic_resistance = db.Column(db.String(255))  # e.g., Puromycin, Blasticidin
    growth_properties = db.Column(db.Text)  # e.g., Adherent, Suspension
    mycoplasma_status = db.Column(db.String(64))  # e.g., Negative (Date), Positive
    date_established = db.Column(db.Date)  # Cell line establishment or receipt date
    notes = db.Column(db.Text)

    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Associated creator
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)  # Record creation or last modification time

    # Associated with all cryovials using this cell line
    cryovials = db.relationship('CryoVial', backref='cell_line_info', lazy='dynamic')

    def __repr__(self):
        return f'<CellLine {self.name}>'


class Tower(db.Model):
    __tablename__ = 'towers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)  # e.g., "Tower 1", "LN2 Main"
    freezer_name = db.Column(db.String(128))  # e.g., "-80C Fridge A"
    description = db.Column(db.Text)

    drawers = db.relationship('Drawer', backref='tower_info', lazy='dynamic')

    def __repr__(self):
        return f'<Tower {self.name} in {self.freezer_name}>'


class Drawer(db.Model):
    __tablename__ = 'drawers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)  # e.g., "Drawer 1", "Shelf A"
    tower_id = db.Column(db.Integer, db.ForeignKey('towers.id'), nullable=False)

    boxes = db.relationship('Box', backref='drawer_info', lazy='dynamic')

    # Ensure drawer name is unique within a tower
    __table_args__ = (db.UniqueConstraint('name', 'tower_id', name='_drawer_name_tower_uc'),)

    def __repr__(self):
        return f'<Drawer {self.name} in Tower ID {self.tower_id}>'


class Box(db.Model):
    __tablename__ = 'boxes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)  # e.g., "Box 001", "P01 Cells"
    drawer_id = db.Column(db.Integer, db.ForeignKey('drawers.id'), nullable=False)
    rows = db.Column(db.Integer, default=9)  # e.g., 9 for a 9x9 box
    columns = db.Column(db.Integer, default=9)  # e.g., 9 for a 9x9 box
    description = db.Column(db.Text)

    cryovials = db.relationship('CryoVial', backref='box_location', lazy='dynamic')

    # Ensure box name is unique within a drawer
    __table_args__ = (db.UniqueConstraint('name', 'drawer_id', name='_box_name_drawer_uc'),)

    def __repr__(self):
        return f'<Box {self.name} in Drawer ID {self.drawer_id}>'


class VialBatch(db.Model):
    __tablename__ = 'vial_batches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    vials = db.relationship('CryoVial', backref='batch', lazy='dynamic')

    def __repr__(self):
        return f'<VialBatch {self.id}: {self.name}>'

class CryoVial(db.Model):
    __tablename__ = 'cryovials'
    id = db.Column(db.Integer, primary_key=True)
    unique_vial_id_tag = db.Column(db.String(128), unique=True, index=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('vial_batches.id'), nullable=False)

    cell_line_id = db.Column(db.Integer, db.ForeignKey('cell_lines.id'), nullable=False)

    box_id = db.Column(db.Integer, db.ForeignKey('boxes.id'), nullable=False)
    row_in_box = db.Column(db.Integer, nullable=False)
    col_in_box = db.Column(db.Integer, nullable=False)

    passage_number = db.Column(db.String(64))
    date_frozen = db.Column(db.Date, nullable=False)
    frozen_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    number_of_vials_at_creation = db.Column(db.Integer, default=1)
    volume_ml = db.Column(db.Float)
    concentration = db.Column(db.String(128))
    fluorescence_tag = db.Column(db.String(128))
    resistance = db.Column(db.String(128))
    parental_cell_line = db.Column(db.String(128))

    status = db.Column(db.String(64), default='Available')
    notes = db.Column(db.Text)

    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # REMOVE or COMMENT OUT the existing UniqueConstraint for position
    # __table_args__ = (db.UniqueConstraint('box_id', 'row_in_box', 'col_in_box', name='_box_position_uc'),)

    # If you have other table arguments, keep them, just remove the specific UniqueConstraint.
    # If this was the only one, you can remove the line entirely.
    # For example, if you wanted to keep other constraints (though we don't have them here for CryoVial yet):
    # __table_args__ = (
    #     # Other constraints here,
    # )
    # Or simply remove the line if it was the only one.

    def __repr__(self):
        return f'<CryoVial {self.unique_vial_id_tag} batch={self.batch_id}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Operating user
    action = db.Column(db.String(255), nullable=False)  # e.g., "LOGIN", "CREATE_VIAL", "EDIT_CELL_LINE"
    target_type = db.Column(db.String(64))  # e.g., "CryoVial", "CellLine", "User"
    target_id = db.Column(db.Integer)  # Related record ID
    details = db.Column(db.Text)  # Can store JSON format change details

    def __repr__(self):
        return f'<AuditLog {self.action} by User ID {self.user_id} at {self.timestamp}>'


class AppConfig(db.Model):
    """Simple key/value store for application-wide settings."""
    __tablename__ = 'app_config'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AppConfig {self.key}={self.value}>"


class AlertConfig(db.Model):
    """Configuration for inventory alerts."""
    __tablename__ = 'alert_configs'
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(64), nullable=False)  # 'low_stock', 'box_capacity', 'old_samples'
    is_enabled = db.Column(db.Boolean, default=True)
    threshold_value = db.Column(db.Integer)  # Threshold value
    threshold_days = db.Column(db.Integer)  # Days threshold
    cell_line_id = db.Column(db.Integer, db.ForeignKey('cell_lines.id'), nullable=True)  # Specific cell line configuration
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cell_line = db.relationship('CellLine', backref='alert_configs')
    created_by = db.relationship('User', backref='alert_configs_created')

    def __repr__(self):
        return f"<AlertConfig {self.alert_type}>"


class Alert(db.Model):
    """Generated alerts for inventory management."""
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(64), nullable=False)
    severity = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high', 'critical'
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Associated objects
    cell_line_id = db.Column(db.Integer, db.ForeignKey('cell_lines.id'), nullable=True)
    box_id = db.Column(db.Integer, db.ForeignKey('boxes.id'), nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('vial_batches.id'), nullable=True)
    
    # Status and time
    is_resolved = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)
    resolved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    dismissed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Additional data (JSON format)
    extra_data = db.Column(db.Text)  # Store additional information like current count, threshold, etc

    # Relationships
    cell_line = db.relationship('CellLine', backref='alerts')
    box = db.relationship('Box', backref='alerts')
    batch = db.relationship('VialBatch', backref='alerts')
    resolved_by = db.relationship('User', backref='alerts_resolved')

    @property
    def is_active(self):
        """Check if alert is still active (unresolved and not dismissed)"""
        return not self.is_resolved and not self.is_dismissed

    @property
    def age_days(self):
        """Number of days the alert has existed"""
        return (datetime.utcnow() - self.created_at).days

    def to_dict(self):
        """Convert to dictionary format"""
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'is_resolved': self.is_resolved,
            'is_dismissed': self.is_dismissed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'age_days': self.age_days,
            'extra_data': json.loads(self.extra_data) if self.extra_data else None
        }

    def __repr__(self):
        return f"<Alert {self.alert_type}: {self.title}>"


class ThemeConfig(db.Model):
    """Theme configuration model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    theme_name = db.Column(db.String(50), nullable=False, default='classic')  # Theme name
    primary_color = db.Column(db.String(7), nullable=False, default='#667eea')  # Primary color
    secondary_color = db.Column(db.String(7), nullable=False, default='#764ba2')  # Secondary color
    accent_color = db.Column(db.String(7), nullable=False, default='#f093fb')  # Accent color
    background_color = db.Column(db.String(7), nullable=False, default='#f8f9fa')  # Background color
    text_color = db.Column(db.String(7), nullable=False, default='#212529')  # Text color
    navbar_style = db.Column(db.String(20), nullable=False, default='light')  # Navbar style
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Associated user
    user = db.relationship('User', backref='theme_config')
    
    def to_dict(self):
        return {
            'id': self.id,
            'theme_name': self.theme_name,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'background_color': self.background_color,
            'text_color': self.text_color,
            'navbar_style': self.navbar_style
        }
