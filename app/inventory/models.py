from datetime import datetime
from .. import db
import json


class InventoryType(db.Model):
    """Inventory categories like Chemical, Antibody, Equipment, etc."""
    __tablename__ = 'inventory_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)  # e.g., "Chemical", "Antibody"
    description = db.Column(db.Text)
    icon = db.Column(db.String(64))  # CSS icon class
    custom_fields = db.Column(db.Text)  # JSON format for custom fields definition
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('InventoryItem', backref='type_info', lazy='dynamic')
    
    def get_custom_fields(self):
        """Get custom fields as Python dict"""
        return json.loads(self.custom_fields) if self.custom_fields else {}
    
    def set_custom_fields(self, fields_dict):
        """Set custom fields from Python dict"""
        self.custom_fields = json.dumps(fields_dict)
    
    def __repr__(self):
        return f'<InventoryType {self.name}>'


class Location(db.Model):
    """Physical storage locations in the lab"""
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)  # e.g., "Room 101", "Fridge A"
    parent_id = db.Column(db.Integer, db.ForeignKey('locations.id'))  # For hierarchical locations
    location_type = db.Column(db.String(32))  # "room", "cabinet", "shelf", "freezer"
    temperature = db.Column(db.String(32))  # e.g., "4°C", "RT", "-20°C"
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Capacity management
    max_capacity = db.Column(db.Integer)  # Maximum number of items
    capacity_unit = db.Column(db.String(32), default='items')  # 'items', 'volume', 'weight'
    current_usage = db.Column(db.Integer, default=0)  # Current number of items
    
    # Self-referential relationship
    children = db.relationship('Location', backref=db.backref('parent', remote_side=[id]))
    items = db.relationship('InventoryItem', backref='location_info', lazy='dynamic')
    
    @property
    def full_path(self):
        """Get full location path like 'Room 101 > Fridge A > Shelf 1'"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)
    
    @property
    def usage_percentage(self):
        """Calculate location usage percentage"""
        if not self.max_capacity or self.max_capacity == 0:
            return 0
        return (self.current_usage / self.max_capacity) * 100
    
    @property
    def is_full(self):
        """Check if location is at capacity"""
        if not self.max_capacity:
            return False
        return self.current_usage >= self.max_capacity
    
    @property
    def is_nearly_full(self):
        """Check if location is nearly full (80% capacity)"""
        return self.usage_percentage >= 80
    
    def update_usage(self):
        """Update current usage count based on actual items"""
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
    
    # Relationships
    items = db.relationship('InventoryItem', backref='supplier_info', lazy='dynamic')
    orders = db.relationship('Order', backref='supplier_info', lazy='dynamic')
    
    def __repr__(self):
        return f'<Supplier {self.name}>'


class InventoryItem(db.Model):
    """Core inventory items"""
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic info
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    catalog_number = db.Column(db.String(128))
    barcode = db.Column(db.String(128), unique=True, index=True)
    cas_number = db.Column(db.String(64))  # Chemical Abstract Service number
    lot_number = db.Column(db.String(64))  # Batch/Lot number
    safety_document_url = db.Column(db.String(255))  # Link to SDS/safety documents
    qr_code = db.Column(db.String(255))  # QR code for item identification
    
    # Classification
    type_id = db.Column(db.Integer, db.ForeignKey('inventory_types.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    
    # Quantities
    current_quantity = db.Column(db.Float, default=0)
    minimum_quantity = db.Column(db.Float, default=0)  # For low stock alerts
    unit = db.Column(db.String(32))  # e.g., "mL", "mg", "pieces"
    
    # Pricing
    unit_price = db.Column(db.Float)
    currency = db.Column(db.String(8), default='USD')
    
    # Dates
    expiration_date = db.Column(db.Date)
    received_date = db.Column(db.Date)
    
    # Status
    status = db.Column(db.String(32), default='Available')  # Available, Expired, Used Up, etc.
    
    # Custom fields (JSON)
    custom_data = db.Column(db.Text)  # Store type-specific custom field data
    
    # Metadata
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    responsible_person_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Person responsible for this item
    storage_conditions = db.Column(db.String(128))  # e.g., "Store at -20°C", "Keep dry"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    usage_logs = db.relationship('UsageLog', backref='item_info', lazy='dynamic')
    order_items = db.relationship('OrderItem', backref='item_info', lazy='dynamic')
    created_by = db.relationship('User', foreign_keys=[created_by_user_id], backref='created_items')
    responsible_person = db.relationship('User', foreign_keys=[responsible_person_id], backref='responsible_items')
    
    @property
    def is_low_stock(self):
        """Check if item is below minimum quantity"""
        return self.current_quantity <= self.minimum_quantity
    
    @property
    def is_expired(self):
        """Check if item is expired"""
        if self.expiration_date:
            return self.expiration_date < datetime.utcnow().date()
        return False
    
    def get_custom_data(self):
        """Get custom data as Python dict"""
        return json.loads(self.custom_data) if self.custom_data else {}
    
    def set_custom_data(self, data_dict):
        """Set custom data from Python dict"""
        self.custom_data = json.dumps(data_dict)
    
    def update_quantity(self, change, reason="", user_id=None):
        """Update quantity and log the change"""
        old_quantity = self.current_quantity
        self.current_quantity += change
        
        # Create usage log
        log = UsageLog(
            item_id=self.id,
            user_id=user_id,
            quantity_change=change,
            quantity_before=old_quantity,
            quantity_after=self.current_quantity,
            reason=reason
        )
        db.session.add(log)
        
        # Update status based on quantity
        if self.current_quantity <= 0:
            self.status = 'Used Up'
        elif self.is_low_stock:
            self.status = 'Low Stock'
        else:
            self.status = 'Available'
    
    def __repr__(self):
        return f'<InventoryItem {self.name} ({self.current_quantity} {self.unit})>'


class UsageLog(db.Model):
    """Log of inventory usage/changes"""
    __tablename__ = 'usage_logs'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    quantity_change = db.Column(db.Float, nullable=False)  # Can be negative for usage
    quantity_before = db.Column(db.Float)
    quantity_after = db.Column(db.Float)
    
    reason = db.Column(db.String(255))  # "Usage", "Received", "Expired", "Adjustment"
    notes = db.Column(db.Text)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<UsageLog Item:{self.item_id} Change:{self.quantity_change}>'


class Order(db.Model):
    """Purchase orders and requests"""
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(64), unique=True, nullable=False)
    
    # Status workflow
    status = db.Column(db.String(32), default='Draft')  # Draft, Submitted, Approved, Ordered, Received, Cancelled
    priority = db.Column(db.String(16), default='Normal')  # Low, Normal, High, Urgent
    
    # People
    requested_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Supplier and costs
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    total_cost = db.Column(db.Float)
    currency = db.Column(db.String(8), default='USD')
    
    # Dates
    requested_date = db.Column(db.DateTime, default=datetime.utcnow)
    needed_by_date = db.Column(db.Date)
    approved_date = db.Column(db.DateTime)
    ordered_date = db.Column(db.DateTime)
    received_date = db.Column(db.DateTime)
    
    # Additional info
    justification = db.Column(db.Text)  # Why this order is needed
    notes = db.Column(db.Text)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order_info', lazy='dynamic', cascade='all, delete-orphan')
    requested_by = db.relationship('User', foreign_keys=[requested_by_user_id], backref='orders_requested')
    approved_by = db.relationship('User', foreign_keys=[approved_by_user_id], backref='orders_approved')
    
    @property
    def can_be_approved(self):
        """Check if order can be approved"""
        return self.status in ['Submitted']
    
    @property
    def is_pending_approval(self):
        """Check if order is waiting for approval"""
        return self.status == 'Submitted'
    
    def calculate_total(self):
        """Calculate total cost from order items"""
        total = sum(item.total_price for item in self.items if item.total_price)
        self.total_cost = total
        return total
    
    def __repr__(self):
        return f'<Order {self.order_number} - {self.status}>'


class OrderItem(db.Model):
    """Items within an order"""
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    # Can be linked to existing inventory item or be a new item request
    inventory_item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'))
    
    # Item details (for new items or override existing)
    item_name = db.Column(db.String(255), nullable=False)
    catalog_number = db.Column(db.String(128))
    description = db.Column(db.Text)
    
    # Quantities and pricing
    quantity_requested = db.Column(db.Float, nullable=False)
    quantity_received = db.Column(db.Float, default=0)
    unit = db.Column(db.String(32))
    unit_price = db.Column(db.Float)
    total_price = db.Column(db.Float)
    
    # Status
    status = db.Column(db.String(32), default='Pending')  # Pending, Ordered, Received, Cancelled
    
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<OrderItem {self.item_name} x{self.quantity_requested}>'


class StockAlert(db.Model):
    """Automated alerts for inventory management"""
    __tablename__ = 'stock_alerts'
    id = db.Column(db.Integer, primary_key=True)
    
    alert_type = db.Column(db.String(32), nullable=False)  # 'low_stock', 'expired', 'expiring_soon'
    severity = db.Column(db.String(16), default='medium')  # low, medium, high, critical
    
    # Target
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    acknowledged_at = db.Column(db.DateTime)
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime)  # When alert should auto-expire
    
    # Additional data
    extra_data = db.Column(db.Text)  # JSON for additional alert-specific data
    
    # Relationships
    item = db.relationship('InventoryItem', backref='alerts')
    location = db.relationship('Location', backref='alerts')
    acknowledged_by = db.relationship('User', backref='alerts_acknowledged')
    
    def acknowledge(self, user_id):
        """Mark alert as acknowledged"""
        self.is_acknowledged = True
        self.acknowledged_by_user_id = user_id
        self.acknowledged_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<StockAlert {self.alert_type}: {self.title}>'


class SupplierContact(db.Model):
    """Contact persons for suppliers"""
    __tablename__ = 'supplier_contacts'
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    
    # Contact details
    name = db.Column(db.String(128), nullable=False)
    title = db.Column(db.String(64))
    email = db.Column(db.String(128))
    phone = db.Column(db.String(32))
    mobile = db.Column(db.String(32))
    
    # Contact preferences
    is_primary = db.Column(db.Boolean, default=False)
    is_technical_contact = db.Column(db.Boolean, default=False)
    is_sales_contact = db.Column(db.Boolean, default=False)
    
    # Additional info
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = db.relationship('Supplier', backref='contacts')
    
    def __repr__(self):
        return f'<SupplierContact {self.name} ({self.supplier.name if self.supplier else "Unknown"})>'


class UserPermission(db.Model):
    """Fine-grained user permissions"""
    __tablename__ = 'user_permissions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission = db.Column(db.String(64), nullable=False)
    
    # Permission details
    resource_type = db.Column(db.String(32))  # e.g., 'inventory', 'location', 'supplier'
    resource_id = db.Column(db.Integer)  # Specific resource ID (optional)
    
    # Grant details
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    granted_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    expires_at = db.Column(db.DateTime)  # Optional expiration
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    granted_by = db.relationship('User', foreign_keys=[granted_by_user_id], backref='permissions_granted')
    
    def __repr__(self):
        return f'<UserPermission {self.permission} for User {self.user_id}>'


class ShoppingCart(db.Model):
    """Shopping cart for purchase requests"""
    __tablename__ = 'shopping_cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Item details
    item_name = db.Column(db.String(255), nullable=False)
    catalog_number = db.Column(db.String(128))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    
    # Quantities and pricing
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(32))
    estimated_price = db.Column(db.Float)
    
    # Additional info
    notes = db.Column(db.Text)
    project_code = db.Column(db.String(64))
    urgency = db.Column(db.String(16), default='Normal')  # Low, Normal, High, Urgent
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='cart_items')
    supplier = db.relationship('Supplier', backref='cart_items')
    
    def __repr__(self):
        return f'<ShoppingCart {self.item_name} x{self.quantity} by User {self.user_id}>'

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
    status = db.Column(db.String(32), default='Draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    review_notes = db.Column(db.Text)

    user = db.relationship('User', foreign_keys=[user_id])
    supplier = db.relationship('Supplier')
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_user_id])

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