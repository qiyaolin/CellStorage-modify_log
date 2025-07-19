#!/usr/bin/env python3
"""
Comprehensive URL endpoint fixer for CellStorage project.
Fixes all 'main.' references to 'cell_storage.' systematically.
"""

import os
import re
from pathlib import Path

def create_endpoint_mapping():
    """Create mapping of all main.* endpoints to cell_storage.* endpoints"""
    return {
        # Main navigation
        'main.index': 'cell_storage.index',
        
        # Cell lines
        'main.list_cell_lines': 'cell_storage.list_cell_lines',
        'main.add_cell_line': 'cell_storage.add_cell_line',
        'main.edit_cell_line': 'cell_storage.edit_cell_line',
        
        # Storage locations
        'main.locations_overview': 'cell_storage.locations_overview',
        'main.add_tower': 'cell_storage.add_tower',
        'main.edit_tower': 'cell_storage.edit_tower',
        'main.add_drawer': 'cell_storage.add_drawer',
        'main.edit_drawer': 'cell_storage.edit_drawer',
        'main.add_box': 'cell_storage.add_box',
        'main.edit_box': 'cell_storage.edit_box',
        
        # Cryovials
        'main.cryovial_inventory': 'cell_storage.cryovial_inventory',
        'main.add_cryovial': 'cell_storage.add_cryovial',
        'main.edit_cryovial': 'cell_storage.edit_cryovial',
        'main.update_cryovial_status': 'cell_storage.update_cryovial_status',
        'main.add_vial_at_position': 'cell_storage.add_vial_at_position',
        'main.delete_cryovial': 'cell_storage.delete_cryovial',
        
        # Batch operations
        'main.batch_edit_vials': 'cell_storage.batch_edit_vials',
        'main.manage_batch': 'cell_storage.manage_batch',
        'main.manage_batch_lookup': 'cell_storage.manage_batch_lookup',
        'main.edit_batch': 'cell_storage.edit_batch',
        'main.update_batch_counter': 'cell_storage.update_batch_counter',
        
        # Inventory and summary
        'main.inventory_summary': 'cell_storage.inventory_summary',
        'main.pickup_selected_vials': 'cell_storage.pickup_selected_vials',
        
        # Import/Export
        'main.import_csv': 'cell_storage.import_csv',
        'main.backup_database': 'cell_storage.backup_database',
        'main.restore_database': 'cell_storage.restore_database',
        
        # Admin functions
        'main.audit_logs': 'cell_storage.audit_logs',
        'main.clear_all': 'cell_storage.clear_all',
        'main.theme_settings': 'cell_storage.theme_settings',
        
        # Alert management
        'main.alerts_management': 'cell_storage.alerts_management',
        'main.resolve_alert': 'cell_storage.resolve_alert',
        'main.dismiss_alert': 'cell_storage.dismiss_alert',
        'main.generate_alerts': 'cell_storage.generate_alerts',
    }

def fix_file_urls(file_path, endpoint_mapping):
    """Fix URL endpoints in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_made = 0
        
        for old_endpoint, new_endpoint in endpoint_mapping.items():
            # Fix url_for('main.xxx') patterns
            old_pattern = f"url_for('{old_endpoint}'"
            new_pattern = f"url_for('{new_endpoint}'"
            
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                fixes_made += 1
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed {fixes_made} URL endpoints in: {file_path}")
            return fixes_made
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return 0

def fix_all_url_endpoints():
    """Fix all URL endpoint references systematically"""
    
    endpoint_mapping = create_endpoint_mapping()
    
    # Files to check
    files_to_check = []
    
    # Add Python files
    for pattern in ['**/*.py']:
        for file_path in Path('.').glob(pattern):
            # Skip virtual environment, __pycache__, etc.
            if any(skip in str(file_path) for skip in ['Lib', '__pycache__', '.git', 'venv', 'env']):
                continue
            files_to_check.append(file_path)
    
    # Add template files  
    for pattern in ['app/templates/**/*.html']:
        for file_path in Path('.').glob(pattern):
            files_to_check.append(file_path)
    
    total_fixes = 0
    files_fixed = 0
    
    print("Starting comprehensive URL endpoint fixes...")
    print(f"Checking {len(files_to_check)} files...")
    
    for file_path in files_to_check:
        fixes_made = fix_file_urls(file_path, endpoint_mapping)
        if fixes_made > 0:
            files_fixed += 1
            total_fixes += fixes_made
    
    print(f"\nSummary:")
    print(f"Files processed: {len(files_to_check)}")
    print(f"Files with fixes: {files_fixed}")
    print(f"Total URL endpoint fixes: {total_fixes}")

if __name__ == "__main__":
    fix_all_url_endpoints()