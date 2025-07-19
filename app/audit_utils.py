# Audit logging utilities for human-readable messages
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


def format_audit_details(action: str, details: str, db_session=None, **kwargs) -> str:
    """
    Convert raw audit details into human-readable messages.
    
    Args:
        action: The action type (e.g., 'CREATE_CRYOVIAL', 'DELETE')
        details: The raw details string (might be JSON or plain text)
        db_session: Database session for querying batch names
        **kwargs: Additional context like vial_ids, batch_id, etc.
    
    Returns:
        Human-readable description of the action
    """
    
    # Try to parse JSON details if it looks like JSON
    parsed_details = None
    if details and details.startswith('{') and details.endswith('}'):
        try:
            parsed_details = json.loads(details.replace("'", '"'))
        except (json.JSONDecodeError, ValueError):
            # If parsing fails, use the raw details
            pass
    
    # Handle different action types
    if action == 'CREATE_CRYOVIAL':
        return _format_create_cryovial(parsed_details, details, db_session, **kwargs)
    elif action == 'DELETE':
        return _format_delete_vial(parsed_details, details, db_session, **kwargs)
    elif action == 'BATCH_DELETE':
        return _format_batch_delete(parsed_details, details, **kwargs)
    elif action == 'UPDATE':
        return _format_update_vial(parsed_details, details, **kwargs)
    elif action == 'UPDATE_STATUS':
        return _format_update_status(parsed_details, details, **kwargs)
    elif action == 'LOGIN':
        return "Signed into the system"
    elif action == 'CREATE_CELL_LINE':
        return _format_create_cell_line(parsed_details, details, **kwargs)
    elif action == 'EXPORT':
        return _format_export_data(parsed_details, details, **kwargs)
    elif action == 'PICKUP_VIALS':
        return _format_pickup_vials(parsed_details, details, db_session, **kwargs)
    elif action in ['LOGIN', 'LOGOUT']:
        return _format_auth_action(action, parsed_details, details, **kwargs)
    elif action in ['BACKUP_EXPORT', 'BACKUP_IMPORT']:
        return _format_backup_action(action, parsed_details, details, **kwargs)
    elif action.startswith('CREATE_'):
        return _format_create_action(action, parsed_details, details, **kwargs)
    elif action.startswith('EDIT_') or action.startswith('UPDATE_'):
        return _format_edit_action(action, parsed_details, details, **kwargs)
    else:
        # Generic fallback
        return _format_generic_action(action, parsed_details, details, **kwargs)


def _format_create_cryovial(parsed_details: Optional[Dict], raw_details: str, db_session=None, **kwargs) -> str:
    """Format CREATE_CRYOVIAL action details."""
    if parsed_details:
        vial_count = len(parsed_details.get('vial_ids', []))
        batch_id = parsed_details.get('batch_id')
        vial_ids = parsed_details.get('vial_ids', [])
        
        # Get batch name if we have a database session
        batch_name = None
        if db_session and batch_id:
            try:
                from app.models import VialBatch
                batch = db_session.query(VialBatch).filter(VialBatch.id == batch_id).first()
                if batch:
                    batch_name = batch.name
            except Exception:
                pass
        
        if vial_count == 1:
            if batch_id:
                if batch_name:
                    return f"Added 1 cryovial (ID: {vial_ids[0]}) to Batch '{batch_name}'"
                else:
                    return f"Added 1 cryovial (ID: {vial_ids[0]}) to Batch #{batch_id}"
            else:
                return f"Added 1 cryovial (ID: {vial_ids[0]})"
        else:
            if batch_id:
                vial_range = f"{min(vial_ids)}-{max(vial_ids)}" if vial_ids else "multiple"
                if batch_name:
                    return f"Added {vial_count} cryovials (IDs: {vial_range}) to Batch '{batch_name}'"
                else:
                    return f"Added {vial_count} cryovials (IDs: {vial_range}) to Batch #{batch_id}"
            else:
                return f"Added {vial_count} cryovials"
    
    # Fallback to raw details
    if "vial(s)" in raw_details:
        return raw_details.replace("added ", "Added ").replace("vial(s)", "cryovials")
    return f"Added new cryovials: {raw_details}"


