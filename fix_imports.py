#!/usr/bin/env python3
"""
Systematic import fixer for CellStorage project.
Fixes all incorrect import references to match the new module structure.
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path, fixes):
    """Apply import fixes to a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Apply each fix
        for old_import, new_import in fixes.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes_made += content.count(new_import) - original_content.count(new_import)
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed {changes_made} imports in: {file_path}")
            return changes_made
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return 0

def fix_all_imports():
    """Fix all import issues systematically"""
    
    # Define the mapping of old imports to new imports
    import_fixes = {
        # Old app.models references should point to specific model modules
        'from app.models import User': 'from app.cell_storage.models import User',
        'from app.models import AuditLog': 'from app.cell_storage.models import AuditLog', 
        'from app.models import Alert': 'from app.cell_storage.models import Alert',
        'from app.models import VialBatch': 'from app.cell_storage.models import VialBatch',
        'from app.models import CellLine': 'from app.cell_storage.models import CellLine',
        'from app.models import CryoVial': 'from app.cell_storage.models import CryoVial',
        'from app.models import Tower': 'from app.cell_storage.models import Tower',
        'from app.models import Drawer': 'from app.cell_storage.models import Drawer',
        'from app.models import Box': 'from app.cell_storage.models import Box',
        'from app.models import ThemeConfig': 'from app.cell_storage.models import ThemeConfig',
        'from app.models import AlertConfig': 'from app.cell_storage.models import AlertConfig',
        'from app.models import AppConfig': 'from app.cell_storage.models import AppConfig',
        
        # For inventory models
        'from app.models import InventoryType': 'from app.inventory.models import InventoryType',
        'from app.models import InventoryItem': 'from app.inventory.models import InventoryItem',
        'from app.models import Location': 'from app.inventory.models import Location',
        'from app.models import Supplier': 'from app.inventory.models import Supplier',
        'from app.models import Order': 'from app.inventory.models import Order',
    }
    
    # Paths to check (exclude virtual environment and other irrelevant paths)
    project_root = Path('.')
    files_to_check = []
    
    # Add specific file patterns
    for pattern in ['**/*.py']:
        for file_path in project_root.glob(pattern):
            # Skip virtual environment, __pycache__, etc.
            if any(skip in str(file_path) for skip in ['Lib', '__pycache__', '.git', 'venv', 'env']):
                continue
            files_to_check.append(file_path)
    
    total_fixes = 0
    files_fixed = 0
    
    print("Starting systematic import fixes...")
    print(f"Checking {len(files_to_check)} Python files...")
    
    for file_path in files_to_check:
        fixes_made = fix_imports_in_file(file_path, import_fixes)
        if fixes_made > 0:
            files_fixed += 1
            total_fixes += fixes_made
    
    print(f"\nSummary:")
    print(f"Files processed: {len(files_to_check)}")
    print(f"Files with fixes: {files_fixed}")
    print(f"Total import fixes applied: {total_fixes}")
    
    # Special handling for relative imports within shared/utils.py
    utils_file = Path('app/shared/utils.py')
    if utils_file.exists():
        print(f"\nChecking relative imports in {utils_file}...")
        fix_relative_imports_in_utils(utils_file)

def fix_relative_imports_in_utils(utils_file):
    """Fix relative imports specifically in the utils.py file"""
    try:
        with open(utils_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix relative imports that should be absolute
        relative_fixes = {
            'from ..cell_storage.models import AlertConfig': 'from app.cell_storage.models import AlertConfig',
            'from ..cell_storage.models import CellLine, CryoVial, Alert': 'from app.cell_storage.models import CellLine, CryoVial, Alert',
            'from ..cell_storage.models import Box, CryoVial, Alert': 'from app.cell_storage.models import Box, CryoVial, Alert', 
            'from ..cell_storage.models import CryoVial, Alert, CellLine, VialBatch': 'from app.cell_storage.models import CryoVial, Alert, CellLine, VialBatch',
            'from ..cell_storage.models import Alert': 'from app.cell_storage.models import Alert',
            'from ..cell_storage.models import ThemeConfig': 'from app.cell_storage.models import ThemeConfig',
        }
        
        for old_import, new_import in relative_fixes.items():
            content = content.replace(old_import, new_import)
        
        if content != original_content:
            with open(utils_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed relative imports in {utils_file}")


if __name__ == "__main__":
    fix_all_imports()