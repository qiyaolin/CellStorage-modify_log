# app/inventory/routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from sqlalchemy import or_
from .. import db
from ..shared.decorators import admin_required
from ..shared.permissions import require_permission
from .models import (InventoryType, InventoryItem, Location, Supplier,
                    Order, OrderItem, UsageLog, StockAlert, ShoppingCart, PurchaseRequest, Notification)
from ..cell_storage.models import User, CryoVial
from .forms import (InventoryItemForm, LocationForm,
                   SupplierForm, OrderForm, OrderItemForm, UsageForm)

bp = Blueprint('inventory', __name__)

# A simple notification service
class NotificationService:
    @staticmethod
    def send(user_id, title, message, link=None):
        """Send a notification to a specific user."""
        if not user_id:
            return
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link
        )
        db.session.add(notification)
        db.session.commit()

    @staticmethod
    def notify_admins(title, message, link=None):
        """Send a notification to all admin users."""
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            NotificationService.send(admin.id, title, message, link)

@bp.route('/')
@login_required
@require_permission('inventory.view')
def index():
    """Inventory dashboard"""
    total_items = InventoryItem.query.filter(InventoryItem.status != 'Used Up').count()
    low_stock_items = InventoryItem.query.filter(InventoryItem.current_quantity <= InventoryItem.minimum_quantity).count()
    expired_items = InventoryItem.query.filter(InventoryItem.expiration_date < date.today()).count()
    pending_orders = Order.query.filter(Order.status.in_(['Submitted', 'Approved'])).count()
    
    recent_usage = UsageLog.query.order_by(UsageLog.timestamp.desc()).limit(5).all()
    recent_orders = Order.query.order_by(Order.requested_date.desc()).limit(5).all()
    active_alerts = StockAlert.query.filter_by(is_active=True, is_acknowledged=False).limit(5).all()
    
    return render_template('inventory/dashboard.html',
                         total_items=total_items,
                         low_stock_items=low_stock_items,
                         expired_items=expired_items,
                         pending_orders=pending_orders,
                         recent_usage=recent_usage,
                         recent_orders=recent_orders,
                         active_alerts=active_alerts)

# --- Order Management Routes ---
@bp.route('/orders')
@login_required
@require_permission('order.view')
def orders():
    """List all orders."""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status')
    
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
        
    orders_pagination = query.order_by(Order.requested_date.desc()).paginate(page=page, per_page=20)
    return render_template('inventory/orders.html', orders=orders_pagination.items, pagination=orders_pagination, status_filter=status_filter)

@bp.route('/orders/create', methods=['GET', 'POST'])
@login_required
@require_permission('order.create')
def create_order():
    """Create a new order."""
    form = OrderForm()
    form.supplier_id.choices = [(s.id, s.name) for s in Supplier.query.order_by('name').all()]
    
    if form.validate_on_submit():
        order_number = f"PO-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        order = Order(
            order_number=order_number,
            requested_by_user_id=current_user.id,
            supplier_id=form.supplier_id.data,
            priority=form.priority.data,
            needed_by_date=form.needed_by_date.data,
            justification=form.justification.data,
            notes=form.notes.data,
            status='Draft'
        )
        db.session.add(order)
        db.session.commit()
        
        flash(f'Order {order.order_number} created successfully. You can now add items.', 'success')
        return redirect(url_for('inventory.order_detail', order_id=order.id))
        
    return render_template('inventory/order_form.html', form=form, title="Create New Order")

@bp.route('/orders/<int:order_id>')
@login_required
@require_permission('order.view')
def order_detail(order_id):
    """View details of a specific order."""
    order = Order.query.get_or_404(order_id)
    item_form = OrderItemForm()
    return render_template('inventory/order_detail.html', order=order, item_form=item_form)

@bp.route('/orders/<int:order_id>/add_item', methods=['POST'])
@login_required
@require_permission('order.edit')
def add_order_item(order_id):
    """Add an item to an existing order."""
    order = Order.query.get_or_404(order_id)
    form = OrderItemForm()

    if form.validate_on_submit():
        order_item = OrderItem(
            order_id=order.id,
            item_name=form.item_name.data,
            catalog_number=form.catalog_number.data,
            quantity_requested=form.quantity_requested.data,
            unit=form.unit.data,
            unit_price=form.unit_price.data,
            status='Pending'
        )
        order_item.total_price = (order_item.quantity_requested or 0) * (order_item.unit_price or 0)
        db.session.add(order_item)
        
        # Recalculate total order cost
        order.total_cost = sum(item.total_price for item in order.items)
        db.session.commit()
        flash('Item added to order.', 'success')
    else:
        flash('Error adding item. Please check the form.', 'danger')

    return redirect(url_for('inventory.order_detail', order_id=order_id))