def _format_delete_vial(parsed_details: Optional[Dict], raw_details: str, db_session=None, **kwargs) -> str:
    """Format DELETE action details."""
    if parsed_details:
        vial_id = parsed_details.get('vial_id')
        vial_tag = parsed_details.get('vial_tag', '')
        batch_id = parsed_details.get('batch_id')
        
        # Get batch name if we have a database session
        batch_name = None
        if db_session and batch_id:
            try:
                from app.models import VialBatch
                batch = db_session.query(VialBatch).filter(VialBatch.id == batch_id).first()
                if batch:
                    batch_name = batch.name
            except Exception:
                pass
        
        if vial_tag and batch_id:
            if batch_name:
                return f"Deleted cryovial '{vial_tag}' (ID: {vial_id}) from Batch '{batch_name}'"
            else:
                return f"Deleted cryovial '{vial_tag}' (ID: {vial_id}) from Batch #{batch_id}"
        elif vial_tag:
            return f"Deleted cryovial '{vial_tag}' (ID: {vial_id})"
        elif vial_id:
            return f"Deleted cryovial ID: {vial_id}"
    
    # Try to extract meaningful info from raw details
    if "Deleted" in raw_details:
        return raw_details
    return f"Deleted a cryovial: {raw_details}"


def _format_batch_delete(parsed_details: Optional[Dict], raw_details: str, **kwargs) -> str:
    """Format BATCH_DELETE action details."""
    if parsed_details:
        vial_count = parsed_details.get('count', 0)
        vial_ids = parsed_details.get('vial_ids', [])
        
        if vial_count > 0:
            if len(vial_ids) > 0:
                vial_range = f"{min(vial_ids)}-{max(vial_ids)}" if len(vial_ids) > 1 else str(vial_ids[0])
                return f"Batch deleted {vial_count} cryovials (IDs: {vial_range})"
            else:
                return f"Batch deleted {vial_count} cryovials"
    
    # Fallback
    if "Batch deleted" in raw_details:
        return raw_details
    return f"Batch deleted multiple cryovials: {raw_details}"


def _format_update_vial(parsed_details: Optional[Dict], raw_details: str, **kwargs) -> str:
    """Format UPDATE action details."""
    if parsed_details:
        vial_id = parsed_details.get('vial_id')
        vial_tag = parsed_details.get('vial_tag', '')
        changes = parsed_details.get('changes', {})
        
        if vial_tag and changes:
            changed_fields = ", ".join(changes.keys())
            return f"Updated cryovial '{vial_tag}' (ID: {vial_id}): modified {changed_fields}"
        elif vial_tag:
            return f"Updated cryovial '{vial_tag}' (ID: {vial_id})"
        elif vial_id:
            return f"Updated cryovial ID: {vial_id}"
    
    return f"Updated cryovial details: {raw_details}"


def _format_update_status(parsed_details: Optional[Dict], raw_details: str, **kwargs) -> str:
    """Format UPDATE_STATUS action details."""
    if parsed_details:
        vial_id = parsed_details.get('vial_id')
        vial_tag = parsed_details.get('vial_tag', '')
        old_status = parsed_details.get('old_status', '')
        new_status = parsed_details.get('new_status', '')
        
        if vial_tag and old_status and new_status:
            return f"Changed status of '{vial_tag}' from '{old_status}' to '{new_status}'"
        elif vial_tag and new_status:
            return f"Set status of '{vial_tag}' to '{new_status}'"
        elif vial_id and new_status:
            return f"Set status of cryovial ID: {vial_id} to '{new_status}'"
    
    return f"Updated vial status: {raw_details}"


