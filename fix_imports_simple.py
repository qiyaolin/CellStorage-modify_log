#!/usr/bin/env python3
"""Fix import issues systematically"""

import os
import re

def fix_file(file_path, fixes):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        changes = 0
        
        for old, new in fixes.items():
            if old in content:
                content = content.replace(old, new)
                changes += 1
        
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed {changes} imports in: {file_path}")
            return changes
        
    except Exception as e:
        print(f"Error: {e}")
    
    return 0

# Define fixes
fixes = {
    'from app.models import User': 'from app.cell_storage.models import User',
    'from app.models import AuditLog': 'from app.cell_storage.models import AuditLog',
    'from app.models import Alert': 'from app.cell_storage.models import Alert',
    'from app.models import VialBatch': 'from app.cell_storage.models import VialBatch',
}

# Fix specific files
files_to_fix = [
    'create_admin.py',
    'app/shared/audit_utils.py', 
    'app/cell_storage/main/routes.py'
]

total = 0
for file_path in files_to_fix:
    if os.path.exists(file_path):
        total += fix_file(file_path, fixes)

print(f"Total fixes: {total}")