from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db  # 从 app 包的 __init__.py 导入 db 对象


# 我们将在 app/__init__.py 中初始化 LoginManager，并设置 user_loader
# from . import login_manager # 这行现在不需要，user_loader 在 __init__.py 中设置

# flask_login UserMixin 提供了用户会话管理所需的默认实现
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    # email = db.Column(db.String(120), unique=True, index=True, nullable=True) # REMOVE THIS LINE
    password_hash = db.Column(db.String(256))
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
    original_passage = db.Column(db.String(64))  # 可以是数字或范围，所以用字符串
    culture_medium = db.Column(db.String(255))
    antibiotic_resistance = db.Column(db.String(255))  # e.g., Puromycin, Blasticidin
    growth_properties = db.Column(db.Text)  # e.g., Adherent, Suspension
    mycoplasma_status = db.Column(db.String(64))  # e.g., Negative (Date), Positive
    date_established = db.Column(db.Date)  # 细胞系建立或接收日期
    notes = db.Column(db.Text)

    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 关联创建者
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)  # 记录创建或最后修改时间

    # 关联到使用此细胞系的所有冻存管
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
    # If this was the only one, you can remove the __table_args__ line entirely.
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 操作用户
    action = db.Column(db.String(255), nullable=False)  # e.g., "LOGIN", "CREATE_VIAL", "EDIT_CELL_LINE"
    target_type = db.Column(db.String(64))  # e.g., "CryoVial", "CellLine", "User"
    target_id = db.Column(db.Integer)  # 相关记录的ID
    details = db.Column(db.Text)  # 可以存JSON格式的变更详情

    def __repr__(self):
        return f'<AuditLog {self.action} by User ID {self.user_id} at {self.timestamp}>'