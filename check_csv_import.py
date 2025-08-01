#!/usr/bin/env python3
"""
Simple check for CSV import issues without requiring Flask app
"""
import csv
import re
import os

def analyze_csv_issues(csv_path):
    """Analyze CSV file for common import issues"""
    print(f"=== CSV Import Issue Analysis ===")
    print(f"File: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"ERROR: File not found: {csv_path}")
        return
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            print(f"\nHeader columns ({len(header)}):")
            for i, col in enumerate(header):
                print(f"  {i+1}. '{col}'")
            
            # Expected headers
            expected_admin = [
                'Vial ID', 'Batch ID', 'Batch Name', 'Vial Tag', 'Cell Line',
                'Passage Number', 'Date Frozen', 'Frozen By', 'Status', 'Location',
                'Volume (ml)', 'Concentration', 'Fluorescence Tag', 
                'Resistance', 'Parental Cell Line', 'Notes'
            ]
            
            expected_user = [
                'Vial ID', 'Batch ID', 'Batch Name', 'Vial Tag', 'Cell Line',
                'Passage Number', 'Date Frozen', 'Frozen By', 'Status',
                'Volume (ml)', 'Concentration', 'Fluorescence Tag', 
                'Resistance', 'Parental Cell Line', 'Notes'
            ]
            
            print(f"\nHeader validation:")
            if header == expected_admin:
                print("OK Header matches admin format")
            elif header == expected_user:
                print("OK Header matches user format")
            else:
                print("ERROR Header doesn't match expected format")
                print("Expected admin format:")
                for i, col in enumerate(expected_admin):
                    match = "OK" if i < len(header) and header[i] == col else "ERROR"
                    current = header[i] if i < len(header) else "MISSING"
                    print(f"  {match} {i+1}. Expected: '{col}' | Got: '{current}'")
            
            print(f"\nData row analysis:")
            for i, row in enumerate(reader, 2):
                if i > 3:  # Only analyze first few rows
                    break
                    
                print(f"\nRow {i} ({len(row)} columns):")
                if len(row) != len(header):
                    print(f"  ERROR Column count mismatch: got {len(row)}, expected {len(header)}")
                    continue
                
                row_data = dict(zip(header, row))
                
                # Check key fields
                vial_id = row_data.get('Vial ID', '').strip()
                vial_tag = row_data.get('Vial Tag', '').strip() 
                batch_name = row_data.get('Batch Name', '').strip()
                cell_line = row_data.get('Cell Line', '').strip()
                status = row_data.get('Status', '').strip()
                location = row_data.get('Location', '').strip()
                
                print(f"  Vial ID: '{vial_id}'")
                print(f"  Vial Tag: '{vial_tag}'")
                print(f"  Batch Name: '{batch_name}'")
                print(f"  Cell Line: '{cell_line}'")
                print(f"  Status: '{status}' -> Normalized: '{status.capitalize()}'")
                print(f"  Location: '{location}'")
                
                # Test location regex
                if location:
                    location_match = re.match(r'(.+)/(.+)/(.+)\s+R(\d+)C(\d+)', location)
                    if location_match:
                        tower, drawer, box, row_num, col_num = location_match.groups()
                        print(f"    OK Location parsed:")
                        print(f"      Tower: '{tower.strip()}'")
                        print(f"      Drawer: '{drawer.strip()}'") 
                        print(f"      Box: '{box.strip()}'")
                        print(f"      Position: R{row_num}C{col_num}")
                    else:
                        print(f"    ERROR Location format invalid for regex pattern")
                        print(f"    Expected pattern: 'Tower/Drawer/Box R#C#'")
                
                # Check required fields for new records
                if not vial_id or not vial_id.isdigit():
                    print(f"  NOTE This appears to be a new record")
                    missing_fields = []
                    if not batch_name:
                        missing_fields.append('Batch Name')
                    if not cell_line:
                        missing_fields.append('Cell Line')
                    if not vial_tag:
                        missing_fields.append('Vial Tag')
                    if not location:
                        missing_fields.append('Location')
                    
                    if missing_fields:
                        print(f"    ERROR Missing required fields: {', '.join(missing_fields)}")
                    else:
                        print(f"    OK All required fields present")
                        
    except Exception as e:
        print(f"Error analyzing CSV: {e}")

if __name__ == "__main__":
    csv_file = r"C:\Users\qiyao\Downloads\inventory_summary.csv"
    analyze_csv_issues(csv_file)