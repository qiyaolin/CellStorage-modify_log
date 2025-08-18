from datetime import datetime, timedelta
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
    created_by = db.relationship('User', backref='batches_created', lazy='select')

    def __repr__(self):
        return f'<VialBatch {self.id}: {self.name}>'
    
    # Dynamic properties that get data from the first vial in the batch
    @property
    def cell_line(self):
        try:
            first_vial = self.vials.first()
            if first_vial and first_vial.cell_line_info:
                return first_vial.cell_line_info.name
            return 'Unknown'
        except Exception:
            return 'Unknown'
    
    @property
    def passage_number(self):
        try:
            first_vial = self.vials.first()
            return getattr(first_vial, 'passage_number', '') if first_vial else ''
        except Exception:
            return ''
    
    @property
    def date_frozen(self):
        try:
            first_vial = self.vials.first()
            return getattr(first_vial, 'date_frozen', None) if first_vial else None
        except Exception:
            return None
    
    @property
    def fluorescence_tag(self):
        first_vial = self.vials.first()
        return getattr(first_vial, 'fluorescence_tag', '') if first_vial else ''
    
    @property
    def resistance(self):
        first_vial = self.vials.first()
        return getattr(first_vial, 'resistance', '') if first_vial else ''
    
    @property
    def parental_cell_line(self):
        try:
            first_vial = self.vials.first()
            return getattr(first_vial, 'parental_cell_line', '') if first_vial else ''
        except Exception:
            return ''
    
    @property
    def notes(self):
        first_vial = self.vials.first()
        return getattr(first_vial, 'notes', '') if first_vial else ''
    
    @property
    def tag(self):
        # For search functionality, we can use the batch name or generate from vials
        return self.name
    
    def get_parent_batches(self):
        """获取父代批次列表，基于parental_cell_line字段匹配"""
        if not self.parental_cell_line:
            return []
        
        # 找到所有名称匹配parental_cell_line的batch
        parent_batches = VialBatch.query.filter_by(name=self.parental_cell_line).all()
        
        # 同时也考虑那些cell_line名称匹配的batch（通过第一个vial的cell_line）
        cell_line_matches = VialBatch.query.join(CryoVial).join(CellLine).filter(
            CellLine.name == self.parental_cell_line
        ).all()
        
        # 合并并去重
        all_parents = list(set(parent_batches + cell_line_matches))
        # 排除自己
        return [batch for batch in all_parents if batch.id != self.id]
    
    def get_child_batches(self):
        """获取子代批次列表，基于其他batch的parental_cell_line指向当前batch"""
        # 找到所有parental_cell_line等于当前batch名称的batch
        name_children = VialBatch.query.join(CryoVial).filter(
            CryoVial.parental_cell_line == self.name
        ).distinct().all()
        
        # 同时考虑parental_cell_line等于当前batch关联cell_line名称的batch
        cell_line_children = []
        if self.cell_line != 'Unknown':
            cell_line_children = VialBatch.query.join(CryoVial).filter(
                CryoVial.parental_cell_line == self.cell_line
            ).distinct().all()
        
        # 合并并去重
        all_children = list(set(name_children + cell_line_children))
        # 排除自己
        return [batch for batch in all_children if batch.id != self.id]
    
    def get_lineage_tree(self, max_depth=5):
        """
        获取完整的家谱树（包括祖先和后代）
        返回格式：{
            'current': batch_info,
            'ancestors': [ancestors_tree],
            'descendants': [descendants_tree]
        }
        """
        def build_ancestor_tree(batch, depth=0):
            if depth >= max_depth:
                return None
            
            batch_info = {
                'id': batch.id,
                'name': batch.name,
                'cell_line': batch.cell_line,
                'passage_number': batch.passage_number,
                'date_frozen': batch.date_frozen.isoformat() if batch.date_frozen else None,
                'parental_cell_line': batch.parental_cell_line,
                'depth': depth,
                'parents': []
            }
            
            parents = batch.get_parent_batches()
            for parent in parents:
                parent_tree = build_ancestor_tree(parent, depth + 1)
                if parent_tree:
                    batch_info['parents'].append(parent_tree)
            
            return batch_info
        
        def build_descendant_tree(batch, depth=0):
            if depth >= max_depth:
                return None
            
            batch_info = {
                'id': batch.id,
                'name': batch.name,
                'cell_line': batch.cell_line,
                'passage_number': batch.passage_number,
                'date_frozen': batch.date_frozen.isoformat() if batch.date_frozen else None,
                'parental_cell_line': batch.parental_cell_line,
                'depth': depth,
                'children': []
            }
            
            children = batch.get_child_batches()
            for child in children:
                child_tree = build_descendant_tree(child, depth + 1)
                if child_tree:
                    batch_info['children'].append(child_tree)
            
            return batch_info
        
        # 构建当前batch信息
        current_info = {
            'id': self.id,
            'name': self.name,
            'cell_line': self.cell_line,
            'passage_number': self.passage_number,
            'date_frozen': self.date_frozen.isoformat() if self.date_frozen else None,
            'parental_cell_line': self.parental_cell_line,
            'vial_count': self.vials.count()
        }
        
        # 构建祖先树
        ancestors = []
        for parent in self.get_parent_batches():
            ancestor_tree = build_ancestor_tree(parent, 1)
            if ancestor_tree:
                ancestors.append(ancestor_tree)
        
        # 构建后代树
        descendants = []
        for child in self.get_child_batches():
            descendant_tree = build_descendant_tree(child, 1)
            if descendant_tree:
                descendants.append(descendant_tree)
        
        return {
            'current': current_info,
            'ancestors': ancestors,
            'descendants': descendants,
            'has_lineage': len(ancestors) > 0 or len(descendants) > 0
        }

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


