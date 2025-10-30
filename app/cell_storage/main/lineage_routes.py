"""
Batch Lineage Management API Routes

Provides CRUD operations for managing batch parent-child relationships.
These endpoints support the History Tree visualization and batch relationship management UI.
"""

from flask import jsonify, request
from flask_login import login_required, current_user
from . import bp
from app import db
from app.cell_storage.models import VialBatch, BatchLineage


@bp.route('/api/batch/<int:batch_id>/lineage/relationships', methods=['GET'])
@login_required
def get_batch_relationships(batch_id):
    """
    Get all direct parent and child relationships for a batch.

    Returns:
        {
            "success": true,
            "batch_id": 123,
            "parents": [
                {
                    "id": 1,
                    "parent_batch_id": 100,
                    "parent_batch_name": "Batch_001",
                    "relationship_type": "passage",
                    "notes": "...",
                    "created_at": "2024-01-15T10:30:00"
                }
            ],
            "children": [...]
        }
    """
    try:
        batch = VialBatch.query.get_or_404(batch_id)

        # Get parent relationships
        parent_rels = BatchLineage.query.filter_by(child_batch_id=batch_id).all()
        parents_data = []
        for rel in parent_rels:
            parent_batch = VialBatch.query.get(rel.parent_batch_id)
            if parent_batch:
                parents_data.append({
                    'id': rel.id,
                    'parent_batch_id': rel.parent_batch_id,
                    'parent_batch_name': parent_batch.name,
                    'relationship_type': rel.relationship_type,
                    'notes': rel.notes,
                    'created_at': rel.created_at.isoformat() if rel.created_at else None,
                    'created_by_user_id': rel.created_by_user_id
                })

        # Get child relationships
        child_rels = BatchLineage.query.filter_by(parent_batch_id=batch_id).all()
        children_data = []
        for rel in child_rels:
            child_batch = VialBatch.query.get(rel.child_batch_id)
            if child_batch:
                children_data.append({
                    'id': rel.id,
                    'child_batch_id': rel.child_batch_id,
                    'child_batch_name': child_batch.name,
                    'relationship_type': rel.relationship_type,
                    'notes': rel.notes,
                    'created_at': rel.created_at.isoformat() if rel.created_at else None,
                    'created_by_user_id': rel.created_by_user_id
                })

        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'batch_name': batch.name,
            'parents': parents_data,
            'children': children_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get batch relationships: {str(e)}'
        }), 500


@bp.route('/api/batch/<int:batch_id>/lineage/add-parent', methods=['POST'])
@login_required
def add_parent_relationship(batch_id):
    """
    Add a parent batch relationship.

    Request body:
        {
            "parent_batch_id": 100,
            "relationship_type": "passage",  # optional, default: passage
            "notes": "..."  # optional
        }

    Returns:
        {
            "success": true,
            "relationship_id": 1,
            "message": "Parent relationship created successfully"
        }
    """
    try:
        data = request.get_json()

        if not data or 'parent_batch_id' not in data:
            return jsonify({
                'success': False,
                'message': 'parent_batch_id is required'
            }), 400

        parent_batch_id = data['parent_batch_id']
        relationship_type = data.get('relationship_type', 'passage')
        notes = data.get('notes', '')

        # Validate batch exists
        batch = VialBatch.query.get_or_404(batch_id)
        parent_batch = VialBatch.query.get_or_404(parent_batch_id)

        # Check for self-reference
        if batch_id == parent_batch_id:
            return jsonify({
                'success': False,
                'message': 'A batch cannot be its own parent'
            }), 400

        # Check if relationship already exists
        existing = BatchLineage.query.filter_by(
            parent_batch_id=parent_batch_id,
            child_batch_id=batch_id
        ).first()

        if existing:
            return jsonify({
                'success': False,
                'message': 'This parent relationship already exists'
            }), 400

        # Create relationship
        lineage = batch.add_parent(
            parent_batch=parent_batch,
            relationship_type=relationship_type,
            notes=notes,
            created_by_user_id=current_user.id
        )

        db.session.commit()

        return jsonify({
            'success': True,
            'relationship_id': lineage.id,
            'message': f'Parent relationship created: {parent_batch.name} -> {batch.name}'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to create parent relationship: {str(e)}'
        }), 500