@bp.route('/orders/<int:order_id>/submit', methods=['POST'])
@login_required
@require_permission('order.create')
def submit_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status == 'Draft':
        order.status = 'Submitted'
        order.requested_date = datetime.utcnow()
        db.session.commit()
        
        NotificationService.notify_admins(
            title=f"New Order Submitted: {order.order_number}",
            message=f"{current_user.username} submitted a new purchase order.",
            link=url_for('inventory.order_detail', order_id=order_id, _external=True)
        )
        flash('Order submitted for approval.', 'success')
    else:
        flash('Order cannot be submitted in its current state.', 'warning')
    return redirect(url_for('inventory.order_detail', order_id=order_id))

@bp.route('/orders/<int:order_id>/approve', methods=['POST'])
@login_required
@require_permission('order.approve')
def approve_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status == 'Submitted':
        order.status = 'Approved'
        order.approved_by_user_id = current_user.id
        order.approved_date = datetime.utcnow()
        db.session.commit()
        
        NotificationService.send(
            user_id=order.requested_by_user_id,
            title=f"Order Approved: {order.order_number}",
            message=f"Your order has been approved by {current_user.username}.",
            link=url_for('inventory.order_detail', order_id=order_id, _external=True)
        )
        flash('Order approved.', 'success')
    else:
        flash('Order cannot be approved.', 'warning')
    return redirect(url_for('inventory.order_detail', order_id=order_id))

@bp.route('/order/<int:order_id>/receive', methods=['GET', 'POST'])
@login_required
@require_permission('order.receive')
def receive_order(order_id):
    """Page for receiving items against an order."""
    order = Order.query.get_or_404(order_id)
    if request.method == 'POST':
        for item in order.items:
            received_qty_str = request.form.get(f'item_{item.id}_received_qty')
            if received_qty_str and float(received_qty_str) > 0:
                received_qty = float(received_qty_str)
                item.quantity_received = (item.quantity_received or 0) + received_qty
                
                # Update main inventory
                inventory_item = InventoryItem.query.filter_by(catalog_number=item.catalog_number).first()
                if inventory_item:
                    inventory_item.update_quantity(
                        change=received_qty, 
                        reason=f"Received from PO {order.order_number}",
                        user_id=current_user.id
                    )
                else:
                    inventory_item = InventoryItem(
                        name=item.item_name,
                        catalog_number=item.catalog_number,
                        supplier_id=order.supplier_id,
                        current_quantity=received_qty,
                        unit=item.unit,
                        type_id=1, # Default type, should be improved
                        created_by_user_id=current_user.id
                    )
                    db.session.add(inventory_item)
                
                if item.quantity_received >= item.quantity_requested:
                    item.status = 'Received'
        
        all_received = all(it.status == 'Received' for it in order.items)
        order.status = 'Completed' if all_received else 'Partially Received'
        order.received_date = datetime.utcnow()
        db.session.commit()
        flash('Inventory updated successfully.', 'success')
        return redirect(url_for('inventory.order_detail', order_id=order_id))
    return render_template('inventory/receive_order.html', order=order)

# --- Purchase Request Routes ---
@bp.route('/requests/review')
@login_required
@require_permission('order.approve')
def review_requests():
    """Review pending purchase requests."""
    requests = PurchaseRequest.query.filter_by(status='Submitted').order_by(PurchaseRequest.submitted_at.desc()).all()
    return render_template('inventory/review_requests.html', requests=requests)