def _format_create_cell_line(parsed_details: Optional[Dict], raw_details: str, **kwargs) -> str:
    """Format CREATE_CELL_LINE action details."""
    if parsed_details:
        cell_line_name = parsed_details.get('name', '')
        cell_line_id = parsed_details.get('id')
        
        if cell_line_name:
            return f"Created cell line '{cell_line_name}' (ID: {cell_line_id})"
        elif cell_line_id:
            return f"Created cell line ID: {cell_line_id}"
    
    return f"Created new cell line: {raw_details}"


def _format_export_data(parsed_details: Optional[Dict], raw_details: str, **kwargs) -> str:
    """Format EXPORT action details."""
    if parsed_details:
        export_type = parsed_details.get('type', 'data')
        record_count = parsed_details.get('count', 0)
        file_format = parsed_details.get('format', 'CSV')
        
        if record_count > 0:
            return f"Exported {record_count} records as {file_format} ({export_type})"
        else:
            return f"Exported {export_type} as {file_format}"
    
    return f"Exported data: {raw_details}"


def _format_generic_action(action: str, parsed_details: Optional[Dict], raw_details: str, **kwargs) -> str:
    """Format generic action details."""
    action_name = action.lower().replace('_', ' ').title()
    
    if parsed_details and isinstance(parsed_details, dict):
        # Try to extract useful information from the parsed details
        important_fields = []
        for key, value in parsed_details.items():
            if key in ['id', 'name', 'count', 'type'] and value:
                important_fields.append(f"{key}: {value}")
        
        if important_fields:
            return f"{action_name} - {', '.join(important_fields)}"
    
    return f"{action_name}: {raw_details}"


def create_audit_log(user_id: int, action: str, target_type: str = None, target_id: int = None, 
                    vial_ids: List[int] = None, batch_id: int = None, 
                    vial_tag: str = None, details: str = None, **extra_context) -> str:
    """
    Create a human-readable audit log message.
    
    Args:
        user_id: ID of the user performing the action
        action: Action type (e.g., 'CREATE_CRYOVIAL')
        target_type: Type of target object (e.g., 'CryoVial')
        target_id: ID of target object
        vial_ids: List of vial IDs involved
        batch_id: Batch ID if applicable
        vial_tag: Vial tag/identifier
        details: Raw details string
        **extra_context: Additional context
    
    Returns:
        Human-readable audit message
    """
    
    # Build structured details for better formatting
    structured_details = {}
    
    if vial_ids:
        structured_details['vial_ids'] = vial_ids
        structured_details['count'] = len(vial_ids)
    
    if batch_id:
        structured_details['batch_id'] = batch_id
    
    if vial_tag:
        structured_details['vial_tag'] = vial_tag
    
    if target_id:
        structured_details['target_id'] = target_id
    
    # Add any extra context
    structured_details.update(extra_context)
    
    # Convert to JSON string for storage
    details_json = json.dumps(structured_details) if structured_details else details
    
    return details_json


def parse_legacy_details(details: str) -> Optional[Dict]:
    """
    Parse legacy details format that might contain dictionary strings.
    
    Args:
        details: Raw details string that might be a dict representation
        
    Returns:
        Parsed dictionary or None if parsing fails
    """
    if not details:
        return None
        
    # Handle Python dict string representation
    if details.startswith("{'") and details.endswith("'}"):
        try:
            # Replace single quotes with double quotes for JSON parsing
            json_str = details.replace("'", '"')
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Handle direct JSON strings
    if details.startswith('{"') and details.endswith('"}'):
        try:
            return json.loads(details)
        except (json.JSONDecodeError, ValueError):
            pass
    
    return None


