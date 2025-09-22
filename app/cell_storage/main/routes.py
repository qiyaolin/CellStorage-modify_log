# In app/main/routes.py
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session,
    Response,
    current_app,
    send_file,
    jsonify,
)
from flask_login import login_required, current_user
from datetime import datetime
import time
from collections import defaultdict
try:
    from markupsafe import Markup
except ImportError:
    from jinja2 import Markup
from urllib.parse import urlparse, parse_qs
from io import StringIO, BytesIO


def get_smart_redirect_url(default_endpoint='main.index', **default_kwargs):
    """
    根据来源页面信息智能决定重定向目标
    优先级：URL参数中的next > HTTP_REFERER > 默认页面
    """
    # 优先检查URL参数中的next
    next_url = request.args.get('next') or request.form.get('next')
    if next_url:
        return next_url
    
    # 其次检查HTTP_REFERER
    referer = request.headers.get('Referer')
    if referer:
        parsed_referer = urlparse(referer)
        # 确保referer是同一域名的请求，避免安全问题
        if parsed_referer.netloc == request.host:
            return referer
    
    # 最后使用默认页面
    return url_for(default_endpoint, **default_kwargs)
import csv
import os
import subprocess
import tempfile
from urllib.parse import urlparse
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, or_, cast, String
from datetime import datetime
import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from . import bp
from ... import db
from sqlalchemy.orm import joinedload
from ...shared.decorators import admin_required
from ..forms import (
    CellLineForm,
    TowerForm,
    DrawerForm,
    BoxForm,
    CryoVialForm,
    CryoVialEditForm,
    VialUsageForm,
    ManualVialForm,
    ConfirmForm,
    RestoreForm,
    BatchEditVialsForm,
    EditBatchForm,
    BatchLookupForm,
    CSVUploadForm,
)
from ..models import (
    CellLine,
    User,
    Tower,
    Drawer,
    Box,
    CryoVial,
    VialBatch,
    AuditLog,
    Alert,
)

from ...shared.utils import log_audit, clear_database_except_admin
from ...shared.utils import get_next_batch_id, get_batch_counter, set_batch_counter, get_next_vial_id, get_vial_counter, set_vial_counter
from ...shared.audit_utils import create_audit_log, format_audit_details
import io
import csv
from io import StringIO
import re

def validate_csrf_token(token):
    """验证CSRF token"""
    from flask_wtf.csrf import generate_csrf
    try:
        # 使用Flask-WTF的CSRF验证
        from flask_wtf.csrf import validate_csrf
        validate_csrf(token)
        return True
    except Exception:
        return False


@bp.route('/') # Defines the root URL for the main blueprint
@bp.route('/index') # Also accessible via /index
@login_required # Ensure only logged-in users can access the main dashboard
def index():
    # 基础统计
    vial_count = CryoVial.query.count()
    
    # 获取预警信息
    from app.shared.utils import get_active_alerts, generate_all_alerts
    
    # 为管理员生成和显示预警
    if current_user.is_admin:
        # 每次访问主页时生成新预警（实际使用中可能需要用定时任务）
        try:
            generate_all_alerts()
        except Exception as e:
            current_app.logger.warning(f'Alert generation failed: {e}')
        
        # 获取最新的活跃预警
        recent_alerts = get_active_alerts(limit=5)
    else:
        recent_alerts = []
    
    # 获取最近活动记录
    from app.cell_storage.models import AuditLog
    recent_activities_raw = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(5).all()
    
    # Format the audit details for better readability
    recent_activities = []
    for activity in recent_activities_raw:
        # Add formatted details to each activity
        activity.formatted_details = format_audit_details(activity.action, activity.details or "", db_session=db.session)
        recent_activities.append(activity)
    
    return render_template(
        'main/index.html', 
        title='Dashboard', 
        vial_count=vial_count,
        recent_alerts=recent_alerts,
        recent_activities=recent_activities
    )


