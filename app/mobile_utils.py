"""
Mobile Utility Functions for CellStorage

This module provides utility functions for mobile device support
without affecting existing desktop functionality.
"""

from flask import request, g, session, url_for, render_template
from .mobile_middleware import MobileDetectionMiddleware


def is_mobile_request():
    """Check if the current request is from a mobile device"""
    return getattr(g, 'is_mobile', False)


def is_tablet_request():
    """Check if the current request is from a tablet device"""
    return getattr(g, 'is_tablet', False)


def get_device_info():
    """Get comprehensive device information"""
    return {
        'is_mobile': getattr(g, 'is_mobile', False),
        'is_tablet': getattr(g, 'is_tablet', False),
        'device_type': getattr(g, 'device_type', 'desktop'),
        'user_agent': getattr(g, 'user_agent', ''),
        'view_mode': getattr(g, 'force_view_mode', 'desktop')
    }


def get_mobile_url(endpoint, **values):
    """Generate URL for mobile version of a page"""
    if not endpoint.startswith('mobile.'):
        endpoint = f'mobile.{endpoint}'
    return url_for(endpoint, **values)


def get_desktop_url(endpoint, **values):
    """Generate URL for desktop version of a page"""
    if endpoint.startswith('mobile.'):
        endpoint = endpoint[7:]  # Remove 'mobile.' prefix
    return url_for(endpoint, **values)


def switch_to_mobile_url(current_endpoint=None, **values):
    """Generate URL to switch to mobile view"""
    if not current_endpoint:
        current_endpoint = request.endpoint
    
    # Get the base endpoint name (without mobile. prefix)
    base_endpoint = current_endpoint
    if base_endpoint.startswith('mobile.'):
        base_endpoint = base_endpoint[7:]
    
    # Try to generate mobile URL
    try:
        return get_mobile_url(base_endpoint, **values)
    except:
        # If mobile route doesn't exist, add view_mode parameter
        return url_for(current_endpoint, view_mode='mobile', **values)


def switch_to_desktop_url(current_endpoint=None, **values):
    """Generate URL to switch to desktop view"""
    if not current_endpoint:
        current_endpoint = request.endpoint
    
    # Get the base endpoint name
    base_endpoint = current_endpoint
    if base_endpoint.startswith('mobile.'):
        base_endpoint = base_endpoint[7:]
    
    return url_for(base_endpoint, view_mode='desktop', **values)


def render_mobile_template(template_name, mobile_template_name=None, **context):
    """Render template with mobile/desktop selection"""
    if MobileDetectionMiddleware.should_use_mobile_template():
        if mobile_template_name:
            return render_template(mobile_template_name, **context)
        else:
            # Auto-generate mobile template name
            mobile_template = f"mobile/{template_name}"
            try:
                return render_template(mobile_template, **context)
            except:
                # Fall back to desktop template if mobile template doesn't exist
                pass
    
    return render_template(template_name, **context)


def get_mobile_navigation_items():
    """Get navigation items optimized for mobile"""
    from flask import url_for
    mobile_nav_items = [
        {
            'name': 'Dashboard',
            'url': url_for('mobile.index'),
            'icon': 'fas fa-home'
        },
        {
            'name': 'Inventory',
            'url': url_for('mobile.cryovial_inventory'),
            'icon': 'fas fa-vials'
        },
        {
            'name': 'Locations',
            'url': url_for('mobile.locations_overview'),
            'icon': 'fas fa-map-marker-alt'
        },
        {
            'name': 'Add Vial',
            'url': url_for('mobile.add_cryovial'),
            'icon': 'fas fa-plus'
        }
    ]
    
    return mobile_nav_items


def get_mobile_quick_actions():
    """Get quick action items for mobile interface"""
    from flask import url_for
    quick_actions = [
        {
            'name': 'Quick Search',
            'url': url_for('mobile.cryovial_inventory'),
            'icon': 'fas fa-search',
            'color': 'primary'
        },
        {
            'name': 'Add Vial',
            'url': url_for('mobile.add_cryovial'),
            'icon': 'fas fa-plus',
            'color': 'success'
        },
        {
            'name': 'Print Labels',
            'url': '#',
            'icon': 'fas fa-print',
            'color': 'info',
            'onclick': 'showMobilePrintInterface()'
        },
        {
            'name': 'Locations',
            'url': url_for('mobile.locations_overview'),
            'icon': 'fas fa-map',
            'color': 'warning'
        }
    ]
    
    return quick_actions