@bp.route('/api/batch/<int:batch_id>/lineage/add-child', methods=['POST'])
@login_required
def add_child_relationship(batch_id):
    """
    Add a child batch relationship.

    Request body:
        {
            "child_batch_id": 200,
            "relationship_type": "passage",  # optional
            "notes": "..."  # optional
        }
    """
    try:
        data = request.get_json()

        if not data or 'child_batch_id' not in data:
            return jsonify({
                'success': False,
                'message': 'child_batch_id is required'
            }), 400

        child_batch_id = data['child_batch_id']
        relationship_type = data.get('relationship_type', 'passage')
        notes = data.get('notes', '')

        # Validate batches exist
        batch = VialBatch.query.get_or_404(batch_id)
        child_batch = VialBatch.query.get_or_404(child_batch_id)

        # Check for self-reference
        if batch_id == child_batch_id:
            return jsonify({
                'success': False,
                'message': 'A batch cannot be its own child'
            }), 400

        # Check if relationship already exists
        existing = BatchLineage.query.filter_by(
            parent_batch_id=batch_id,
            child_batch_id=child_batch_id
        ).first()

        if existing:
            return jsonify({
                'success': False,
                'message': 'This child relationship already exists'
            }), 400

        # Create relationship
        lineage = batch.add_child(
            child_batch=child_batch,
            relationship_type=relationship_type,
            notes=notes,
            created_by_user_id=current_user.id
        )

        db.session.commit()

        return jsonify({
            'success': True,
            'relationship_id': lineage.id,
            'message': f'Child relationship created: {batch.name} -> {child_batch.name}'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to create child relationship: {str(e)}'
        }), 500


@bp.route('/api/batch/lineage/<int:relationship_id>', methods=['DELETE'])
@login_required
def delete_relationship(relationship_id):
    """
    Delete a batch lineage relationship.

    Returns:
        {
            "success": true,
            "message": "Relationship deleted successfully"
        }
    """
    try:
        lineage = BatchLineage.query.get_or_404(relationship_id)

        # Get info for response message
        parent = VialBatch.query.get(lineage.parent_batch_id)
        child = VialBatch.query.get(lineage.child_batch_id)

        db.session.delete(lineage)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Relationship deleted: {parent.name if parent else "?"} -> {child.name if child else "?"}'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete relationship: {str(e)}'
        }), 500


@bp.route('/api/batch/lineage/<int:relationship_id>', methods=['PATCH'])
@login_required
def update_relationship(relationship_id):
    """
    Update a batch lineage relationship.

    Request body:
        {
            "relationship_type": "split",  # optional
            "notes": "..."  # optional
        }

    Returns:
        {
            "success": true,
            "message": "Relationship updated successfully"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400

        lineage = BatchLineage.query.get_or_404(relationship_id)

        # Update fields if provided
        if 'relationship_type' in data:
            lineage.relationship_type = data['relationship_type']

        if 'notes' in data:
            lineage.notes = data['notes']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Relationship updated successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to update relationship: {str(e)}'
        }), 500


@bp.route('/api/batch/search-for-lineage', methods=['GET'])
@login_required
def search_batches_for_lineage():
    """
    Search batches for adding as parent/child relationships.
    Excludes the current batch from results.

    Query parameters:
        q: Search query (batch name or cell line)
        exclude_batch_id: Batch ID to exclude from results
        limit: Maximum number of results (default: 20)

    Returns:
        {
            "success": true,
            "batches": [
                {
                    "id": 123,
                    "name": "Batch_001",
                    "cell_line": "HEK293",
                    "date_frozen": "2024-01-15",
                    "vial_count": 10
                }
            ]
        }
    """
    try:
        query = request.args.get('q', '').strip()
        exclude_batch_id = request.args.get('exclude_batch_id', type=int)
        limit = request.args.get('limit', 20, type=int)

        if not query or len(query) < 2:
            return jsonify({
                'success': True,
                'batches': []
            })

        # Search batches by name
        batch_query = VialBatch.query.filter(
            VialBatch.name.like(f'%{query}%')
        )

        # Exclude specified batch
        if exclude_batch_id:
            batch_query = batch_query.filter(VialBatch.id != exclude_batch_id)

        batches = batch_query.order_by(VialBatch.timestamp.desc()).limit(limit).all()

        results = []
        for batch in batches:
            results.append({
                'id': batch.id,
                'name': batch.name,
                'cell_line': batch.cell_line,
                'date_frozen': batch.date_frozen.isoformat() if batch.date_frozen else None,
                'vial_count': batch.vials.count()
            })

        return jsonify({
            'success': True,
            'batches': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Search failed: {str(e)}'
        }), 500
