import os
import re

def fix_url_references(directory):
    """Fix URL references from 'main.' to 'cell_storage.' in template files."""
    
    # Define the replacements needed
    replacements = {
        "url_for('main.": "url_for('cell_storage.",
    }
    
    files_fixed = 0
    total_replacements = 0
    
    # Walk through all files in the templates directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Apply replacements
                    for old, new in replacements.items():
                        content = content.replace(old, new)
                    
                    # If content changed, write it back
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        # Count replacements
                        replacements_made = original_content.count("url_for('main.")
                        total_replacements += replacements_made
                        files_fixed += 1
                        
                        print(f"Fixed {replacements_made} URL references in: {file_path}")
                
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    print(f"\nSummary:")
    print(f"Files fixed: {files_fixed}")
    print(f"Total URL references updated: {total_replacements}")

if __name__ == "__main__":
    templates_dir = os.path.join(os.path.dirname(__file__), 'app', 'templates')
    print(f"Fixing URL references in: {templates_dir}")
    fix_url_references(templates_dir)