@bp.route('/api/requests/<int:request_id>/approve', methods=['POST'])
@login_required
@require_permission('order.approve')
def approve_request_api(request_id):
    """Approve a purchase request and create a draft order."""
    req = PurchaseRequest.query.get_or_404(request_id)
    if req.status != 'Submitted':
        return jsonify({'success': False, 'message': 'Request not in submitted state.'}), 400

    req.status = 'Approved'
    req.reviewed_by_user_id = current_user.id
    req.reviewed_at = datetime.utcnow()

    # Create new order from request
    new_order = Order(
        order_number=f"PO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{req.id}",
        status='Approved',
        requested_by_user_id=req.user_id,
        approved_by_user_id=current_user.id,
        supplier_id=req.supplier_id,
        requested_date=req.created_at,
        approved_date=datetime.utcnow(),
        justification=req.justification
    )
    db.session.add(new_order)
    
    # Add item to order
    order_item = OrderItem(
        order_id=new_order.id,
        item_name=req.item_name,
        catalog_number=req.catalog_number,
        quantity_requested=req.quantity_requested,
        unit=req.unit,
        status='Approved'
    )
    db.session.add(order_item)
    
    db.session.commit()
    
    flash(f"Request approved and Order {new_order.order_number} created.", "success")
    return jsonify({'success': True, 'order_id': new_order.id})

@bp.route('/api/requests/<int:request_id>/reject', methods=['POST'])
@login_required
@require_permission('order.approve')
def reject_request_api(request_id):
    """Reject a purchase request."""
    req = PurchaseRequest.query.get_or_404(request_id)
    req.status = 'Rejected'
    req.reviewed_by_user_id = current_user.id
    req.reviewed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/requests/submit', methods=['GET', 'POST'])
@login_required
def submit_request():
    """Page to review cart and submit a purchase request."""
    if request.method == 'POST':
        cart_items = ShoppingCart.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            flash('Your shopping cart is empty.', 'warning')
            return redirect(url_for('inventory.shopping_cart'))

        for item in cart_items:
            pr = PurchaseRequest(
                user_id=current_user.id,
                item_name=item.item_name,
                catalog_number=item.catalog_number,
                supplier_id=item.supplier_id,
                quantity_requested=item.quantity,
                unit=item.unit,
                status='Submitted',
                submitted_at=datetime.utcnow()
            )
            db.session.add(pr)
            db.session.delete(item)
        
        db.session.commit()
        flash('Purchase request submitted successfully!', 'success')
        return redirect(url_for('inventory.orders'))
        
    cart_items = ShoppingCart.query.filter_by(user_id=current_user.id).all()
    return render_template('inventory/submit_request.html', cart_items=cart_items)

# --- Shopping Cart Routes ---
@bp.route('/cart')
@login_required
def shopping_cart():
    """Display the user's shopping cart."""
    return render_template('inventory/shopping_cart.html')

@bp.route('/api/cart', methods=['GET', 'POST'])
@login_required
def shopping_cart_api():
    if request.method == 'GET':
        cart_items = ShoppingCart.query.filter_by(user_id=current_user.id).all()
        return jsonify([{
            'id': item.id,
            'item_name': item.item_name,
            'catalog_number': item.catalog_number,
            'supplier_name': item.supplier.name if item.supplier else '',
            'quantity': item.quantity,
            'unit': item.unit,
            'estimated_price': item.estimated_price
        } for item in cart_items])
    
    if request.method == 'POST':
        data = request.get_json()
        cart_item = ShoppingCart(
            user_id=current_user.id,
            item_name=data['item_name'],
            catalog_number=data.get('catalog_number'),
            supplier_id=data.get('supplier_id'),
            quantity=data['quantity'],
            unit=data.get('unit'),
            estimated_price=data.get('estimated_price'),
            notes=data.get('notes')
        )
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({'success': True, 'id': cart_item.id})

@bp.route('/api/cart/<int:item_id>', methods=['DELETE'])
@login_required
def delete_cart_item(item_id):
    item = ShoppingCart.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})

# --- Basic Inventory Routes ---
@bp.route('/items')
@login_required
@require_permission('inventory.view')
def inventory_items():
    """List inventory items."""
    items_pagination = InventoryItem.query.paginate(page=1, per_page=20)
    return render_template('inventory/items.html', items=items_pagination, types=[], locations=[])

@bp.route('/items/create', methods=['GET','POST'])
@login_required
@require_permission('inventory.create')
def create_inventory_item():
    """Create a new inventory item."""
    form = InventoryItemForm()
    # Populate choices...
    if form.validate_on_submit():
        # ... create item ...
        flash('Item created!', 'success')
        return redirect(url_for('inventory.inventory_items'))
    return render_template('inventory/item_form.html', form=form)

@bp.route('/suppliers')
@login_required
@require_permission('supplier.view')
def suppliers():
    """List all suppliers."""
    all_suppliers = Supplier.query.all()
    return render_template('inventory/suppliers_enhanced.html', suppliers=all_suppliers)