# Printing System Models
class PrintJob(db.Model):
    """Print job model for centralized printing system"""
    __tablename__ = 'print_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    label_data = db.Column(db.Text, nullable=False)  # JSON string containing label data
    priority = db.Column(db.String(20), nullable=False, default='normal')  # low, normal, high, urgent
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, processing, completed, failed
    
    # User who requested the print job
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Error handling
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0, nullable=False)
    max_retries = db.Column(db.Integer, default=3, nullable=False)
    
    # Print server info
    print_server_id = db.Column(db.String(100), nullable=True)  # Which server processed this job
    
    # Batch association
    batch_id = db.Column(db.Integer, db.ForeignKey('vial_batches.id'), nullable=True)  # Associated batch
    
    # Relationships
    user = db.relationship('User', backref='print_jobs')
    batch = db.relationship('VialBatch', backref='print_jobs')
    
    @property
    def can_retry(self):
        """Check if job can be retried"""
        return self.status == 'failed' and self.retry_count < self.max_retries
    
    @property
    def label_data_json(self):
        """Get label data as parsed JSON"""
        try:
            return json.loads(self.label_data) if self.label_data else {}
        except json.JSONDecodeError:
            return {}
    
    @label_data_json.setter
    def label_data_json(self, value):
        """Set label data from dictionary"""
        self.label_data = json.dumps(value) if value else '{}'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'label_data': self.label_data_json,
            'priority': self.priority,
            'status': self.status,
            'requested_by': self.requested_by,
            'requested_by_username': self.user.username if self.user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'can_retry': self.can_retry,
            'print_server_id': self.print_server_id,
            'batch_id': self.batch_id,
            'batch_name': self.batch.name if self.batch else None
        }
    
    def mark_processing(self, server_id=None, notes=None):
        """Mark job as processing"""
        old_status = self.status
        self.status = 'processing'
        self.started_at = datetime.utcnow()
        if server_id:
            self.print_server_id = server_id
        self._record_status_change(old_status, 'processing', notes)
        
    def mark_completed(self, notes=None):
        """Mark job as completed"""
        old_status = self.status
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self._record_status_change(old_status, 'completed', notes)
        
    def mark_failed(self, error_message=None, notes=None):
        """Mark job as failed and increment retry count"""
        old_status = self.status
        self.status = 'failed'
        self.retry_count += 1
        if error_message:
            self.error_message = error_message
        self._record_status_change(old_status, 'failed', notes or error_message)
        
    def _record_status_change(self, status_from, status_to, notes=None):
        """Record status change in history"""
        from . import db  # Import here to avoid circular imports
        history = PrintJobHistory(
            print_job_id=self.id,
            status_from=status_from,
            status_to=status_to,
            notes=notes
        )
        db.session.add(history)
    
    def __repr__(self):
        return f'<PrintJob {self.id}: {self.status}>'


class PrintServer(db.Model):
    """Print server registration model"""
    __tablename__ = 'print_servers'
    
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(100), unique=True, nullable=False)  # Unique server identifier
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    
    # Status tracking
    status = db.Column(db.String(20), nullable=False, default='offline')  # online, offline, error
    last_heartbeat = db.Column(db.DateTime, nullable=True)
    
    # Capabilities
    printer_types = db.Column(db.Text, nullable=True)  # JSON array of supported printer types
    max_concurrent_jobs = db.Column(db.Integer, default=1, nullable=False)
    
    # Statistics
    total_jobs_processed = db.Column(db.Integer, default=0, nullable=False)
    successful_jobs = db.Column(db.Integer, default=0, nullable=False)
    failed_jobs = db.Column(db.Integer, default=0, nullable=False)
    
    # Timestamps
    registered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def is_online(self):
        """Check if server is considered online based on last heartbeat"""
        if not self.last_heartbeat or self.status != 'online':
            return False
        
        # Consider offline if no heartbeat in last 5 minutes
        time_diff = datetime.utcnow() - self.last_heartbeat
        return time_diff.total_seconds() < 300  # 5 minutes
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.total_jobs_processed == 0:
            return 0
        return round((self.successful_jobs / self.total_jobs_processed) * 100, 2)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'name': self.name,
            'location': self.location,
            'status': self.status,
            'is_online': self.is_online,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'printer_types': json.loads(self.printer_types) if self.printer_types else [],
            'max_concurrent_jobs': self.max_concurrent_jobs,
            'total_jobs_processed': self.total_jobs_processed,
            'successful_jobs': self.successful_jobs,
            'failed_jobs': self.failed_jobs,
            'success_rate': self.success_rate,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None
        }
    
    def __repr__(self):
        return f'<PrintServer {self.server_id}: {self.status}>'


class PrintJobHistory(db.Model):
    """Print job status change history for audit tracking"""
    __tablename__ = 'print_job_history'
    
    id = db.Column(db.Integer, primary_key=True)
    print_job_id = db.Column(db.Integer, db.ForeignKey('print_jobs.id', ondelete='CASCADE'), nullable=False)
    status_from = db.Column(db.String(20), nullable=True)  # Previous status
    status_to = db.Column(db.String(20), nullable=False)   # New status
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text, nullable=True)  # Additional notes about the change
    
    # Relationships
    print_job = db.relationship('PrintJob', backref=db.backref('history', lazy='dynamic', cascade='all, delete-orphan'))
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'print_job_id': self.print_job_id,
            'status_from': self.status_from,
            'status_to': self.status_to,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None,
            'notes': self.notes
        }
    
    def __repr__(self):
        return f'<PrintJobHistory {self.print_job_id}: {self.status_from} -> {self.status_to}>'
