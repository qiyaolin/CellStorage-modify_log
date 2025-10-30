from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView, expose
from flask_admin.actions import action
from flask import flash, redirect, url_for, render_template_string, current_app, request
from flask_login import current_user
from sqlalchemy import text
from wtforms import StringField, TextAreaField, FloatField, SelectField
from wtforms import fields as forms
from markupsafe import Markup
from datetime import datetime
import json

class BaseModelView(ModelView):
    """Base ModelView with consistent access control and GAE compatibility"""
    page_size = 100  # Display 100 records per page

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access admin panel', 'warning')
            return redirect(url_for('auth.login'))
        else:
            flash('Admin access required', 'error')
            return redirect(url_for('cell_storage.index'))

    def render(self, template, **kwargs):
        """Enhanced render method with error handling for GAE"""
        try:
            return super().render(template, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Template rendering error in admin: {str(e)}")
            # Fallback to simple error page
            return self._render_error_page(str(e))

    def _render_error_page(self, error_msg):
        """Render a simple error page when template rendering fails"""
        error_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Error</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .error { background: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; }
                .btn { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Cell Storage Admin - Temporary Error</h1>
            <div class="error">
                <h3>Template Rendering Error</h3>
                <p>There was an issue rendering the admin interface. This is likely due to template compatibility.</p>
                <p><strong>Error:</strong> {{ error }}</p>
            </div>
            <p>
                <a href="{{ url_for('cell_storage.index') }}" class="btn">Return to Main Application</a>
                <a href="{{ url_for('admin.index') }}" class="btn">Try Admin Again</a>
            </p>
        </body>
        </html>
        """
        return render_template_string(error_template, error=error_msg)

class CustomAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if not current_user.is_authenticated:
            return False

        # Debug info - remove this in production later
        current_app.logger.info(f'Flask-Admin access check: user={current_user.username}, role={current_user.role}, is_admin={current_user.is_admin}')

        return current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access admin panel', 'warning')
            return redirect(url_for('auth.login'))
        else:
            flash('Admin access required', 'error')
            return redirect(url_for('cell_storage.index'))

    # Remove custom index method, use Flask-Admin default home page
    # This ensures the complete Flask-Admin interface including navigation menu is displayed

    def _render_fallback_index(self):
        """Fallback admin index when main template fails"""
        fallback_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cell Storage Admin</title>
            <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/4.6.0/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container-fluid">
                <div class="jumbotron">
                    <h1 class="display-4"><i class="fas fa-database"></i> Cell Storage Admin</h1>
                    <p class="lead">Administrative interface for Cell Storage Management System</p>
                    <hr class="my-4">
                    <p>The admin interface is temporarily using a simplified view. Core functionality is available through the navigation menu.</p>
                    <a class="btn btn-primary btn-lg" href="{{ url_for('cell_storage.index') }}" role="button">
                        <i class="fas fa-arrow-left"></i> Return to Main Application
                    </a>
                </div>

                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-header">
                                <h3><i class="fas fa-cogs"></i> Admin Functions</h3>
                            </div>
                            <div class="card-body">
                                <div class="alert alert-info">
                                    <strong>Available Admin Features:</strong>
                                    <ul class="mb-0">
                                        <li>User Management</li>
                                        <li>Cell Line Management</li>
                                        <li>Storage System Management (Towers, Drawers, Boxes)</li>
                                        <li>Vial and Batch Management</li>
                                        <li>Print System Management</li>
                                        <li>Inventory Management</li>
                                        <li>System Configuration</li>
                                    </ul>
                                </div>
                                <p>Use the navigation menu to access specific admin sections.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return render_template_string(fallback_template)

    def _render_fallback_index_with_stats(self, stats):
        """Fallback admin index with statistics when main template fails"""
        fallback_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cell Storage Admin</title>
            <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/4.6.0/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet">
            <style>
                .stat-card {
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    padding: 20px;
                    margin-bottom: 20px;
                    border-left: 4px solid #667eea;
                }
                .stat-number { font-size: 2rem; font-weight: bold; color: #667eea; }
                .stat-label { color: #6c757d; font-size: 0.9rem; }
                .admin-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    margin-bottom: 30px;
                    border-radius: 8px;
                }
            </style>
        </head>
        <body class="bg-light">
            <div class="container-fluid">
                <div class="admin-header">
                    <h1 class="display-4"><i class="fas fa-database"></i> Cell Storage Admin</h1>
                    <p class="lead">Administrative interface for Cell Storage Management System</p>
                </div>

                <div class="row">
                    <div class="col-md-3">
                        <div class="stat-card text-center">
                            <div class="stat-number">{{ stats.users }}</div>
                            <div class="stat-label">Total Users</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card text-center">
                            <div class="stat-number">{{ stats.vials }}</div>
                            <div class="stat-label">Total Vials</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card text-center">
                            <div class="stat-number">{{ stats.available_vials }}</div>
                            <div class="stat-label">Available Vials</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card text-center">
                            <div class="stat-number">{{ stats.batches }}</div>
                            <div class="stat-label">Total Batches</div>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-4">
                        <div class="stat-card text-center">
                            <div class="stat-number">{{ stats.cell_lines }}</div>
                            <div class="stat-label">Cell Lines</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stat-card text-center">
                            <div class="stat-number">{{ stats.towers }}</div>
                            <div class="stat-label">Storage Towers</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stat-card text-center">
                            <div class="stat-number">{{ stats.boxes }}</div>
                            <div class="stat-label">Storage Boxes</div>
                        </div>
                    </div>
                </div>

                <div class="alert alert-info mt-4">
                    <h5><i class="fas fa-info-circle"></i> Note</h5>
                    <p>This is a simplified admin interface. Use the navigation menu to access specific admin sections for managing users, cell lines, storage locations, vials, and system configuration.</p>
                    <a href="{{ url_for('cell_storage.index') }}" class="btn btn-primary">
                        <i class="fas fa-arrow-left"></i> Return to Main Application
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        return render_template_string(fallback_template, stats=stats)

class UserAdmin(BaseModelView):
    column_list = ['username', 'role', 'password_plain']
    column_searchable_list = ['username', 'role']
    column_filters = ['role']
    column_sortable_list = ['username', 'role']

class CellLineAdmin(BaseModelView):
    column_list = ['name', 'source', 'species', 'timestamp']
    column_searchable_list = ['name', 'source', 'species']
    column_filters = ['timestamp']
    column_sortable_list = ['name', 'source', 'timestamp']

class StorageBoxAdmin(BaseModelView):
    column_list = ['name', 'drawer_id', 'rows', 'columns']
    column_searchable_list = ['name']
    column_filters = ['drawer_id']
    column_sortable_list = ['name', 'drawer_id']

class VialBatchAdmin(BaseModelView):
    """VialBatch management - edit batch metadata and access vial editing through 'Edit Vials' link"""

    # Display columns: include basic fields and safe calculated fields
    column_list = ['id', 'name', 'timestamp', 'created_by_user_id', 'vial_count', 'first_vial_info', 'edit_vials_link']
    column_searchable_list = ['name']
    column_filters = ['timestamp', 'created_by_user_id']
    column_sortable_list = ['id', 'name', 'timestamp', 'created_by_user_id']

    # Form fields: only batch-level metadata (not individual vial data)
    form_columns = ['name', 'created_by_user_id']

    # Add labels for columns and forms
    column_labels = {
        'id': 'Batch ID',
        'name': 'Batch Name',
        'timestamp': 'Created Date',
        'created_by_user_id': 'Created By User ID',
        'vial_count': 'Vial Count',
        'first_vial_info': 'Sample Vial Info',
        'edit_vials_link': 'Edit Vials'
    }

    # Allow viewing details and editing
    can_view_details = True
    can_edit = True
    can_delete = True  # Enable default delete - cascade should handle it properly
    can_create = True

    # Custom column formatting functions
    def _vial_count_formatter(view, context, model, name):
        """Display the number of vials in the batch"""
        try:
            return model.vials.count()
        except:
            return "0"

    def _first_vial_info_formatter(view, context, model, name):
        """Display basic information of the first vial, avoid recursion"""
        try:
            first_vial = model.vials.first()
            if first_vial:
                info_parts = []
                if hasattr(first_vial, 'cell_line_info') and first_vial.cell_line_info:
                    info_parts.append(f"Cell Line: {first_vial.cell_line_info.name}")
                if first_vial.passage_number:
                    info_parts.append(f"Passage: {first_vial.passage_number}")
                if first_vial.date_frozen:
                    info_parts.append(f"Frozen Date: {first_vial.date_frozen}")
                return " | ".join(info_parts) if info_parts else "No detailed information"
            return "No vials"
        except Exception as e:
            return f"Failed to get information: {str(e)}"

    def _edit_vials_link_formatter(view, context, model, name):
        """Display a link to edit vials in this batch"""
        try:
            vial_count = model.vials.count()
            if vial_count > 0:
                # Create a link to dedicated batch vial editing page
                url = url_for('vialbatch.edit_batch_vials_view', batch_id=model.id)
                return Markup(f'<a href="{url}" class="btn btn-sm btn-primary">Edit {vial_count} Vials</a>')
            return "No vials"
        except Exception as e:
            return f"Error: {str(e)}"

    column_formatters = {
        'vial_count': _vial_count_formatter,
        'first_vial_info': _first_vial_info_formatter,
        'edit_vials_link': _edit_vials_link_formatter
    }

    def on_model_change(self, form, model, is_created):
        """Handle model changes - ensure timestamp is set"""
        try:
            # Ensure timestamp is set for new records
            if is_created and not model.timestamp:
                model.timestamp = datetime.utcnow()

            # Save batch information
            super().on_model_change(form, model, is_created)

        except Exception as e:
            current_app.logger.error(f"VialBatch model change error: {str(e)}")
            flash(f'Error saving VialBatch: {str(e)}', 'error')
            raise e

    @expose('/edit-vials/<int:batch_id>', methods=['GET', 'POST'])
    def edit_batch_vials_view(self, batch_id):
        """Custom view for editing all vials in a specific batch"""
        from app.cell_storage.models import VialBatch, CryoVial, CellLine, Box

        # Get batch and vials
        batch = VialBatch.query.get_or_404(batch_id)
        vials = CryoVial.query.filter_by(batch_id=batch_id).order_by(CryoVial.id).all()

        if request.method == 'POST':
            try:
                action = request.form.get('action', 'batch_update')

                if action == 'batch_update':
                    # Get form data for batch update
                    passage_number = request.form.get('passage_number', '').strip()
                    fluorescence_tag = request.form.get('fluorescence_tag', '').strip()
                    resistance = request.form.get('resistance', '').strip()
                    parental_cell_line = request.form.get('parental_cell_line', '').strip()
                    status = request.form.get('status', '').strip()

                    # Build update query
                    update_count = 0
                    for vial in vials:
                        updated = False
                        if passage_number:
                            vial.passage_number = passage_number
                            updated = True
                        if fluorescence_tag:
                            vial.fluorescence_tag = fluorescence_tag
                            updated = True
                        if resistance:
                            vial.resistance = resistance
                            updated = True
                        if parental_cell_line:
                            vial.parental_cell_line = parental_cell_line
                            updated = True
                        if status:
                            vial.status = status
                            updated = True
                        if updated:
                            vial.last_updated = datetime.utcnow()
                            update_count += 1

                    if update_count > 0:
                        self.session.commit()
                        flash(f'Successfully updated {update_count} vials in batch {batch.name}', 'success')
                    else:
                        flash('No fields provided for update', 'warning')

                elif action == 'save_locations':
                    # Save individual vial locations
                    update_count = 0
                    for vial in vials:
                        box_id = request.form.get(f'box_id_{vial.id}', '').strip()
                        row = request.form.get(f'row_{vial.id}', '').strip()
                        col = request.form.get(f'col_{vial.id}', '').strip()

                        updated = False
                        if box_id and box_id != str(vial.box_id):
                            vial.box_id = int(box_id)
                            updated = True
                        if row and row != str(vial.row_in_box):
                            vial.row_in_box = int(row)
                            updated = True
                        if col and col != str(vial.col_in_box):
                            vial.col_in_box = int(col)
                            updated = True

                        if updated:
                            vial.last_updated = datetime.utcnow()
                            update_count += 1

                    if update_count > 0:
                        self.session.commit()
                        flash(f'Successfully updated storage locations for {update_count} vials', 'success')
                    else:
                        flash('No location changes detected', 'info')

                # Reload vials to show updated data
                vials = CryoVial.query.filter_by(batch_id=batch_id).order_by(CryoVial.id).all()

            except Exception as e:
                self.session.rollback()
                flash(f'Error updating vials: {str(e)}', 'error')
                current_app.logger.error(f"Batch vial update error: {str(e)}")

        # Get all boxes for dropdown
        all_boxes = Box.query.order_by(Box.name).all()
        box_choices = [(box.id, f"{box.name} ({box.rows}x{box.columns})") for box in all_boxes]

        # Create box info dict for JavaScript
        box_info = {box.id: {'name': box.name, 'rows': box.rows, 'columns': box.columns} for box in all_boxes}

        # Prepare vial data with relationships
        vial_data = []
        for vial in vials:
            cell_line = CellLine.query.get(vial.cell_line_id) if vial.cell_line_id else None
            box = Box.query.get(vial.box_id) if vial.box_id else None

            vial_data.append({
                'id': vial.id,
                'unique_vial_id_tag': vial.unique_vial_id_tag,
                'cell_line_name': cell_line.name if cell_line else 'N/A',
                'box_id': vial.box_id,
                'box_name': box.name if box else 'N/A',
                'box_rows': box.rows if box else 10,
                'box_columns': box.columns if box else 10,
                'row_in_box': vial.row_in_box or 1,
                'col_in_box': vial.col_in_box or 1,
                'position': f"R{vial.row_in_box}C{vial.col_in_box}" if vial.row_in_box and vial.col_in_box else 'N/A',
                'passage_number': vial.passage_number or '',
                'date_frozen': vial.date_frozen.strftime('%Y-%m-%d') if vial.date_frozen else 'N/A',
                'fluorescence_tag': vial.fluorescence_tag or '',
                'resistance': vial.resistance or '',
                'parental_cell_line': vial.parental_cell_line or '',
                'status': vial.status or 'Available',
                'notes': vial.notes or ''
            })

        # Render custom template
        return self.render('admin/edit_batch_vials.html',
                          batch=batch,
                          vials=vial_data,
                          vial_count=len(vials),
                          box_choices=box_choices,
                          box_info=box_info)

    @action('edit_batch_vials', 'Edit Batch Vials', 'Edit all vials information in the selected batch')
    def action_edit_batch_vials(self, ids):
        """Batch edit vials in the batch"""
        try:
            if len(ids) != 1:
                flash('Please select one batch to edit', 'error')
                return redirect(url_for('.index_view'))

            batch_id = int(ids[0])
            # Redirect to vials management page, filter by this batch
            # Endpoint name is derived from model name 'CryoVial' -> 'cryovial'
            flash(f'Editing vials in batch {batch_id}', 'info')
            return redirect(url_for('cryovial.index_view', flt1_batch_id_equals=batch_id))

        except Exception as e:
            flash(f'Failed to edit batch vials: {str(e)}', 'error')
            return redirect(url_for('.index_view'))

    @action('delete', 'Delete', 'Are you sure you want to delete the selected records?')
    def action_delete(self, ids):
        """Custom bulk delete method, fixes PostgreSQL type conversion and handles foreign key constraints"""
        try:
            # Convert string IDs to integers
            int_ids = [int(id_str) for id_str in ids]

            # Use raw SQL to avoid type conversion issues
            query = text("SELECT * FROM vial_batches WHERE id = ANY(:ids)")
            result = self.session.execute(query, {'ids': int_ids})
            records = result.fetchall()

            if not records:
                flash('No records found to delete', 'error')
                return redirect(url_for('.index_view'))

            # Delete related alerts records first to avoid foreign key constraints
            delete_alerts_query = text("DELETE FROM alerts WHERE batch_id = ANY(:ids)")
            alerts_result = self.session.execute(delete_alerts_query, {'ids': int_ids})
            deleted_alerts_count = alerts_result.rowcount

            # Delete related cryovials records
            delete_vials_query = text("DELETE FROM cryovials WHERE batch_id = ANY(:ids)")
            vials_result = self.session.execute(delete_vials_query, {'ids': int_ids})
            deleted_vials_count = vials_result.rowcount

            # Finally delete vial_batches records
            delete_query = text("DELETE FROM vial_batches WHERE id = ANY(:ids)")
            self.session.execute(delete_query, {'ids': int_ids})

            self.session.commit()

            flash(f'Successfully deleted {len(records)} batch records (also deleted {deleted_alerts_count} related alerts and {deleted_vials_count} related cryovials)', 'success')

        except Exception as e:
            self.session.rollback()
            flash(f'Delete failed: {str(e)}', 'error')

        return redirect(url_for('.index_view'))

class CryoVialAdmin(BaseModelView):
    """Complete CryoVial record management with full vial information editing capabilities"""

    # Display all important fields
    column_list = ['id', 'unique_vial_id_tag', 'batch_id', 'cell_line_id', 'box_id',
                   'row_in_box', 'col_in_box', 'passage_number', 'date_frozen', 'status']

    column_searchable_list = ['unique_vial_id_tag', 'notes', 'passage_number', 'fluorescence_tag', 'resistance']
    column_filters = ['status', 'date_frozen', 'batch_id', 'box_id', 'cell_line_id', 'frozen_by_user_id']
    column_sortable_list = ['id', 'unique_vial_id_tag', 'batch_id', 'date_frozen', 'date_created']

    # Complete form fields, allow editing all important information
    form_columns = [
        'unique_vial_id_tag', 'batch_id', 'cell_line_id', 'box_id', 'row_in_box', 'col_in_box',
        'passage_number', 'date_frozen', 'frozen_by_user_id', 'number_of_vials_at_creation',
        'volume_ml', 'concentration', 'fluorescence_tag', 'resistance', 'parental_cell_line',
        'status', 'notes'
    ]

    column_labels = {
        'id': 'Vial ID',
        'unique_vial_id_tag': 'Vial Tag',
        'batch_id': 'Batch ID',
        'cell_line_id': 'Cell Line ID',
        'box_id': 'Storage Box ID',
        'row_in_box': 'Row Position',
        'col_in_box': 'Column Position',
        'passage_number': 'Passage Number',
        'date_frozen': 'Frozen Date',
        'frozen_by_user_id': 'Frozen By User',
        'number_of_vials_at_creation': 'Vials at Creation',
        'volume_ml': 'Volume (ml)',
        'concentration': 'Concentration',
        'fluorescence_tag': 'Fluorescence Tag',
        'resistance': 'Resistance Marker',
        'parental_cell_line': 'Parental Cell Line',
        'status': 'Status',
        'notes': 'Notes',
        'date_created': 'Created Date'
    }

    # Default sort by batch_id and id
    column_default_sort = [('batch_id', False), ('id', False)]

    # Enable complete database management functionality
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    # Set page size
    page_size = 50

    @action('batch_update_common_fields', 'Batch Update Fields', 'Batch update common information for selected vials')
    def action_batch_update_common_fields(self, ids):
        """Batch update common fields for selected vials"""
        if request.method == 'POST':
            # Process form submission
            try:
                int_ids = [int(id_str) for id_str in ids]

                # Get form data
                passage_number = request.form.get('passage_number', '').strip()
                fluorescence_tag = request.form.get('fluorescence_tag', '').strip()
                resistance = request.form.get('resistance', '').strip()
                parental_cell_line = request.form.get('parental_cell_line', '').strip()
                status = request.form.get('status', '').strip()

                # Use raw SQL update, only update non-empty fields
                update_parts = []
                params = {'ids': int_ids}

                if passage_number:
                    update_parts.append("passage_number = :passage_number")
                    params['passage_number'] = passage_number
                if fluorescence_tag:
                    update_parts.append("fluorescence_tag = :fluorescence_tag")
                    params['fluorescence_tag'] = fluorescence_tag
                if resistance:
                    update_parts.append("resistance = :resistance")
                    params['resistance'] = resistance
                if parental_cell_line:
                    update_parts.append("parental_cell_line = :parental_cell_line")
                    params['parental_cell_line'] = parental_cell_line
                if status:
                    update_parts.append("status = :status")
                    params['status'] = status

                if update_parts:
                    update_query = text(f"""
                        UPDATE cryovials
                        SET {', '.join(update_parts)},
                            last_updated = NOW()
                        WHERE id = ANY(:ids)
                    """)
                    result = self.session.execute(update_query, params)
                    self.session.commit()

                    flash(f'Successfully updated {result.rowcount} vials', 'success')
                else:
                    flash('No fields provided for update', 'warning')

            except Exception as e:
                self.session.rollback()
                flash(f'Batch update failed: {str(e)}', 'error')

            return redirect(url_for('.index_view'))

        # Display batch update form
        form_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Batch Update Vials</title>
            <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/4.6.0/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                <h2>Batch Update Vials Common Fields</h2>
                <p class="text-info">Selected {{ ids|length }} vials for batch update. Only filled fields will be updated.</p>

                <form method="POST" class="row">
                    <div class="col-md-6">
                        <div class="form-group">
                            <label>Passage Number:</label>
                            <input type="text" name="passage_number" class="form-control" placeholder="Leave empty to skip update">
                        </div>
                        <div class="form-group">
                            <label>Fluorescence Tag:</label>
                            <input type="text" name="fluorescence_tag" class="form-control" placeholder="Leave empty to skip update">
                        </div>
                        <div class="form-group">
                            <label>Resistance Marker:</label>
                            <input type="text" name="resistance" class="form-control" placeholder="Leave empty to skip update">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="form-group">
                            <label>Parental Cell Line:</label>
                            <input type="text" name="parental_cell_line" class="form-control" placeholder="Leave empty to skip update">
                        </div>
                        <div class="form-group">
                            <label>Status:</label>
                            <select name="status" class="form-control">
                                <option value="">-- Do not update status --</option>
                                <option value="Available">Available</option>
                                <option value="Used">Used</option>
                                <option value="Contaminated">Contaminated</option>
                                <option value="Lost">Lost</option>
                            </select>
                        </div>
                    </div>

                    <div class="col-12 mt-3">
                        <button type="submit" class="btn btn-primary">Batch Update</button>
                        <a href="{{ url_for('.index_view') }}" class="btn btn-secondary ml-2">Cancel</a>
                    </div>
                </form>
            </div>
        </body>
        </html>
        """

        return render_template_string(form_template, ids=ids)

    @action('delete', 'Delete', 'Are you sure you want to delete the selected records?')
    def action_delete(self, ids):
        """Custom bulk delete method, fixes PostgreSQL type conversion issues"""
        try:
            # Convert string IDs to integers
            int_ids = [int(id_str) for id_str in ids]

            # Use raw SQL to avoid type conversion issues
            query = text("SELECT * FROM cryovials WHERE id = ANY(:ids)")
            result = self.session.execute(query, {'ids': int_ids})
            records = result.fetchall()

            if not records:
                flash('No records found to delete', 'error')
                return redirect(url_for('.index_view'))

            # Execute delete operation
            delete_query = text("DELETE FROM cryovials WHERE id = ANY(:ids)")
            self.session.execute(delete_query, {'ids': int_ids})
            self.session.commit()

            flash(f'Successfully deleted {len(records)} records', 'success')

        except Exception as e:
            self.session.rollback()
            flash(f'Delete failed: {str(e)}', 'error')

        return redirect(url_for('.index_view'))

class StorageLocationAdmin(BaseModelView):
    column_list = ['name', 'location_type', 'parent_id', 'is_active']
    column_searchable_list = ['name', 'location_type']
    column_filters = ['location_type', 'is_active']
    column_sortable_list = ['name', 'location_type']

class InventoryItemAdmin(BaseModelView):
    column_list = ['name', 'type_id', 'current_quantity', 'location_id', 'status', 'created_at']
    column_searchable_list = ['name', 'status']
    column_filters = ['type_id', 'status', 'created_at']
    column_sortable_list = ['name', 'current_quantity', 'created_at']


class PrintJobAdmin(BaseModelView):
    """Print job management - supports viewing, deleting and status modification"""

    column_list = ['id', 'label_data_preview', 'priority', 'status', 'requested_by',
                   'created_at', 'started_at', 'completed_at', 'error_message', 'retry_count']
    column_searchable_list = ['label_data', 'error_message']
    column_filters = ['status', 'priority', 'created_at', 'requested_by']
    column_sortable_list = ['id', 'priority', 'status', 'created_at', 'retry_count']
    column_labels = {
        'id': 'Job ID',
        'label_data_preview': 'Label Data Preview',
        'priority': 'Priority',
        'status': 'Status',
        'requested_by': 'Requested By User',
        'created_at': 'Created Date',
        'started_at': 'Started Date',
        'completed_at': 'Completed Date',
        'error_message': 'Error Message',
        'retry_count': 'Retry Count'
    }

    # Default sort by creation time in descending order, newest first
    column_default_sort = ('created_at', True)

    # Allow delete, disable create, allow editing status-related fields
    can_create = False
    can_edit = True
    can_delete = True
    can_view_details = True

    # Only allow editing status-related fields
    form_columns = ['status', 'error_message', 'retry_count']

    def _label_data_preview(view, context, model, name):
        """Display short preview of label data"""
        if model.label_data:
            # Try to parse JSON and display key information
            try:
                data = json.loads(model.label_data)
                if isinstance(data, dict):
                    # Extract key fields for preview
                    preview_parts = []
                    for key in ['batch_name', 'vial_id', 'cell_line', 'location']:
                        if key in data:
                            preview_parts.append(f"{key}: {data[key]}")
                    return " | ".join(preview_parts[:2]) if preview_parts else "JSON Data"
                return f"Data length: {len(str(data))}"
            except:
                return f"Data length: {len(model.label_data)}"
        return "No Data"
    
    column_formatters = {
        'label_data_preview': _label_data_preview
    }
    
    @action('reset_to_pending', 'Reset to Pending', 'Are you sure you want to reset the selected jobs to pending status?')
    def action_reset_to_pending(self, ids):
        """Reset selected job status to pending for reprocessing failed jobs"""
        try:
            int_ids = [int(id_str) for id_str in ids]

            # Use raw SQL to update status
            update_query = text("""
                UPDATE print_jobs
                SET status = 'pending',
                    error_message = NULL,
                    started_at = NULL,
                    completed_at = NULL
                WHERE id = ANY(:ids)
            """)
            result = self.session.execute(update_query, {'ids': int_ids})
            self.session.commit()

            flash(f'Successfully reset {result.rowcount} print jobs to pending status', 'success')

        except Exception as e:
            self.session.rollback()
            flash(f'Failed to reset job status: {str(e)}', 'error')

        return redirect(url_for('.index_view'))

    @action('delete', 'Delete', 'Are you sure you want to delete the selected print jobs?')
    def action_delete(self, ids):
        """Delete selected print jobs"""
        try:
            int_ids = [int(id_str) for id_str in ids]

            # First delete related history records
            delete_history_query = text("DELETE FROM print_job_history WHERE print_job_id = ANY(:ids)")
            history_result = self.session.execute(delete_history_query, {'ids': int_ids})

            # Then delete print jobs
            delete_query = text("DELETE FROM print_jobs WHERE id = ANY(:ids)")
            job_result = self.session.execute(delete_query, {'ids': int_ids})
            self.session.commit()

            flash(f'Successfully deleted {job_result.rowcount} print jobs (also deleted {history_result.rowcount} history records)', 'success')

        except Exception as e:
            self.session.rollback()
            flash(f'Delete failed: {str(e)}', 'error')

        return redirect(url_for('.index_view'))

class PrintServerAdmin(BaseModelView):
    """Print server management"""

    column_list = ['id', 'server_id', 'name', 'location', 'status', 'last_heartbeat',
                   'total_jobs_processed', 'successful_jobs', 'failed_jobs', 'success_rate']
    column_searchable_list = ['server_id', 'name', 'location']
    column_filters = ['status', 'last_heartbeat']
    column_sortable_list = ['id', 'server_id', 'name', 'status', 'last_heartbeat', 'total_jobs_processed']
    column_labels = {
        'id': 'ID',
        'server_id': 'Server ID',
        'name': 'Server Name',
        'location': 'Location',
        'status': 'Status',
        'last_heartbeat': 'Last Heartbeat',
        'total_jobs_processed': 'Total Jobs Processed',
        'successful_jobs': 'Successful Jobs',
        'failed_jobs': 'Failed Jobs',
        'success_rate': 'Success Rate'
    }

    # Default sort by last heartbeat time in descending order
    column_default_sort = ('last_heartbeat', True)

    # Allow create, edit and delete
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    def _success_rate(view, context, model, name):
        """Calculate success rate"""
        if model.total_jobs_processed > 0:
            rate = (model.successful_jobs / model.total_jobs_processed) * 100
            return f"{rate:.1f}%"
        return "0%"
    
    column_formatters = {
        'success_rate': _success_rate
    }

class AppConfigAdmin(BaseModelView):
    """Application configuration management, including Batch ID and Vial ID counters"""

    column_list = ['key', 'value', 'description', 'created_at', 'updated_at']
    column_searchable_list = ['key', 'value', 'description']
    column_filters = ['key', 'created_at']
    column_sortable_list = ['key', 'created_at', 'updated_at']
    column_labels = {
        'key': 'Config Key',
        'value': 'Config Value',
        'description': 'Description',
        'created_at': 'Created Date',
        'updated_at': 'Updated Date'
    }

    # Only allow editing value and description fields
    form_columns = ['value', 'description']

    def on_model_change(self, form, model, is_created):
        """Validate on model change and synchronize database sequence"""
        from app import db

        # Validate counter value must be positive integer
        if model.key in ['batch_counter', 'vial_counter']:
            try:
                val = int(model.value)
                if val < 1:
                    raise ValueError(f"{model.key} must be a positive integer")
                model.value = str(val)

                # Synchronize PostgreSQL sequence
                if model.key == 'vial_counter':
                    # Check if less than current max ID
                    from app.cell_storage.models import CryoVial
                    max_id = db.session.query(db.func.max(CryoVial.id)).scalar() or 0
                    if val <= max_id:
                        flash(f'Warning: Set Vial ID ({val}) is less than or equal to current max ID ({max_id}), may cause ID conflicts', 'warning')

                    # Update sequence
                    db.session.execute(text(f"ALTER SEQUENCE cryovials_id_seq RESTART WITH {val}"))
                    flash(f'Vial ID sequence updated to start from {val}', 'info')

                elif model.key == 'batch_counter':
                    # Check if less than current max ID
                    from app.cell_storage.models import VialBatch
                    max_id = db.session.query(db.func.max(VialBatch.id)).scalar() or 0
                    if val <= max_id:
                        flash(f'Warning: Set Batch ID ({val}) is less than or equal to current max ID ({max_id}), may cause ID conflicts', 'warning')

                    # Update sequence
                    db.session.execute(text(f"ALTER SEQUENCE vial_batches_id_seq RESTART WITH {val}"))
                    flash(f'Batch ID sequence updated to start from {val}', 'info')

            except ValueError as e:
                flash(f'Invalid value for {model.key}: {str(e)}', 'error')
                raise e
            except Exception as e:
                flash(f'Error updating sequence: {str(e)}', 'error')
                raise e

        # Update timestamp
        model.updated_at = datetime.utcnow()

        super().on_model_change(form, model, is_created)

def init_admin(app):
    """Initialize Flask-Admin"""
    from app import db
    # Import models at the top of the function
    from app.cell_storage.models import User, CellLine, Box, VialBatch, CryoVial, Tower, Drawer, AppConfig, PrintJob, PrintServer
    from app.inventory.models import Location, InventoryItem, InventoryType, Supplier

    # Create Admin instance - use Flask-Admin default template to ensure navigation menu displays correctly
    admin = Admin(
        app,
        name='Cell Storage Admin',
        index_view=CustomAdminIndexView(name='Home', url='/flask-admin'),
        # Remove custom base_template, use Flask-Admin default template
        url='/flask-admin'
    )

    # Register model views - organized by hierarchy
    admin.add_view(UserAdmin(User, db.session, name='Users'))
    admin.add_view(CellLineAdmin(CellLine, db.session, name='Cell Lines'))

    # Storage hierarchy management
    admin.add_view(BaseModelView(Tower, db.session, name='Towers'))
    admin.add_view(BaseModelView(Drawer, db.session, name='Drawers'))
    admin.add_view(StorageBoxAdmin(Box, db.session, name='Storage Boxes'))

    # Sample management
    admin.add_view(VialBatchAdmin(VialBatch, db.session, name='Vial Batches'))
    admin.add_view(CryoVialAdmin(CryoVial, db.session, name='Cryo Vials'))

    # Printing system management
    admin.add_view(PrintJobAdmin(PrintJob, db.session, name='Print Jobs'))
    admin.add_view(PrintServerAdmin(PrintServer, db.session, name='Print Servers'))

    # Inventory management
    admin.add_view(StorageLocationAdmin(Location, db.session, name='Storage Locations'))
    admin.add_view(InventoryItemAdmin(InventoryItem, db.session, name='Inventory Items'))
    admin.add_view(BaseModelView(InventoryType, db.session, name='Inventory Types'))
    admin.add_view(BaseModelView(Supplier, db.session, name='Suppliers'))

    # System configuration management
    admin.add_view(AppConfigAdmin(AppConfig, db.session, name='System Configuration'))

    return admin