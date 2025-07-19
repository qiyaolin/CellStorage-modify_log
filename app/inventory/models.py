from datetime import datetime, date
from .. import db
import json


class InventoryType(db.Model):
    """Inventory categories like Chemical, Antibody, Equipment, etc."""
    __tablename__ = 'inventory_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(64))
    custom_fields = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('InventoryItem', backref='type_info', lazy='dynamic')

    def get_custom_fields(self):
        return json.loads(self.custom_fields) if self.custom_fields else {}

    def set_custom_fields(self, fields_dict):
        self.custom_fields = json.dumps(fields_dict)

    def __repr__(self):
        return f'<InventoryType {self.name}>'


class Location(db.Model):
    """Physical storage locations in the lab"""
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    location_type = db.Column(db.String(32))
    temperature = db.Column(db.String(32))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

    # NEW: Capacity management fields from plan
    max_capacity = db.Column(db.Integer)
    capacity_unit = db.Column(db.String(32), default='items')
    current_usage = db.Column(db.Integer, default=0)

    children = db.relationship('Location', backref=db.backref('parent', remote_side=[id]))
    items = db.relationship('InventoryItem', backref='location_info', lazy='dynamic')

    @property
    def full_path(self):
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)
    
    @property
    def usage_percentage(self):
        if not self.max_capacity or self.max_capacity == 0:
            return 0
        return (self.current_usage / self.max_capacity) * 100
    
    @property
    def is_full(self):
        if not self.max_capacity:
            return False
        return self.current_usage >= self.max_capacity
    
    @property
    def is_nearly_full(self):
        return self.usage_percentage >= 80

    def update_usage(self):
        self.current_usage = self.items.count()
        return self.current_usage

    def __repr__(self):
        return f'<Location {self.full_path}>'


class Supplier(db.Model):
    """Vendor/supplier information"""
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    contact_person = db.Column(db.String(128))
    email = db.Column(db.String(128))
    phone = db.Column(db.String(32))
    website = db.Column(db.String(255))
    address = db.Column(db.Text)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('InventoryItem', backref='supplier_info', lazy='dynamic')
    orders = db.relationship('Order', backref='supplier_info', lazy='dynamic')

    def __repr__(self):
        return f'<Supplier {self.name}>'


class InventoryItem(db.Model):
    """Core inventory items"""
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    catalog_number = db.Column(db.String(128))
    barcode = db.Column(db.String(128), unique=True, index=True)
    type_id = db.Column(db.Integer, db.ForeignKey('inventory_types.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    current_quantity = db.Column(db.Float, default=0)
    minimum_quantity = db.Column(db.Float, default=0)
    unit = db.Column(db.String(32))
    unit_price = db.Column(db.Float)
    currency = db.Column(db.String(8), default='USD')
    expiration_date = db.Column(db.Date)
    received_date = db.Column(db.Date)
    status = db.Column(db.String(32), default='Available')
    custom_data = db.Column(db.Text)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # NEW: Columns from development plan
    cas_number = db.Column(db.String(64))
    lot_number = db.Column(db.String(64))
    safety_document_url = db.Column(db.String(255))
    responsible_person_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    storage_conditions = db.Column(db.String(128))
    qr_code = db.Column(db.String(255))

    usage_logs = db.relationship('UsageLog', backref='item_info', lazy='dynamic')
    order_items = db.relationship('OrderItem', backref='item_info', lazy='dynamic')
    created_by = db.relationship('User', foreign_keys=[created_by_user_id], backref='created_items')
    responsible_person = db.relationship('User', foreign_keys=[responsible_person_id], backref='responsible_items')

    @property
    def is_low_stock(self):
        return self.current_quantity <= self.minimum_quantity

    @property
    def is_expired(self):
        if self.expiration_date:
            return self.expiration_date < date.today()
        return False

    def get_custom_data(self):
        return json.loads(self.custom_data) if self.custom_data else {}

    def set_custom_data(self, data_dict):
        self.custom_data = json.dumps(data_dict)

    def update_quantity(self, change, reason="", user_id=None):
        old_quantity = self.current_quantity
        self.current_quantity += change
        log = UsageLog(
            item_id=self.id, user_id=user_id, quantity_change=change,
            quantity_before=old_quantity, quantity_after=self.current_quantity,
            reason=reason
        )
        db.session.add(log)
        if self.current_quantity <= 0:
            self.status = 'Used Up'
        elif self.is_low_stock:
            self.status = 'Low Stock'
        else:
            self.status = 'Available'

    def __repr__(self):
        return f'<InventoryItem {self.name}>'

# --- NEW MODELS BASED ON THE DEVELOPMENT PLAN ---

class PurchaseRequest(db.Model):
    __tablename__ = 'purchase_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    catalog_number = db.Column(db.String(128))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    quantity_requested = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(32))
    justification = db.Column(db.Text)
    project_code = db.Column(db.String(64))
    priority = db.Column(db.String(16), default='Normal')
    status = db.Column(db.String(32), default='Draft') # Draft, Submitted, Approved, Rejected, Ordered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    review_notes = db.Column(db.Text)

    user = db.relationship('User', foreign_keys=[user_id])
    supplier = db.relationship('Supplier')
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_user_id])

