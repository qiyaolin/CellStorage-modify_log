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
)
from flask_login import login_required, current_user
from io import StringIO, BytesIO
import csv
import os
import subprocess
import tempfile
from urllib.parse import urlparse
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json
from app.main import bp
from app import db
from app.decorators import admin_required
from app.forms import (
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
)
from app.models import (
    CellLine,
    User,
    Tower,
    Drawer,
    Box,
    CryoVial,
    VialBatch,
    AuditLog,
)

from app.utils import log_audit, clear_database_except_admin


@bp.route('/') # Defines the root URL for the main blueprint
@bp.route('/index') # Also accessible via /index
@login_required # Ensure only logged-in users can access the main dashboard
def index():
    # For now, just render a simple welcome page.
    # Later, this can be a dashboard showing inventory summaries, etc.
    return render_template('main/index.html', title='Dashboard')


@bp.route('/audit_logs')
@login_required
@admin_required
def audit_logs():
    search_user = request.args.get('user', '').strip()
    keyword = request.args.get('keyword', '').strip()
    start = request.args.get('start', '').strip()
    end = request.args.get('end', '').strip()

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
    logs_raw = query.order_by(AuditLog.timestamp.desc()).all()
    parsed_logs = []
    for log in logs_raw:
        details = {}
        if log.details:
            try:
                details = json.loads(log.details)
            except ValueError:
                details = {'raw': log.details}
        parsed_logs.append({'log': log, 'details': details})

    all_users = User.query.order_by(User.username).all()

    return render_template(
        'main/audit_logs.html',
        logs=parsed_logs,
        all_users=all_users,
        search_user=search_user,
        keyword=keyword,
        start=start,
        end=end,
        title='Inventory Logs'
    )

@bp.route('/inventory/summary')
@login_required
@admin_required
def inventory_summary():
    """Display all cryovials for admin review with optional filters."""
    search_q = request.args.get('q', '').strip()
    search_status = request.args.get('status', '').strip()

    query = CryoVial.query.join(VialBatch).join(CellLine).join(Box).join(Drawer).join(Tower)
    if search_q:
        like = f"%{search_q}%"
        query = query.filter(
            CryoVial.unique_vial_id_tag.ilike(like) |
            VialBatch.name.ilike(like) |
            CellLine.name.ilike(like)
        )
    if search_status:
        query = query.filter(CryoVial.status == search_status)

    vials = query.order_by(VialBatch.id, CryoVial.unique_vial_id_tag).all()
    statuses = ['Available', 'Used', 'Depleted', 'Discarded']

    if request.args.get('export') == 'csv':
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Vial ID',
            'Batch ID',
            'Batch Name',
            'Vial Tag',
            'Cell Line',
            'Location',
            'Date Frozen',
            'Status',
        ])
        for v in vials:
            location = (
                f"{v.box_location.drawer_info.tower_info.name}/"
                f"{v.box_location.drawer_info.name}/"
                f"{v.box_location.name} R{v.row_in_box}C{v.col_in_box}"
            )
            writer.writerow([
                v.id,
                v.batch.id,
                v.batch.name,
                v.unique_vial_id_tag,
                v.cell_line_info.name,
                location,
                v.date_frozen,
                v.status,
            ])
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=inventory_summary.csv'},
        )

    return render_template(
        'main/inventory_summary.html',
        title='Inventory Summary',
        vials=vials,
        statuses=statuses,
        search_q=search_q,
        search_status=search_status,
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
            creator=current_user # Associate with the current user
        )
        db.session.add(cell_line)
        db.session.commit()
        flash(f'Cell line "{cell_line.name}" added successfully!', 'success')
        return redirect(url_for('main.list_cell_lines'))
    return render_template('main/cell_line_form.html', title='Add Cell Line', form=form, form_action=url_for('main.add_cell_line'))