@bp.route('/audit_logs')
@login_required
@admin_required
def audit_logs():
    search_user = request.args.get('user', '').strip()
    keyword = request.args.get('keyword', '').strip()
    start = request.args.get('start', '').strip()
    end = request.args.get('end', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 50  # 每页显示50条记录

    query = AuditLog.query.join(User)
    if search_user:
        query = query.filter(User.username.ilike(f'%{search_user}%'))
    if start:
        try:
            start_dt = datetime.strptime(start, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= start_dt)
        except ValueError:
            pass
    if end:
        try:
            end_dt = datetime.strptime(end, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp <= end_dt)
        except ValueError:
            pass
    if keyword:
        like = f'%{keyword}%'
        query = query.filter(
            AuditLog.action.ilike(like) |
            AuditLog.details.ilike(like) |
            AuditLog.target_type.ilike(like)
        )
    
    # 使用分页查询
    logs_pagination = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    logs_raw = logs_pagination.items
    
    parsed_logs = []
    for log in logs_raw:
        details = {}
        if log.details:
            try:
                details = json.loads(log.details)
            except ValueError:
                details = {'raw': log.details}

        vial_ids = []
        if isinstance(details, dict):
            if isinstance(details.get('vial_ids'), list):
                vial_ids = details['vial_ids']
            elif details.get('vial_id') is not None:
                vial_ids = [details['vial_id']]
        if not vial_ids and log.target_type == 'CryoVial' and log.target_id:
            vial_ids = [log.target_id]

        display_vials = []
        if vial_ids:
            vials = CryoVial.query.filter(CryoVial.id.in_(vial_ids)).join(VialBatch).all()
            id_map = {v.id: v for v in vials}
            for vid in vial_ids:
                v = id_map.get(vid)
                if v:
                    display_vials.append(f"{v.batch.name}({v.unique_vial_id_tag})")
                else:
                    display_vials.append(str(vid))

        parsed_logs.append({'log': log, 'details': details, 'display_vials': display_vials})

    all_users = User.query.order_by(User.username).all()

    return render_template(
        'main/audit_logs.html',
        logs=parsed_logs,
        pagination=logs_pagination,
        all_users=all_users,
        search_user=search_user,
        keyword=keyword,
        start=start,
        end=end,
        title='Inventory Logs'
    )

@bp.route('/cell_lines')
@login_required
@admin_required
def list_cell_lines():
    cell_lines = CellLine.query.order_by(CellLine.name).all()
    return render_template('main/cell_lines.html', title='Cell Lines', cell_lines=cell_lines)

@bp.route('/cell_line/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_cell_line():
    form = CellLineForm()
    if form.validate_on_submit():
        cell_line = CellLine(
            name=form.name.data,
            source=form.source.data,
            species=form.species.data,
            original_passage=form.original_passage.data,
            culture_medium=form.culture_medium.data,
            antibiotic_resistance=form.antibiotic_resistance.data,
            growth_properties=form.growth_properties.data,
            mycoplasma_status=form.mycoplasma_status.data,
            date_established=form.date_established.data,
            notes=form.notes.data,
            created_by_user_id=current_user.id
        )
        db.session.add(cell_line)
        db.session.commit()
        log_audit(current_user.id, 'CREATE', target_type='CellLine', target_id=cell_line.id, details=f"Cell line '{cell_line.name}' created.")
        
        add_batch_url = url_for('cell_storage.add_cryovial', cell_line_id=cell_line.id)
        flash(Markup(f'Cell line has been successfully added! <a href="{add_batch_url}" class="btn btn-sm btn-success ms-2">Add Batch for this Cell Line</a>'), 'success')

        return redirect(url_for('cell_storage.list_cell_lines'))
    return render_template('main/cell_line_form.html', form=form, title='Add New Cell Line')

@bp.route('/cell_line/<int:cell_line_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_cell_line(cell_line_id):
    cell_line = CellLine.query.get_or_404(cell_line_id)
    form = CellLineForm(obj=cell_line) # Pre-populate form with existing data

    if form.validate_on_submit():
        # 记录变更前的状态
        changes = {}
        if cell_line.name != form.name.data:
            changes['name'] = {'old': cell_line.name, 'new': form.name.data}
        if cell_line.source != form.source.data:
            changes['source'] = {'old': cell_line.source, 'new': form.source.data}
        if cell_line.species != form.species.data:
            changes['species'] = {'old': cell_line.species, 'new': form.species.data}
        if cell_line.original_passage != form.original_passage.data:
            changes['original_passage'] = {'old': cell_line.original_passage, 'new': form.original_passage.data}
        if cell_line.culture_medium != form.culture_medium.data:
            changes['culture_medium'] = {'old': cell_line.culture_medium, 'new': form.culture_medium.data}
        if cell_line.antibiotic_resistance != form.antibiotic_resistance.data:
            changes['antibiotic_resistance'] = {'old': cell_line.antibiotic_resistance, 'new': form.antibiotic_resistance.data}
        if cell_line.growth_properties != form.growth_properties.data:
            changes['growth_properties'] = {'old': cell_line.growth_properties, 'new': form.growth_properties.data}
        if cell_line.mycoplasma_status != form.mycoplasma_status.data:
            changes['mycoplasma_status'] = {'old': cell_line.mycoplasma_status, 'new': form.mycoplasma_status.data}
        if cell_line.date_established != form.date_established.data:
            changes['date_established'] = {'old': cell_line.date_established.strftime('%Y-%m-%d') if cell_line.date_established else None, 'new': form.date_established.data.strftime('%Y-%m-%d') if form.date_established.data else None}
        if cell_line.notes != form.notes.data:
            changes['notes'] = {'old': cell_line.notes, 'new': form.notes.data}
        
        cell_line.name = form.name.data
        cell_line.source = form.source.data
        cell_line.species = form.species.data
        cell_line.original_passage = form.original_passage.data
        cell_line.culture_medium = form.culture_medium.data
        cell_line.antibiotic_resistance = form.antibiotic_resistance.data
        cell_line.growth_properties = form.growth_properties.data
        cell_line.mycoplasma_status = form.mycoplasma_status.data
        cell_line.date_established = form.date_established.data
        cell_line.notes = form.notes.data
        # cell_line.timestamp can be updated automatically if model configured, or set manually:
        # from datetime import datetime
        # cell_line.timestamp = datetime.utcnow()
        db.session.commit()
        
        # 只有在有实际变更时才记录审计日志
        if changes:
            log_audit(
                current_user.id, 
                'EDIT_CELL_LINE', 
                target_type='CellLine', 
                target_id=cell_line.id, 
                details={
                    'cell_line_name': cell_line.name,
                    'changes': changes
                }
            )
        
        flash(f'Cell line "{cell_line.name}" updated successfully!', 'success')
        return redirect(get_smart_redirect_url('main.list_cell_lines'))

    # For GET request, populate form fields from the object if not submitting
    # This is already handled by form = CellLineForm(obj=cell_line) for GET requests
    # but to be explicit for setting form data on GET:
    # if request.method == 'GET':
    #     form.name.data = cell_line.name
    #     # ... populate other fields ...

    return render_template('main/cell_line_form.html', title='Edit Cell Line', form=form, cell_line=cell_line, form_action=url_for('cell_storage.edit_cell_line', cell_line_id=cell_line.id))

@bp.route('/locations')
@login_required
@admin_required
def locations_overview():
    towers = Tower.query.order_by(Tower.name).all()
    # You might want to pass drawers and boxes too, or fetch them in the template via tower.drawers, drawer.boxes
    return render_template('main/locations_overview_simplified.html', title='Storage Location Management', towers=towers)

# --- Tower Routes ---
@bp.route('/tower/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_tower():
    form = TowerForm()
    if form.validate_on_submit():
        # Create the tower
        tower = Tower(name=form.name.data, freezer_name=form.freezer_name.data, description=form.description.data)
        db.session.add(tower)
        db.session.flush()  # Flush to get the tower ID
        
        # Automatically create 5 drawers for the new tower
        for drawer_num in range(1, 6):
            drawer = Drawer(name=f'Drawer {drawer_num}', tower_id=tower.id)
            db.session.add(drawer)
            db.session.flush()  # Get drawer.id

            # Automatically create 5 boxes (9x9) for each drawer
            # Each drawer has boxes numbered 1-5
            for box_num in range(1, 6):
                box = Box(
                    name=f'Box {box_num}',
                    drawer_id=drawer.id,
                    rows=9,
                    columns=9,
                    description=f'Auto-created 9x9 box for Drawer {drawer_num}'
                )
                db.session.add(box)
        
        db.session.commit()
        log_audit(current_user.id, 'CREATE_TOWER', target_type='Tower', target_id=tower.id, details=f'Tower "{tower.name}" in freezer "{tower.freezer_name}" with 5 drawers and 25 boxes')
        flash(f'Tower "{tower.name}" added successfully with 5 drawers and 25 boxes (9x9 each)!', 'success')
        return redirect(url_for('cell_storage.locations_overview'))
    return render_template('main/tower_form.html', title='Add Tower', form=form, form_action=url_for('cell_storage.add_tower'))

@bp.route('/tower/<int:tower_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_tower(tower_id):
    tower = Tower.query.get_or_404(tower_id)
    form = TowerForm(obj=tower)
    if form.validate_on_submit():
        tower.name = form.name.data
        tower.freezer_name = form.freezer_name.data
        tower.description = form.description.data
        db.session.commit()
        flash(f'Tower "{tower.name}" updated successfully!', 'success')
        return redirect(url_for('cell_storage.locations_overview'))
    return render_template('main/tower_form.html', title='Edit Tower', form=form, tower=tower, form_action=url_for('cell_storage.edit_tower', tower_id=tower.id))

@bp.route('/tower/<int:tower_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_tower(tower_id):
    tower = Tower.query.get_or_404(tower_id)
    tower_name = tower.name
    
    # Delete all associated drawers, boxes, and vials
    for drawer in tower.drawers:
        for box in drawer.boxes:
            # Delete all vials in this box
            for vial in box.cryovials:
                db.session.delete(vial)
            # Delete the box
            db.session.delete(box)
        # Delete the drawer
        db.session.delete(drawer)
    
    # Delete the tower
    db.session.delete(tower)
    db.session.commit()
    
    log_audit(current_user.id, 'DELETE_TOWER', target_type='Tower', target_id=tower_id, details=f'Tower "{tower_name}" and all contents deleted')
    flash(f'Tower "{tower_name}" and all its contents have been deleted successfully!', 'success')
    return redirect(url_for('cell_storage.locations_overview'))

# --- Drawer Routes ---
@bp.route('/drawer/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_drawer():
    form = DrawerForm()
    form.tower_id.choices = [(t.id, t.name) for t in Tower.query.order_by(Tower.name).all()]
    
    # Pre-select tower if tower_id is provided in URL
    if request.method == 'GET':
        tower_id = request.args.get('tower_id', type=int)
        if tower_id:
            form.tower_id.data = tower_id
            
    if form.validate_on_submit():
        drawer = Drawer(name=form.name.data, tower_id=form.tower_id.data)
        db.session.add(drawer)
        db.session.commit()
        flash(f'Drawer "{drawer.name}" added successfully to tower ID {drawer.tower_id}!', 'success')
        return redirect(url_for('cell_storage.locations_overview'))
    return render_template('main/drawer_form.html', title='Add Drawer', form=form, form_action=url_for('cell_storage.add_drawer'))

@bp.route('/drawer/<int:drawer_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_drawer(drawer_id):
    drawer = Drawer.query.get_or_404(drawer_id)
    form = DrawerForm(obj=drawer)
    form.tower_id.choices = [(t.id, t.name) for t in Tower.query.order_by(Tower.name).all()]
    if form.validate_on_submit():
        drawer.name = form.name.data
        drawer.tower_id = form.tower_id.data
        db.session.commit()
        flash(f'Drawer "{drawer.name}" updated successfully!', 'success')
        return redirect(url_for('cell_storage.locations_overview'))
    # Ensure tower_id is set correctly for the form on GET request if not using obj
    # form.tower_id.data = drawer.tower_id # This is handled by obj=drawer
    return render_template('main/drawer_form.html', title='Edit Drawer', form=form, drawer=drawer, form_action=url_for('cell_storage.edit_drawer', drawer_id=drawer.id))

@bp.route('/drawer/<int:drawer_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_drawer(drawer_id):
    drawer = Drawer.query.get_or_404(drawer_id)
    drawer_name = drawer.name
    
    # Delete all associated boxes and vials
    for box in drawer.boxes:
        # Delete all vials in this box
        for vial in box.cryovials:
            db.session.delete(vial)
        # Delete the box
        db.session.delete(box)
    
    # Delete the drawer
    db.session.delete(drawer)
    db.session.commit()
    
    log_audit(current_user.id, 'DELETE_DRAWER', target_type='Drawer', target_id=drawer_id, details=f'Drawer "{drawer_name}" and all contents deleted')
    flash(f'Drawer "{drawer_name}" and all its contents have been deleted successfully!', 'success')
    return redirect(url_for('cell_storage.locations_overview'))

# --- Box Routes ---
@bp.route('/box/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_box():
    form = BoxForm()
    form.drawer_id.choices = [(d.id, f"{d.tower_info.name} - {d.name}") for d in Drawer.query.join(Tower).order_by(Tower.name, Drawer.name).all()]
    
    # Pre-select drawer if drawer_id is provided in URL
    if request.method == 'GET':
        drawer_id = request.args.get('drawer_id', type=int)
        if drawer_id:
            form.drawer_id.data = drawer_id
            
    if form.validate_on_submit():
        box = Box(
            name=form.name.data,
            drawer_id=form.drawer_id.data,
            rows=form.rows.data,
            columns=form.columns.data,
            description=form.description.data,
        )
        db.session.add(box)
        try:
            db.session.commit()
            flash(
                f'Box "{box.name}" added successfully to drawer ID {box.drawer_id}!',
                'success',
            )
            return redirect(url_for('cell_storage.locations_overview'))
        except IntegrityError:
            db.session.rollback()
            flash('A box with that name already exists in the selected drawer.', 'danger')
    return render_template('main/box_form.html', title='Add Box', form=form, form_action=url_for('cell_storage.add_box'))

@bp.route('/box/<int:box_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_box(box_id):
    box = Box.query.get_or_404(box_id)
    form = BoxForm(obj=box)
    form.drawer_id.choices = [(d.id, f"{d.tower_info.name} - {d.name}") for d in Drawer.query.join(Tower).order_by(Tower.name, Drawer.name).all()]
    if form.validate_on_submit():
        box.name = form.name.data
        box.drawer_id = form.drawer_id.data
        box.rows = form.rows.data
        box.columns = form.columns.data
        box.description = form.description.data
        db.session.commit()
        flash(f'Box "{box.name}" updated successfully!', 'success')
        return redirect(url_for('cell_storage.locations_overview'))
    # form.drawer_id.data = box.drawer_id # Handled by obj=box
    return render_template('main/box_form.html', title='Edit Box', form=form, box=box, form_action=url_for('cell_storage.edit_box', box_id=box.id))

@bp.route('/box/<int:box_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_box(box_id):
    box = Box.query.get_or_404(box_id)
    box_name = box.name
    
    # Delete all vials in this box
    for vial in box.cryovials:
        db.session.delete(vial)
    
    # Delete the box
    db.session.delete(box)
    db.session.commit()
    
    log_audit(current_user.id, 'DELETE_BOX', target_type='Box', target_id=box_id, details=f'Box "{box_name}" and all contents deleted')
    flash(f'Box "{box_name}" and all its contents have been deleted successfully!', 'success')
    return redirect(url_for('cell_storage.locations_overview'))

@bp.route('/cryovial/<int:vial_id>/update_status', methods=['GET', 'POST'])
@login_required # Normal users can update status (declare usage)
def update_cryovial_status(vial_id):
    vial = CryoVial.query.get_or_404(vial_id)
    form = VialUsageForm(obj=vial) # Pre-populate if form has 'status' or 'notes'

    # If GET request, perhaps just show vial info and form.
    # If POST, process the form.
    if form.validate_on_submit():
        old_status = vial.status
        vial.status = form.new_status.data
        if form.notes.data:  # Append usage notes to existing notes or set them
            vial.notes = (vial.notes + "\n" if vial.notes else "") + f"Usage update ({datetime.utcnow().strftime('%Y-%m-%d')}): {form.notes.data}"
        vial.last_updated = datetime.utcnow()
        # Create readable audit log for status update
        readable_details = create_audit_log(
            user_id=current_user.id,
            action='UPDATE_STATUS',
            target_type='CryoVial',
            target_id=vial.id,
            vial_tag=vial.unique_vial_id_tag,
            batch_id=vial.batch_id,
            old_status=old_status,
            new_status=vial.status,
            notes=form.notes.data
        )
        log_audit(
            current_user.id,
            'UPDATE_STATUS',
            target_type='CryoVial',
            target_id=vial.id,
            details=readable_details
        )
        db.session.commit()
        flash(f'Status of vial "{vial.unique_vial_id_tag}" updated to {vial.status}.', 'success')
        return redirect(url_for('cell_storage.cryovial_inventory')) # Or back to where they were (e.g., box view)

    # For GET request, it's better to have a dedicated page to confirm this action.
    # This simple example directly uses a form, but a confirmation step is good UX.
    return render_template('main/update_vial_status_form.html', title='Update Vial Status',
                           form=form, vial=vial,
                           form_action=url_for('cell_storage.update_cryovial_status', vial_id=vial.id))

# Add Edit/View Detail routes for CryoVials (perhaps admin only for edit, all for view)
@bp.route('/cryovial/<int:vial_id>/edit', methods=['GET', 'POST'])
@login_required # Or @admin_required if only admins can edit vial details
def edit_cryovial(vial_id):
    vial = CryoVial.query.get_or_404(vial_id)
    # Permission check: e.g., only admin or the user who froze it can edit.
    # if not current_user.is_admin and vial.frozen_by_user_id != current_user.id:
    #     flash('You do not have permission to edit this vial.', 'danger')
    #     return redirect(url_for('cell_storage.cryovial_inventory'))

    form = CryoVialEditForm(obj=vial)
    form.cell_line_id.choices = [(cl.id, cl.name) for cl in CellLine.query.order_by(CellLine.name).all()]
    form.box_id.choices = [
        (b.id, f"{b.drawer_info.tower_info.name} - {b.drawer_info.name} - {b.name} ({b.rows}x{b.columns})")
        for b in Box.query.join(Drawer).join(Tower).order_by(Tower.name, Drawer.name, Box.name).all()
    ]

    # Ensure these fields are correctly populated on GET if obj doesn't do it perfectly for SelectFields after validation fail
    if request.method == 'GET':
        form.cell_line_id.data = vial.cell_line_id
        form.box_id.data = vial.box_id
        form.resistance.data = vial.resistance.split(',') if vial.resistance else []
        form.unique_vial_id_tag.data = vial.unique_vial_id_tag
        form.row_in_box.data = vial.row_in_box
        form.col_in_box.data = vial.col_in_box
        form.passage_number.data = vial.passage_number
        form.date_frozen.data = vial.date_frozen
        form.number_of_vials_at_creation.data = vial.number_of_vials_at_creation
        form.volume_ml.data = vial.volume_ml
        form.concentration.data = vial.concentration
        form.fluorescence_tag.data = vial.fluorescence_tag
        form.parental_cell_line.data = vial.parental_cell_line
        form.status.data = vial.status
        form.notes.data = vial.notes

    if form.validate_on_submit():
        # Basic check for position change and occupancy, more complex if vial moves
        if (form.box_id.data != vial.box_id or \
            form.row_in_box.data != vial.row_in_box or \
            form.col_in_box.data != vial.col_in_box):
            existing_vial_at_new_pos = CryoVial.query.filter(
                CryoVial.id != vial.id,  # Exclude the current vial
                CryoVial.box_id == form.box_id.data,
                CryoVial.row_in_box == form.row_in_box.data,
                CryoVial.col_in_box == form.col_in_box.data,
                CryoVial.status == 'Available'
            ).first()
            if existing_vial_at_new_pos:
                flash(f'Error: New position {form.row_in_box.data}-{form.col_in_box.data} in selected box is already occupied by vial {existing_vial_at_new_pos.unique_vial_id_tag}.', 'danger')
                return render_template('main/cryovial_form.html', title='Edit CryoVial', form=form, vial=vial, form_action=url_for('cell_storage.edit_cryovial', vial_id=vial.id))

        selected_box = Box.query.get(form.box_id.data)
        if not selected_box or not (1 <= form.row_in_box.data <= selected_box.rows and 1 <= form.col_in_box.data <= selected_box.columns):
            flash(f'Error: Row/Column number is outside the dimensions of the selected box ({selected_box.rows}x{selected_box.columns}).', 'danger')
            return render_template('main/cryovial_form.html', title='Edit CryoVial', form=form, vial=vial, form_action=url_for('cell_storage.edit_cryovial', vial_id=vial.id))

        vial.unique_vial_id_tag = form.unique_vial_id_tag.data
        vial.cell_line_id = form.cell_line_id.data
        vial.box_id = form.box_id.data
        vial.row_in_box = form.row_in_box.data
        vial.col_in_box = form.col_in_box.data
        vial.passage_number = form.passage_number.data
        vial.date_frozen = form.date_frozen.data
        # frozen_by_user_id should generally not change, or only by admin
        vial.number_of_vials_at_creation = form.number_of_vials_at_creation.data
        vial.volume_ml = form.volume_ml.data
        vial.concentration = form.concentration.data
        vial.fluorescence_tag = form.fluorescence_tag.data
        vial.resistance = ','.join(form.resistance.data) if form.resistance.data else None
        vial.parental_cell_line = form.parental_cell_line.data
        vial.status = form.status.data
        vial.notes = form.notes.data
        vial.last_updated = datetime.utcnow()

        current_details_for_edit = {
            'general_info': 'vial edited',
            'vial_id': vial.id,  # Storing the single vial_id being edited
            'batch_id': vial.batch_id  # Storing the associated batch_id
            # You could add more specific changed fields here if desired
            # e.g., 'changed_fields': {'status': vial.status, 'notes': vial.notes}
        }
        log_audit(
            current_user.id,
            'EDIT_CRYOVIAL',
            target_type='CryoVial',
            target_id=vial.id,
            details=current_details_for_edit
        )
        db.session.commit()
        flash(f'CryoVial "{vial.unique_vial_id_tag}" updated successfully!', 'success')
        return redirect(get_smart_redirect_url('cell_storage.cryovial_inventory'))

    return render_template('main/edit_cryovial_form.html', title='Edit CryoVial', form=form, vial=vial, form_action=url_for('cell_storage.edit_cryovial', vial_id=vial.id))


@bp.route('/box/<int:box_id>/add/<int:row>/<int:col>', methods=['GET', 'POST'], endpoint='add_vial_at_position')
@login_required
@admin_required
def add_vial_at_position(box_id, row, col):
    box = Box.query.get_or_404(box_id)
    if not (1 <= row <= box.rows and 1 <= col <= box.columns):
        flash('Invalid position for this box.', 'danger')
        return redirect(url_for('cell_storage.cryovial_inventory'))

    existing = CryoVial.query.filter_by(
        box_id=box.id,
        row_in_box=row,
        col_in_box=col,
        status='Available'
    ).first()
    if existing:
        flash('That position is already occupied.', 'danger')
        return redirect(url_for('cell_storage.cryovial_inventory'))

    form = ManualVialForm()
    form.cell_line_id.choices = [(c.id, c.name) for c in CellLine.query.order_by(CellLine.name).all()]

    if form.validate_on_submit():
        if form.batch_id.data:
            batch = VialBatch.query.get(form.batch_id.data)
            if not batch:
                flash('Batch ID not found.', 'danger')
                return render_template('main/manual_vial_form.html', form=form, box=box, row=row, col=col, form_action=url_for('cell_storage.add_vial_at_position', box_id=box_id, row=row, col=col), title='Add Vial')
        else:
            batch = VialBatch(
                id=get_next_batch_id(),
                name=form.batch_name.data,
                created_by_user_id=current_user.id,
            )
            db.session.add(batch)
            db.session.commit()

        # Use vial counter for unique ID generation
        # 使用正确的批次标签格式
        base_tag = f"B{batch.id}"
        count = batch.vials.count()
        unique_tag = base_tag if count == 0 else f"{base_tag}-{count + 1}"

        vial = CryoVial(
            unique_vial_id_tag=unique_tag,
            batch_id=batch.id,
            cell_line_id=form.cell_line_id.data,
            box_id=box.id,
            row_in_box=row,
            col_in_box=col,
            passage_number=form.passage_number.data,
            date_frozen=form.date_frozen.data,
            frozen_by_user_id=current_user.id,
            volume_ml=form.volume_ml.data,
            concentration=form.concentration.data,
            fluorescence_tag=form.fluorescence_tag.data,
            resistance=','.join(form.resistance.data) if form.resistance.data else None,
            parental_cell_line=form.parental_cell_line.data,
            status='Available',
            notes=form.notes.data,
            date_created=datetime.utcnow(),
        )
        db.session.add(vial)
        db.session.commit()
        log_audit(current_user.id, 'CREATE_CRYOVIAL', target_type='CryoVial', target_id=vial.id, details=f'box {box.id} R{row}C{col}')
        flash('Vial added.', 'success')
        return redirect(url_for('cell_storage.cryovial_inventory'))

    return render_template('main/manual_vial_form.html', form=form, box=box, row=row, col=col, form_action=url_for('cell_storage.add_vial_at_position', box_id=box_id, row=row, col=col), title='Add Vial')


@bp.route('/cryovial/<int:vial_id>/delete')
@login_required
@admin_required
def delete_cryovial(vial_id):
    vial = CryoVial.query.get_or_404(vial_id)
    db.session.delete(vial)
    db.session.commit()
    log_audit(current_user.id, 'DELETE_CRYOVIAL', target_type='CryoVial', target_id=vial_id)
    flash('Vial deleted.', 'success')
    return redirect(url_for('cell_storage.cryovial_inventory'))

@bp.route('/admin/batch_counter', methods=['POST'])
@login_required
@admin_required
def update_batch_counter():
    value = request.form.get('batch_counter')
    try:
        new_val = int(value)
        if new_val < 1:
            raise ValueError
        set_batch_counter(new_val)
        flash('Batch counter updated.', 'success')
    except (TypeError, ValueError):
        flash('Invalid batch counter value.', 'danger')
    return redirect(url_for('cell_storage.cryovial_inventory'))


@bp.route('/admin/vial_counter', methods=['POST'])
@login_required
@admin_required
def update_vial_counter():
    value = request.form.get('vial_counter')
    try:
        new_val = int(value)
        if new_val < 1:
            raise ValueError
        set_vial_counter(new_val)
        flash('Vial counter updated.', 'success')
    except (TypeError, ValueError):
        flash('Invalid vial counter value.', 'danger')
    return redirect(url_for('cell_storage.cryovial_inventory'))

@bp.route('/inventory/pickup', methods=['GET', 'POST'])
@login_required
def pickup_selected_vials():
    """Show selected vials and their locations for pick up."""
    selected_ids = session.get('pickup_ids', [])
    if not selected_ids:
        flash('No vials selected for pick up.', 'info')
        return redirect(url_for('cell_storage.cryovial_inventory'))

    vials = CryoVial.query.filter(CryoVial.id.in_(selected_ids)).join(Box).join(Drawer).join(Tower).join(VialBatch).join(CellLine).all()

    batches = {}
    color_map = {}
    color_index = 0
    for v in vials:
        b = batches.setdefault(v.batch_id, {
            'batch': v.batch,
            'cell_line': v.cell_line_info.name,
            'date_frozen': v.date_frozen,
            'vials': []
        })
        if v.date_frozen < b['date_frozen']:
            b['date_frozen'] = v.date_frozen
        b['vials'].append(v)

        if v.batch.name not in color_map:
            color_map[v.batch.name] = color_index % 7
            color_index += 1

    if request.method == 'POST':
        picked_boxes = {}
        picked_vials = []
        used_ids = []
        for bid, info in batches.items():
            qty = int(request.form.get(f'qty_{bid}', 0))
            to_use = info['vials'][:qty]
            for vial in to_use:
                vial.status = 'Used'
                vial.last_updated = datetime.utcnow()
                used_ids.append(vial.id)
                picked_vials.append(vial)
                box = vial.box_location
                pb = picked_boxes.setdefault(
                    box.id,
                    {
                        'box': box,
                        'rows': box.rows,
                        'columns': box.columns,
                        'cells': {},
                    },
                )
                pb['cells'][(vial.row_in_box, vial.col_in_box)] = vial
        db.session.commit()
        batch_ids = list({v.batch_id for v in picked_vials})
        log_audit(
            current_user.id,
            'PICKUP_VIALS',
            target_type='CryoVial',
            details={'vial_ids': used_ids, 'batch_ids': batch_ids},
        )
        session.pop('pickup_ids', None)
        
        # 显示拾取结果页面，包含位置信息
        return render_template('main/pickup_confirmation.html', 
                             title='Pick Up Confirmation',
                             picked_boxes=picked_boxes, 
                             picked_vials=picked_vials,
                             current_datetime=datetime.now())

    return render_template('main/pickup_selected_vials.html', batches=batches)


def find_available_slots_in_box(box, num_slots_needed):
    """Return up to ``num_slots_needed`` empty slots in ``box``."""
    occupied_slots = {
        (v.row_in_box, v.col_in_box)
        for v in CryoVial.query.filter_by(box_id=box.id, status='Available').all()
    }
    available_positions = []
    for r in range(1, box.rows + 1):
        for c in range(1, box.columns + 1):
            if (r, c) not in occupied_slots:
                available_positions.append({'row': r, 'col': c})
            if len(available_positions) >= num_slots_needed:
                return available_positions[:num_slots_needed]
    return available_positions

@bp.route('/cryovial/add', methods=['GET', 'POST'])
@login_required
def add_cryovial():
    form = CryoVialForm()
    form.cell_line_id.choices = [(cl.id, cl.name) for cl in CellLine.query.order_by(CellLine.name).all()]
    
    if request.method == 'GET':
        # Pre-select cell line if provided in URL, for workflow improvement
        cell_line_id = request.args.get('cell_line_id', type=int)
        if cell_line_id:
            form.cell_line_id.data = cell_line_id

    if 'proposed_placements' in session and request.method == 'POST' and request.form.get('confirm_placement') == 'yes':
        # Confirmation step for auto-placed vials
        placements = session.pop('proposed_placements', [])
        vial_common_data = session.pop('vial_common_data', {})

        if not placements or not vial_common_data:
            flash('Placement confirmation data lost. Please try again.', 'danger')
            return redirect(url_for('cell_storage.add_cryovial'))

        try:
            batch_id = get_next_batch_id(auto_commit=False)
            batch = VialBatch(
                id=batch_id,
                name=vial_common_data.get('batch_name'),
                created_by_user_id=current_user.id,
            )
            db.session.add(batch)
            db.session.flush()  # 确保batch ID可用但不提交
        except Exception as e:
            current_app.logger.error(f'Error creating batch: {str(e)}', exc_info=True)
            # If batch creation fails, clean up session and retry with a simple approach
            db.session.rollback()
            # Use simple max+1 approach as fallback
            max_id = db.session.query(db.func.max(VialBatch.id)).scalar() or 0
            batch = VialBatch(
                id=max_id + 1,
                name=vial_common_data.get('batch_name'),
                created_by_user_id=current_user.id,
            )
            db.session.add(batch)
            db.session.flush()
        created_vials_info = []
        quantity_being_added = len(placements) # Get the actual number from placements

        for i, p in enumerate(placements):
            # Use vial counter for unique ID generation
            # 使用正确的批次标签格式
            base_tag = f"B{batch.id}"
            unique_tag_suffix = f"-{i+1}" if quantity_being_added > 1 else ""
            unique_tag = f"{base_tag}{unique_tag_suffix}"

            existing_tag_vial = CryoVial.query.filter_by(unique_vial_id_tag=unique_tag).first()
            if existing_tag_vial:
                flash(f'Error: Generated vial tag "{unique_tag}" already exists. Please try again.', 'danger')
                session.pop('proposed_placements', None)
                session.pop('vial_common_data', None)
                return redirect(url_for('cell_storage.add_cryovial'))

            vial = CryoVial(
                unique_vial_id_tag=unique_tag,
                batch_id=batch.id,
                cell_line_id=vial_common_data['cell_line_id'],
                box_id=p['box_id'],
                row_in_box=p['row'],
                col_in_box=p['col'],
                passage_number=vial_common_data['passage_number'],
                date_frozen=datetime.strptime(vial_common_data['date_frozen_str'], '%Y-%m-%d').date(),
                frozen_by_user_id=current_user.id,
                volume_ml=vial_common_data['volume_ml'],
                concentration=vial_common_data['concentration'],
                fluorescence_tag=vial_common_data.get('fluorescence_tag'),
                resistance=vial_common_data.get('resistance'),
                parental_cell_line=vial_common_data.get('parental_cell_line'),
                status='Available',
                notes=vial_common_data['notes'],
                date_created=datetime.utcnow()
            )
            db.session.add(vial)
            created_vials_info.append(f"Vial {unique_tag} at Box ID {p['box_id']}, R{p['row']}C{p['col']}")

        try:
            db.session.flush() # Ensure vial IDs are available before commit
            # Get vial IDs for the audit log - collect them directly from created vials
            created_vials = db.session.query(CryoVial).filter_by(batch_id=batch.id).all()
            vial_ids = [v.id for v in created_vials if v.id is not None]
            
            # Create human-readable audit log
            readable_details = create_audit_log(
                user_id=current_user.id,
                action='CREATE_CRYOVIAL',
                target_type='VialBatch',
                target_id=batch.id,
                vial_ids=vial_ids,
                batch_id=batch.id,
                count=len(placements),
                batch_name=batch.name if batch.name else f"Batch #{batch.id}"
            )
            
            log_audit(
                current_user.id,
                'CREATE_CRYOVIAL',
                target_type='VialBatch',
                target_id=batch.id,
                details=readable_details
            )
            db.session.commit()
            flash(
                f"Batch #{batch.id} '{batch.name}' added with base ID {base_tag} and {len(placements)} vial(s): "
                + "; ".join(created_vials_info),
                'success'
            )
            return redirect(url_for('cell_storage.cryovial_inventory'))
        except Exception as e:
            db.session.rollback()
            # Log the full error for debugging
            current_app.logger.error(f'Error in vial placement confirmation: {str(e)}', exc_info=True)
            flash(f'Error saving vial(s): {str(e)}. Please try again.', 'danger')
            # Clear session data to prevent stuck state
            session.pop('proposed_placements', None)
            session.pop('vial_common_data', None)
            return redirect(url_for('cell_storage.add_cryovial'))

    if form.validate_on_submit():
        quantity = form.quantity_to_add.data # This will be 1 or more

        common_data_for_session = {
            'batch_name': form.batch_name.data,
            'cell_line_id': form.cell_line_id.data,
            'passage_number': form.passage_number.data,
            'date_frozen_str': form.date_frozen.data.strftime('%Y-%m-%d') if form.date_frozen.data else None,
            'volume_ml': form.volume_ml.data,
            'concentration': form.concentration.data,
            'fluorescence_tag': form.fluorescence_tag.data,
            'resistance': ','.join(form.resistance.data) if form.resistance.data else None,
            'parental_cell_line': form.parental_cell_line.data,
            'notes': form.notes.data
        }

        # Auto-allocation logic for ANY quantity (1 or more)
        # Modified logic: First try to find a single box that can accommodate all vials
        # Priority: boxes with smaller numeric identifiers (1-5) regardless of tower/drawer
        allocated_positions = []
        selected_boxes = []

        # Create a custom sorting function to prioritize boxes with numbers 1-5
        def box_priority_key(box):
            # Extract numeric part from box name for sorting
            import re
            numbers = re.findall(r'\d+', box.name)
            if numbers:
                # Convert first number found to integer for sorting
                first_num = int(numbers[0])
                # Prioritize boxes 1-5, then others
                if 1 <= first_num <= 5:
                    return (0, first_num)  # High priority group, sorted by number
                else:
                    return (1, first_num)  # Low priority group, sorted by number
            else:
                # Boxes without numbers go to the end
                return (2, box.name)

        all_boxes = Box.query.join(Drawer).join(Tower).all()
        # Sort boxes by priority: numbered 1-5 first, then others
        all_boxes_sorted = sorted(all_boxes, key=box_priority_key)

        # First attempt: try to find a single box that can accommodate all vials
        for box_candidate in all_boxes_sorted:
            slots = find_available_slots_in_box(box_candidate, quantity)
            if len(slots) == quantity:  # Found a box that can fit all vials
                selected_boxes.append(box_candidate)
                for slot in slots:
                    allocated_positions.append({
                        'box_id': box_candidate.id,
                        'box_name': box_candidate.name,
                        'tower_name': box_candidate.drawer_info.tower_info.name,
                        'drawer_name': box_candidate.drawer_info.name,
                        'row': slot['row'],
                        'col': slot['col']
                    })
                break  # Found a single box for all vials, stop here

        # If no single box can accommodate all vials, fall back to multiple boxes
        if len(allocated_positions) < quantity:
            allocated_positions = []
            selected_boxes = []
            for box_candidate in all_boxes_sorted:
                remaining = quantity - len(allocated_positions)
                if remaining <= 0:
                    break
                slots = find_available_slots_in_box(box_candidate, remaining)
                if slots:
                    selected_boxes.append(box_candidate)
                    for slot in slots:
                        allocated_positions.append({
                            'box_id': box_candidate.id,
                            'box_name': box_candidate.name,
                            'tower_name': box_candidate.drawer_info.tower_info.name,
                            'drawer_name': box_candidate.drawer_info.name,
                            'row': slot['row'],
                            'col': slot['col']
                        })

        if len(allocated_positions) == quantity:
            session['proposed_placements'] = allocated_positions
            session['vial_common_data'] = common_data_for_session

            boxes_details_for_map = []
            for b in selected_boxes:
                boxes_details_for_map.append({
                    'id': b.id,
                    'name': b.name,
                    'tower_name': b.drawer_info.tower_info.name,
                    'drawer_name': b.drawer_info.name,
                    'rows': b.rows,
                    'columns': b.columns,
                    'occupied': [
                        {'row': v.row_in_box, 'col': v.col_in_box, 'tag': v.batch_id}
                        for v in CryoVial.query.filter_by(box_id=b.id, status='Available').all()
                    ]
                })
            cell_line_name_for_confirm = CellLine.query.get(common_data_for_session['cell_line_id']).name

            return render_template(
                'main/confirm_multi_vial_placement.html',
                title='Confirm Vial Placement',
                placements=allocated_positions,
                common_data=common_data_for_session,
                cell_line_name_for_confirm=cell_line_name_for_confirm,
                boxes_details_for_map=boxes_details_for_map,
                quantity_to_add=quantity
            )
        else:
            flash(
                f'Could not find enough available slots for {quantity} vial(s).',
                'danger'
            )

    if request.method == 'GET' or not form.is_submitted():
        session.pop('proposed_placements', None)
        session.pop('vial_common_data', None)

    return render_template('main/cryovial_form.html', title='Add CryoVial(s)', form=form,
                           form_action=url_for('cell_storage.add_cryovial'))

@bp.route('/inventory', methods=['GET', 'POST'])
@login_required
def cryovial_inventory():
    """Display freezer inventory and provide a search with selectable results."""

    allowed_targets = {'batch', 'vial', 'cell_line', 'tag'}
    data_source = request.form if request.method == 'POST' else request.args

    def _clean(value):
        return value.strip() if value else ''

    search_q = _clean(data_source.get('q'))
    search_target = (data_source.get('target') or 'batch').lower()
    if search_target not in allowed_targets:
        search_target = 'batch'
    search_creator = _clean(data_source.get('creator'))
    search_fluorescence = _clean(data_source.get('fluorescence'))
    search_resistance = _clean(data_source.get('resistance'))
    search_status = _clean(data_source.get('status'))
    max_passage = _clean(data_source.get('max_passage'))
    date_from = _clean(data_source.get('date_from'))
    search_cell_line_raw = _clean(data_source.get('cell_line_id'))
    search_cell_line_id = int(search_cell_line_raw) if search_cell_line_raw.isdigit() else None
    view_all_flag = (data_source.get('view_all') or '').lower() == 'true'

    search_fields_used = any([
        search_q,
        search_creator,
        search_fluorescence,
        search_resistance,
        search_status,
        max_passage,
        date_from,
        search_cell_line_id,
    ])

    if view_all_flag:
        session['view_all_active'] = True
    elif search_fields_used:
        session.pop('view_all_active', None)
    else:
        view_all_flag = session.get('view_all_active', False)

    selected_ids = session.get('pickup_ids', [])
    if request.method == 'POST':
        if 'selected_batches' in request.form:
            batch_ids = request.form.getlist('selected_batches')
            added = 0
            for bid in batch_ids:
                try:
                    bid_int = int(bid)
                except ValueError:
                    continue
                vials_in_batch = CryoVial.query.filter_by(batch_id=bid_int, status='Available').all()
                for vial in vials_in_batch:
                    if vial.id not in selected_ids:
                        selected_ids.append(vial.id)
                        added += 1
            session['pickup_ids'] = selected_ids
            if added:
                flash(f"{added} vial(s) added to pick-up list.", 'success')
            redirect_params = {
                'q': search_q,
                'target': search_target,
                'creator': search_creator,
                'fluorescence': search_fluorescence,
                'resistance': search_resistance,
                'status': search_status,
                'max_passage': max_passage,
                'date_from': date_from,
            }
            if search_cell_line_id:
                redirect_params['cell_line_id'] = search_cell_line_id
            if view_all_flag:
                redirect_params['view_all'] = 'true'
            return redirect(url_for('cell_storage.cryovial_inventory', **redirect_params))
        elif 'remove_batches' in request.form:
            remove_ids = request.form.getlist('remove_batches')
            removed = 0
            for rid in remove_ids:
                try:
                    rid_int = int(rid)
                except ValueError:
                    continue
                remove_vials = CryoVial.query.filter(CryoVial.id.in_(selected_ids), CryoVial.batch_id == rid_int).all()
                for vial in remove_vials:
                    if vial.id in selected_ids:
                        selected_ids.remove(vial.id)
                        removed += 1
            if removed:
                if selected_ids:
                    session['pickup_ids'] = selected_ids
                else:
                    session.pop('pickup_ids', None)
                flash(f"{removed} vial(s) removed from pick-up list.", 'success')
            redirect_params = {
                'q': search_q,
                'target': search_target,
                'creator': search_creator,
                'fluorescence': search_fluorescence,
                'resistance': search_resistance,
                'status': search_status,
                'max_passage': max_passage,
                'date_from': date_from,
            }
            if search_cell_line_id:
                redirect_params['cell_line_id'] = search_cell_line_id
            if view_all_flag:
                redirect_params['view_all'] = 'true'
            return redirect(url_for('cell_storage.cryovial_inventory', **redirect_params))

    towers = Tower.query.order_by(Tower.name).all()
    all_creators = User.query.order_by(User.username).all()
    all_cell_lines = CellLine.query.order_by(CellLine.name).all()
    inventory = {}

    all_batches = VialBatch.query.all()
    batch_color_map = {batch.id: index % 12 for index, batch in enumerate(all_batches)}

    for tower in towers:
        tower_dict = {}
        for drawer in tower.drawers.order_by(Drawer.name).all():
            drawer_boxes = []
            for box in drawer.boxes.order_by(Box.name).all():
                vials_map = {}
                for vial in box.cryovials.order_by(CryoVial.unique_vial_id_tag):
                    if vial.status != 'Available':
                        continue
                    key = f"{vial.row_in_box}-{vial.col_in_box}"
                    vials_map[key] = {
                        'tag': vial.batch_id,
                        'status': vial.status,
                        'id': vial.id,
                        'batch_id': vial.batch_id,
                        'batch_color': batch_color_map.get(vial.batch_id, 0),
                    }
                drawer_boxes.append(
                    {
                        'id': box.id,
                        'name': box.name,
                        'drawer_name': drawer.name,
                        'tower_name': tower.name,
                        'rows': box.rows,
                        'columns': box.columns,
                        'vials': vials_map,
                    }
                )
            tower_dict[drawer.name] = drawer_boxes
        inventory[tower.name] = tower_dict

    search_results = None
    search_feedback = None
    search_suggestion = None
    recent_searches = session.get('recent_cryovial_searches', [])

    general_filters = []
    if search_creator:
        general_filters.append(User.username == search_creator)
    if search_fluorescence:
        general_filters.append(CryoVial.fluorescence_tag.ilike(f"%{search_fluorescence}%"))
    if search_resistance:
        general_filters.append(CryoVial.resistance.ilike(f"%{search_resistance}%"))
    if search_status:
        general_filters.append(CryoVial.status == search_status)
    if search_cell_line_id:
        general_filters.append(CryoVial.cell_line_id == search_cell_line_id)
    if max_passage:
        try:
            general_filters.append(CryoVial.passage <= int(max_passage))
        except ValueError:
            pass
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            general_filters.append(CryoVial.date_added >= from_date)
        except ValueError:
            pass

    base_query = (
        CryoVial.query.join(VialBatch)
        .join(CellLine)
        .join(User, VialBatch.created_by_user_id == User.id)
        .join(Box)
        .join(Drawer)
        .join(Tower)
    )
    if general_filters:
        for filter_clause in general_filters:
            base_query = base_query.filter(filter_clause)

    quality_rank = {'filter': 0, 'partial': 1, 'exact': 2}
    target_exact_labels = {
        'batch': 'Batch name exact match',
        'vial': 'Vial ID exact match',
        'cell_line': 'Cell line exact match',
        'tag': 'Tag exact match',
    }
    target_partial_labels = {
        'batch': 'Batch name partial match',
        'vial': 'Vial ID partial match',
        'cell_line': 'Cell line partial match',
        'tag': 'Tag partial match',
    }
    target_filter_labels = {
        'batch': 'Filtered results',
        'vial': 'Filtered results',
        'cell_line': 'Cell line filter',
        'tag': 'Filtered results',
    }

    vials = []
    match_quality = 'filter'

    if view_all_flag and not search_fields_used:
        vials = base_query.order_by(VialBatch.id, CryoVial.unique_vial_id_tag).all()
        match_quality = 'filter'
    elif search_q or search_fields_used:
        normalized_q = search_q.lower()
        if search_target == 'batch':
            exact_filters = []
            if search_q:
                exact_filters.append(func.lower(VialBatch.name) == normalized_q)
                if search_q.isdigit():
                    exact_filters.append(VialBatch.id == int(search_q))
            exact_match_results = base_query.filter(or_(*exact_filters)).all() if exact_filters else []
            if exact_match_results:
                vials = exact_match_results
                match_quality = 'exact'
                search_feedback = f"Exact batch match for \"{search_q}\"."
            else:
                like_pattern = f"%{search_q}%" if search_q else '%'
                partial_filters = [VialBatch.name.ilike(like_pattern)]
                if search_q and search_q.isdigit():
                    partial_filters.append(cast(VialBatch.id, String).ilike(like_pattern))
                vials = base_query.filter(or_(*partial_filters)).all()
                match_quality = 'partial' if search_q else 'filter'
                if search_q:
                    if vials:
                        search_feedback = f"No exact batch match for \"{search_q}\". Showing partial results."
                        search_suggestion = 'Found similarly named cell lines. Try switching search target to "Cell Line" if that was your intent.'
                    else:
                        search_feedback = f"No batch found for \"{search_q}\"."
        elif search_target == 'vial':
            exact_match_results = []
            if search_q:
                exact_match_results = base_query.filter(func.lower(CryoVial.unique_vial_id_tag) == normalized_q).all()
            if exact_match_results:
                vials = exact_match_results
                match_quality = 'exact'
                search_feedback = f"Found vial ID \"{search_q}\"."
            else:
                like_pattern = f"%{search_q}%" if search_q else '%'
                vials = base_query.filter(CryoVial.unique_vial_id_tag.ilike(like_pattern)).all()
                match_quality = 'partial' if search_q else 'filter'
                if search_q and not vials:
                    search_feedback = f"No vial found for \"{search_q}\"."
        elif search_target == 'cell_line':
            if search_cell_line_id:
                vials = base_query.all()
                match_quality = 'exact'
                search_feedback = 'Filtered by selected cell line.'
            elif search_q:
                exact_match_results = base_query.filter(func.lower(CellLine.name) == normalized_q).all()
                if exact_match_results:
                    vials = exact_match_results
                    match_quality = 'exact'
                    search_feedback = f"Exact cell line match for \"{search_q}\"."
                else:
                    like_pattern = f"%{search_q}%"
                    vials = base_query.filter(CellLine.name.ilike(like_pattern)).all()
                    match_quality = 'partial'
                    if vials:
                        search_feedback = f"No exact cell line match for \"{search_q}\". Showing partial results."
                    else:
                        search_feedback = f"No cell line found for \"{search_q}\"."
            else:
                vials = base_query.all()
                match_quality = 'filter'
        elif search_target == 'tag':
            if search_q:
                exact_match_results = base_query.filter(
                    or_(
                        func.lower(CryoVial.fluorescence_tag) == normalized_q,
                        func.lower(CryoVial.resistance) == normalized_q,
                    )
                ).all()
                if exact_match_results:
                    vials = exact_match_results
                    match_quality = 'exact'
                    search_feedback = f"Exact tag match for \"{search_q}\"."
                else:
                    like_pattern = f"%{search_q}%"
                    vials = base_query.filter(
                        or_(
                            CryoVial.fluorescence_tag.ilike(like_pattern),
                            CryoVial.resistance.ilike(like_pattern),
                            CryoVial.parental_cell_line.ilike(like_pattern),
                            CryoVial.notes.ilike(like_pattern),
                        )
                    ).all()
                    match_quality = 'partial'
                    if vials:
                        search_feedback = f"No exact tag match for \"{search_q}\". Showing partial results."
                    else:
                        search_feedback = f"No tags found for \"{search_q}\"."
            else:
                vials = base_query.all()
                match_quality = 'filter'
    else:
        vials = []

    grouped = {}
    for vial in vials:
        info = grouped.get(vial.batch_id)
        if not info:
            info = {
                'batch': vial.batch,
                'date_frozen': vial.date_frozen,
                'cell_line': vial.cell_line_info.name,
                'passage_number': vial.passage_number,
                'volume_ml': vial.volume_ml,
                'concentration': vial.concentration,
                'fluorescence_tag': vial.fluorescence_tag,
                'resistance': vial.resistance,
                'parental_cell_line': vial.parental_cell_line,
                'notes': vial.notes,
                'available_quantity': 0,
                'match_labels': set(),
                'match_quality': 'filter',
            }
            grouped[vial.batch_id] = info
        if vial.status == 'Available':
            info['available_quantity'] += 1
        if vial.date_frozen and (not info['date_frozen'] or vial.date_frozen < info['date_frozen']):
            info['date_frozen'] = vial.date_frozen

        if match_quality == 'exact':
            current_label = target_exact_labels.get(search_target, 'Exact match')
        elif match_quality == 'partial':
            current_label = target_partial_labels.get(search_target, 'Partial match')
        else:
            current_label = target_filter_labels.get(search_target, 'Filtered results')

        info['match_labels'].add(current_label)
        if quality_rank[match_quality] > quality_rank.get(info['match_quality'], 0):
            info['match_quality'] = match_quality

    if grouped:
        for entry in grouped.values():
            entry['match_labels'] = sorted(entry['match_labels'])
        search_results = list(grouped.values())
    elif search_fields_used or search_q or view_all_flag:
        search_results = []

    if request.method == 'GET' and search_q:
        recent_entry = {'q': search_q, 'target': search_target}
        recent_searches = [item for item in recent_searches if item != recent_entry]
        recent_searches.insert(0, recent_entry)
        session['recent_cryovial_searches'] = recent_searches[:5]
    recent_searches = session.get('recent_cryovial_searches', [])

    selected_batches = None
    if selected_ids:
        selected_vials = CryoVial.query.filter(CryoVial.id.in_(selected_ids)).join(VialBatch).join(CellLine).all()
        grouped_sel = {}
        for vial in selected_vials:
            info = grouped_sel.get(vial.batch_id)
            if not info:
                grouped_sel[vial.batch_id] = {
                    'batch': vial.batch,
                    'date_frozen': vial.date_frozen,
                    'count': 1,
                }
            else:
                info['count'] += 1
                if vial.date_frozen and (not info['date_frozen'] or vial.date_frozen < info['date_frozen']):
                    info['date_frozen'] = vial.date_frozen
        selected_batches = list(grouped_sel.values())

    all_fluorescence_tags = [
        item[0]
        for item in db.session.query(CryoVial.fluorescence_tag)
        .filter(CryoVial.fluorescence_tag.isnot(None) & (CryoVial.fluorescence_tag != ''))
        .distinct()
        .all()
    ]
    all_resistances = [
        item[0]
        for item in db.session.query(CryoVial.resistance)
        .filter(CryoVial.resistance.isnot(None) & (CryoVial.resistance != ''))
        .distinct()
        .all()
    ]

    return render_template(
        'main/cryovial_inventory.html',
        title='CryoVial Inventory',
        inventory=inventory,
        search_results=search_results,
        search_q=search_q,
        search_target=search_target,
        search_creator=search_creator,
        search_fluorescence=search_fluorescence,
        search_resistance=search_resistance,
        search_status=search_status,
        max_passage=max_passage,
        date_from=date_from,
        search_cell_line_id=search_cell_line_id,
        selected_batches=selected_batches,
        selected_ids=selected_ids,
        all_creators=all_creators,
        all_cell_lines=all_cell_lines,
        all_fluorescence_tags=all_fluorescence_tags,
        all_resistances=all_resistances,
        batch_counter=get_batch_counter(),
        vial_counter=get_vial_counter(),
        batch_color_map=batch_color_map,
        view_all=view_all_flag,
        recent_searches=recent_searches,
        search_feedback=search_feedback,
        search_suggestion=search_suggestion,
    )

# --- Moved Inventory Summary Route ---
@bp.route('/inventory/summary')
@login_required
@admin_required
def inventory_summary():
    """Display all cryovials for all users, grouped by batch with analytics."""
    search_q = request.args.get('q', '').strip()
    search_status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 25  # 每页显示25个批次

    query = CryoVial.query.join(VialBatch).join(CellLine)
    
    # Only join location tables if the user is an admin
    if current_user.is_admin:
        query = query.join(Box).join(Drawer).join(Tower)

    if search_q:
        like = f"%{search_q}%"
        query = query.filter(
            CryoVial.unique_vial_id_tag.ilike(like) |
            VialBatch.name.ilike(like) |
            CellLine.name.ilike(like)
        )
    if search_status:
        query = query.filter(CryoVial.status == search_status)

    # 计算总体统计数据（不受搜索筛选影响）
    total_stats = {}
    status_counts = db.session.query(
        CryoVial.status, 
        db.func.count(CryoVial.id)
    ).group_by(CryoVial.status).all()
    
    total_stats = {
        'total': sum(count for _, count in status_counts),
        'available': 0,
        'used': 0,
        'depleted': 0,
        'discarded': 0
    }
    
    for status, count in status_counts:
        if status == 'Available':
            total_stats['available'] = count
        elif status == 'Used':
            total_stats['used'] = count
        elif status == 'Depleted':
            total_stats['depleted'] = count
        elif status == 'Discarded':
            total_stats['discarded'] = count

    # 批次统计
    batch_stats = {
        'total_batches': VialBatch.query.count()
    }

    # 库存量低于2的库存记录
    low_stock_records = db.session.query(
        CellLine.name.label('cell_line_name'),
        VialBatch.name.label('batch_name'),
        VialBatch.id.label('batch_id'),
        db.func.count(CryoVial.id).label('available_count')
    ).join(CryoVial, CryoVial.cell_line_id == CellLine.id)\
     .join(VialBatch, CryoVial.batch_id == VialBatch.id)\
     .filter(CryoVial.status == 'Available')\
     .group_by(CellLine.name, VialBatch.name, VialBatch.id)\
     .having(db.func.count(CryoVial.id) < 2)\
     .order_by(db.func.count(CryoVial.id).asc(), CellLine.name.asc())\
     .all()
    
    low_stock_stats = {
        'total_cell_lines': CellLine.query.count(),
        'low_stock_records': [
            {
                'cell_line_name': record.cell_line_name,
                'batch_name': record.batch_name,
                'batch_id': record.batch_id,
                'available_count': record.available_count
            } for record in low_stock_records
        ]
    }

    # 先获取批次分页，然后获取对应的冻存管
    batch_query = db.session.query(VialBatch.id).distinct()
    if search_q:
        like = f"%{search_q}%"
        batch_query = batch_query.join(CryoVial).join(CellLine).filter(
            CryoVial.unique_vial_id_tag.ilike(like) |
            VialBatch.name.ilike(like) |
            CellLine.name.ilike(like)
        )
    if search_status:
        batch_query = batch_query.join(CryoVial).filter(CryoVial.status == search_status)
    
    batch_pagination = batch_query.order_by(VialBatch.id).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    batch_ids = [b.id for b in batch_pagination.items]
    
    if batch_ids:
        vials = query.filter(VialBatch.id.in_(batch_ids)).order_by(VialBatch.id, CryoVial.unique_vial_id_tag).all()
    else:
        vials = []
    
    statuses = ['Available', 'Used', 'Depleted', 'Discarded']

    # Manual grouping
    grouped_vials_dict = {}
    for vial in vials:
        if vial.batch.id not in grouped_vials_dict:
            grouped_vials_dict[vial.batch.id] = {
                'batch_obj': vial.batch,
                'cell_line_name': vial.cell_line_info.name,
                'passage_number': vial.passage_number,
                'date_frozen': vial.date_frozen,
                'vials': [],
                'total_count': 0,
                'status_counts': {status: 0 for status in statuses}
            }
        grouped_vials_dict[vial.batch.id]['vials'].append(vial)
        grouped_vials_dict[vial.batch.id]['total_count'] += 1
        if vial.status in grouped_vials_dict[vial.batch.id]['status_counts']:
            grouped_vials_dict[vial.batch.id]['status_counts'][vial.status] += 1
    
    # 按batch_ids的顺序排列
    grouped_vials = [grouped_vials_dict[bid] for bid in batch_ids if bid in grouped_vials_dict]

    if request.args.get('export') == 'csv':
        # CSV导出逻辑保持不变，但要获取所有数据而不是分页数据
        all_vials = query.order_by(VialBatch.id, CryoVial.unique_vial_id_tag).all()
        output = StringIO()
        writer = csv.writer(output)
        
        # Complete headers including all vial information
        headers = [
            'Vial ID', 'Batch ID', 'Batch Name', 'Vial Tag', 'Cell Line',
            'Passage Number', 'Date Frozen', 'Frozen By', 'Status'
        ]
        if current_user.is_admin:
            headers.append('Location')
        headers.extend([
            'Volume (ml)', 'Concentration', 'Fluorescence Tag', 
            'Resistance', 'Parental Cell Line', 'Notes'
        ])
        writer.writerow(headers)

        for v in all_vials:
            row_data = [
                v.id,
                v.batch.id,
                v.batch.name,
                v.unique_vial_id_tag,
                v.cell_line_info.name,
                v.passage_number or '',
                v.date_frozen,
                v.freezer_operator.username if v.freezer_operator else '',
                v.status,
            ]
            if current_user.is_admin:
                location = (
                    f"{v.box_location.drawer_info.tower_info.name}/"
                    f"{v.box_location.drawer_info.name}/"
                    f"{v.box_location.name} R{vial.row_in_box}C{vial.col_in_box}"
                )
                row_data.append(location)
            
            row_data.extend([
                v.volume_ml or '',
                v.concentration or '',
                v.fluorescence_tag or '',
                v.resistance or '',
                v.parental_cell_line or '',
                v.notes or ''
            ])
            writer.writerow(row_data)

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=inventory_summary.csv'},
        )

    return render_template(
        'main/inventory_summary.html',
        title='Analytics Dashboard',
        grouped_vials=grouped_vials,
        pagination=batch_pagination,
        statuses=statuses,
        search_q=search_q,
        search_status=search_status,
        total_stats=total_stats,
        batch_stats=batch_stats,
        low_stock_stats=low_stock_stats,
    )

@bp.route('/admin/import_csv', methods=['GET', 'POST'])
@login_required
@admin_required
def import_csv():
    form = CSVUploadForm()
    if form.validate_on_submit():
        if form.csv_files.data:
            # Process first file for now (TODO: enhance to handle multiple files)
            csv_file = form.csv_files.data[0]
            # 文件大小检查 (最大10MB)
            MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
            csv_file.seek(0, 2)  # 移动到文件末尾
            file_size = csv_file.tell()
            csv_file.seek(0)  # 重置到开始
            
            if file_size > MAX_FILE_SIZE:
                flash(f'File size ({file_size // (1024*1024)}MB) exceeds the maximum allowed size (10MB).', 'danger')
                return redirect(url_for('cell_storage.import_csv'))
            
            if file_size == 0:
                flash('The uploaded file is empty.', 'danger')
                return redirect(url_for('cell_storage.import_csv'))
            
            updated_count = 0
            created_count = 0
            skipped_rows = []
            try:
                # Ensure the file pointer is at the beginning
                csv_file.seek(0)
                
                # 尝试检测文件编码
                try:
                    raw_data = csv_file.read()
                    try:
                        content = raw_data.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            content = raw_data.decode('latin-1')
                        except UnicodeDecodeError:
                            content = raw_data.decode('utf-8', errors='replace')
                            flash('Warning: Some characters in the file could not be decoded properly.', 'warning')
                except Exception as e:
                    flash(f'Error reading file: {e}', 'danger')
                    return redirect(url_for('cell_storage.import_csv'))
                
                stream = io.StringIO(content, newline=None)
                try:
                    csv_input = csv.reader(stream)
                    header = next(csv_input)
                except StopIteration:
                    flash('The CSV file appears to be empty or has no header row.', 'danger')
                    return redirect(url_for('cell_storage.import_csv'))
                except csv.Error as e:
                    flash(f'Error parsing CSV file: {e}', 'danger')
                    return redirect(url_for('cell_storage.import_csv'))
                
                # 验证表头
                expected_headers_admin = [
                    'Vial ID', 'Batch ID', 'Batch Name', 'Vial Tag', 'Cell Line',
                    'Passage Number', 'Date Frozen', 'Frozen By', 'Status', 'Location',
                    'Volume (ml)', 'Concentration', 'Fluorescence Tag', 
                    'Resistance', 'Parental Cell Line', 'Notes'
                ]
                expected_headers_user = [
                    'Vial ID', 'Batch ID', 'Batch Name', 'Vial Tag', 'Cell Line',
                    'Passage Number', 'Date Frozen', 'Frozen By', 'Status',
                    'Volume (ml)', 'Concentration', 'Fluorescence Tag', 
                    'Resistance', 'Parental Cell Line', 'Notes'
                ]
                
                if header not in [expected_headers_admin, expected_headers_user]:
                    flash('CSV header does not match the expected format. Please use an unmodified export file from Inventory Summary.', 'danger')
                    return redirect(url_for('cell_storage.import_csv'))

                has_location = 'Location' in header
                row_count = 0
                
                for i, row in enumerate(csv_input, 2): # Start from line 2
                    row_count += 1
                    if row_count > 10000:  # 限制最大行数
                        flash('File contains too many rows (maximum 10,000 allowed). Please split into smaller files.', 'danger')
                        break
                        
                    if not any(field.strip() for field in row): # Skip empty rows
                        continue
                        
                    if len(row) != len(header):
                        skipped_rows.append((i, row, f"Row has {len(row)} columns, expected {len(header)} columns."))
                        continue
                        
                    row_data = dict(zip(header, row))

                    vial_id = row_data.get('Vial ID', '').strip()
                    vial_tag = row_data.get('Vial Tag', '').strip()
                    batch_name = row_data.get('Batch Name', '').strip()
                    cell_line_name = row_data.get('Cell Line', '').strip()
                    
                    # Determine if this is a new record or existing record
                    vial = None
                    is_new_record = False
                    
                    if vial_id:
                        # Try to find existing vial by ID
                        try:
                            vial = CryoVial.query.get(int(vial_id))
                        except (ValueError, TypeError):
                            # Invalid Vial ID format, treat as new record
                            is_new_record = True
                        else:
                            if vial:
                                # Found existing vial, sanity check vial tag
                                if vial_tag and vial.unique_vial_id_tag != vial_tag:
                                    skipped_rows.append((i, row, "Vial Tag in file does not match database record."))
                                    continue
                                # This is an update to existing record
                                is_new_record = False
                            else:
                                # Vial ID not found in database, treat as new record
                                is_new_record = True
                    else:
                        # Vial ID is empty, this is definitely a new record
                        is_new_record = True
                    
                    # For new records, validate required fields and check uniqueness
                    if is_new_record:
                        if not all([batch_name, cell_line_name, vial_tag]):
                            skipped_rows.append((i, row, "New records require Batch Name, Cell Line, and Vial Tag."))
                            continue
                            
                        # Check if vial tag already exists
                        if CryoVial.query.filter_by(unique_vial_id_tag=vial_tag).first():
                            skipped_rows.append((i, row, f"Vial Tag '{vial_tag}' already exists."))
                            continue

                    # Parse and validate date
                    date_frozen_str = row_data.get('Date Frozen', '').strip()
                    date_frozen = None
                    if date_frozen_str:
                        try:
                            date_frozen = datetime.strptime(date_frozen_str, '%Y-%m-%d').date()
                        except ValueError:
                            skipped_rows.append((i, row, "Invalid Date Frozen format (must be YYYY-MM-DD)."))
                            continue
                    
                    # Parse and validate location
                    box_id = None
                    row_in_box = None
                    col_in_box = None
                    if has_location:
                        location_str = row_data.get('Location', '').strip()
                        if location_str:
                            # Parse location string: "Tower 1/Drawer 1/Box 1 R1C2" (handles spaces in names)
                            location_match = re.match(r'(.+)/(.+)/(.+)\s+R(\d+)C(\d+)', location_str)
                            if location_match:
                                tower_name, drawer_name, box_name, row_str, col_str = location_match.groups()
                                # Strip whitespace from names
                                tower_name = tower_name.strip()
                                drawer_name = drawer_name.strip() 
                                box_name = box_name.strip()
                                
                                box = Box.query.join(Drawer).join(Tower).filter(
                                    Tower.name == tower_name,
                                    Drawer.name == drawer_name,
                                    Box.name == box_name
                                ).first()
                                
                                if box:
                                    box_id = box.id
                                    row_in_box = int(row_str)
                                    col_in_box = int(col_str)
                                else:
                                    skipped_rows.append((i, row, f"Location '{location_str}' not found. Looking for Tower: '{tower_name}', Drawer: '{drawer_name}', Box: '{box_name}'."))
                                    continue
                            else:
                                skipped_rows.append((i, row, "Invalid Location format."))
                                continue

                    if is_new_record:
                        # Create new vial record
                        
                        # Find or create batch
                        batch_id_from_csv = row_data.get('Batch ID', '').strip()
                        batch = None
                        
                        # First try to find batch by ID if provided in CSV
                        if batch_id_from_csv:
                            try:
                                batch = VialBatch.query.get(int(batch_id_from_csv))
                                if batch and batch.name != batch_name:
                                    # Batch ID exists but name doesn't match
                                    skipped_rows.append((i, row, f"Batch ID '{batch_id_from_csv}' exists but has different name '{batch.name}' (expected '{batch_name}')."))
                                    continue
                            except (ValueError, TypeError):
                                # Invalid Batch ID format, treat as new batch creation
                                pass
                        
                        # 修复：如果CSV指定了Batch ID但未找到对应记录，不应该通过名称查找
                        # 这会导致不同Batch ID的记录被错误合并
                        # if not batch:
                        #     batch = VialBatch.query.filter_by(name=batch_name).first()
                        
                        # 修复：正确的导入逻辑
                        if not batch:
                            # 如果CSV指定了Batch ID但数据库中不存在，使用指定的ID创建新batch
                            if batch_id_from_csv:
                                try:
                                    requested_id = int(batch_id_from_csv)
                                    # 检查ID是否已被其他batch占用
                                    existing_batch_with_id = VialBatch.query.get(requested_id)
                                    if existing_batch_with_id:
                                        # 这种情况在前面已经处理过了，不应该到达这里
                                        skipped_rows.append((i, row, f"Batch ID '{batch_id_from_csv}' already exists with different name."))
                                        continue
                                    
                                    # 创建具有指定ID的新batch
                                    batch = VialBatch(
                                        id=requested_id,
                                        name=batch_name,
                                        created_by_user_id=current_user.id
                                    )
                                    db.session.add(batch)
                                    db.session.flush()  # 获取ID但不提交
                                except ValueError:
                                    skipped_rows.append((i, row, f"Invalid Batch ID format: '{batch_id_from_csv}'"))
                                    continue
                            else:
                                # CSV没有指定Batch ID，尝试通过名称查找现有batch
                                batch = VialBatch.query.filter_by(name=batch_name).first()
                        
                        # 如果仍然没有找到batch，创建新batch（不指定ID，让数据库自动分配）
                        if not batch:
                            batch = VialBatch(
                                name=batch_name,
                                created_by_user_id=current_user.id
                            )
                            # If CSV specifies a Batch ID, try to use it
                            if batch_id_from_csv:
                                try:
                                    requested_id = int(batch_id_from_csv)
                                    # Check if this ID is already taken
                                    existing_batch = VialBatch.query.get(requested_id)
                                    if not existing_batch:
                                        batch.id = requested_id
                                except (ValueError, TypeError):
                                    # Invalid ID format, let database auto-assign
                                    pass
                            
                            db.session.add(batch)
                            db.session.flush()  # Get the ID
                        
                        # Find cell line
                        cell_line = CellLine.query.filter_by(name=cell_line_name).first()
                        if not cell_line:
                            skipped_rows.append((i, row, f"Cell Line '{cell_line_name}' not found. Please create it first."))
                            continue
                        
                        # For new records, location is required
                        if not all([box_id, row_in_box, col_in_box]):
                            skipped_rows.append((i, row, "New records require a valid Location."))
                            continue
                        
                        # Create new vial
                        vial = CryoVial(
                            unique_vial_id_tag=vial_tag,
                            batch_id=batch.id,
                            cell_line_id=cell_line.id,
                            box_id=box_id,
                            row_in_box=row_in_box,
                            col_in_box=col_in_box,
                            date_frozen=date_frozen or datetime.utcnow().date(),
                            frozen_by_user_id=current_user.id,
                            status=row_data.get('Status', 'Available').strip().capitalize(),
                            passage_number=row_data.get('Passage Number', ''),
                            volume_ml=float(row_data.get('Volume (ml)')) if row_data.get('Volume (ml)') and row_data.get('Volume (ml)').strip() else None,
                            concentration=row_data.get('Concentration', ''),
                            fluorescence_tag=row_data.get('Fluorescence Tag', ''),
                            resistance=row_data.get('Resistance', ''),
                            parental_cell_line=row_data.get('Parental Cell Line', ''),
                            notes=row_data.get('Notes', '')
                        )
                        
                        # If CSV specifies a Vial ID, try to use it
                        if vial_id:
                            try:
                                requested_vial_id = int(vial_id)
                                # Check if this ID is already taken
                                existing_vial = CryoVial.query.get(requested_vial_id)
                                if not existing_vial:
                                    vial.id = requested_vial_id
                            except (ValueError, TypeError):
                                # Invalid ID format, let database auto-assign
                                pass
                        db.session.add(vial)
                        created_count += 1
                        
                    else:
                        # Update existing vial
                        
                        # Update status if changed
                        new_status = row_data.get('Status', '').strip().capitalize()
                        if new_status and new_status != vial.status:
                            vial.status = new_status
                        
                        # Update date frozen if changed
                        if date_frozen and date_frozen != vial.date_frozen:
                            vial.date_frozen = date_frozen
                        
                        # Update location if changed and provided
                        if all([box_id, row_in_box, col_in_box]):
                            if (vial.box_id != box_id or 
                                vial.row_in_box != row_in_box or 
                                vial.col_in_box != col_in_box):
                                vial.box_id = box_id
                                vial.row_in_box = row_in_box
                                vial.col_in_box = col_in_box
                        
                        # Update additional fields
                        new_passage = row_data.get('Passage Number', '').strip()
                        if new_passage and new_passage != vial.passage_number:
                            vial.passage_number = new_passage
                        
                        new_volume = row_data.get('Volume (ml)', '').strip()
                        if new_volume:
                            try:
                                volume_float = float(new_volume)
                                if volume_float != vial.volume_ml:
                                    vial.volume_ml = volume_float
                            except ValueError:
                                pass  # Ignore invalid volume values
                        
                        new_concentration = row_data.get('Concentration', '').strip()
                        if new_concentration and new_concentration != vial.concentration:
                            vial.concentration = new_concentration
                        
                        new_fluorescence = row_data.get('Fluorescence Tag', '').strip()
                        if new_fluorescence and new_fluorescence != vial.fluorescence_tag:
                            vial.fluorescence_tag = new_fluorescence
                        
                        new_resistance = row_data.get('Resistance', '').strip()
                        if new_resistance and new_resistance != vial.resistance:
                            vial.resistance = new_resistance
                        
                        new_parental = row_data.get('Parental Cell Line', '').strip()
                        if new_parental and new_parental != vial.parental_cell_line:
                            vial.parental_cell_line = new_parental
                        
                        new_notes = row_data.get('Notes', '').strip()
                        if new_notes and new_notes != vial.notes:
                            vial.notes = new_notes

                        db.session.add(vial)
                        updated_count += 1

                db.session.commit()
                
                message_parts = []
                if updated_count > 0:
                    message_parts.append(f"{updated_count} vials updated")
                if created_count > 0:
                    message_parts.append(f"{created_count} new vials created")
                
                if message_parts:
                    flash(f'CSV import completed successfully! {", ".join(message_parts)}. You can now import another file or check the Inventory Summary to view your data.', 'success')
                else:
                    flash('CSV processed successfully. No changes were made as all data was already up to date.', 'info')
                    
                if skipped_rows:
                    # Create a summary of skipped reasons for a cleaner message
                    reasons_summary = {}
                    for _, _, reason in skipped_rows:
                        reasons_summary[reason] = reasons_summary.get(reason, 0) + 1
                    
                    summary_messages = [f"{count} rows skipped ({reason})" for reason, count in reasons_summary.items()]
                    flash(f'{len(skipped_rows)} total rows were skipped. Reasons: {"; ".join(summary_messages)}', 'warning')

                return redirect(url_for('cell_storage.import_csv'))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'CSV import error: {e}')
                flash(f'An unexpected error occurred during import: {e}', 'danger')
                return redirect(url_for('cell_storage.import_csv'))

    return render_template('main/import_csv.html', title='Import CSV', form=form)

@bp.route('/vial/<int:vial_id>/test')
@login_required
def vial_test(vial_id):
    """Simple test endpoint to verify basic functionality"""
    try:
        current_app.logger.info(f'Test endpoint accessed for vial ID {vial_id}')
        vial = CryoVial.query.get(vial_id)
        if not vial:
            return jsonify({"error": "Vial not found"}), 404
        return jsonify({
            "success": True,
            "vial_id": vial.id,
            "tag": vial.unique_vial_id_tag,
            "message": "Test endpoint working"
        })
    except Exception as e:
        current_app.logger.error(f'Test endpoint error: {e}')
        return jsonify({"error": str(e)}), 500

@bp.route('/vial/<int:vial_id>/details')
@login_required
def vial_details(vial_id):
    try:
        current_app.logger.info(f'Fetching vial details for ID {vial_id} by user {current_user.username}')
        
        vial = db.session.query(
            CryoVial
        ).options(
            joinedload(CryoVial.cell_line_info),
            joinedload(CryoVial.batch),
            joinedload(CryoVial.freezer_operator),
            joinedload(CryoVial.box_location).joinedload(Box.drawer_info).joinedload(Drawer.tower_info)
        ).get(vial_id)

        if not vial:
            current_app.logger.warning(f'Vial not found for ID {vial_id}')
            return jsonify({"error": "Vial not found"}), 404
        
        current_app.logger.debug(f'Found vial: {vial.unique_vial_id_tag} (ID: {vial.id})')

        # 安全地获取相关信息，防止None值导致的AttributeError
        try:
            cell_line_name = vial.cell_line_info.name if vial.cell_line_info else "Unknown"
            current_app.logger.debug(f'Cell line name: {cell_line_name}')
        except AttributeError as e:
            current_app.logger.warning(f'Error getting cell line name: {e}')
            cell_line_name = "Unknown"
            
        try:
            batch_name = vial.batch.name if vial.batch else "Unknown"
            current_app.logger.debug(f'Batch name: {batch_name}')
        except AttributeError as e:
            current_app.logger.warning(f'Error getting batch name: {e}')
            batch_name = "Unknown"
            
        try:
            frozen_by = vial.freezer_operator.username if vial.freezer_operator else "Unknown"
            current_app.logger.debug(f'Frozen by: {frozen_by}')
        except AttributeError as e:
            current_app.logger.warning(f'Error getting frozen by: {e}')
            frozen_by = "Unknown"
            
        try:
            if vial.box_location and vial.box_location.drawer_info and vial.box_location.drawer_info.tower_info:
                location = f"{vial.box_location.drawer_info.tower_info.name}/{vial.box_location.drawer_info.name}/{vial.box_location.name} (R{vial.row_in_box}C{vial.col_in_box})"
            else:
                location = "Location not available"
            current_app.logger.debug(f'Location: {location}')
        except AttributeError as e:
            current_app.logger.warning(f'Error getting location: {e}')
            location = "Location not available"

        response_data = {
            "id": vial.id,
            "unique_vial_id_tag": vial.unique_vial_id_tag or "Unknown",
            "cell_line": cell_line_name,
            "batch_name": batch_name,
            "passage_number": vial.passage_number or "N/A",
            "date_frozen": vial.date_frozen.strftime('%Y-%m-%d') if vial.date_frozen else "N/A",
            "frozen_by": frozen_by,
            "status": vial.status or "Unknown",
            "notes": vial.notes or "No notes available",
            "location": location,
            "is_admin": current_user.is_admin  # 添加用户权限信息
        }
        
        current_app.logger.info(f'Successfully fetched vial details for ID {vial_id}')
        return jsonify(response_data)
    except Exception as e:
        current_app.logger.error(f'Error fetching vial details for ID {vial_id}: {e}')
        current_app.logger.error(f'Error details: {str(e)}')
        return jsonify({"error": "Unable to fetch vial details. Please try again later."}), 500


@bp.route('/vial/<int:vial_id>/delete', methods=['POST'])
@login_required 
@admin_required
def delete_vial(vial_id):
    try:
        # 验证CSRF token
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token or not validate_csrf_token(csrf_token):
            return jsonify({"success": False, "error": "CSRF token validation failed"}), 400
        
        vial = CryoVial.query.get_or_404(vial_id)
        
        # 记录日志
        readable_details = create_audit_log(
            user_id=current_user.id,
            action='DELETE',
            target_type='CryoVial',
            target_id=vial.id,
            vial_tag=vial.unique_vial_id_tag,
            batch_id=vial.batch_id,
            batch_name=vial.batch.name if vial.batch else 'Unknown'
        )
        log_audit(current_user.id, 'DELETE', target_type='CryoVial', target_id=vial.id, details=readable_details)
        
        # 删除vial
        db.session.delete(vial)
        db.session.commit()
        
        return jsonify({"success": True, "message": f"Successfully deleted {vial_info}"})
    except Exception as e:
        current_app.logger.error(f'Error deleting vial {vial_id}: {e}')
        return jsonify({"success": False, "error": "Unable to delete vial. Please try again later."}), 500


@bp.route('/admin/batch_delete_vials', methods=['POST'])
@login_required 
@admin_required
def batch_delete_vials():
    try:
        # 验证CSRF token
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token or not validate_csrf_token(csrf_token):
            return jsonify({"success": False, "error": "CSRF token validation failed"}), 400
        
        data = request.get_json()
        vial_ids = data.get('vial_ids', [])
        
        if not vial_ids:
            return jsonify({"success": False, "error": "No vial IDs provided"}), 400
        
        # 获取要删除的vials
        vials = CryoVial.query.filter(CryoVial.id.in_(vial_ids)).all()
        
        if not vials:
            return jsonify({"success": False, "error": "No vials found"}), 404
        
        deleted_count = 0
        vial_info_list = []
        
        for vial in vials:
            vial_info = f"Vial {vial.unique_vial_id_tag} (Batch: {vial.batch.name if vial.batch else 'Unknown'})"
            vial_info_list.append(vial_info)
            
            # 删除vial
            db.session.delete(vial)
            deleted_count += 1
        
        # 记录批量删除的总体日志
        readable_details = create_audit_log(
            user_id=current_user.id,
            action='BATCH_DELETE',
            target_type='Batch',
            target_id=None,
            vial_ids=vial_ids,
            count=deleted_count
        )
        log_audit(current_user.id, 'BATCH_DELETE', target_type='Batch', target_id=None, details=readable_details)
        
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} vials"
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error batch deleting vials {vial_ids}: {e}')
        return jsonify({"success": False, "error": "Unable to delete vials. Please try again later."}), 500

# =============================================================================
# 预警管理相关路由
# =============================================================================

@bp.route('/alerts')
@login_required
@admin_required
def alerts_management():
    """预警管理页面"""
    from app.shared.utils import get_active_alerts
    from app.cell_storage.models import Alert
    
    # 获取查询参数
    status_filter = request.args.get('status', 'active')  # active, resolved, dismissed, all
    alert_type_filter = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 构建查询
    query = Alert.query
    
    if status_filter == 'active':
        query = query.filter_by(is_resolved=False, is_dismissed=False)
    elif status_filter == 'resolved':
        query = query.filter_by(is_resolved=True)
    elif status_filter == 'dismissed':
        query = query.filter_by(is_dismissed=True)
    # 'all' 不添加额外过滤条件
    
    if alert_type_filter:
        query = query.filter_by(alert_type=alert_type_filter)
    
    # 分页查询
    alerts_pagination = query.order_by(Alert.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取统计信息
    alert_stats = {
        'active': Alert.query.filter_by(is_resolved=False, is_dismissed=False).count(),
        'resolved': Alert.query.filter_by(is_resolved=True).count(),
        'dismissed': Alert.query.filter_by(is_dismissed=True).count(),
        'total': Alert.query.count()
    }
    
    # 获取预警类型列表
    alert_types = db.session.query(Alert.alert_type).distinct().all()
    alert_types = [t[0] for t in alert_types]
    
    return render_template(
        'main/alerts_management.html',
        title='Alerts Management',
        alerts_pagination=alerts_pagination,
        alert_stats=alert_stats,
        alert_types=alert_types,
        status_filter=status_filter,
        alert_type_filter=alert_type_filter
    )


@bp.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_alert_api(alert_id):
    """解决预警API"""
    from app.shared.utils import resolve_alert
    
    try:
        alert = resolve_alert(alert_id, current_user.id)
        if alert:
            return jsonify({
                'success': True,
                'message': f'Alert "{alert.title}" has been resolved.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Alert not found or already resolved.'
            }), 404
    except Exception as e:
        current_app.logger.error(f'Error resolving alert {alert_id}: {e}')
        return jsonify({
            'success': False,
            'message': 'An error occurred while resolving the alert.'
        }), 500


@bp.route('/api/alerts/<int:alert_id>/dismiss', methods=['POST'])
@login_required
@admin_required
def dismiss_alert_api(alert_id):
    """忽略预警API"""
    from app.shared.utils import dismiss_alert
    
    try:
        alert = dismiss_alert(alert_id, current_user.id)
        if alert:
            return jsonify({
                'success': True,
                'message': f'Alert "{alert.title}" has been dismissed.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Alert not found or already dismissed.'
            }), 404
    except Exception as e:
        current_app.logger.error(f'Error dismissing alert {alert_id}: {e}')
        return jsonify({
            'success': False,
            'message': 'An error occurred while dismissing the alert.'
        }), 500


@bp.route('/api/alerts/generate', methods=['POST'])
@login_required
@admin_required
def generate_alerts_api():
    """手动生成预警API"""
    from app.shared.utils import generate_all_alerts
    
    try:
        alert_count = generate_all_alerts()
        return jsonify({
            'success': True,
            'message': f'Generated {alert_count} new alerts.',
            'alert_count': alert_count
        })
    except Exception as e:
        current_app.logger.error(f'Error generating alerts: {e}')
        return jsonify({
            'success': False,
            'message': 'An error occurred while generating alerts.'
        }), 500


# =============================================================================
# 高级搜索相关API
# =============================================================================

@bp.route('/api/search/suggestions')
@login_required
def search_suggestions():
    """搜索建议API"""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', 'all')  # all, vials, batches, cell_lines
    limit = min(int(request.args.get('limit', 10)), 20)  # 最多20个建议
    
    if len(query) < 2:
        return jsonify({'suggestions': []})
    
    suggestions = []
    
    try:
        if category in ['all', 'vials']:
            # 冻存管标签建议
            vial_tags = db.session.query(CryoVial.unique_vial_id_tag)\
                .filter(CryoVial.unique_vial_id_tag.ilike(f'%{query}%'))\
                .distinct().limit(limit//3 if category == 'all' else limit).all()
            
            for tag, in vial_tags:
                suggestions.append({
                    'type': 'vial',
                    'value': tag,
                    'label': f'Vial: {tag}',
                    'icon': 'thermometer-snow'
                })
        
        if category in ['all', 'batches']:
            # 批次名称建议
            batch_names = db.session.query(VialBatch.name)\
                .filter(VialBatch.name.ilike(f'%{query}%'))\
                .distinct().limit(limit//3 if category == 'all' else limit).all()
            
            for name, in batch_names:
                suggestions.append({
                    'type': 'batch',
                    'value': name,
                    'label': f'Batch: {name}',
                    'icon': 'collection'
                })
        
        if category in ['all', 'cell_lines']:
            # 细胞系名称建议
            cell_line_names = db.session.query(CellLine.name)\
                .filter(CellLine.name.ilike(f'%{query}%'))\
                .distinct().limit(limit//3 if category == 'all' else limit).all()
            
            for name, in cell_line_names:
                suggestions.append({
                    'type': 'cell_line',
                    'value': name,
                    'label': f'Cell Line: {name}',
                    'icon': 'diagram-3'
                })
        
        # 荧光标签建议
        if category in ['all']:
            fluorescence_tags = db.session.query(CryoVial.fluorescence_tag)\
                .filter(CryoVial.fluorescence_tag.ilike(f'%{query}%'))\
                .filter(CryoVial.fluorescence_tag.isnot(None))\
                .filter(CryoVial.fluorescence_tag != '')\
                .distinct().limit(3).all()
            
            for tag, in fluorescence_tags:
                suggestions.append({
                    'type': 'fluorescence',
                    'value': tag,
                    'label': f'Fluorescence: {tag}',
                    'icon': 'lightbulb'
                })
        
        # 排序并限制结果
        suggestions = suggestions[:limit]
        
        return jsonify({
            'suggestions': suggestions,
            'query': query
        })
        
    except Exception as e:
        current_app.logger.error(f'Error generating search suggestions: {e}')
        return jsonify({'suggestions': []})


@bp.route('/api/search/history')
@login_required
def search_history():
    """获取用户搜索历史"""
    # 从session中获取搜索历史
    search_history = session.get('search_history', [])
    return jsonify({'history': search_history[-10:]})  # 最近10个搜索


@bp.route('/api/search/history', methods=['POST'])
@login_required
def add_search_history():
    """添加搜索历史"""
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if query and len(query) >= 2:
        search_history = session.get('search_history', [])
        
        # 移除重复项
        if query in search_history:
            search_history.remove(query)
        
        # 添加到开头
        search_history.insert(0, query)
        
        # 限制历史记录数量
        search_history = search_history[:20]
        
        session['search_history'] = search_history
        session.permanent = True
        
        return jsonify({'success': True})
    
    return jsonify({'success': False})


@bp.route('/api/search/advanced')
@login_required
def advanced_search_api():
    """高级搜索API"""
    # 搜索参数
    query = request.args.get('q', '').strip()
    cell_line_id = request.args.get('cell_line_id', type=int)
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    creator_id = request.args.get('creator_id', type=int)
    fluorescence = request.args.get('fluorescence', '')
    resistance = request.args.get('resistance', '')
    batch_id = request.args.get('batch_id', type=int)
    location_type = request.args.get('location_type', '')  # tower, drawer, box
    location_id = request.args.get('location_id', type=int)
    
    # 基础查询
    vial_query = CryoVial.query.join(VialBatch).join(CellLine)
    
    # 添加用户权限相关的表
    vial_query = vial_query.join(User, VialBatch.created_by_user_id == User.id)
    
    # 添加位置相关的表
    if current_user.is_admin:
        vial_query = vial_query.join(Box).join(Drawer).join(Tower)
    
    # 应用搜索条件
    if query:
        like_pattern = f'%{query}%'
        vial_query = vial_query.filter(
            (CryoVial.unique_vial_id_tag.ilike(like_pattern)) |
            (VialBatch.name.ilike(like_pattern)) |
            (CellLine.name.ilike(like_pattern)) |
            (CryoVial.fluorescence_tag.ilike(like_pattern)) |
            (CryoVial.resistance.ilike(like_pattern)) |
            (CryoVial.notes.ilike(like_pattern))
        )
    
    if cell_line_id:
        vial_query = vial_query.filter(CryoVial.cell_line_id == cell_line_id)
    
    if status:
        vial_query = vial_query.filter(CryoVial.status == status)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            vial_query = vial_query.filter(CryoVial.date_frozen >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            vial_query = vial_query.filter(CryoVial.date_frozen <= to_date)
        except ValueError:
            pass
    
    if creator_id:
        vial_query = vial_query.filter(VialBatch.created_by_user_id == creator_id)
    
    if fluorescence:
        vial_query = vial_query.filter(CryoVial.fluorescence_tag.ilike(f'%{fluorescence}%'))
    
    if resistance:
        vial_query = vial_query.filter(CryoVial.resistance.ilike(f'%{resistance}%'))
    
    if batch_id:
        vial_query = vial_query.filter(CryoVial.batch_id == batch_id)
    
    # 位置过滤
    if current_user.is_admin and location_type and location_id:
        if location_type == 'tower':
            vial_query = vial_query.filter(Tower.id == location_id)
        elif location_type == 'drawer':
            vial_query = vial_query.filter(Drawer.id == location_id)
        elif location_type == 'box':
            vial_query = vial_query.filter(Box.id == location_id)
    
    # 执行查询并分页
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    
    vials_pagination = vial_query.order_by(VialBatch.id, CryoVial.unique_vial_id_tag)\
                                .paginate(page=page, per_page=per_page, error_out=False)
    
    # 格式化结果
    results = []
    for vial in vials_pagination.items:
        vial_data = {
            'id': vial.id,
            'unique_vial_id_tag': vial.unique_vial_id_tag,
            'batch_name': vial.batch.name,
            'batch_id': vial.batch_id,
            'cell_line_name': vial.cell_line_info.name,
            'status': vial.status,
            'date_frozen': vial.date_frozen.strftime('%Y-%m-%d') if vial.date_frozen else None,
            'fluorescence_tag': vial.fluorescence_tag,
            'resistance': vial.resistance,
            'notes': vial.notes
        }
        
        # 添加位置信息（如果用户是管理员）
        if current_user.is_admin:
            vial_data.update({
                'location': {
                    'tower_name': vial.box_location.drawer_info.tower_info.name,
                    'drawer_name': vial.box_location.drawer_info.name,
                    'box_name': vial.box_location.name,
                    'position': f'R{vial.row_in_box}C{vial.col_in_box}'
                }
            })
        
        results.append(vial_data)
    
    return jsonify({
        'results': results,
        'pagination': {
            'page': vials_pagination.page,
            'pages': vials_pagination.pages,
            'per_page': vials_pagination.per_page,
            'total': vials_pagination.total,
            'has_prev': vials_pagination.has_prev,
            'has_next': vials_pagination.has_next
        }
    })


# =============================================================================
# 批量操作相关API
# =============================================================================

@bp.route('/api/vials/batch-update-status', methods=['POST'])
@login_required
@admin_required
def batch_update_vials_status():
    """批量更新冻存管状态"""
    try:
        data = request.get_json()
        vial_ids = data.get('vial_ids', [])
        new_status = data.get('status', '')
        
        if not vial_ids or not new_status:
            return jsonify({
                'success': False,
                'message': 'Missing vial IDs or status.'
            }), 400
        
        if new_status not in ['Available', 'Used', 'Depleted', 'Discarded']:
            return jsonify({
                'success': False,
                'message': 'Invalid status value.'
            }), 400
        
        # 查询要更新的冻存管
        vials = CryoVial.query.filter(CryoVial.id.in_(vial_ids)).all()
        
        if not vials:
            return jsonify({
                'success': False,
                'message': 'No vials found with the provided IDs.'
            }), 404
        
        # 记录更新前的状态
        old_statuses = {vial.id: vial.status for vial in vials}
        
        # 批量更新状态
        updated_count = 0
        for vial in vials:
            old_status = vial.status
            vial.status = new_status
            updated_count += 1
            
            # 记录审计日志
            log_audit(
                user_id=current_user.id,
                action='UPDATE_VIAL_STATUS',
                target_type='CryoVial',
                target_id=vial.id,
                details={
                    'old_status': old_status,
                    'new_status': new_status,
                    'vial_tag': vial.unique_vial_id_tag,
                    'batch_operation': True
                }
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated {updated_count} vials to status: {new_status}',
            'updated_count': updated_count
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in batch status update: {e}')
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating vial statuses.'
        }), 500


@bp.route('/api/vials/batch-export', methods=['POST'])
@login_required
@admin_required
def batch_export_vials():
    """批量导出选中的冻存管"""
    try:
        data = request.get_json()
        vial_ids = data.get('vial_ids', [])
        
        if not vial_ids:
            return jsonify({
                'success': False,
                'message': 'No vials selected for export.'
            }), 400
        
        # 查询选中的冻存管
        vials = db.session.query(CryoVial).join(VialBatch).join(CellLine)\
                          .filter(CryoVial.id.in_(vial_ids))\
                          .order_by(VialBatch.id, CryoVial.unique_vial_id_tag).all()
        
        if not vials:
            return jsonify({
                'success': False,
                'message': 'No vials found with the provided IDs.'
            }), 404
        
        # 生成CSV数据
        output = StringIO()
        writer = csv.writer(output)
        
        # 表头
        headers = [
            'Vial ID', 'Batch ID', 'Batch Name', 'Vial Tag', 'Cell Line',
            'Passage Number', 'Date Frozen', 'Frozen By', 'Status'
        ]
        if current_user.is_admin:
            headers.append('Location')
        headers.extend([
            'Volume (ml)', 'Concentration', 'Fluorescence Tag', 
            'Resistance', 'Parental Cell Line', 'Notes'
        ])
        writer.writerow(headers)
        
        # 数据行
        for vial in vials:
            row_data = [
                vial.id,
                vial.batch.id,
                vial.batch.name,
                vial.unique_vial_id_tag,
                vial.cell_line_info.name,
                vial.passage_number or '',
                vial.date_frozen,
                vial.freezer_operator.username if vial.freezer_operator else '',
                vial.status,
            ]
            if current_user.is_admin:
                location = (
                    f"{vial.box_location.drawer_info.tower_info.name}/"
                    f"{vial.box_location.drawer_info.name}/"
                    f"{vial.box_location.name} R{vial.row_in_box}C{vial.col_in_box}"
                )
                row_data.append(location)
            
            row_data.extend([
                vial.volume_ml or '',
                vial.concentration or '',
                vial.fluorescence_tag or '',
                vial.resistance or '',
                vial.parental_cell_line or '',
                vial.notes or ''
            ])
            writer.writerow(row_data)
        
        # 记录审计日志
        log_audit(
            user_id=current_user.id,
            action='BATCH_EXPORT_VIALS',
            details={
                'vial_count': len(vials),
                'vial_ids': vial_ids[:10]  # 只记录前10个ID
            }
        )
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment;filename=selected_vials_{len(vials)}_items.csv'
            }
        )
        
    except Exception as e:
        current_app.logger.error(f'Error in batch export: {e}')
        return jsonify({
            'success': False,
            'message': 'An error occurred while exporting vials.'
        }), 500

@bp.route('/theme-settings')
@login_required
def theme_settings():
    """Theme settings page"""
    from app.shared.utils import get_available_themes, get_user_theme
    
    available_themes = get_available_themes()
    current_theme = get_user_theme(current_user.id)
    
    return render_template(
        'main/theme_settings.html',
        title='Theme Settings',
        available_themes=available_themes,
        current_theme=current_theme
    )

@bp.route('/api/theme/switch', methods=['POST'])
@login_required
def switch_theme():
    """Switch theme API"""
    try:
        # CSRF token validation
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token:
            current_app.logger.error('Theme switch error: Missing CSRF token')
            return jsonify({'success': False, 'message': 'Missing CSRF token'}), 400
        
        try:
            from flask_wtf.csrf import validate_csrf
            validate_csrf(csrf_token)
        except Exception as csrf_error:
            current_app.logger.error(f'Theme switch CSRF validation error: {csrf_error}')
            return jsonify({'success': False, 'message': 'Invalid CSRF token'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        theme_name = data.get('theme_name')
        if not theme_name:
            return jsonify({'success': False, 'message': 'Theme name cannot be empty'}), 400
        
        from app.shared.utils import update_user_theme
        success, message = update_user_theme(current_user.id, theme_name)
        
        if success:
            current_app.logger.info(f'Theme switched successfully for user {current_user.id} to {theme_name}')
            return jsonify({'success': True, 'message': message})
        else:
            current_app.logger.error(f'Theme switch failed for user {current_user.id}: {message}')
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f'Theme switch error: {e}')
        return jsonify({'success': False, 'message': f'Theme switch failed: {str(e)}'}), 500

@bp.route('/api/theme/current')
@login_required
def get_current_theme():
    """Get current theme configuration API"""
    try:
        from app.shared.utils import get_user_theme, get_theme_css_variables
        theme_config = get_user_theme(current_user.id)
        css_variables = get_theme_css_variables(theme_config)
        
        return jsonify({
            'success': True,
            'theme': theme_config,
            'css_variables': css_variables
        })
    except Exception as e:
        current_app.logger.error(f'Get theme error: {e}')
        return jsonify({'success': False, 'message': 'Failed to get theme configuration'}), 500

@bp.route('/api/dashboard/stats')
@login_required
def get_dashboard_stats():
    """Get dashboard statistics API"""
    try:
        # 总体统计
        total_vials = CryoVial.query.count()
        available_vials = CryoVial.query.filter_by(status='Available').count()
        used_vials = CryoVial.query.filter_by(status='Used').count()
        
        # 存储容量统计（基于实际box尺寸）
        total_boxes = Box.query.count()
        occupied_positions = CryoVial.query.filter_by(status='Available').count()
        
        # 计算实际总容量（每个box的rows * columns）
        boxes = Box.query.all()
        actual_total_capacity = sum(box.rows * box.columns for box in boxes)
        capacity_used_percent = (occupied_positions / actual_total_capacity * 100) if actual_total_capacity > 0 else 0
        
        # Low stock统计 - 基于batch的vials数量
        # 只统计有vials的batch，计算其中可用vials数量少于阈值的batch数量
        from sqlalchemy import func
        batch_vial_counts = db.session.query(
            VialBatch.id,
            func.count(CryoVial.id).label('total_count'),
            func.sum(func.case([(CryoVial.status == 'Available', 1)], else_=0)).label('available_count')
        ).join(
            CryoVial, CryoVial.batch_id == VialBatch.id
        ).group_by(VialBatch.id).all()
        
        # 定义低库存阈值为可用vials少于2个（且batch中有vials存在）
        low_stock_threshold = 2
        low_stock_batches = sum(1 for _, total_count, available_count in batch_vial_counts 
                              if total_count > 0 and (available_count or 0) < low_stock_threshold)
        
        return jsonify({
            'success': True,
            'stats': {
                'total_vials': total_vials,
                'available_vials': available_vials,
                'used_vials': used_vials,
                'capacity_used_percent': round(capacity_used_percent, 1),
                'low_stock_batches': low_stock_batches,
                'actual_total_capacity': actual_total_capacity,
                'total_boxes': total_boxes
            }
        })
    except Exception as e:
        current_app.logger.error(f'Dashboard stats error: {e}')
        return jsonify({'success': False, 'message': 'Failed to get dashboard statistics'}), 500


# --- Batch Lineage API Endpoints ---

@bp.route('/api/batch/<int:batch_id>/lineage')
@login_required
def get_batch_lineage(batch_id):
    """Get complete batch lineage tree"""
    try:
        from app.services.batch_lineage_service import BatchLineageService
        
        # Check if batch exists first
        batch = VialBatch.query.get(batch_id)
        if not batch:
            return jsonify({'success': False, 'message': f'Batch {batch_id} not found'}), 404
        
        max_depth = request.args.get('max_depth', 5, type=int)
        lineage = BatchLineageService.get_batch_lineage(batch_id, max_depth)
        
        return jsonify({
            'success': True,
            'lineage': lineage
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f'Batch lineage error for batch {batch_id}: {e}\n{error_details}')
        return jsonify({
            'success': False, 
            'message': f'Failed to get batch lineage: {str(e)}'
        }), 500


@bp.route('/api/batch/<int:batch_id>/lineage/statistics')
@login_required
def get_batch_lineage_statistics(batch_id):
    """获取batch家谱的统计信息"""
    try:
        from app.services.batch_lineage_service import BatchLineageService
        
        stats = BatchLineageService.get_lineage_statistics(batch_id)
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        current_app.logger.error(f'Batch lineage statistics error: {e}')
        return jsonify({'success': False, 'message': 'Failed to get lineage statistics'}), 500


@bp.route('/api/batch/<int:batch_id>/related')
@login_required
def get_related_batches(batch_id):
    """获取与指定batch相关的batch列表"""
    try:
        from app.services.batch_lineage_service import BatchLineageService
        
        relationship_type = request.args.get('type', 'all')  # parents, children, siblings, all
        related_batches = BatchLineageService.find_related_batches(batch_id, relationship_type)
        
        # 将batch对象转换为JSON格式
        related_data = []
        for batch in related_batches:
            related_data.append({
                'id': batch.id,
                'name': batch.name,
                'cell_line': batch.cell_line,
                'passage_number': batch.passage_number,
                'date_frozen': batch.date_frozen.isoformat() if batch.date_frozen else None,
                'parental_cell_line': batch.parental_cell_line,
                'vial_count': batch.vials.count(),
                'timestamp': batch.timestamp.isoformat() if batch.timestamp else None
            })
        
        return jsonify({
            'success': True,
            'related_batches': related_data,
            'relationship_type': relationship_type,
            'count': len(related_data)
        })
    except Exception as e:
        current_app.logger.error(f'Related batches error: {e}')
        return jsonify({'success': False, 'message': 'Failed to get related batches'}), 500


@bp.route('/api/batch/suggest-parental-lines')
@login_required
def suggest_parental_lines():
    """为新batch建议可能的parental cell line"""
    try:
        from app.services.batch_lineage_service import BatchLineageService
        
        query = request.args.get('q', '')
        limit = request.args.get('limit', 10, type=int)
        
        suggestions = BatchLineageService.suggest_parental_cell_lines(query, limit)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        current_app.logger.error(f'Suggest parental lines error: {e}')
        return jsonify({'success': False, 'message': 'Failed to get suggestions'}), 500


@bp.route('/api/batch/<int:batch_id>/lineage/validate')
@login_required
def validate_batch_lineage(batch_id):
    """验证batch家谱的一致性"""
    try:
        from app.services.batch_lineage_service import BatchLineageService
        
        validation_result = BatchLineageService.validate_lineage_consistency(batch_id)
        
        return jsonify({
            'success': True,
            'validation': validation_result
        })
    except Exception as e:
        current_app.logger.error(f'Batch lineage validation error: {e}')
        return jsonify({'success': False, 'message': 'Failed to validate lineage'}), 500


@bp.route('/api/batch/<int:batch_id>/lineage/paths')
@login_required
def get_batch_lineage_paths(batch_id):
    """获取从根节点到当前batch的所有路径"""
    try:
        from app.services.batch_lineage_service import BatchLineageService
        
        paths = BatchLineageService.find_lineage_paths(batch_id)
        
        # 转换路径中的batch对象为JSON格式
        paths_data = []
        for path in paths:
            path_data = []
            for batch in path:
                path_data.append({
                    'id': batch.id,
                    'name': batch.name,
                    'cell_line': batch.cell_line,
                    'passage_number': batch.passage_number,
                    'date_frozen': batch.date_frozen.isoformat() if batch.date_frozen else None,
                    'parental_cell_line': batch.parental_cell_line
                })
            paths_data.append(path_data)
        
        return jsonify({
            'success': True,
            'paths': paths_data,
            'path_count': len(paths_data)
        })
    except Exception as e:
        current_app.logger.error(f'Batch lineage paths error: {e}')
        return jsonify({'success': False, 'message': 'Failed to get lineage paths'}), 500


# --- History Tree Standalone Page ---

@bp.route('/history-tree')
@login_required
def history_tree():
    """独立的History Tree页面"""
    return render_template('main/history_tree.html', title='Batch History Tree')


@bp.route('/api/batch/search')
@login_required
def search_batches():
    """搜索batch的API端点"""
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({
                'success': True,
                'batches': []
            })
        
        # 搜索batch - 按名称、cell line或parental cell line
        batches = VialBatch.query.join(CryoVial).join(CellLine).filter(
            db.or_(
                VialBatch.name.ilike(f'%{query}%'),
                CellLine.name.ilike(f'%{query}%'),
                CryoVial.parental_cell_line.ilike(f'%{query}%')
            )
        ).distinct().limit(limit).all()
        
        # 转换为JSON格式
        batch_data = []
        for batch in batches:
            batch_data.append({
                'id': batch.id,
                'name': batch.name,
                'cell_line': batch.cell_line,
                'passage_number': batch.passage_number,
                'date_frozen': batch.date_frozen.isoformat() if batch.date_frozen else None,
                'parental_cell_line': batch.parental_cell_line,
                'vial_count': batch.vials.count(),
                'timestamp': batch.timestamp.isoformat() if batch.timestamp else None
            })
        
        return jsonify({
            'success': True,
            'batches': batch_data
        })
        
    except Exception as e:
        current_app.logger.error(f'Batch search error: {e}')
        return jsonify({'success': False, 'message': 'Failed to search batches'}), 500


@bp.route('/api/batch/recent')
@login_required
def get_recent_batches():
    """获取最近的batch列表"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # 获取最近创建的batch
        recent_batches = VialBatch.query.order_by(
            VialBatch.timestamp.desc()
        ).limit(limit).all()
        
        # 转换为JSON格式
        batch_data = []
        for batch in recent_batches:
            batch_data.append({
                'id': batch.id,
                'name': batch.name,
                'cell_line': batch.cell_line,
                'passage_number': batch.passage_number,
                'date_frozen': batch.date_frozen.isoformat() if batch.date_frozen else None,
                'parental_cell_line': batch.parental_cell_line,
                'vial_count': batch.vials.count(),
                'timestamp': batch.timestamp.isoformat() if batch.timestamp else None
            })
        
        return jsonify({
            'success': True,
            'batches': batch_data
        })
        
    except Exception as e:
        current_app.logger.error(f'Recent batches error: {e}')
        return jsonify({'success': False, 'message': 'Failed to get recent batches'}), 500


@bp.route('/api/batch/with-lineage')
@login_required
def get_batches_with_lineage():
    """获取有家谱关系的batch列表"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        # 获取有parental_cell_line的batch，或者被其他batch引用作为parental的batch
        batches_with_parents = VialBatch.query.join(CryoVial).filter(
            CryoVial.parental_cell_line.isnot(None),
            CryoVial.parental_cell_line != ''
        ).distinct()
        
        # 获取被引用作为parent的batch
        referenced_names = db.session.query(CryoVial.parental_cell_line).filter(
            CryoVial.parental_cell_line.isnot(None),
            CryoVial.parental_cell_line != ''
        ).distinct().all()
        
        # 提取实际的名称列表
        referenced_name_list = [name[0] for name in referenced_names if name[0]]
        
        batches_referenced = VialBatch.query.filter(
            VialBatch.name.in_(referenced_name_list)
        ) if referenced_name_list else VialBatch.query.filter(False)
        
        # 合并结果
        all_lineage_batches = batches_with_parents.union(batches_referenced).order_by(
            VialBatch.timestamp.desc()
        ).limit(limit).all()
        
        # 转换为JSON格式
        batch_data = []
        for batch in all_lineage_batches:
            batch_data.append({
                'id': batch.id,
                'name': batch.name,
                'cell_line': batch.cell_line,
                'passage_number': batch.passage_number,
                'date_frozen': batch.date_frozen.isoformat() if batch.date_frozen else None,
                'parental_cell_line': batch.parental_cell_line,
                'vial_count': batch.vials.count(),
                'timestamp': batch.timestamp.isoformat() if batch.timestamp else None,
                'has_parents': bool(batch.parental_cell_line),
                'has_children': len(batch.get_child_batches()) > 0
            })
        
        return jsonify({
            'success': True,
            'batches': batch_data
        })
        
    except Exception as e:
        current_app.logger.error(f'Batches with lineage error: {e}')
        return jsonify({'success': False, 'message': 'Failed to get batches with lineage'}), 500


# --- Enhanced Lineage API Endpoints (Phase 1 Optimization) ---

@bp.route('/api/v2/batch/<int:batch_id>/lineage/optimized')
@login_required
def get_optimized_batch_lineage(batch_id):
    """
    Get frontend-optimized batch lineage with lazy loading support
    NEW ENDPOINT - Does not modify existing /api/batch/<id>/lineage
    """
    try:
        from app.services.batch_lineage_service import BatchLineageService
        from app.services.lineage_cache_service import LineageCacheService
        
        # Check if batch exists
        batch = VialBatch.query.get(batch_id)
        if not batch:
            return jsonify({'success': False, 'message': f'Batch {batch_id} not found'}), 404
        
        # Get parameters
        viewport_depth = request.args.get('viewport_depth', 3, type=int)
        include_details = request.args.get('include_details', 'true').lower() == 'true'
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'
        
        # Try to get from cache first
        lineage_data = None
        if use_cache:
            lineage_data = LineageCacheService.get_cached_lineage(
                batch_id, viewport_depth, include_details
            )
        
        # If not in cache, compute and cache
        if lineage_data is None:
            lineage_data = BatchLineageService.get_optimized_lineage_for_frontend(
                batch_id, viewport_depth, include_details
            )
            
            if use_cache:
                LineageCacheService.set_cached_lineage(
                    batch_id, lineage_data, viewport_depth, include_details
                )
        
        return jsonify({
            'success': True,
            'lineage': lineage_data,
            'cached': lineage_data is not None and use_cache,
            'api_version': 'v2'
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f'Optimized lineage error for batch {batch_id}: {e}\n{error_details}')
        return jsonify({
            'success': False,
            'message': f'Failed to get optimized lineage: {str(e)}'
        }), 500


@bp.route('/api/v2/batch/<int:batch_id>/lineage/summary')
@login_required
def get_lineage_summary_stats(batch_id):
    """
    Get lightweight summary statistics for quick loading
    NEW ENDPOINT - Optimized for performance
    """
    try:
        from app.services.batch_lineage_service import BatchLineageService
        from app.services.lineage_cache_service import LineageCacheService
        
        # Check if batch exists
        batch = VialBatch.query.get(batch_id)
        if not batch:
            return jsonify({'success': False, 'message': f'Batch {batch_id} not found'}), 404
        
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'
        
        # Try cache first
        summary_data = None
        if use_cache:
            summary_data = LineageCacheService.get_cached_summary_stats(batch_id)
        
        # If not cached, compute and cache
        if summary_data is None:
            summary_data = BatchLineageService.get_lineage_summary_stats(batch_id)
            
            if use_cache:
                LineageCacheService.set_cached_summary_stats(batch_id, summary_data)
        
        return jsonify({
            'success': True,
            'summary': summary_data,
            'cached': summary_data is not None and use_cache,
            'api_version': 'v2'
        })
        
    except Exception as e:
        current_app.logger.error(f'Lineage summary error for batch {batch_id}: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to get lineage summary: {str(e)}'
        }), 500


@bp.route('/api/v2/batch/<int:batch_id>/lineage/depth/<int:depth_level>')
@login_required
def get_lineage_nodes_by_depth(batch_id, depth_level):
    """
    Get batch nodes at specific depth level for lazy loading
    NEW ENDPOINT - Supports pagination for large trees
    """
    try:
        from app.services.batch_lineage_service import BatchLineageService
        from app.services.lineage_cache_service import LineageCacheService
        
        # Check if batch exists
        batch = VialBatch.query.get(batch_id)
        if not batch:
            return jsonify({'success': False, 'message': f'Batch {batch_id} not found'}), 404
        
        # Get parameters
        node_type = request.args.get('type', 'descendants')  # 'ancestors' or 'descendants'
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'
        
        # Validate parameters
        if node_type not in ['ancestors', 'descendants']:
            return jsonify({
                'success': False,
                'message': 'Invalid node_type. Must be "ancestors" or "descendants"'
            }), 400
        
        if depth_level < 1 or depth_level > 10:
            return jsonify({
                'success': False,
                'message': 'Invalid depth_level. Must be between 1 and 10'
            }), 400
        
        # Try cache first
        depth_data = None
        if use_cache:
            depth_data = LineageCacheService.get_cached_depth_nodes(
                batch_id, depth_level, node_type, offset, limit
            )
        
        # If not cached, compute and cache
        if depth_data is None:
            depth_data = BatchLineageService.get_batch_nodes_by_depth(
                batch_id, depth_level, node_type, limit, offset
            )
            
            if use_cache:
                LineageCacheService.set_cached_depth_nodes(
                    batch_id, depth_data, depth_level, node_type, offset, limit
                )
        
        return jsonify({
            'success': True,
            'data': depth_data,
            'cached': depth_data is not None and use_cache,
            'api_version': 'v2'
        })
        
    except Exception as e:
        current_app.logger.error(f'Lineage depth nodes error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to get lineage depth nodes: {str(e)}'
        }), 500


@bp.route('/api/v2/lineage/cache/stats')
@login_required
def get_lineage_cache_stats():
    """
    Get cache usage statistics for monitoring
    NEW ENDPOINT - For debugging and monitoring
    """
    try:
        from app.services.lineage_cache_service import LineageCacheService
        
        # Only allow admin users to view cache stats
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        
        cache_stats = LineageCacheService.get_cache_stats()
        
        return jsonify({
            'success': True,
            'cache_stats': cache_stats,
            'api_version': 'v2'
        })
        
    except Exception as e:
        current_app.logger.error(f'Cache stats error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to get cache statistics: {str(e)}'
        }), 500


@bp.route('/api/v2/lineage/cache/warm/<int:batch_id>', methods=['POST'])
@login_required
def warm_lineage_cache(batch_id):
    """
    Pre-warm cache for a specific batch
    NEW ENDPOINT - For performance optimization
    """
    try:
        from app.services.lineage_cache_service import LineageCacheService
        
        # Check if batch exists
        batch = VialBatch.query.get(batch_id)
        if not batch:
            return jsonify({'success': False, 'message': f'Batch {batch_id} not found'}), 404
        
        # Warm the cache
        LineageCacheService.warm_cache_for_batch(batch_id)
        
        return jsonify({
            'success': True,
            'message': f'Cache warmed for batch {batch_id}',
            'api_version': 'v2'
        })
        
    except Exception as e:
        current_app.logger.error(f'Cache warming error for batch {batch_id}: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to warm cache: {str(e)}'
        }), 500


@bp.route('/api/v2/lineage/cache/invalidate/<int:batch_id>', methods=['POST'])
@login_required  
def invalidate_lineage_cache(batch_id):
    """
    Invalidate cache for a specific batch
    NEW ENDPOINT - For data consistency
    """
    try:
        from app.services.lineage_cache_service import LineageCacheService
        
        # Check if batch exists
        batch = VialBatch.query.get(batch_id)
        if not batch:
            return jsonify({'success': False, 'message': f'Batch {batch_id} not found'}), 404
        
        # Invalidate the cache
        LineageCacheService.invalidate_batch_cache(batch_id)
        
        return jsonify({
            'success': True,
            'message': f'Cache invalidated for batch {batch_id}',
            'api_version': 'v2'
        })
        
    except Exception as e:
        current_app.logger.error(f'Cache invalidation error for batch {batch_id}: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to invalidate cache: {str(e)}'
        }), 500


# Phase 4 Analytics and Collaborative Features API Endpoints

@bp.route('/api/v4/analytics/track', methods=['POST'])
@login_required
def track_user_interaction():
    """
    Track user interactions for analytics
    Phase 4 - Advanced analytics tracking
    """
    try:
        from app.services.lineage_analytics_service import LineageAnalyticsService
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['batch_id', 'interaction_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False, 
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Track the interaction
        LineageAnalyticsService.track_user_interaction(
            user_id=current_user.id,
            batch_id=data['batch_id'],
            interaction_type=data['interaction_type'],
            metadata=data.get('metadata', {})
        )
        
        return jsonify({
            'success': True,
            'message': 'Interaction tracked successfully',
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Analytics tracking error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to track interaction: {str(e)}'
        }), 500


@bp.route('/api/v4/analytics/performance', methods=['POST'])
@login_required
def track_performance_metric():
    """
    Track performance metrics for optimization
    Phase 4 - Performance analytics
    """
    try:
        from app.services.lineage_analytics_service import LineageAnalyticsService
        
        data = request.get_json()
        
        # Validate required fields
        if 'metric_type' not in data or 'value' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required fields: metric_type, value'
            }), 400
        
        # Track the performance metric
        LineageAnalyticsService.track_performance_metric(
            metric_type=data['metric_type'],
            value=data['value'],
            batch_id=data.get('batch_id'),
            user_id=current_user.id
        )
        
        return jsonify({
            'success': True,
            'message': 'Performance metric tracked successfully',
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Performance tracking error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to track performance: {str(e)}'
        }), 500


@bp.route('/api/v4/analytics/usage-patterns')
@login_required
def get_usage_patterns():
    """
    Get usage pattern analytics
    Phase 4 - Advanced analytics insights
    """
    try:
        from app.services.lineage_analytics_service import LineageAnalyticsService
        
        # Get query parameters
        batch_id = request.args.get('batch_id', type=int)
        time_range_hours = request.args.get('time_range', type=int, default=24)
        
        # Limit time range for performance
        time_range_hours = min(time_range_hours, 168)  # Max 7 days
        
        # Get usage patterns
        patterns = LineageAnalyticsService.get_usage_patterns(
            batch_id=batch_id,
            time_range_hours=time_range_hours
        )
        
        return jsonify({
            'success': True,
            'usage_patterns': patterns,
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Usage patterns error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to get usage patterns: {str(e)}'
        }), 500


@bp.route('/api/v4/analytics/performance-insights')
@login_required
def get_performance_insights():
    """
    Get performance insights and optimization recommendations
    Phase 4 - Performance analytics
    """
    try:
        from app.services.lineage_analytics_service import LineageAnalyticsService
        
        # Get query parameters
        metric_type = request.args.get('metric_type')
        time_range_hours = request.args.get('time_range', type=int, default=24)
        
        # Limit time range for performance
        time_range_hours = min(time_range_hours, 168)  # Max 7 days
        
        # Get performance insights
        insights = LineageAnalyticsService.get_performance_insights(
            metric_type=metric_type,
            time_range_hours=time_range_hours
        )
        
        return jsonify({
            'success': True,
            'performance_insights': insights,
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Performance insights error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to get performance insights: {str(e)}'
        }), 500


@bp.route('/api/v4/analytics/collaboration')
@login_required
def get_collaboration_insights():
    """
    Get collaboration insights and opportunities
    Phase 4 - Collaborative features
    """
    try:
        from app.services.lineage_analytics_service import LineageAnalyticsService
        
        # Get query parameters
        time_range_hours = request.args.get('time_range', type=int, default=24)
        
        # Limit time range for performance
        time_range_hours = min(time_range_hours, 168)  # Max 7 days
        
        # Get collaboration insights
        insights = LineageAnalyticsService.get_collaboration_insights(
            time_range_hours=time_range_hours
        )
        
        return jsonify({
            'success': True,
            'collaboration_insights': insights,
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Collaboration insights error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to get collaboration insights: {str(e)}'
        }), 500


@bp.route('/api/v4/analytics/recommendations/<int:user_id>')
@login_required
def get_batch_recommendations(user_id):
    """
    Get ML-based batch recommendations for a user
    Phase 4 - Machine learning recommendations
    """
    try:
        from app.services.lineage_analytics_service import LineageAnalyticsService
        
        # Check if user can access recommendations (own or admin)
        if current_user.id != user_id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        
        # Get query parameters
        limit = request.args.get('limit', type=int, default=10)
        limit = min(limit, 50)  # Max 50 recommendations
        
        # Get recommendations
        recommendations = LineageAnalyticsService.predict_batch_interest(
            user_id=user_id,
            limit=limit
        )
        
        # Enrich with batch information
        enriched_recommendations = []
        for rec in recommendations:
            batch = VialBatch.query.get(rec['batch_id'])
            if batch:
                enriched_recommendations.append({
                    'batch_id': rec['batch_id'],
                    'batch_name': batch.name,
                    'cell_line': batch.cell_line.name if batch.cell_line else None,
                    'confidence': rec['confidence'],
                    'reason': rec['reason'],
                    'created_date': batch.created_date.isoformat() if batch.created_date else None
                })
        
        return jsonify({
            'success': True,
            'recommendations': enriched_recommendations,
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Batch recommendations error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to get recommendations: {str(e)}'
        }), 500


@bp.route('/api/v4/analytics/system-health')
@login_required
def get_system_health():
    """
    Get system health metrics and recommendations
    Phase 4 - System monitoring (Admin only)
    """
    try:
        from app.services.lineage_analytics_service import LineageAnalyticsService
        
        # Only allow admin users
        if not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Admin access required'
            }), 403
        
        # Get system health metrics
        health_metrics = LineageAnalyticsService.get_system_health_metrics()
        
        return jsonify({
            'success': True,
            'system_health': health_metrics,
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'System health error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to get system health: {str(e)}'
        }), 500


@bp.route('/api/v4/collaboration/active-users')
@login_required
def get_active_users():
    """
    Get currently active users in the system
    Phase 4 - Real-time collaboration awareness
    """
    try:
        from app.services.lineage_analytics_service import LineageAnalyticsService
        
        # Get recent user activity (last 30 minutes)
        cutoff_time = time.time() - (30 * 60)
        active_users = set()
        
        for batch_data in LineageAnalyticsService._usage_analytics.values():
            for interaction in batch_data:
                if interaction['timestamp'] > cutoff_time:
                    active_users.add(interaction['user_id'])
        
        # Get user details
        active_user_details = []
        for user_id in active_users:
            user = User.query.get(user_id)
            if user:
                active_user_details.append({
                    'user_id': user.id,
                    'username': user.username,
                    'is_current_user': user.id == current_user.id
                })
        
        return jsonify({
            'success': True,
            'active_users': active_user_details,
            'total_active': len(active_user_details),
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Active users error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to get active users: {str(e)}'
        }), 500


@bp.route('/api/v4/collaboration/shared-batches')
@login_required
def get_shared_batches():
    """
    Get batches currently being viewed by multiple users
    Phase 4 - Collaborative awareness
    """
    try:
        from app.services.lineage_analytics_service import LineageAnalyticsService
        
        # Get recent activity (last 15 minutes)
        cutoff_time = time.time() - (15 * 60)
        batch_users = defaultdict(set)
        
        for batch_id, interactions in LineageAnalyticsService._usage_analytics.items():
            for interaction in interactions:
                if interaction['timestamp'] > cutoff_time:
                    batch_users[batch_id].add(interaction['user_id'])
        
        # Find batches with multiple users
        shared_batches = []
        for batch_id, users in batch_users.items():
            if len(users) > 1:
                batch = VialBatch.query.get(batch_id)
                if batch:
                    user_details = []
                    for user_id in users:
                        user = User.query.get(user_id)
                        if user:
                            user_details.append({
                                'user_id': user.id,
                                'username': user.username
                            })
                    
                    shared_batches.append({
                        'batch_id': batch.id,
                        'batch_name': batch.name,
                        'cell_line': batch.cell_line.name if batch.cell_line else None,
                        'active_users': user_details,
                        'user_count': len(users)
                    })
        
        return jsonify({
            'success': True,
            'shared_batches': shared_batches,
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Shared batches error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to get shared batches: {str(e)}'
        }), 500


# Phase 4 Advanced Layout API Endpoints

@bp.route('/api/v4/layouts/available')
@login_required
def get_available_layouts():
    """
    Get list of available layout types
    Phase 4 - Advanced layout options
    """
    try:
        from app.services.advanced_layouts_service import AdvancedLayoutsService
        
        layouts = AdvancedLayoutsService.get_available_layouts()
        
        return jsonify({
            'success': True,
            'layouts': layouts,
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Available layouts error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to get available layouts: {str(e)}'
        }), 500


@bp.route('/api/v4/layouts/<layout_type>/generate/<int:batch_id>')
@login_required
def generate_advanced_layout(layout_type, batch_id):
    """
    Generate advanced layout for a specific batch
    Phase 4 - Advanced layout generation
    """
    try:
        from app.services.advanced_layouts_service import AdvancedLayoutsService
        from app.services.batch_lineage_service import BatchLineageService
        
        # Validate batch exists
        batch = VialBatch.query.get(batch_id)
        if not batch:
            return jsonify({
                'success': False,
                'message': f'Batch {batch_id} not found'
            }), 404
        
        # Get layout parameters
        width = request.args.get('width', type=int, default=800)
        height = request.args.get('height', type=int, default=600)
        
        # Validate dimensions
        width = max(400, min(width, 2000))  # Limit between 400-2000px
        height = max(300, min(height, 1500))  # Limit between 300-1500px
        
        # Get lineage data
        lineage_data = BatchLineageService.get_batch_lineage(batch_id)
        
        # Generate layout based on type
        layout_data = None
        if layout_type == 'force_directed':
            layout_data = AdvancedLayoutsService.generate_force_directed_layout(
                lineage_data, width, height
            )
        elif layout_type == 'timeline':
            layout_data = AdvancedLayoutsService.generate_timeline_layout(
                lineage_data, width, height
            )
        elif layout_type == 'circular':
            layout_data = AdvancedLayoutsService.generate_circular_layout(
                lineage_data, width, height
            )
        elif layout_type == 'matrix':
            layout_data = AdvancedLayoutsService.generate_matrix_layout(
                lineage_data, width, height
            )
        else:
            return jsonify({
                'success': False,
                'message': f'Unknown layout type: {layout_type}'
            }), 400
        
        return jsonify({
            'success': True,
            'layout_data': layout_data,
            'batch_id': batch_id,
            'layout_type': layout_type,
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Advanced layout generation error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to generate layout: {str(e)}'
        }), 500


@bp.route('/api/v4/layouts/<layout_type>/config')
@login_required
def get_layout_config(layout_type):
    """
    Get configuration options for a specific layout type
    Phase 4 - Layout configuration
    """
    try:
        from app.services.advanced_layouts_service import AdvancedLayoutsService
        
        config = AdvancedLayoutsService.get_layout_config(layout_type)
        
        return jsonify({
            'success': True,
            'layout_type': layout_type,
            'config': config,
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Layout config error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to get layout config: {str(e)}'
        }), 500


# Phase 4 Real-time Collaboration API Endpoints

@bp.route('/api/v4/realtime/collaboration-stats')
@login_required
def get_realtime_collaboration_stats():
    """
    Get real-time collaboration statistics
    Phase 4 - Real-time collaboration monitoring
    """
    try:
        from app.services.realtime_collaboration_service import RealtimeCollaborationService
        
        stats = RealtimeCollaborationService.get_collaboration_stats()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Realtime collaboration stats error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to get collaboration stats: {str(e)}'
        }), 500


@bp.route('/api/v4/realtime/batch-viewers/<int:batch_id>')
@login_required
def get_batch_active_viewers(batch_id):
    """
    Get active viewers for a specific batch
    Phase 4 - Real-time collaboration awareness
    """
    try:
        from app.services.realtime_collaboration_service import RealtimeCollaborationService
        
        # Validate batch exists
        batch = VialBatch.query.get(batch_id)
        if not batch:
            return jsonify({
                'success': False,
                'message': f'Batch {batch_id} not found'
            }), 404
        
        active_users = RealtimeCollaborationService.get_active_users_for_batch(batch_id)
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'active_users': active_users,
            'total_viewers': len(active_users),
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Batch active viewers error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to get active viewers: {str(e)}'
        }), 500


# Phase 4 Workflow Integration API Endpoints

@bp.route('/api/v4/workflow/batch-export', methods=['POST'])
@login_required
def export_batch_for_workflow():
    """
    Export batch data for external workflow integration
    Phase 4 - Workflow integration
    """
    try:
        data = request.get_json()
        
        if 'batch_id' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required field: batch_id'
            }), 400
        
        batch_id = data['batch_id']
        export_format = data.get('format', 'json')
        include_lineage = data.get('include_lineage', True)
        
        # Validate batch exists
        batch = VialBatch.query.get(batch_id)
        if not batch:
            return jsonify({
                'success': False,
                'message': f'Batch {batch_id} not found'
            }), 404
        
        # Build export data
        export_data = {
            'batch': {
                'id': batch.id,
                'name': batch.name,
                'cell_line': batch.cell_line.name if batch.cell_line else None,
                'cell_line_id': batch.cell_line_id,
                'passage_number': batch.passage_number,
                'frozen_by': batch.frozen_by,
                'date_frozen': batch.date_frozen.isoformat() if batch.date_frozen else None,
                'created_date': batch.created_date.isoformat() if batch.created_date else None,
                'notes': batch.notes,
                'vial_count': len(batch.vials)
            },
            'vials': []
        }
        
        # Include vial information
        for vial in batch.vials:
            vial_data = {
                'id': vial.id,
                'tag': vial.tag,
                'status': vial.status,
                'volume_ml': float(vial.volume_ml) if vial.volume_ml else None,
                'concentration': vial.concentration,
                'fluorescence_tag': vial.fluorescence_tag,
                'resistance': vial.resistance,
                'location': None
            }
            
            # Include location if vial is stored
            if vial.box_id:
                box = vial.box
                if box:
                    vial_data['location'] = {
                        'tower': box.drawer.tower.name if box.drawer and box.drawer.tower else None,
                        'drawer': box.drawer.name if box.drawer else None,
                        'box': box.name,
                        'position': f"R{vial.row_in_box}C{vial.col_in_box}"
                    }
            
            export_data['vials'].append(vial_data)
        
        # Include lineage data if requested
        if include_lineage:
            from app.services.batch_lineage_service import BatchLineageService
            lineage_data = BatchLineageService.get_batch_lineage(batch_id)
            export_data['lineage'] = lineage_data
        
        # Add metadata
        export_data['metadata'] = {
            'export_timestamp': datetime.now().isoformat(),
            'exported_by': current_user.username,
            'format': export_format,
            'version': '4.0'
        }
        
        return jsonify({
            'success': True,
            'export_data': export_data,
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Workflow export error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to export batch: {str(e)}'
        }), 500


