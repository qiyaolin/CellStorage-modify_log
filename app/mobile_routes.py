from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from .cell_storage.models import db, CellLine, CryoVial, Tower, Drawer, Box, VialBatch, User
from sqlalchemy import func, or_, and_
from datetime import datetime

mobile_bp = Blueprint('mobile', __name__)

@mobile_bp.route('/mobile')
@login_required
def mobile_index():
    return render_template('mobile/index.html')

@mobile_bp.route('/mobile/api/search-vials')
@login_required
def mobile_api_search_vials():
    """Search CryoVials - Corresponding to desktop search functionality"""
    try:
        # Get search parameters
        q = request.args.get('q', '').strip()
        creator = request.args.get('creator', '').strip()
        fluorescence = request.args.get('fluorescence', '').strip()
        resistance = request.args.get('resistance', '').strip()
        view_all = request.args.get('view_all', '').strip()
        
        # Build query
        query = db.session.query(
            VialBatch.id.label('batch_id'),
            VialBatch.name.label('batch_name'),
            CellLine.name.label('cell_line'),
            CryoVial.passage_number,
            CryoVial.date_frozen,
            func.count(CryoVial.id).label('available_quantity'),
            CryoVial.volume_ml,
            CryoVial.concentration,
            CryoVial.fluorescence_tag,
            CryoVial.resistance,
            CryoVial.parental_cell_line,
            CryoVial.notes
        ).join(CryoVial, VialBatch.id == CryoVial.batch_id)\
         .join(CellLine, CryoVial.cell_line_id == CellLine.id)\
         .filter(CryoVial.status == 'Available')\
         .group_by(
            VialBatch.id, VialBatch.name, CellLine.name,
            CryoVial.passage_number, CryoVial.date_frozen,
            CryoVial.volume_ml, CryoVial.concentration,
            CryoVial.fluorescence_tag, CryoVial.resistance,
            CryoVial.parental_cell_line, CryoVial.notes
        )
        
        # Apply search filters
        if q:
            query = query.filter(or_(
                VialBatch.name.ilike(f'%{q}%'),
                CellLine.name.ilike(f'%{q}%'),
                CryoVial.unique_vial_id_tag.ilike(f'%{q}%'),
                CryoVial.fluorescence_tag.ilike(f'%{q}%')
            ))
        
        if creator:
            query = query.join(User, VialBatch.created_by_user_id == User.id)\
                         .filter(User.username == creator)
        
        if fluorescence:
            query = query.filter(CryoVial.fluorescence_tag == fluorescence)
            
        if resistance:
            query = query.filter(CryoVial.resistance == resistance)
        
        # If no search conditions and not view all, return empty results
        if not (q or creator or fluorescence or resistance or view_all):
            return jsonify({'success': True, 'data': []})
        
        results = query.limit(50).all()
        
        # Format results
        search_results = []
        for result in results:
            search_results.append({
                'batch_id': result.batch_id,
                'batch_name': result.batch_name,
                'cell_line': result.cell_line,
                'passage_number': result.passage_number or '',
                'date_frozen': result.date_frozen.strftime('%Y-%m-%d') if result.date_frozen else '',
                'available_quantity': result.available_quantity,
                'volume_ml': result.volume_ml,
                'concentration': result.concentration or '',
                'fluorescence_tag': result.fluorescence_tag or '',
                'resistance': result.resistance or '',
                'parental_cell_line': result.parental_cell_line or '',
                'notes': result.notes or ''
            })
        
        return jsonify({'success': True, 'data': search_results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_bp.route('/mobile/api/browse-inventory')
@login_required
def mobile_api_browse_inventory():
    """Browse inventory - Corresponding to desktop Browse by Location functionality"""
    try:
        inventory = {}
        towers = Tower.query.all()
        
        for tower in towers:
            tower_data = {}
            for drawer in tower.drawers:
                drawer_data = []
                for box in drawer.boxes:
                    # Get all vials in this box
                    vials = {}
                    box_vials = CryoVial.query.filter_by(box_id=box.id).all()
                    
                    for vial in box_vials:
                        key = f"{vial.row_in_box}-{vial.col_in_box}"
                        vials[key] = {
                            'id': vial.id,
                            'tag': vial.unique_vial_id_tag,
                            'batch_id': vial.batch_id,
                            'status': vial.status,
                            'cell_line': vial.cell_line_info.name if vial.cell_line_info else 'Unknown'
                        }
                    
                    box_data = {
                        'id': box.id,
                        'name': box.name,
                        'rows': box.rows,
                        'columns': box.columns,
                        'vials': vials
                    }
                    drawer_data.append(box_data)
                
                if drawer_data:  # Only add drawers with boxes
                    tower_data[drawer.name] = drawer_data
            
            if tower_data:  # Only add towers with drawers
                inventory[tower.name] = tower_data
        
        return jsonify({'success': True, 'data': inventory})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_bp.route('/mobile/api/pickup-list', methods=['GET', 'POST'])
@login_required
def mobile_api_pickup_list():
    """Manage pickup list"""
    try:
        if request.method == 'POST':
            # Add to pickup list
            data = request.get_json()
            selected_batches = data.get('selected_batches', [])
            
            if not selected_batches:
                return jsonify({'success': False, 'error': 'No batches selected'}), 400
            
            # Add selected batches to pickup list in session
            if 'pickup_list' not in session:
                session['pickup_list'] = []
            
            for batch_id in selected_batches:
                if batch_id not in session['pickup_list']:
                    session['pickup_list'].append(batch_id)
            
            session.modified = True
            return jsonify({'success': True, 'message': f'Added {len(selected_batches)} batches to pickup list'})
        
        else:
            # Get pickup list
            pickup_list = session.get('pickup_list', [])
            if not pickup_list:
                return jsonify({'success': True, 'data': []})
            
            # Get batch details
            selected_batches = []
            for batch_id in pickup_list:
                batch = VialBatch.query.get(batch_id)
                if batch:
                    # Get first vial info for this batch
                    sample_vial = CryoVial.query.filter_by(batch_id=batch_id).first()
                    if sample_vial:
                        count = CryoVial.query.filter_by(batch_id=batch_id, status='Available').count()
                        selected_batches.append({
                            'batch_id': batch.id,
                            'batch_name': batch.name,
                            'date_frozen': sample_vial.date_frozen.strftime('%Y-%m-%d') if sample_vial.date_frozen else '',
                            'count': count
                        })
            
            return jsonify({'success': True, 'data': selected_batches})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_bp.route('/mobile/api/remove-from-pickup', methods=['POST'])
@login_required
def mobile_api_remove_from_pickup():
    """Remove batches from pickup list"""
    try:
        data = request.get_json()
        remove_batches = data.get('remove_batches', [])
        
        if 'pickup_list' in session:
            for batch_id in remove_batches:
                if batch_id in session['pickup_list']:
                    session['pickup_list'].remove(batch_id)
            session.modified = True
        
        return jsonify({'success': True, 'message': f'Removed {len(remove_batches)} batches from pickup list'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_bp.route('/mobile/api/vial-details/<int:vial_id>')
@login_required
def mobile_api_vial_details(vial_id):
    """Get vial details - Corresponding to desktop modal functionality"""
    try:
        vial = CryoVial.query.get_or_404(vial_id)
        
        # Get location information
        location = "Unknown"
        if vial.box_location:
            box = vial.box_location
            drawer = box.drawer_info
            tower = drawer.tower_info if drawer else None
            if tower and drawer:
                location = f"{tower.name} > {drawer.name} > {box.name} ({vial.row_in_box}, {vial.col_in_box})"
        
        vial_data = {
            'id': vial.id,
            'unique_vial_id_tag': vial.unique_vial_id_tag,
            'batch_name': vial.batch.name if vial.batch else 'Unknown',
            'cell_line': vial.cell_line_info.name if vial.cell_line_info else 'Unknown',
            'location': location,
            'passage_number': vial.passage_number or '',
            'date_frozen': vial.date_frozen.strftime('%Y-%m-%d') if vial.date_frozen else '',
            'frozen_by': vial.freezer_operator.username if vial.freezer_operator else 'Unknown',
            'status': vial.status,
            'notes': vial.notes or '',
            'volume_ml': vial.volume_ml,
            'concentration': vial.concentration or '',
            'fluorescence_tag': vial.fluorescence_tag or '',
            'resistance': vial.resistance or '',
            'parental_cell_line': vial.parental_cell_line or '',
            'is_admin': current_user.is_admin
        }
        
        return jsonify({'success': True, 'data': vial_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_bp.route('/mobile/api/filter-options')
@login_required
def mobile_api_filter_options():
    """获取过滤选项 - 对应桌面端的下拉菜单"""
    try:
        # 获取所有创建者
        creators = db.session.query(User.username).join(VialBatch, User.id == VialBatch.created_by_user_id).distinct().all()
        all_creators = [creator[0] for creator in creators]
        
        # 获取所有荧光标签
        fluorescence_tags = db.session.query(CryoVial.fluorescence_tag).filter(CryoVial.fluorescence_tag.isnot(None)).distinct().all()
        all_fluorescence_tags = [tag[0] for tag in fluorescence_tags if tag[0]]
        
        # 获取所有抗性
        resistances = db.session.query(CryoVial.resistance).filter(CryoVial.resistance.isnot(None)).distinct().all()
        all_resistances = [res[0] for res in resistances if res[0]]
        
        return jsonify({
            'success': True,
            'data': {
                'creators': all_creators,
                'fluorescence_tags': all_fluorescence_tags,
                'resistances': all_resistances
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_bp.route('/mobile/api/add-cryovial', methods=['POST'])
@login_required
def mobile_api_add_cryovial():
    """添加新的CryoVial - 对应桌面端的Add new cryovial功能"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['cell_line_id', 'batch_name', 'tower_id', 'drawer_id', 'box_id', 'row', 'col']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # 检查位置是否已被占用
        existing_vial = CryoVial.query.filter_by(
            box_id=data['box_id'],
            row_in_box=data['row'],
            col_in_box=data['col']
        ).first()
        
        if existing_vial:
            return jsonify({'success': False, 'error': 'Position already occupied'}), 400
        
        # 创建或获取VialBatch
        batch = VialBatch.query.filter_by(name=data['batch_name']).first()
        if not batch:
            batch = VialBatch(
                name=data['batch_name'],
                created_by_user_id=current_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(batch)
            db.session.flush()  # 获取batch.id
        
        # 生成unique_vial_id_tag
        vial_count = CryoVial.query.count() + 1
        unique_tag = f"V{vial_count:06d}"
        
        # 创建新的CryoVial
        new_vial = CryoVial(
            unique_vial_id_tag=unique_tag,
            batch_id=batch.id,
            cell_line_id=data['cell_line_id'],
            box_id=data['box_id'],
            row_in_box=data['row'],
            col_in_box=data['col'],
            passage_number=data.get('passage_number'),
            date_frozen=datetime.strptime(data['date_frozen'], '%Y-%m-%d').date() if data.get('date_frozen') else None,
            frozen_by_user_id=current_user.id,
            status='Available',
            volume_ml=data.get('volume_ml'),
            concentration=data.get('concentration'),
            fluorescence_tag=data.get('fluorescence_tag'),
            resistance=data.get('resistance'),
            parental_cell_line=data.get('parental_cell_line'),
            notes=data.get('notes')
        )
        
        db.session.add(new_vial)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'vial_id': new_vial.id,
                'unique_tag': unique_tag,
                'message': 'CryoVial added successfully'
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_bp.route('/mobile/api/form-options')
@login_required
def mobile_api_form_options():
    """获取添加表单的选项数据"""
    try:
        # 获取所有细胞系
        cell_lines = CellLine.query.all()
        cell_line_options = [{'id': cl.id, 'name': cl.name} for cl in cell_lines]
        
        # 获取所有存储位置
        towers = Tower.query.all()
        location_options = []
        
        for tower in towers:
            tower_data = {
                'id': tower.id,
                'name': tower.name,
                'drawers': []
            }
            
            for drawer in tower.drawers:
                drawer_data = {
                    'id': drawer.id,
                    'name': drawer.name,
                    'boxes': []
                }
                
                for box in drawer.boxes:
                    # 获取可用位置
                    occupied_positions = set()
                    existing_vials = CryoVial.query.filter_by(box_id=box.id).all()
                    for vial in existing_vials:
                        occupied_positions.add((vial.row_in_box, vial.col_in_box))
                    
                    available_positions = []
                    for row in range(1, box.rows + 1):
                        for col in range(1, box.columns + 1):
                            if (row, col) not in occupied_positions:
                                available_positions.append({'row': row, 'col': col})
                    
                    box_data = {
                        'id': box.id,
                        'name': box.name,
                        'rows': box.rows,
                        'columns': box.columns,
                        'available_positions': available_positions
                    }
                    drawer_data['boxes'].append(box_data)
                
                tower_data['drawers'].append(drawer_data)
            location_options.append(tower_data)
        
        return jsonify({
            'success': True,
            'data': {
                'cell_lines': cell_line_options,
                'locations': location_options
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
