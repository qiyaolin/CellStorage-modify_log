from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_, func
from .. import db
from ..shared.decorators import admin_required
from ..shared.permissions import require_permission
from .models import (InventoryType, InventoryItem, Location, Supplier, 
                    Order, OrderItem, UsageLog, StockAlert, SupplierContact)
from ..cell_storage.models import User
from .forms import (InventoryTypeForm, InventoryItemForm, LocationForm, 
                   SupplierForm, OrderForm, OrderItemForm, UsageForm)
from .services import DataImportExportService

bp = Blueprint('inventory', __name__)

@bp.route('/')
@login_required
def index():
    """Inventory dashboard"""
    # Get summary statistics
    total_items = InventoryItem.query.filter_by(status='Available').count()
    low_stock_items = InventoryItem.query.filter(
        InventoryItem.current_quantity <= InventoryItem.minimum_quantity
    ).count()
    expired_items = InventoryItem.query.filter(
        InventoryItem.expiration_date < date.today()
    ).count()
    pending_orders = Order.query.filter_by(status='Submitted').count()
    
    # Recent activities
    recent_usage = UsageLog.query.order_by(UsageLog.timestamp.desc()).limit(10).all()
    recent_orders = Order.query.order_by(Order.requested_date.desc()).limit(5).all()
    
    # Active alerts
    active_alerts = StockAlert.query.filter_by(is_active=True, is_acknowledged=False).limit(10).all()
    
    return render_template('inventory/dashboard.html',
                         total_items=total_items,
                         low_stock_items=low_stock_items,
                         expired_items=expired_items,
                         pending_orders=pending_orders,
                         recent_usage=recent_usage,
                         recent_orders=recent_orders,
                         active_alerts=active_alerts)

# Inventory Types Management
@bp.route('/types')
@login_required
def inventory_types():
    """List all inventory types"""
    types = InventoryType.query.filter_by(is_active=True).all()
    return render_template('inventory/types.html', types=types)