@bp.route('/cell_line/<int:cell_line_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_cell_line(cell_line_id):
    cell_line = CellLine.query.get_or_404(cell_line_id)
    form = CellLineForm(obj=cell_line) # Pre-populate form with existing data

    if form.validate_on_submit():
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
        flash(f'Cell line "{cell_line.name}" updated successfully!', 'success')
        return redirect(url_for('main.list_cell_lines'))

    # For GET request, populate form fields from the object if not submitting
    # This is already handled by form = CellLineForm(obj=cell_line) for GET requests
    # but to be explicit for setting form data on GET:
    # if request.method == 'GET':
    #     form.name.data = cell_line.name
    #     # ... populate other fields ...

    return render_template('main/cell_line_form.html', title='Edit Cell Line', form=form, cell_line=cell_line, form_action=url_for('main.edit_cell_line', cell_line_id=cell_line.id))

@bp.route('/locations')
@login_required
@admin_required
def locations_overview():
    towers = Tower.query.order_by(Tower.name).all()
    # You might want to pass drawers and boxes too, or fetch them in the template via tower.drawers, drawer.boxes
    return render_template('main/locations_overview.html', title='Freezer Locations', towers=towers)

# --- Tower Routes ---
@bp.route('/tower/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_tower():
    form = TowerForm()
    if form.validate_on_submit():
        tower = Tower(name=form.name.data, freezer_name=form.freezer_name.data, description=form.description.data)
        db.session.add(tower)
        db.session.commit()
        flash(f'Tower "{tower.name}" added successfully!', 'success')
        return redirect(url_for('main.locations_overview'))
    return render_template('main/tower_form.html', title='Add Tower', form=form, form_action=url_for('main.add_tower'))

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
        return redirect(url_for('main.locations_overview'))
    return render_template('main/tower_form.html', title='Edit Tower', form=form, tower=tower, form_action=url_for('main.edit_tower', tower_id=tower.id))

# --- Drawer Routes ---
@bp.route('/drawer/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_drawer():
    form = DrawerForm()
    form.tower_id.choices = [(t.id, t.name) for t in Tower.query.order_by(Tower.name).all()]
    if form.validate_on_submit():
        drawer = Drawer(name=form.name.data, tower_id=form.tower_id.data)
        db.session.add(drawer)
        db.session.commit()
        flash(f'Drawer "{drawer.name}" added successfully to tower ID {drawer.tower_id}!', 'success')
        return redirect(url_for('main.locations_overview'))
    return render_template('main/drawer_form.html', title='Add Drawer', form=form, form_action=url_for('main.add_drawer'))

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
        return redirect(url_for('main.locations_overview'))
    # Ensure tower_id is set correctly for the form on GET request if not using obj
    # form.tower_id.data = drawer.tower_id # This is handled by obj=drawer
    return render_template('main/drawer_form.html', title='Edit Drawer', form=form, drawer=drawer, form_action=url_for('main.edit_drawer', drawer_id=drawer.id))

# --- Box Routes ---
@bp.route('/box/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_box():
    form = BoxForm()
    form.drawer_id.choices = [(d.id, f"{d.tower_info.name} - {d.name}") for d in Drawer.query.join(Tower).order_by(Tower.name, Drawer.name).all()]
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
            return redirect(url_for('main.locations_overview'))
        except IntegrityError:
            db.session.rollback()
            flash('A box with that name already exists in the selected drawer.', 'danger')
    return render_template('main/box_form.html', title='Add Box', form=form, form_action=url_for('main.add_box'))

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
        return redirect(url_for('main.locations_overview'))
    # form.drawer_id.data = box.drawer_id # Handled by obj=box
    return render_template('main/box_form.html', title='Edit Box', form=form, box=box, form_action=url_for('main.edit_box', box_id=box.id))

@bp.route('/inventory', methods=['GET', 'POST'])
@login_required
def cryovial_inventory():
    """Display freezer inventory and provide a search with selectable results."""

    if request.method == 'POST':
        search_q = request.form.get('q', '').strip()
        search_creator = request.form.get('creator', '').strip()
        search_fluorescence = request.form.get('fluorescence', '').strip()
        search_resistance = request.form.get('resistance', '').strip()
    else:
        search_q = request.args.get('q', '').strip()
        search_creator = request.args.get('creator', '').strip()
        search_fluorescence = request.args.get('fluorescence', '').strip()
        search_resistance = request.args.get('resistance', '').strip()

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
                flash(f'{added} vial(s) added to pick-up list.', 'success')
            return redirect(url_for(
                'main.cryovial_inventory',
                q=search_q,
                creator=search_creator,
                fluorescence=search_fluorescence,
                resistance=search_resistance,
            ))
        elif 'remove_batches' in request.form:
            remove_ids = request.form.getlist('remove_batches')
            removed = 0
            for rid in remove_ids:
                try:
                    rid_int = int(rid)
                except ValueError:
                    continue
                remove_vials = CryoVial.query.filter(CryoVial.id.in_(selected_ids), CryoVial.batch_id == rid_int).all()
                for v in remove_vials:
                    if v.id in selected_ids:
                        selected_ids.remove(v.id)
                        removed += 1
            if removed:
                if selected_ids:
                    session['pickup_ids'] = selected_ids
                else:
                    session.pop('pickup_ids', None)
                flash(f'{removed} vial(s) removed from pick-up list.', 'success')
            return redirect(url_for(
                'main.cryovial_inventory',
                q=search_q,
                creator=search_creator,
                fluorescence=search_fluorescence,
                resistance=search_resistance,
            ))

    towers = Tower.query.order_by(Tower.name).all()
    all_creators = User.query.order_by(User.username).all()
    inventory = {}

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
                        'id': vial.id
                    }
                drawer_boxes.append({
                    'id': box.id,
                    'name': box.name,
                    'drawer_name': drawer.name,
                    'tower_name': tower.name,
                    'rows': box.rows,
                    'columns': box.columns,
                    'vials': vials_map
                })
            tower_dict[drawer.name] = drawer_boxes
        inventory[tower.name] = tower_dict

    search_results = None
    if search_q or search_creator or search_fluorescence or search_resistance:
        query = CryoVial.query.join(VialBatch).join(CellLine).join(User, VialBatch.created_by_user_id == User.id)
        query = query.join(Box).join(Drawer).join(Tower)
        if search_q:
            like = f"%{search_q}%"
            query = query.filter(
                (CryoVial.unique_vial_id_tag.ilike(like)) |
                (VialBatch.name.ilike(like)) |
                (CellLine.name.ilike(like)) |
                (CryoVial.fluorescence_tag.ilike(like)) |
                (CryoVial.resistance.ilike(like)) |
                (CryoVial.parental_cell_line.ilike(like))
            )
        if search_creator:
            query = query.filter(User.username == search_creator)
        if search_fluorescence:
            query = query.filter(CryoVial.fluorescence_tag.ilike(f"%{search_fluorescence}%"))
        if search_resistance:
            query = query.filter(CryoVial.resistance.ilike(f"%{search_resistance}%"))
        query = query.order_by(VialBatch.id, CryoVial.unique_vial_id_tag)
        vials = query.all()
        grouped = {}
        for v in vials:
            info = grouped.get(v.batch_id)
            if not info:
                grouped[v.batch_id] = {
                    'batch': v.batch,
                    'date_frozen': v.date_frozen,
                    'cell_line': v.cell_line_info.name,
                    'passage_number': v.passage_number,
                    'volume_ml': v.volume_ml,
                    'concentration': v.concentration,
                    'fluorescence_tag': v.fluorescence_tag,
                    'resistance': v.resistance,
                    'parental_cell_line': v.parental_cell_line,
                    'notes': v.notes,
                }
            else:
                if v.date_frozen < info['date_frozen']:
                    info['date_frozen'] = v.date_frozen
        search_results = list(grouped.values())

    selected_batches = None
    if selected_ids:
        selected_vials = CryoVial.query.filter(CryoVial.id.in_(selected_ids)).join(VialBatch).join(CellLine).all()
        grouped_sel = {}
        for v in selected_vials:
            info = grouped_sel.get(v.batch_id)
            if not info:
                grouped_sel[v.batch_id] = {
                    'batch': v.batch,
                    'date_frozen': v.date_frozen,
                    'count': 1
                }
            else:
                info['count'] += 1
                if v.date_frozen < info['date_frozen']:
                    info['date_frozen'] = v.date_frozen
        selected_batches = list(grouped_sel.values())

    return render_template(
        'main/cryovial_inventory.html',
        title='CryoVial Inventory',
        inventory=inventory,
        search_results=search_results,
        search_q=search_q,
        search_creator=search_creator,
        search_fluorescence=search_fluorescence,
        search_resistance=search_resistance,
        selected_batches=selected_batches,
        selected_ids=selected_ids,
        all_creators=all_creators
    )


@bp.route('/inventory/pickup', methods=['GET', 'POST'])
@login_required
def pickup_selected_vials():
    """Show selected vials and their locations for pick up."""
    selected_ids = session.get('pickup_ids', [])
    if not selected_ids:
        flash('No vials selected for pick up.', 'info')
        return redirect(url_for('main.cryovial_inventory'))

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
        flash('Pick up recorded and vials marked as Used.', 'success')
        return render_template(
            'main/pickup_result.html',
            boxes=picked_boxes,
            color_map=color_map,
            picked_vials=picked_vials,
        )

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
    # No longer need to populate form.box_id.choices here as the field is removed

    if 'proposed_placements' in session and request.method == 'POST' and request.form.get('confirm_placement') == 'yes':
        # Confirmation step for auto-placed vials
        placements = session.pop('proposed_placements', [])
        vial_common_data = session.pop('vial_common_data', {})

        if not placements or not vial_common_data:
            flash('Placement confirmation data lost. Please try again.', 'danger')
            return redirect(url_for('main.add_cryovial'))

        batch = VialBatch(name=vial_common_data.get('batch_name'), created_by_user_id=current_user.id)
        db.session.add(batch)
        db.session.flush()  # assign ID without committing
        base_tag = f"B{batch.id}"

        created_vials_info = []
        quantity_being_added = len(placements) # Get the actual number from placements

        for i, p in enumerate(placements):
            unique_tag_suffix = f"-{i+1}" if quantity_being_added > 1 else ""
            unique_tag = f"{base_tag}{unique_tag_suffix}"

            existing_tag_vial = CryoVial.query.filter_by(unique_vial_id_tag=unique_tag).first()
            if existing_tag_vial:
                flash(f'Error: Generated vial tag "{unique_tag}" already exists. Please try again.', 'danger')
                session.pop('proposed_placements', None)
                session.pop('vial_common_data', None)
                return redirect(url_for('main.add_cryovial'))

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
            db.session.flush() # Ensure vial IDs are available if batch.vials.all() needs them before commit
            current_details_for_create = {
                'general_info': f'added {len(placements)} vial(s)',
                # It's good practice for batch.vials.all() to reflect the currently added vials.
                # If batch.vials is populated by flush, this is fine. Otherwise, collect vial IDs differently.
                'vial_ids': [v.id for v in batch.vials.all() if v.id is not None], # Ensure IDs are populated
                'batch_id': batch.id
            }
            # MODIFICATION: Convert dictionary to JSON string for details
            # Also ensure the call is details=... and NOT **...
            log_audit(
                current_user.id,
                'CREATE_CRYOVIALS',
                target_type='VialBatch',
                target_id=batch.id,
                details=json.dumps(current_details_for_create) #
            )
            db.session.commit()
            # The subsequent log_audit call is for a simpler post-commit message,
            # its details are already a string.
            log_audit(
                current_user.id,
                'CREATE_CRYOVIALS_COMMITTED', # Changed action slightly for clarity if needed
                target_type='VialBatch',
                target_id=batch.id,
                details=f'Successfully committed batch {batch.id} with {len(placements)} vial(s).' #
            )
            flash(
                f"Batch #{batch.id} '{batch.name}' added with base ID {base_tag} and {len(placements)} vial(s): "
                + "; ".join(created_vials_info),
                'success'
            )
            return redirect(url_for('main.cryovial_inventory'))
        except Exception as e:
            db.session.rollback()
            # The error message reported by the user indicates the exception 'e' contains the specific Python error.
            flash(f'Error saving vial(s): {e}. Please try again.', 'danger')
            return redirect(url_for('main.add_cryovial'))

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
        allocated_positions = []
        selected_boxes = []

        all_boxes = Box.query.join(Drawer).join(Tower).order_by(Tower.name, Drawer.name, Box.id).all()
        for box_candidate in all_boxes:
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
                           form_action=url_for('main.add_cryovial'))

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
        current_details_for_status_update = {
            'old_status': old_status,
            'new_status': vial.status,
            'notes': form.notes.data,
            'vial_id': vial.id,  # Storing the single vial_id
            'batch_id': vial.batch_id  # Storing the associated batch_id
        }
        log_audit(
            current_user.id,
            'UPDATE_VIAL_STATUS',
            target_type='CryoVial',
            target_id=vial.id,  # Target_id still refers to the primary entity being acted upon
            details=current_details_for_status_update
        )
        db.session.commit()
        # The subsequent log_audit call can remain or be adjusted
        log_audit(
            current_user.id,
            'UPDATE_VIAL_STATUS_COMMITTED',  # Example: more specific action
            target_type='CryoVial',
            target_id=vial.id,
            details=f'Status for vial {vial.id} successfully updated to {vial.status}.'
        )
        flash(f'Status of vial "{vial.unique_vial_id_tag}" updated to {vial.status}.', 'success')
        return redirect(url_for('main.cryovial_inventory')) # Or back to where they were (e.g., box view)

    # For GET request, it's better to have a dedicated page to confirm this action.
    # This simple example directly uses a form, but a confirmation step is good UX.
    return render_template('main/update_vial_status_form.html', title='Update Vial Status',
                           form=form, vial=vial,
                           form_action=url_for('main.update_cryovial_status', vial_id=vial.id))

# Add Edit/View Detail routes for CryoVials (perhaps admin only for edit, all for view)
@bp.route('/cryovial/<int:vial_id>/edit', methods=['GET', 'POST'])
@login_required # Or @admin_required if only admins can edit vial details
def edit_cryovial(vial_id):
    vial = CryoVial.query.get_or_404(vial_id)
    # Permission check: e.g., only admin or the user who froze it can edit.
    # if not current_user.is_admin and vial.frozen_by_user_id != current_user.id:
    #     flash('You do not have permission to edit this vial.', 'danger')
    #     return redirect(url_for('main.cryovial_inventory'))

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
                return render_template('main/cryovial_form.html', title='Edit CryoVial', form=form, vial=vial, form_action=url_for('main.edit_cryovial', vial_id=vial.id))

        selected_box = Box.query.get(form.box_id.data)
        if not selected_box or not (1 <= form.row_in_box.data <= selected_box.rows and 1 <= form.col_in_box.data <= selected_box.columns):
            flash(f'Error: Row/Column number is outside the dimensions of the selected box ({selected_box.rows}x{selected_box.columns}).', 'danger')
            return render_template('main/cryovial_form.html', title='Edit CryoVial', form=form, vial=vial, form_action=url_for('main.edit_cryovial', vial_id=vial.id))

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
        return redirect(url_for('main.cryovial_inventory'))

    return render_template('main/edit_cryovial_form.html', title='Edit CryoVial', form=form, vial=vial, form_action=url_for('main.edit_cryovial', vial_id=vial.id))


@bp.route('/box/<int:box_id>/add/<int:row>/<int:col>', methods=['GET', 'POST'], endpoint='add_vial_at_position')
@login_required
@admin_required
def add_vial_at_position(box_id, row, col):
    box = Box.query.get_or_404(box_id)
    if not (1 <= row <= box.rows and 1 <= col <= box.columns):
        flash('Invalid position for this box.', 'danger')
        return redirect(url_for('main.cryovial_inventory'))

    existing = CryoVial.query.filter_by(
        box_id=box.id,
        row_in_box=row,
        col_in_box=col,
        status='Available'
    ).first()
    if existing:
        flash('That position is already occupied.', 'danger')
        return redirect(url_for('main.cryovial_inventory'))

    form = ManualVialForm()
    form.cell_line_id.choices = [(c.id, c.name) for c in CellLine.query.order_by(CellLine.name).all()]

    if form.validate_on_submit():
        if form.batch_id.data:
            batch = VialBatch.query.get(form.batch_id.data)
            if not batch:
                flash('Batch ID not found.', 'danger')
                return render_template('main/manual_vial_form.html', form=form, box=box, row=row, col=col, form_action=url_for('main.add_vial_at_position', box_id=box_id, row=row, col=col), title='Add Vial')
        else:
            batch = VialBatch(name=form.batch_name.data, created_by_user_id=current_user.id)
            db.session.add(batch)
            db.session.commit()

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
        return redirect(url_for('main.cryovial_inventory'))

    return render_template('main/manual_vial_form.html', form=form, box=box, row=row, col=col, form_action=url_for('main.add_vial_at_position', box_id=box_id, row=row, col=col), title='Add Vial')


@bp.route('/cryovial/<int:vial_id>/delete')
@login_required
@admin_required
def delete_cryovial(vial_id):
    vial = CryoVial.query.get_or_404(vial_id)
    db.session.delete(vial)
    db.session.commit()
    log_audit(current_user.id, 'DELETE_CRYOVIAL', target_type='CryoVial', target_id=vial_id)
    flash('Vial deleted.', 'success')
    return redirect(url_for('main.cryovial_inventory'))


@bp.route('/admin/clear_all', methods=['GET', 'POST'])
@login_required
@admin_required
def clear_all():
    form = ConfirmForm()
    if form.validate_on_submit():
        if form.confirm.data.strip() == 'confirm_hayer':
            clear_database_except_admin()
            log_audit(current_user.id, 'CLEAR_ALL', target_type='System')
            flash('All records except admin accounts have been removed.', 'success')
            return redirect(url_for('main.index'))
        flash('Incorrect confirmation phrase.', 'danger')
    return render_template('main/clear_all.html', form=form, title='Clear Database')


@bp.route('/admin/backup')
@login_required
@admin_required
def backup_database():
    db.session.commit()
    uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    scheme = urlparse(uri).scheme

    if scheme == 'sqlite':
        path = uri.replace('sqlite:///', '')
        log_audit(current_user.id, 'BACKUP_EXPORT', target_type='System')
        return send_file(path, as_attachment=True, download_name='backup.db')

    if scheme.startswith('postgres'):
        try:
            result = subprocess.run(
                ['pg_dump', '--format', 'custom', '--dbname', uri],
                check=True,
                capture_output=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            current_app.logger.error('pg_dump failed: %s', exc)
            flash('PostgreSQL backup failed.', 'danger')
            return redirect(url_for('main.index'))

        buf = BytesIO(result.stdout)
        buf.seek(0)
        log_audit(current_user.id, 'BACKUP_EXPORT', target_type='System')
        return send_file(buf, as_attachment=True, download_name='backup.dump', mimetype='application/octet-stream')

    flash('Unsupported database type.', 'danger')
    return redirect(url_for('main.index'))


@bp.route('/admin/restore', methods=['GET', 'POST'])
@login_required
@admin_required
def restore_database():
    form = RestoreForm()
    if form.validate_on_submit():
        file = form.backup_file.data
        if file:
            uri = current_app.config['SQLALCHEMY_DATABASE_URI']
            scheme = urlparse(uri).scheme

            if scheme == 'sqlite':
                path = uri.replace('sqlite:///', '')
                db.session.remove()
                file.save(path)
                log_audit(current_user.id, 'BACKUP_IMPORT', target_type='System')
                flash('Database restored from backup.', 'success')

            elif scheme.startswith('postgres'):
                tmp = tempfile.NamedTemporaryFile(delete=False)
                try:
                    file.save(tmp.name)
                    subprocess.run([
                        'pg_restore', '--clean', '--if-exists', '--dbname', uri, tmp.name
                    ], check=True)
                except (OSError, subprocess.CalledProcessError) as exc:
                    current_app.logger.error('pg_restore failed: %s', exc)
                    flash('PostgreSQL restore failed.', 'danger')
                    return redirect(url_for('main.index'))
                finally:
                    tmp.close()
                    os.unlink(tmp.name)

                log_audit(current_user.id, 'BACKUP_IMPORT', target_type='System')
                flash('Database restored from backup.', 'success')

            else:
                flash('Unsupported database type.', 'danger')
            return redirect(url_for('main.index'))
    return render_template('main/restore_backup.html', form=form, title='Restore Backup')