def format_mobile_search_result(vial):
    """Format vial data for mobile display"""
    return {
        'id': vial.id,
        'batch_id': vial.batch_id,
        'tag': vial.unique_vial_id_tag,
        'batch_name': getattr(vial.batch, 'name', 'Unknown'),
        'cell_line': getattr(vial.batch, 'cell_line', 'Unknown'),
        'location': f"{vial.box_location.drawer_info.tower_info.name}/{vial.box_location.drawer_info.name}/{vial.box_location.name}" if vial.box_location else 'Unknown',
        'position': f"R{vial.row_in_box}C{vial.col_in_box}" if vial.row_in_box and vial.col_in_box else '',
        'status': vial.status,
        'date_frozen': vial.date_frozen.strftime('%Y-%m-%d') if vial.date_frozen else '',
        'available': vial.status == 'Available'
    }


def format_mobile_batch_summary(batch_results):
    """Format batch results for mobile card display"""
    formatted_batches = []
    
    for result in batch_results:
        batch = result.batch
        formatted_batch = {
            'id': batch.id,
            'name': batch.name,
            'cell_line': result.cell_line,
            'available_count': result.available_quantity,
            'total_count': len(batch.vials) if batch.vials else 0,
            'date_frozen': result.date_frozen,
            'passage_number': result.passage_number,
            'creator': batch.created_by.username if batch.created_by else 'Unknown',
            'fluorescence_tag': result.fluorescence_tag,
            'resistance': result.resistance
        }
        formatted_batches.append(formatted_batch)
    
    return formatted_batches


def get_mobile_table_columns():
    """Get optimized table columns for mobile display"""
    return [
        {'key': 'batch_id', 'label': 'Batch ID', 'width': '15%'},
        {'key': 'batch_name', 'label': 'Name', 'width': '30%'},
        {'key': 'cell_line', 'label': 'Cell Line', 'width': '25%'},
        {'key': 'available', 'label': 'Available', 'width': '15%'},
        {'key': 'actions', 'label': 'Actions', 'width': '15%'}
    ]


def get_mobile_print_data(vial_positions):
    """Format vial positions data for mobile printing interface"""
    mobile_print_jobs = []
    
    for index, position in enumerate(vial_positions):
        job = {
            'index': index,
            'vial_number': index + 1,
            'location': f"{position.tower_name}/{position.drawer_name}/{position.box_name}",
            'position': f"R{position.row}C{position.col}",
            'status': 'ready',
            'print_data': {
                'vial_number': index + 1,
                'location': f"{position.tower_name}/{position.drawer_name}/{position.box_name}",
                'position': f"R{position.row}C{position.col}"
            }
        }
        mobile_print_jobs.append(job)
    
    return mobile_print_jobs


def is_mobile_user_agent(user_agent_string):
    """Check if a user agent string indicates a mobile device"""
    mobile_indicators = [
        'Mobile', 'Android', 'iPhone', 'iPad', 'Windows Phone',
        'BlackBerry', 'Opera Mini', 'IEMobile'
    ]
    
    for indicator in mobile_indicators:
        if indicator.lower() in user_agent_string.lower():
            return True
    
    return False


def get_simplified_location_path(vial):
    """Get simplified location path for mobile display"""
    if not vial.box_location:
        return 'Unknown Location'
    
    tower = vial.box_location.drawer_info.tower_info.name if vial.box_location.drawer_info.tower_info else '?'
    drawer = vial.box_location.drawer_info.name if vial.box_location.drawer_info else '?'
    box = vial.box_location.name if vial.box_location else '?'
    
    return f"{tower}/{drawer}/{box}"


def mobile_pagination_info(page, per_page, total):
    """Generate pagination information for mobile display"""
    start = (page - 1) * per_page + 1
    end = min(page * per_page, total)
    
    return {
        'current_page': page,
        'per_page': per_page,
        'total_items': total,
        'total_pages': (total + per_page - 1) // per_page,
        'start_item': start,
        'end_item': end,
        'has_prev': page > 1,
        'has_next': end < total,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if end < total else None
    }