@bp.route('/types/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_inventory_type():
    """Create new inventory type"""
    form = InventoryTypeForm()
    if form.validate_on_submit():
        inventory_type = InventoryType(
            name=form.name.data,
            description=form.description.data,
            icon=form.icon.data
        )
        
        # Handle custom fields
        custom_fields = {}
        if form.custom_fields.data:
            try:
                custom_fields = eval(form.custom_fields.data)  # Simple eval for demo
            except:
                flash('Invalid custom fields format', 'error')
                return render_template('inventory/type_form.html', form=form)
        
        inventory_type.set_custom_fields(custom_fields)
        
        db.session.add(inventory_type)
        db.session.commit()
        flash(f'Inventory type "{inventory_type.name}" created successfully!', 'success')
        return redirect(url_for('inventory.inventory_types'))
    
    return render_template('inventory/type_form.html', form=form)

# Inventory Items Management
@bp.route('/items')
@login_required
@require_permission('inventory.view')
def inventory_items():
    """List inventory items with search and filters"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    type_id = request.args.get('type_id', type=int)
    location_id = request.args.get('location_id', type=int)
    status = request.args.get('status', '')
    
    # Base query
    query = InventoryItem.query
    
    # Apply filters
    if search:
        query = query.filter(or_(
            InventoryItem.name.contains(search),
            InventoryItem.description.contains(search),
            InventoryItem.catalog_number.contains(search)
        ))
    
    if type_id:
        query = query.filter_by(type_id=type_id)
    
    if location_id:
        query = query.filter_by(location_id=location_id)
    
    if status:
        query = query.filter_by(status=status)
    
    # Special filters
    if request.args.get('low_stock'):
        query = query.filter(InventoryItem.current_quantity <= InventoryItem.minimum_quantity)
    
    if request.args.get('expired'):
        query = query.filter(InventoryItem.expiration_date < date.today())
    
    # Pagination
    items = query.order_by(InventoryItem.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get filter options
    types = InventoryType.query.filter_by(is_active=True).all()
    locations = Location.query.filter_by(is_active=True).all()
    
    return render_template('inventory/items.html', 
                         items=items, 
                         types=types, 
                         locations=locations,
                         search=search,
                         type_id=type_id,
                         location_id=location_id,
                         status=status)

@bp.route('/items/create', methods=['GET', 'POST'])
@login_required
@require_permission('inventory.create')
def create_inventory_item():
    """Create new inventory item"""
    form = InventoryItemForm()
    form.type_id.choices = [(t.id, t.name) for t in InventoryType.query.filter_by(is_active=True).all()]
    form.supplier_id.choices = [(0, 'Select Supplier')] + [(s.id, s.name) for s in Supplier.query.filter_by(is_active=True).all()]
    form.location_id.choices = [(0, 'Select Location')] + [(l.id, l.full_path) for l in Location.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        item = InventoryItem(
            name=form.name.data,
            description=form.description.data,
            catalog_number=form.catalog_number.data,
            barcode=form.barcode.data,
            type_id=form.type_id.data,
            supplier_id=form.supplier_id.data if form.supplier_id.data else None,
            location_id=form.location_id.data if form.location_id.data else None,
            current_quantity=form.current_quantity.data,
            minimum_quantity=form.minimum_quantity.data,
            unit=form.unit.data,
            unit_price=form.unit_price.data,
            currency=form.currency.data,
            expiration_date=form.expiration_date.data,
            received_date=form.received_date.data,
            created_by_user_id=current_user.id
        )
        
        db.session.add(item)
        db.session.commit()
        
        # Log initial quantity
        if item.current_quantity > 0:
            item.update_quantity(0, "Initial stock", current_user.id)
            db.session.commit()
        
        flash(f'Inventory item "{item.name}" created successfully!', 'success')
        return redirect(url_for('inventory.inventory_items'))
    
    return render_template('inventory/item_form.html', form=form)

@bp.route('/items/<int:id>')
@login_required
def item_detail(id):
    """View item details"""
    item = InventoryItem.query.get_or_404(id)
    usage_logs = UsageLog.query.filter_by(item_id=id).order_by(UsageLog.timestamp.desc()).limit(20).all()
    return render_template('inventory/item_detail.html', item=item, usage_logs=usage_logs)

@bp.route('/items/<int:id>/use', methods=['GET', 'POST'])
@login_required
def use_item(id):
    """Record item usage"""
    item = InventoryItem.query.get_or_404(id)
    form = UsageForm()
    
    if form.validate_on_submit():
        quantity_used = form.quantity_used.data
        if quantity_used > item.current_quantity:
            flash('Cannot use more than current quantity!', 'error')
        else:
            item.update_quantity(-quantity_used, form.reason.data, current_user.id)
            db.session.commit()
            flash(f'Used {quantity_used} {item.unit} of {item.name}', 'success')
            return redirect(url_for('inventory.item_detail', id=id))
    
    return render_template('inventory/use_item.html', form=form, item=item)

# Location Management
@bp.route('/locations')
@login_required
@require_permission('location.view')
def locations():
    """Enhanced location management with capacity tracking"""
    locations = Location.query.filter_by(is_active=True).all()
    
    # Build hierarchical structure
    root_locations = [loc for loc in locations if loc.parent_id is None]
    
    # Calculate summary statistics
    total_items = sum(loc.items.count() for loc in locations)
    locations_with_capacity = [loc for loc in locations if loc.max_capacity]
    
    if locations_with_capacity:
        avg_utilization = sum(loc.usage_percentage for loc in locations_with_capacity) / len(locations_with_capacity)
    else:
        avg_utilization = 0
    
    nearly_full_count = sum(1 for loc in locations if loc.is_nearly_full)
    
    return render_template('inventory/locations.html', 
                         locations=locations,
                         root_locations=root_locations,
                         total_items=total_items,
                         avg_utilization=avg_utilization,
                         nearly_full_count=nearly_full_count)

@bp.route('/locations/create', methods=['GET', 'POST'])
@login_required
@require_permission('location.create')
def create_location():
    """Create new location with capacity management"""
    form = LocationForm()
    form.parent_id.choices = [(0, 'No Parent')] + [(l.id, l.full_path) for l in Location.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        location = Location(
            name=form.name.data,
            parent_id=form.parent_id.data if form.parent_id.data else None,
            location_type=form.location_type.data,
            temperature=form.temperature.data,
            description=form.description.data,
            max_capacity=form.max_capacity.data,
            capacity_unit=form.capacity_unit.data,
            current_usage=0  # Start with 0, will be updated automatically
        )
        
        db.session.add(location)
        db.session.commit()
        flash(f'Location "{location.name}" created successfully!', 'success')
        return redirect(url_for('inventory.locations'))
    
    return render_template('inventory/location_form.html', form=form)

@bp.route('/locations/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_location(id):
    """Edit existing location"""
    location = Location.query.get_or_404(id)
    form = LocationForm(obj=location)
    form.parent_id.choices = [(0, 'No Parent')] + [
        (l.id, l.full_path) for l in Location.query.filter_by(is_active=True).all() 
        if l.id != location.id  # Prevent self-referencing
    ]
    
    if form.validate_on_submit():
        location.name = form.name.data
        location.parent_id = form.parent_id.data if form.parent_id.data else None
        location.location_type = form.location_type.data
        location.temperature = form.temperature.data
        location.description = form.description.data
        location.max_capacity = form.max_capacity.data
        location.capacity_unit = form.capacity_unit.data
        
        # Update current usage based on actual items
        location.update_usage()
        
        db.session.commit()
        flash(f'Location "{location.name}" updated successfully!', 'success')
        return redirect(url_for('inventory.locations'))
    
    return render_template('inventory/location_form.html', form=form)

@bp.route('/locations/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_location(id):
    """Delete location (only if empty)"""
    location = Location.query.get_or_404(id)
    
    # Check if location has items
    if location.items.count() > 0:
        return jsonify({'error': 'Cannot delete location with items'}), 400
    
    # Check if location has children
    if location.children:
        return jsonify({'error': 'Cannot delete location with child locations'}), 400
    
    location.is_active = False
    db.session.commit()
    
    return jsonify({'success': True})

# Supplier Management
@bp.route('/suppliers')
@login_required
@require_permission('supplier.view')
def suppliers():
    """Enhanced supplier management with contacts"""
    suppliers = Supplier.query.filter_by(is_active=True).all()
    return render_template('inventory/suppliers_enhanced.html', suppliers=suppliers)

@bp.route('/suppliers/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_supplier():
    """Create new supplier"""
    form = SupplierForm()
    
    if form.validate_on_submit():
        supplier = Supplier(
            name=form.name.data,
            contact_person=form.contact_person.data,
            email=form.email.data,
            phone=form.phone.data,
            website=form.website.data,
            address=form.address.data,
            notes=form.notes.data
        )
        
        db.session.add(supplier)
        db.session.commit()
        flash(f'Supplier "{supplier.name}" created successfully!', 'success')
        return redirect(url_for('inventory.suppliers'))
    
    return render_template('inventory/supplier_form.html', form=form)

@bp.route('/cart')
@login_required
def shopping_cart():
    """Display the user's shopping cart"""
    return render_template('inventory/shopping_cart.html')

# Shopping Cart API
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
            estimated_price=data.get('estimated_price')
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


# Order Management
@bp.route('/orders')
@login_required
def orders():
    """List orders"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    orders = query.order_by(Order.requested_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('inventory/orders.html', orders=orders, status_filter=status_filter)

@bp.route('/orders/create', methods=['GET', 'POST'])
@login_required
def create_order():
    """Create new order"""
    form = OrderForm()
    form.supplier_id.choices = [(0, 'Select Supplier')] + [(s.id, s.name) for s in Supplier.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        # Generate order number
        order_count = Order.query.count() + 1
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{order_count:04d}"
        
        order = Order(
            order_number=order_number,
            supplier_id=form.supplier_id.data if form.supplier_id.data else None,
            needed_by_date=form.needed_by_date.data,
            justification=form.justification.data,
            notes=form.notes.data,
            requested_by_user_id=current_user.id
        )
        
        db.session.add(order)
        db.session.commit()
        flash(f'Order "{order.order_number}" created successfully!', 'success')
        return redirect(url_for('inventory.order_detail', id=order.id))
    
    return render_template('inventory/order_form.html', form=form)

@bp.route('/orders/<int:id>')
@login_required
def order_detail(id):
    """View order details"""
    order = Order.query.get_or_404(id)
    return render_template('inventory/order_detail.html', order=order)

@bp.route('/orders/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_order(id):
    """Approve an order"""
    order = Order.query.get_or_404(id)
    
    if order.can_be_approved:
        order.status = 'Approved'
        order.approved_by_user_id = current_user.id
        order.approved_date = datetime.utcnow()
        
        db.session.commit()
        flash(f'Order {order.order_number} approved successfully!', 'success')
    else:
        flash('Order cannot be approved in its current status', 'error')
    
    return redirect(url_for('inventory.order_detail', id=id))

# API endpoints for search/autocomplete
@bp.route('/api/items/search')
@login_required
def api_search_items():
    """API endpoint for item search"""
    query = request.args.get('q', '')
    items = InventoryItem.query.filter(
        InventoryItem.name.contains(query)
    ).limit(10).all()
    
    return jsonify([{
        'id': item.id,
        'name': item.name,
        'catalog_number': item.catalog_number,
        'current_quantity': item.current_quantity,
        'unit': item.unit
    } for item in items])

@bp.route('/api/alerts/acknowledge/<int:id>', methods=['POST'])
@login_required
def acknowledge_alert(id):
    """Acknowledge an alert"""
    alert = StockAlert.query.get_or_404(id)
    alert.acknowledge(current_user.id)
    db.session.commit()
    
    return jsonify({'success': True})

# Enhanced API Endpoints for Phase 1.2

@bp.route('/items/enhanced')
@login_required
def inventory_items_enhanced():
    """Enhanced inventory items list interface"""
    # Get filter options for dropdowns
    locations = Location.query.filter_by(is_active=True).order_by(Location.name).all()
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    inventory_types = InventoryType.query.filter_by(is_active=True).order_by(InventoryType.name).all()
    users = db.session.query(User).all()  # For responsible person filter
    
    return render_template('inventory/items_enhanced.html',
                         locations=locations,
                         suppliers=suppliers,
                         inventory_types=inventory_types,
                         users=users)

@bp.route('/api/search')
@login_required
def api_search():
    """Advanced search API for DataTables"""
    # DataTables parameters
    draw = request.args.get('draw', type=int)
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 10, type=int)
    
    # Search parameters
    search_value = request.args.get('q', '')
    location_id = request.args.get('location', type=int)
    supplier_id = request.args.get('supplier', type=int)
    type_id = request.args.get('type', type=int)
    status = request.args.get('status', '')
    expiry_from = request.args.get('expiry_from', '')
    expiry_to = request.args.get('expiry_to', '')
    quantity_min = request.args.get('quantity_min', type=float)
    quantity_max = request.args.get('quantity_max', type=float)
    responsible_id = request.args.get('responsible', type=int)
    
    # Base query with joins
    query = db.session.query(InventoryItem).join(
        Supplier, InventoryItem.supplier_id == Supplier.id, isouter=True
    ).join(
        Location, InventoryItem.location_id == Location.id, isouter=True
    ).join(
        User, InventoryItem.responsible_person_id == User.id, isouter=True
    )
    
    # Apply filters
    if search_value:
        search_filter = or_(
            InventoryItem.name.ilike(f'%{search_value}%'),
            InventoryItem.catalog_number.ilike(f'%{search_value}%'),
            InventoryItem.cas_number.ilike(f'%{search_value}%'),
            InventoryItem.description.ilike(f'%{search_value}%'),
            InventoryItem.lot_number.ilike(f'%{search_value}%')
        )
        query = query.filter(search_filter)
    
    if location_id:
        query = query.filter(InventoryItem.location_id == location_id)
    
    if supplier_id:
        query = query.filter(InventoryItem.supplier_id == supplier_id)
    
    if type_id:
        query = query.filter(InventoryItem.type_id == type_id)
    
    if status:
        query = query.filter(InventoryItem.status == status)
    
    if responsible_id:
        query = query.filter(InventoryItem.responsible_person_id == responsible_id)
    
    # Date range filters
    if expiry_from:
        try:
            from_date = datetime.strptime(expiry_from, '%Y-%m-%d').date()
            query = query.filter(InventoryItem.expiration_date >= from_date)
        except ValueError:
            pass
    
    if expiry_to:
        try:
            to_date = datetime.strptime(expiry_to, '%Y-%m-%d').date()
            query = query.filter(InventoryItem.expiration_date <= to_date)
        except ValueError:
            pass
    
    # Quantity range filters
    if quantity_min is not None:
        query = query.filter(InventoryItem.current_quantity >= quantity_min)
    
    if quantity_max is not None:
        query = query.filter(InventoryItem.current_quantity <= quantity_max)
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply sorting
    order_column = request.args.get('order[0][column]', '1')  # Default to name column
    order_dir = request.args.get('order[0][dir]', 'asc')
    
    column_map = {
        '1': InventoryItem.name,
        '2': InventoryItem.catalog_number,
        '3': InventoryItem.cas_number,
        '4': Supplier.name,
        '5': InventoryItem.current_quantity,
        '6': InventoryItem.minimum_quantity,
        '7': Location.name,
        '8': InventoryItem.expiration_date,
        '9': User.username,
        '10': InventoryItem.status
    }
    
    if order_column in column_map:
        order_col = column_map[order_column]
        if order_dir == 'desc':
            order_col = order_col.desc()
        query = query.order_by(order_col)
    else:
        query = query.order_by(InventoryItem.name)
    
    # Apply pagination
    items = query.offset(start).limit(length).all()
    
    # Format response data
    data = []
    for item in items:
        data.append({
            'id': item.id,
            'name': item.name,
            'catalog_number': item.catalog_number or '',
            'cas_number': item.cas_number or '',
            'supplier_name': item.supplier_info.name if item.supplier_info else '',
            'current_quantity': item.current_quantity,
            'minimum_quantity': item.minimum_quantity,
            'unit': item.unit or '',
            'location_path': item.location_info.full_path if item.location_info else '',
            'expiration_date': item.expiration_date.isoformat() if item.expiration_date else None,
            'responsible_person': item.responsible_person.username if item.responsible_person else '',
            'status': item.status,
            'is_low_stock': item.is_low_stock,
            'is_expired': item.is_expired
        })
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_count,
        'recordsFiltered': total_count,
        'data': data
    })

@bp.route('/api/items/<int:item_id>')
@login_required
def api_get_item(item_id):
    """Get single item data for editing"""
    item = InventoryItem.query.get_or_404(item_id)
    
    return jsonify({
        'id': item.id,
        'name': item.name,
        'catalog_number': item.catalog_number,
        'cas_number': item.cas_number,
        'current_quantity': item.current_quantity,
        'minimum_quantity': item.minimum_quantity,
        'unit': item.unit,
        'location_id': item.location_id,
        'supplier_id': item.supplier_id,
        'responsible_person_id': item.responsible_person_id,
        'expiration_date': item.expiration_date.isoformat() if item.expiration_date else None,
        'description': item.description,
        'lot_number': item.lot_number,
        'storage_conditions': item.storage_conditions
    })

@bp.route('/api/items/<int:item_id>', methods=['PUT'])
@login_required
def api_update_item(item_id):
    """Quick update item via API"""
    item = InventoryItem.query.get_or_404(item_id)
    data = request.get_json()
    
    try:
        # Update allowed fields
        if 'current_quantity' in data:
            old_quantity = item.current_quantity
            item.current_quantity = float(data['current_quantity'])
            
            # Log the change
            log = UsageLog(
                item_id=item.id,
                user_id=current_user.id,
                quantity_change=item.current_quantity - old_quantity,
                quantity_before=old_quantity,
                quantity_after=item.current_quantity,
                reason='Quick Edit Update'
            )
            db.session.add(log)
        
        if 'minimum_quantity' in data:
            item.minimum_quantity = float(data['minimum_quantity'])
        
        if 'location_id' in data and data['location_id']:
            item.location_id = int(data['location_id'])
        
        if 'expiration_date' in data and data['expiration_date']:
            item.expiration_date = datetime.strptime(data['expiration_date'], '%Y-%m-%d').date()
        
        # Update status based on quantity
        if item.current_quantity <= 0:
            item.status = 'Used Up'
        elif item.is_low_stock:
            item.status = 'Low Stock'
        elif item.is_expired:
            item.status = 'Expired'
        else:
            item.status = 'Available'
        
        item.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Item updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/items/import', methods=['POST'])
@login_required
@require_permission('inventory.create')
def api_import_items():
    """Import items from a CSV or Excel file"""
    if 'file' not in request.files:
        return jsonify({'errors': ['No file part']}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'errors': ['No selected file']}), 400

    try:
        # Use a helper service to process the file
        result = DataImportExportService.import_inventory_from_file(file, current_user.id)
        
        if result['success']:
            return jsonify({'message': f'{result["imported_count"]} items imported successfully.'})
        else:
            return jsonify({'errors': result['errors']}), 400
            
    except Exception as e:
        return jsonify({'errors': [str(e)]}), 500

@bp.route('/api/items/template')
@login_required
def api_download_template():
    """Download a template for importing items"""
    try:
        output = DataImportExportService.export_template()
        
        from flask import make_response
        response = make_response(output.read())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = 'attachment; filename=inventory_template.xlsx'
        
        return response
        
    except Exception as e:
        flash(f'Error generating template: {str(e)}', 'error')
        return redirect(url_for('inventory.inventory_items_enhanced'))

@bp.route('/api/items/bulk-delete', methods=['POST'])
@login_required
@require_permission('inventory.delete')
def api_bulk_delete_items():
    """Delete multiple items in bulk"""
    data = request.get_json()
    item_ids = data.get('ids', [])
    
    if not item_ids:
        return jsonify({'success': False, 'error': 'No item IDs provided'}), 400
    
    try:
        # Perform bulk deletion
        num_deleted = InventoryItem.query.filter(InventoryItem.id.in_(item_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{num_deleted} items deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/items/<int:item_id>/adjust', methods=['POST'])
@login_required
def api_adjust_quantity(item_id):
    """Adjust item quantity with logging"""
    item = InventoryItem.query.get_or_404(item_id)
    data = request.get_json()
    
    try:
        adjustment_type = data.get('adjustment_type')
        quantity = float(data.get('quantity', 0))
        reason = data.get('reason', 'Manual Adjustment')
        notes = data.get('notes', '')
        
        old_quantity = item.current_quantity
        
        if adjustment_type == 'add':
            item.current_quantity += quantity
            quantity_change = quantity
        elif adjustment_type == 'remove':
            item.current_quantity -= quantity
            quantity_change = -quantity
        elif adjustment_type == 'set':
            quantity_change = quantity - item.current_quantity
            item.current_quantity = quantity
        else:
            return jsonify({'success': False, 'error': 'Invalid adjustment type'}), 400
        
        # Ensure quantity doesn't go negative
        if item.current_quantity < 0:
            item.current_quantity = 0
            quantity_change = -old_quantity
        
        # Update status
        if item.current_quantity <= 0:
            item.status = 'Used Up'
        elif item.is_low_stock:
            item.status = 'Low Stock'
        else:
            item.status = 'Available'
        
        # Log the adjustment
        log = UsageLog(
            item_id=item.id,
            user_id=current_user.id,
            quantity_change=quantity_change,
            quantity_before=old_quantity,
            quantity_after=item.current_quantity,
            reason=reason,
            notes=notes
        )
        db.session.add(log)
        
        item.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Quantity adjusted successfully',
            'new_quantity': item.current_quantity,
            'change': quantity_change
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/export')
@login_required
def export_items():
    """Export inventory items to Excel"""
    try:
        import pandas as pd
        from io import BytesIO
        
        # Query all items with related data
        items = db.session.query(
            InventoryItem.name,
            InventoryItem.catalog_number,
            InventoryItem.cas_number,
            InventoryItem.lot_number,
            InventoryItem.current_quantity,
            InventoryItem.minimum_quantity,
            InventoryItem.unit,
            InventoryItem.expiration_date,
            InventoryItem.status,
            InventoryItem.storage_conditions,
            Supplier.name.label('supplier_name'),
            Location.full_path.label('location_path'),
            User.username.label('responsible_person')
        ).outerjoin(Supplier).outerjoin(Location).outerjoin(
            User, InventoryItem.responsible_person_id == User.id
        ).all()
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'Name': item.name,
            'Catalog Number': item.catalog_number,
            'CAS Number': item.cas_number,
            'Lot Number': item.lot_number,
            'Current Quantity': item.current_quantity,
            'Minimum Quantity': item.minimum_quantity,
            'Unit': item.unit,
            'Expiration Date': item.expiration_date,
            'Status': item.status,
            'Storage Conditions': item.storage_conditions,
            'Supplier': item.supplier_name,
            'Location': item.location_path,
            'Responsible Person': item.responsible_person
        } for item in items])
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Inventory Items')
        
        output.seek(0)
        
        from flask import make_response
        response = make_response(output.read())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=inventory_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response
        
    except ImportError:
        flash('Excel export requires pandas and openpyxl libraries', 'error')
        return redirect(url_for('inventory.inventory_items_enhanced'))
    except Exception as e:
        flash(f'Export error: {str(e)}', 'error')
        return redirect(url_for('inventory.inventory_items_enhanced'))

# Location API endpoints
@bp.route('/api/locations/<int:location_id>')
@login_required
def api_get_location(location_id):
    """Get location details with capacity and items"""
    location = Location.query.get_or_404(location_id)
    
    # Get recent items in this location
    recent_items = location.items.order_by(InventoryItem.updated_at.desc()).limit(10).all()
    
    return jsonify({
        'id': location.id,
        'name': location.name,
        'location_type': location.location_type,
        'temperature': location.temperature,
        'description': location.description,
        'full_path': location.full_path,
        'max_capacity': location.max_capacity,
        'capacity_unit': location.capacity_unit,
        'current_usage': location.current_usage,
        'usage_percentage': location.usage_percentage,
        'is_full': location.is_full,
        'is_nearly_full': location.is_nearly_full,
        'items': [{
            'id': item.id,
            'name': item.name,
            'current_quantity': item.current_quantity,
            'unit': item.unit,
            'status': item.status
        } for item in recent_items]
    })

@bp.route('/api/locations/<int:location_id>/capacity')
@login_required
def api_location_capacity(location_id):
    """Get location capacity information"""
    location = Location.query.get_or_404(location_id)
    
    return jsonify({
        'location_id': location.id,
        'name': location.name,
        'max_capacity': location.max_capacity,
        'current_usage': location.current_usage,
        'capacity_unit': location.capacity_unit,
        'usage_percentage': location.usage_percentage,
        'available_space': location.max_capacity - location.current_usage if location.max_capacity else None,
        'is_full': location.is_full,
        'is_nearly_full': location.is_nearly_full
    })

@bp.route('/api/locations/<int:location_id>/update-usage', methods=['POST'])
@login_required
@admin_required
def api_update_location_usage(location_id):
    """Manually update location usage count"""
    location = Location.query.get_or_404(location_id)
    
    # Recalculate usage based on actual items
    location.update_usage()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'current_usage': location.current_usage,
        'usage_percentage': location.usage_percentage
    })

# Supplier Contact Management API Endpoints

@bp.route('/api/suppliers', methods=['POST'])
@login_required
@require_permission('supplier.create')
def api_create_supplier():
    """Create new supplier via API"""
    data = request.get_json()
    
    try:
        supplier = Supplier(
            name=data['name'],
            website=data.get('website'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            notes=data.get('notes')
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Supplier created successfully',
            'supplier_id': supplier.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/contacts', methods=['POST'])
@login_required
@require_permission('supplier.manage_contacts')
def api_create_contact():
    """Create new supplier contact"""
    data = request.get_json()
    
    try:
        # If setting as primary, unset other primary contacts for this supplier
        if data.get('is_primary'):
            existing_primary = SupplierContact.query.filter_by(
                supplier_id=data['supplier_id'],
                is_primary=True
            ).first()
            if existing_primary:
                existing_primary.is_primary = False
        
        contact = SupplierContact(
            supplier_id=data['supplier_id'],
            name=data['name'],
            title=data.get('title'),
            email=data.get('email'),
            phone=data.get('phone'),
            mobile=data.get('mobile'),
            is_primary=data.get('is_primary', False),
            is_technical_contact=data.get('is_technical_contact', False),
            is_sales_contact=data.get('is_sales_contact', False),
            notes=data.get('notes')
        )
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact created successfully',
            'contact_id': contact.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/contacts/<int:contact_id>')
@login_required
@require_permission('supplier.view')
def api_get_contact(contact_id):
    """Get contact details"""
    contact = SupplierContact.query.get_or_404(contact_id)
    
    return jsonify({
        'id': contact.id,
        'supplier_id': contact.supplier_id,
        'name': contact.name,
        'title': contact.title,
        'email': contact.email,
        'phone': contact.phone,
        'mobile': contact.mobile,
        'is_primary': contact.is_primary,
        'is_technical_contact': contact.is_technical_contact,
        'is_sales_contact': contact.is_sales_contact,
        'notes': contact.notes,
        'created_at': contact.created_at.isoformat() if contact.created_at else None
    })

@bp.route('/api/contacts/<int:contact_id>', methods=['PUT'])
@login_required
@require_permission('supplier.manage_contacts')
def api_update_contact(contact_id):
    """Update supplier contact"""
    contact = SupplierContact.query.get_or_404(contact_id)
    data = request.get_json()
    
    try:
        # If setting as primary, unset other primary contacts for this supplier
        if data.get('is_primary') and not contact.is_primary:
            existing_primary = SupplierContact.query.filter_by(
                supplier_id=contact.supplier_id,
                is_primary=True
            ).first()
            if existing_primary:
                existing_primary.is_primary = False
        
        # Update contact fields
        contact.name = data.get('name', contact.name)
        contact.title = data.get('title', contact.title)
        contact.email = data.get('email', contact.email)
        contact.phone = data.get('phone', contact.phone)
        contact.mobile = data.get('mobile', contact.mobile)
        contact.is_primary = data.get('is_primary', contact.is_primary)
        contact.is_technical_contact = data.get('is_technical_contact', contact.is_technical_contact)
        contact.is_sales_contact = data.get('is_sales_contact', contact.is_sales_contact)
        contact.notes = data.get('notes', contact.notes)
        contact.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
@login_required
@require_permission('supplier.manage_contacts')
def api_delete_contact(contact_id):
    """Delete supplier contact"""
    contact = SupplierContact.query.get_or_404(contact_id)
    
    try:
        db.session.delete(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/suppliers/<int:supplier_id>/contacts')
@login_required
@require_permission('supplier.view')
def supplier_contacts(supplier_id):
    """List contacts for a specific supplier"""
    supplier = Supplier.query.get_or_404(supplier_id)
    contacts = SupplierContact.query.filter_by(supplier_id=supplier_id).order_by(
        SupplierContact.is_primary.desc(),
        SupplierContact.name
    ).all()
    
    return render_template('inventory/supplier_contacts.html', 
                         supplier=supplier, 
                         contacts=contacts)

@bp.route('/suppliers/export')
@login_required
@require_permission('data.export')
def export_suppliers():
    """Export suppliers and contacts to Excel"""
    try:
        import pandas as pd
        from io import BytesIO
        
        # Query suppliers with contact information
        suppliers_data = []
        for supplier in Supplier.query.filter_by(is_active=True).all():
            base_data = {
                'Supplier Name': supplier.name,
                'Website': supplier.website,
                'Email': supplier.email,
                'Phone': supplier.phone,
                'Address': supplier.address,
                'Notes': supplier.notes,
                'Items Count': supplier.items.count(),
                'Orders Count': supplier.orders.count(),
                'Total Contacts': len(supplier.contacts)
            }
            
            if supplier.contacts:
                for contact in supplier.contacts:
                    contact_data = base_data.copy()
                    contact_data.update({
                        'Contact Name': contact.name,
                        'Contact Title': contact.title,
                        'Contact Email': contact.email,
                        'Contact Phone': contact.phone,
                        'Contact Mobile': contact.mobile,
                        'Is Primary': contact.is_primary,
                        'Is Technical': contact.is_technical_contact,
                        'Is Sales': contact.is_sales_contact,
                        'Contact Notes': contact.notes
                    })
                    suppliers_data.append(contact_data)
            else:
                # Add supplier without contacts
                suppliers_data.append(base_data)
        
        # Create DataFrame
        df = pd.DataFrame(suppliers_data)
        
        # Create Excel file with multiple sheets
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Suppliers & Contacts')
            
            # Create summary sheet
            summary_data = []
            for supplier in Supplier.query.filter_by(is_active=True).all():
                summary_data.append({
                    'Supplier': supplier.name,
                    'Contacts': len(supplier.contacts),
                    'Primary Contact': next((c.name for c in supplier.contacts if c.is_primary), 'None'),
                    'Items': supplier.items.count(),
                    'Orders': supplier.orders.count(),
                    'Last Order': supplier.orders.order_by(Order.requested_date.desc()).first().requested_date.strftime('%Y-%m-%d') if supplier.orders.first() else 'Never'
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, index=False, sheet_name='Summary')
        
        output.seek(0)
        
        from flask import make_response
        response = make_response(output.read())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=suppliers_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response
        
    except ImportError:
        flash('Excel export requires pandas and openpyxl libraries', 'error')
        return redirect(url_for('inventory.suppliers'))
    except Exception as e:
        flash(f'Export error: {str(e)}', 'error')
        return redirect(url_for('inventory.suppliers'))