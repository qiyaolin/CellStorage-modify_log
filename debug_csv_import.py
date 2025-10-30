#!/usr/bin/env python3
"""
Debug script to help troubleshoot CSV import issues
"""
import sys
import os
import csv
import re

# Add the app directory to the path
sys.path.insert(0, '.')

try:
    from app import create_app
    from app.cell_storage.models import Tower, Drawer, Box, CellLine, CryoVial
    
    def analyze_csv_file(csv_path):
        """Analyze the CSV file and report potential issues"""
        print(f"=== Analyzing CSV file: {csv_path} ===")
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                print(f"Header: {header}")
                
                # Check first few rows
                for i, row in enumerate(reader, 2):
                    if i > 5:  # Only check first few rows
                        break
                    print(f"\nRow {i}: {row}")
                    
                    if len(row) >= len(header):
                        row_data = dict(zip(header, row))
                        
                        # Check location format
                        location = row_data.get('Location', '').strip()
                        if location:
                            print(f"  Location: '{location}'")
                            location_match = re.match(r'(.+)/(.+)/(.+)\s+R(\d+)C(\d+)', location)
                            if location_match:
                                tower, drawer, box, row_num, col_num = location_match.groups()
                                print(f"    Parsed - Tower: '{tower.strip()}', Drawer: '{drawer.strip()}', Box: '{box.strip()}', Position: R{row_num}C{col_num}")
                            else:
                                print(f"    ERROR: Location format doesn't match regex pattern")
                        
                        # Check status
                        status = row_data.get('Status', '').strip()
                        print(f"  Status: '{status}' -> Normalized: '{status.capitalize()}'")
                        
                        # Check cell line
                        cell_line = row_data.get('Cell Line', '').strip()
                        print(f"  Cell Line: '{cell_line}'")
                        
        except Exception as e:
            print(f"Error reading CSV: {e}")
    
    def check_database_locations():
        """Check what storage locations exist in the database"""
        app = create_app()
        with app.app_context():
            print("\n=== Database Storage Locations ===")
            
            towers = Tower.query.all()
            print(f"Towers found: {len(towers)}")
            
            for tower in towers:
                print(f"\nTower: '{tower.name}'")
                for drawer in tower.drawers:
                    print(f"  Drawer: '{drawer.name}'")
                    for box in drawer.boxes:
                        print(f"    Box: '{box.name}'")
            
            print(f"\n=== Cell Lines ===")
            cell_lines = CellLine.query.all()
            print(f"Cell lines found: {len(cell_lines)}")
            for cl in cell_lines[:10]:  # Show first 10
                print(f"  - '{cl.name}'")
            if len(cell_lines) > 10:
                print(f"  ... and {len(cell_lines) - 10} more")
    
    if __name__ == "__main__":
        csv_file = r"C:\Users\qiyao\Downloads\inventory_summary.csv"
        if os.path.exists(csv_file):
            analyze_csv_file(csv_file)
        else:
            print(f"CSV file not found: {csv_file}")
        
        try:
            check_database_locations()
        except Exception as e:
            print(f"Error checking database: {e}")
            print("Make sure Flask app dependencies are installed and database is accessible")

except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure Flask dependencies are installed")
    print("Try running: pip install -r requirements.txt")