@bp.route('/api/v4/workflow/batch-import', methods=['POST'])
@login_required
def import_batch_from_workflow():
    """
    Import batch data from external workflow systems
    Phase 4 - Workflow integration
    """
    try:
        data = request.get_json()
        
        if 'batch_data' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required field: batch_data'
            }), 400
        
        batch_data = data['batch_data']
        update_existing = data.get('update_existing', False)
        
        # Validate required fields
        required_fields = ['name', 'cell_line']
        for field in required_fields:
            if field not in batch_data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required batch field: {field}'
                }), 400
        
        # Check if batch already exists
        existing_batch = VialBatch.query.filter_by(name=batch_data['name']).first()
        if existing_batch and not update_existing:
            return jsonify({
                'success': False,
                'message': f'Batch {batch_data["name"]} already exists'
            }), 409
        
        # Get or create cell line
        cell_line = CellLine.query.filter_by(name=batch_data['cell_line']).first()
        if not cell_line:
            return jsonify({
                'success': False,
                'message': f'Cell line {batch_data["cell_line"]} not found'
            }), 404
        
        # Create or update batch
        if existing_batch and update_existing:
            batch = existing_batch
        else:
            batch = VialBatch()
            db.session.add(batch)
        
        # Update batch fields
        batch.name = batch_data['name']
        batch.cell_line_id = cell_line.id
        batch.passage_number = batch_data.get('passage_number')
        batch.frozen_by = batch_data.get('frozen_by', current_user.username)
        batch.notes = batch_data.get('notes')
        
        # Parse date_frozen if provided
        if batch_data.get('date_frozen'):
            try:
                batch.date_frozen = datetime.fromisoformat(batch_data['date_frozen'].replace('Z', '+00:00'))
            except ValueError:
                pass  # Keep existing date or None
        
        try:
            db.session.commit()
            
            # Log the import
            from app.services.lineage_analytics_service import LineageAnalyticsService
            LineageAnalyticsService.track_user_interaction(
                user_id=current_user.id,
                batch_id=batch.id,
                interaction_type='workflow_import',
                metadata={
                    'source': data.get('source', 'external'),
                    'update_existing': update_existing
                }
            )
            
            return jsonify({
                'success': True,
                'batch_id': batch.id,
                'batch_name': batch.name,
                'operation': 'updated' if existing_batch and update_existing else 'created',
                'api_version': 'v4'
            })
            
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        current_app.logger.error(f'Workflow import error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to import batch: {str(e)}'
        }), 500


