"""
Mobile-Specific Routes for CellStorage

This module provides mobile-optimized routes that work alongside
existing desktop functionality without interfering with it.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, g
from flask_login import login_required, current_user
from datetime import datetime

from . import db
from .cell_storage.models import CryoVial, VialBatch, CellLine, User, Tower, Drawer, Box
from .cell_storage.forms import CryoVialForm
from .mobile_utils import (
    get_device_info, format_mobile_search_result, format_mobile_batch_summary,
    get_mobile_navigation_items, get_mobile_quick_actions, get_mobile_print_data,
    mobile_pagination_info, render_mobile_template
)
from .shared.utils import get_next_batch_id, get_next_vial_id
from .shared.decorators import admin_required

# Create mobile blueprint
mobile_bp = Blueprint('mobile', __name__, url_prefix='/mobile')


@mobile_bp.before_request
def before_mobile_request():
    """Ensure mobile view mode is set for all mobile routes"""
    g.force_view_mode = 'mobile'


@mobile_bp.route('/')
@login_required
def index():
    """Mobile dashboard - simplified version of main dashboard"""
    # Get recent activity (limited for mobile)
    recent_vials = CryoVial.query.order_by(CryoVial.date_created.desc()).limit(5).all()
    
    # Get summary statistics
    total_vials = CryoVial.query.count()
    available_vials = CryoVial.query.filter_by(status='Available').count()
    total_batches = VialBatch.query.count()
    
    # Format recent vials for mobile display
    formatted_recent = [format_mobile_search_result(vial) for vial in recent_vials]
    
    context = {
        'total_vials': total_vials,
        'available_vials': available_vials,
        'total_batches': total_batches,
        'recent_vials': formatted_recent,
        'navigation_items': get_mobile_navigation_items(),
        'quick_actions': get_mobile_quick_actions(),
        'device_info': get_device_info()
    }
    
    return render_template('mobile/dashboard.html', **context)


@mobile_bp.route('/inventory')
@login_required
def cryovial_inventory():
    """Mobile CryoVial inventory with optimized interface"""
    # Get search parameters
    search_q = request.args.get('q', '').strip()
    search_creator = request.args.get('creator', '').strip()
    search_fluorescence = request.args.get('fluorescence', '').strip()
    search_resistance = request.args.get('resistance', '').strip()
    view_all = request.args.get('view_all', '').lower() == 'true'
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Smaller page size for mobile
    
    # Build search query
    query = VialBatch.query
    
    if search_q:
        query = query.filter(
            db.or_(
                VialBatch.name.contains(search_q),
                VialBatch.cell_line.contains(search_q),
                VialBatch.tag.contains(search_q)
            )
        )
    
    if search_creator:
        creator_user = User.query.filter_by(username=search_creator).first()
        if creator_user:
            query = query.filter_by(created_by_id=creator_user.id)
    
    if search_fluorescence:
        query = query.filter_by(fluorescence_tag=search_fluorescence)
    
    if search_resistance:
        query = query.filter_by(resistance=search_resistance)
    
    # Execute query with pagination
    if search_q or search_creator or search_fluorescence or search_resistance or view_all:
        batches = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
    else:
        # Don't show all results by default on mobile
        batches = None
    
    # Format results for mobile display
    search_results = []
    if batches and batches.items:
        for batch in batches.items:
            # Get available vial count
            available_count = CryoVial.query.filter_by(
                batch_id=batch.id, status='Available'
            ).count()
            
            result = {
                'batch': batch,
                'cell_line': batch.cell_line,
                'available_quantity': available_count,
                'passage_number': batch.passage_number,
                'date_frozen': batch.date_frozen,
                'fluorescence_tag': batch.fluorescence_tag,
                'resistance': batch.resistance,
                'parental_cell_line': batch.parental_cell_line,
                'notes': batch.notes
            }
            search_results.append(result)
    
    # Get filter options
    all_creators = User.query.distinct().all()
    all_fluorescence_tags = db.session.query(VialBatch.fluorescence_tag).distinct().all()
    all_resistances = db.session.query(VialBatch.resistance).distinct().all()
    
    # Clean up filter options
    all_fluorescence_tags = [tag[0] for tag in all_fluorescence_tags if tag[0]]
    all_resistances = [res[0] for res in all_resistances if res[0]]
    
    # Get selected batches for pickup
    selected_ids = session.get('pickup_ids', [])
    selected_batches = []
    if selected_ids:
        selected_vials = CryoVial.query.filter(CryoVial.id.in_(selected_ids)).all()
        batch_counts = {}
        for vial in selected_vials:
            batch_id = vial.batch_id
            if batch_id not in batch_counts:
                batch_counts[batch_id] = {
                    'batch': vial.batch,
                    'count': 0,
                    'date_frozen': vial.batch.date_frozen
                }
            batch_counts[batch_id]['count'] += 1
        selected_batches = list(batch_counts.values())
    
    # Pagination info
    pagination_info = None
    if batches:
        pagination_info = mobile_pagination_info(page, per_page, batches.total)
    
    context = {
        'search_results': search_results,
        'selected_batches': selected_batches,
        'search_q': search_q,
        'search_creator': search_creator,
        'search_fluorescence': search_fluorescence,
        'search_resistance': search_resistance,
        'view_all': view_all,
        'all_creators': all_creators,
        'all_fluorescence_tags': all_fluorescence_tags,
        'all_resistances': all_resistances,
        'pagination': pagination_info,
        'device_info': get_device_info()
    }
    
    return render_template('mobile/cryovial_inventory.html', **context)


@mobile_bp.route('/inventory', methods=['POST'])
@login_required
def cryovial_inventory_post():
    """Handle mobile inventory POST requests (add/remove from pickup list)"""
    selected_ids = session.get('pickup_ids', [])
    
    if 'selected_batches' in request.form:
        # Add batches to pickup list
        batch_ids = request.form.getlist('selected_batches')
        added = 0
        for bid in batch_ids:
            try:
                bid_int = int(bid)
                vials_in_batch = CryoVial.query.filter_by(
                    batch_id=bid_int, status='Available'
                ).all()
                for vial in vials_in_batch:
                    if vial.id not in selected_ids:
                        selected_ids.append(vial.id)
                        added += 1
            except ValueError:
                continue
        
        session['pickup_ids'] = selected_ids
        if added:
            flash(f'{added} vial(s) added to pick-up list.', 'success')
    
    elif 'remove_batches' in request.form:
        # Remove batches from pickup list
        remove_ids = request.form.getlist('remove_batches')
        removed = 0
        for rid in remove_ids:
            try:
                rid_int = int(rid)
                remove_vials = CryoVial.query.filter(
                    CryoVial.id.in_(selected_ids), 
                    CryoVial.batch_id == rid_int
                ).all()
                for v in remove_vials:
                    if v.id in selected_ids:
                        selected_ids.remove(v.id)
                        removed += 1
            except ValueError:
                continue
        
        if removed:
            if selected_ids:
                session['pickup_ids'] = selected_ids
            else:
                session.pop('pickup_ids', None)
            flash(f'{removed} vial(s) removed from pick-up list.', 'success')
    
    # Redirect back to inventory with current search parameters
    redirect_params = {
        'q': request.form.get('q', ''),
        'creator': request.form.get('creator', ''),
        'fluorescence': request.form.get('fluorescence', ''),
        'resistance': request.form.get('resistance', ''),
    }
    
    # Remove empty parameters
    redirect_params = {k: v for k, v in redirect_params.items() if v}
    
    return redirect(url_for('mobile.cryovial_inventory', **redirect_params))


@mobile_bp.route('/search')
@login_required
def quick_search():
    """Mobile quick search interface"""
    query = request.args.get('q', '').strip()
    results = []
    
    if query:
        # Search in vials and batches
        vials = CryoVial.query.join(VialBatch).filter(
            db.or_(
                CryoVial.unique_vial_id_tag.contains(query),
                VialBatch.name.contains(query),
                VialBatch.cell_line.contains(query),
                VialBatch.tag.contains(query)
            )
        ).limit(20).all()
        
        results = [format_mobile_search_result(vial) for vial in vials]
    
    return render_template('mobile/quick_search.html', 
                         query=query, 
                         results=results,
                         device_info=get_device_info())


@mobile_bp.route('/locations')
@login_required
def locations_overview():
    """Mobile locations overview with simplified navigation"""
    towers = Tower.query.all()
    
    # Build simplified location structure for mobile
    location_data = []
    for tower in towers:
        tower_info = {
            'name': tower.name,
            'drawers': []
        }
        
        for drawer in tower.drawers:
            drawer_info = {
                'name': drawer.name,
                'boxes': []
            }
            
            for box in drawer.boxes:
                # Count vials in box
                total_positions = box.rows * box.columns
                occupied_positions = CryoVial.query.filter_by(box_id=box.id).count()
                
                box_info = {
                    'name': box.name,
                    'occupied': occupied_positions,
                    'total': total_positions,
                    'occupancy_rate': (occupied_positions / total_positions * 100) if total_positions > 0 else 0
                }
                drawer_info['boxes'].append(box_info)
            
            tower_info['drawers'].append(drawer_info)
        
        location_data.append(tower_info)
    
    return render_template('mobile/locations_overview.html',
                         location_data=location_data,
                         device_info=get_device_info())


@mobile_bp.route('/print')
@login_required
def print_interface():
    """Mobile printing interface"""
    # Get selected vials for printing
    selected_ids = session.get('pickup_ids', [])
    selected_vials = []
    
    if selected_ids:
        vials = CryoVial.query.filter(CryoVial.id.in_(selected_ids)).all()
        selected_vials = [format_mobile_search_result(vial) for vial in vials]
    
    return render_template('mobile/print_interface.html',
                         selected_vials=selected_vials,
                         device_info=get_device_info())


@mobile_bp.route('/add-vial')
@login_required
def add_cryovial():
    """Mobile add vial interface"""
    form = CryoVialForm()
    
    # Get next IDs for form defaults
    next_batch_id = get_next_batch_id()
    next_vial_id = get_next_vial_id()
    
    return render_template('mobile/add_vial.html',
                         form=form,
                         next_batch_id=next_batch_id,
                         next_vial_id=next_vial_id,
                         device_info=get_device_info())


@mobile_bp.route('/pickup')
@login_required
def pickup_selected_vials():
    """Mobile pickup confirmation"""
    selected_ids = session.get('pickup_ids', [])
    if not selected_ids:
        flash('No vials selected for pickup.', 'warning')
        return redirect(url_for('mobile.cryovial_inventory'))
    
    vials = CryoVial.query.filter(CryoVial.id.in_(selected_ids)).all()
    formatted_vials = [format_mobile_search_result(vial) for vial in vials]
    
    return render_template('mobile/pickup_confirmation.html',
                         vials=formatted_vials,
                         device_info=get_device_info())


@mobile_bp.route('/api/vial/<int:vial_id>/details')
@login_required
def mobile_vial_details(vial_id):
    """API endpoint for mobile vial details"""
    vial = CryoVial.query.get_or_404(vial_id)
    
    details = {
        'id': vial.id,
        'unique_vial_id_tag': vial.unique_vial_id_tag,
        'batch_name': vial.batch.name if vial.batch else 'Unknown',
        'cell_line': vial.batch.cell_line if vial.batch else 'Unknown',
        'location': f"{vial.box.drawer.tower.name}/{vial.box.drawer.name}/{vial.box.name}" if vial.box else 'Unknown',
        'position': f"R{vial.row}C{vial.col}" if vial.row and vial.col else '',
        'passage_number': vial.batch.passage_number if vial.batch else '',
        'date_frozen': vial.date_frozen.strftime('%Y-%m-%d') if vial.date_frozen else '',
        'frozen_by': vial.batch.created_by.username if vial.batch and vial.batch.created_by else 'Unknown',
        'status': vial.status,
        'notes': vial.batch.notes if vial.batch else '',
        'is_admin': current_user.is_admin
    }
    
    return jsonify(details)


@mobile_bp.route('/switch-to-desktop')
def switch_to_desktop():
    """Switch from mobile to desktop view"""
    session['view_mode'] = 'desktop'
    
    # Try to redirect to equivalent desktop page
    referrer = request.referrer
    if referrer and 'mobile' in referrer:
        # Extract the endpoint and redirect to desktop equivalent
        desktop_url = url_for('cell_storage.index')
        if 'inventory' in referrer:
            desktop_url = url_for('cell_storage.cryovial_inventory')
        elif 'locations' in referrer:
            desktop_url = url_for('cell_storage.locations_overview')
        
        return redirect(desktop_url)
    
    return redirect(url_for('cell_storage.index'))


# Error handlers for mobile blueprint
@mobile_bp.errorhandler(404)
def mobile_not_found(error):
    """Mobile 404 error handler"""
    return render_template('mobile/error.html', 
                         error_code=404,
                         error_message="Page not found",
                         device_info=get_device_info()), 404


@mobile_bp.errorhandler(500)
def mobile_internal_error(error):
    """Mobile 500 error handler"""
    return render_template('mobile/error.html',
                         error_code=500,
                         error_message="Internal server error",
                         device_info=get_device_info()), 500