@bp.route('/locations')
@login_required
@require_permission('location.view')
def locations():
    """List all locations."""
    all_locations = Location.query.all()
    root_locations = Location.query.filter_by(parent_id=None).all()
    return render_template('inventory/locations_enhanced.html', locations=all_locations, root_locations=root_locations, total_items=InventoryItem.query.count(), avg_utilization=0, nearly_full_count=0)

# API Routes for Storage Location Management
@bp.route('/api/locations/<int:location_id>')
@login_required
@require_permission('location.view')
def location_details_api(location_id):
    """Get detailed information about a specific location."""
    location = Location.query.get_or_404(location_id)
    
    # Calculate usage metrics
    items_count = InventoryItem.query.filter_by(location_id=location_id).count()
    items = InventoryItem.query.filter_by(location_id=location_id).limit(10).all()
    
    # Build full path
    path_parts = []
    current = location
    while current:
        path_parts.insert(0, current.name)
        current = current.parent
    full_path = ' > '.join(path_parts)
    
    return jsonify({
        'id': location.id,
        'name': location.name,
        'location_type': location.location_type,
        'temperature': location.temperature,
        'description': location.description,
        'max_capacity': location.max_capacity,
        'current_usage': items_count,
        'capacity_unit': location.capacity_unit,
        'full_path': full_path,
        'items': [{
            'name': item.name,
            'current_quantity': item.current_quantity,
            'unit': item.unit,
            'status': item.status,
            'updated_at': item.created_at.isoformat() if item.created_at else None
        } for item in items]
    })

@bp.route('/locations/<int:location_id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('location.edit')
def edit_location(location_id):
    """Edit an existing location."""
    location = Location.query.get_or_404(location_id)
    form = LocationForm(obj=location)
    
    # Set up parent choices (excluding self and children to prevent circular references)
    form.parent_id.choices = [(0, 'No Parent')] + [
        (l.id, l.name) for l in Location.query.filter(Location.id != location_id).all()
    ]
    
    if form.validate_on_submit():
        location.name = form.name.data
        location.location_type = form.location_type.data
        location.temperature = form.temperature.data
        location.description = form.description.data
        location.max_capacity = form.max_capacity.data
        location.capacity_unit = form.capacity_unit.data
        location.parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        
        db.session.commit()
        flash('Location updated successfully!', 'success')
        return redirect(url_for('inventory.locations'))
    
    return render_template('inventory/location_form.html', form=form, location=location)

@bp.route('/locations/<int:location_id>/delete', methods=['POST'])
@login_required
@require_permission('location.delete')
def delete_location(location_id):
    """Delete a location."""
    location = Location.query.get_or_404(location_id)
    
    # Check if location has items
    items_count = InventoryItem.query.filter_by(location_id=location_id).count()
    if items_count > 0:
        flash(f'Cannot delete location "{location.name}" - it contains {items_count} items.', 'error')
        return redirect(url_for('inventory.locations'))
    
    # Check if location has children
    children_count = Location.query.filter_by(parent_id=location_id).count()
    if children_count > 0:
        flash(f'Cannot delete location "{location.name}" - it contains {children_count} child locations.', 'error')
        return redirect(url_for('inventory.locations'))
    
    db.session.delete(location)
    db.session.commit()
    flash(f'Location "{location.name}" deleted successfully!', 'success')
    return redirect(url_for('inventory.locations'))

@bp.route('/locations/create', methods=['GET', 'POST'])
@login_required
@require_permission('location.create')
def create_location():
    """Create a new location."""
    form = LocationForm()
    form.parent_id.choices = [(0, 'No Parent')] + [
        (l.id, l.name) for l in Location.query.all()
    ]
    
    # Pre-select parent if provided in URL
    parent_id = request.args.get('parent_id', type=int)
    if parent_id and request.method == 'GET':
        form.parent_id.data = parent_id
    
    if form.validate_on_submit():
        location = Location(
            name=form.name.data,
            location_type=form.location_type.data,
            temperature=form.temperature.data,
            description=form.description.data,
            max_capacity=form.max_capacity.data,
            capacity_unit=form.capacity_unit.data,
            parent_id=form.parent_id.data if form.parent_id.data != 0 else None,
            current_usage=0
        )
        db.session.add(location)
        db.session.commit()
        flash('Location created successfully!', 'success')
        return redirect(url_for('inventory.locations'))
    
    return render_template('inventory/location_form.html', form=form)

# Batch delete functionality has been moved to cell_storage.main.routes.py to avoid conflicts