@bp.route('/api/v4/workflow/webhook', methods=['POST'])
@login_required
def handle_workflow_webhook():
    """
    Handle incoming webhooks from external workflow systems
    Phase 4 - Webhook integration
    """
    try:
        # Only allow admin users to configure webhooks
        if not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Admin access required'
            }), 403
        
        data = request.get_json()
        
        # Validate webhook data
        if 'event_type' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required field: event_type'
            }), 400
        
        event_type = data['event_type']
        payload = data.get('payload', {})
        
        # Process different event types
        result = None
        if event_type == 'batch_created':
            result = cls._handle_batch_created_webhook(payload)
        elif event_type == 'batch_updated':
            result = cls._handle_batch_updated_webhook(payload)
        elif event_type == 'lineage_changed':
            result = cls._handle_lineage_changed_webhook(payload)
        else:
            return jsonify({
                'success': False,
                'message': f'Unknown event type: {event_type}'
            }), 400
        
        # Log webhook processing
        current_app.logger.info(f"Processed webhook: {event_type} from {request.remote_addr}")
        
        return jsonify({
            'success': True,
            'event_type': event_type,
            'processed': True,
            'result': result,
            'api_version': 'v4'
        })
        
    except Exception as e:
        current_app.logger.error(f'Webhook processing error: {e}')
        return jsonify({
            'success': False,
            'message': f'Failed to process webhook: {str(e)}'
        }), 500