def _format_pickup_vials(parsed_details: Optional[Dict], raw_details: str, db_session=None, **kwargs) -> str:
    """Format PICKUP_VIALS action details."""
    if parsed_details:
        vial_ids = parsed_details.get('vial_ids', [])
        batch_ids = parsed_details.get('batch_ids', [])
        vial_count = len(vial_ids)
        batch_count = len(batch_ids)
        
        # Get batch names if we have a database session
        batch_names = []
        if db_session and batch_ids:
            try:
                from app.models import VialBatch
                batches = db_session.query(VialBatch).filter(VialBatch.id.in_(batch_ids)).all()
                batch_names = [batch.name for batch in batches]
            except Exception:
                pass
        
        if vial_count > 0 and batch_count > 0:
            if vial_count == 1:
                if batch_names:
                    if len(batch_names) == 1:
                        return f"Retrieved 1 cryovial from Batch '{batch_names[0]}'"
                    else:
                        batch_list = ", ".join([f"'{name}'" for name in batch_names])
                        return f"Retrieved 1 cryovial from Batches {batch_list}"
                else:
                    return f"Retrieved 1 cryovial from {batch_count} batch{'es' if batch_count > 1 else ''}"
            else:
                vial_range = f"{min(vial_ids)}-{max(vial_ids)}" if len(vial_ids) > 1 else str(vial_ids[0])
                if batch_names:
                    if len(batch_names) == 1:
                        return f"Retrieved {vial_count} cryovials (IDs: {vial_range}) from Batch '{batch_names[0]}'"
                    else:
                        batch_list = ", ".join([f"'{name}'" for name in batch_names])
                        return f"Retrieved {vial_count} cryovials (IDs: {vial_range}) from Batches {batch_list}"
                else:
                    return f"Retrieved {vial_count} cryovials (IDs: {vial_range}) from {batch_count} batch{'es' if batch_count > 1 else ''}"
        elif vial_count > 0:
            return f"Retrieved {vial_count} cryovial{'s' if vial_count > 1 else ''}"
    
    # Fallback
    if "vial" in raw_details.lower():
        return "Retrieved cryovials for pickup"
    return f"Pickup operation: {raw_details}"


def _format_auth_action(action: str, parsed_details: Optional[Dict], raw_details: str, **kwargs) -> str:
    """Format authentication actions."""
    if action == 'LOGIN':
        return "Signed into the system"
    elif action == 'LOGOUT':
        return "Signed out of the system"
    return f"Authentication: {action.lower()}"


def _format_backup_action(action: str, parsed_details: Optional[Dict], raw_details: str, **kwargs) -> str:
    """Format backup-related actions."""
    if action == 'BACKUP_EXPORT':
        if parsed_details:
            backup_type = parsed_details.get('type', 'database')
            return f"Exported {backup_type} backup"
        return "Created system backup"
    elif action == 'BACKUP_IMPORT':
        if parsed_details:
            backup_type = parsed_details.get('type', 'database')
            return f"Restored {backup_type} from backup"
        return "Restored system from backup"
    return f"Backup operation: {action.lower().replace('_', ' ')}"


def _format_create_action(action: str, parsed_details: Optional[Dict], raw_details: str, **kwargs) -> str:
    """Format generic CREATE actions."""
    entity_type = action.replace('CREATE_', '').lower().replace('_', ' ')
    
    if parsed_details:
        name = parsed_details.get('name', '')
        entity_id = parsed_details.get('id')
        
        if name:
            return f"Created {entity_type} '{name}'"
        elif entity_id:
            return f"Created {entity_type} (ID: {entity_id})"
    
    return f"Created new {entity_type}"


def _format_edit_action(action: str, parsed_details: Optional[Dict], raw_details: str, **kwargs) -> str:
    """Format generic EDIT/UPDATE actions."""
    if action.startswith('EDIT_'):
        entity_type = action.replace('EDIT_', '').lower().replace('_', ' ')
        operation = "Modified"
    else:
        entity_type = action.replace('UPDATE_', '').lower().replace('_', ' ')
        operation = "Updated"
    
    if parsed_details:
        name = parsed_details.get('name', '')
        entity_id = parsed_details.get('id')
        changes = parsed_details.get('changes', {})
        
        if name and changes:
            changed_fields = ", ".join(changes.keys())
            return f"{operation} {entity_type} '{name}': {changed_fields}"
        elif name:
            return f"{operation} {entity_type} '{name}'"
        elif entity_id:
            return f"{operation} {entity_type} (ID: {entity_id})"
    
    return f"{operation} {entity_type}"