class ShoppingCart(db.Model):
    __tablename__ = 'shopping_cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    catalog_number = db.Column(db.String(128))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(32))
    estimated_price = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='cart_items')
    supplier = db.relationship('Supplier', backref='cart_items')

class SupplierContact(db.Model):
    __tablename__ = 'supplier_contacts'
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    title = db.Column(db.String(64))
    email = db.Column(db.String(128))
    phone = db.Column(db.String(32))
    mobile = db.Column(db.String(32))
    is_primary = db.Column(db.Boolean, default=False)
    is_technical_contact = db.Column(db.Boolean, default=False)
    is_sales_contact = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    supplier = db.relationship('Supplier', backref='contacts')

class UserPermission(db.Model):
    __tablename__ = 'user_permissions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission = db.Column(db.String(64), nullable=False)
    resource_type = db.Column(db.String(64))
    resource_id = db.Column(db.Integer)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    granted_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    granted_by = db.relationship('User', foreign_keys=[granted_by_user_id])
    user = db.relationship('User', foreign_keys=[user_id], backref='permissions')
    
    def __repr__(self):
        return f'<UserPermission {self.permission} for user {self.user_id}>'

class SupplierRating(db.Model):
    __tablename__ = 'supplier_ratings'
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    delivery_rating = db.Column(db.Integer)
    quality_rating = db.Column(db.Integer)
    service_rating = db.Column(db.Integer)
    overall_rating = db.Column(db.Float)
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    supplier = db.relationship('Supplier', backref='ratings')
    order = db.relationship('Order', backref='rating')
    user = db.relationship('User', backref='supplier_ratings')

class ItemPriceHistory(db.Model):
    __tablename__ = 'item_price_history'
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    catalog_number = db.Column(db.String(128))
    item_name = db.Column(db.String(255))
    unit_price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(8), default='USD')
    effective_date = db.Column(db.Date, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    supplier = db.relationship('Supplier', backref='price_history')
    order = db.relationship('Order', backref='price_history')

# --- EXISTING MODELS (for context) ---
class UsageLog(db.Model):
    __tablename__ = 'usage_logs'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    quantity_change = db.Column(db.Float, nullable=False)
    quantity_before = db.Column(db.Float)
    quantity_after = db.Column(db.Float)
    reason = db.Column(db.String(255))
    notes = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(32), default='Draft')
    priority = db.Column(db.String(16), default='Normal')
    requested_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    total_cost = db.Column(db.Float)
    currency = db.Column(db.String(8), default='USD')
    requested_date = db.Column(db.DateTime, default=datetime.utcnow)
    needed_by_date = db.Column(db.Date)
    approved_date = db.Column(db.DateTime)
    ordered_date = db.Column(db.DateTime)
    received_date = db.Column(db.DateTime)
    justification = db.Column(db.Text)
    notes = db.Column(db.Text)
    items = db.relationship('OrderItem', backref='order_info', lazy='dynamic', cascade='all, delete-orphan')
    requested_by = db.relationship('User', foreign_keys=[requested_by_user_id], backref='orders_requested')
    approved_by = db.relationship('User', foreign_keys=[approved_by_user_id], backref='orders_approved')

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'))
    item_name = db.Column(db.String(255), nullable=False)
    catalog_number = db.Column(db.String(128))
    description = db.Column(db.Text)
    quantity_requested = db.Column(db.Float, nullable=False)
    quantity_received = db.Column(db.Float, default=0)
    unit = db.Column(db.String(32))
    unit_price = db.Column(db.Float)
    total_price = db.Column(db.Float)
    status = db.Column(db.String(32), default='Pending')
    notes = db.Column(db.Text)

class StockAlert(db.Model):
    __tablename__ = 'stock_alerts'
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(32), nullable=False)
    severity = db.Column(db.String(16), default='medium')
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    acknowledged_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime)
    extra_data = db.Column(db.Text)
    
    item = db.relationship('InventoryItem', backref='alerts')
    location = db.relationship('Location', backref='alerts')
    acknowledged_by = db.relationship('User', foreign_keys=[acknowledged_by_user_id], backref='acknowledged_alerts')
    
    def acknowledge(self, user_id):
        self.is_acknowledged = True
        self.acknowledged_by_user_id = user_id
        self.acknowledged_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<StockAlert {self.title}>'


class Notification(db.Model):
    """User notifications system"""
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref='notifications')
    
    def mark_as_read(self):
        self.is_read = True
    
    def __repr__(self):
        return f'<Notification {self.title} for user {self.user_id}>'