#!/usr/bin/env python3
"""
Quick verification script to check if database migration was successful.
"""

import sqlite3
import os

def verify_migration():
    """Verify that the migration was successful"""
    print("=== Verifying Database Migration ===")
    
    db_path = os.path.join(os.path.dirname(__file__), 'app.db')
    if not os.path.exists(db_path):
        print("[ERROR] Database file not found!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check inventory_items table structure
        print("Checking inventory_items table...")
        cursor.execute("PRAGMA table_info(inventory_items)")
        columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = [
            'cas_number', 'lot_number', 'safety_document_url', 
            'qr_code', 'responsible_person_id', 'storage_conditions'
        ]
        
        missing_columns = [col for col in required_columns if col not in columns]
        if missing_columns:
            print(f"[ERROR] Missing columns in inventory_items: {missing_columns}")
            return False
        else:
            print("[SUCCESS] All required columns present in inventory_items")
        
        # Check locations table structure
        print("Checking locations table...")
        cursor.execute("PRAGMA table_info(locations)")
        columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = ['max_capacity', 'capacity_unit', 'current_usage']
        missing_columns = [col for col in required_columns if col not in columns]
        if missing_columns:
            print(f"[ERROR] Missing columns in locations: {missing_columns}")
            return False
        else:
            print("[SUCCESS] All required columns present in locations")
        
        # Check new tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['supplier_contacts', 'user_permissions', 'shopping_cart']
        missing_tables = [table for table in required_tables if table not in tables]
        if missing_tables:
            print(f"[ERROR] Missing tables: {missing_tables}")
            return False
        else:
            print("[SUCCESS] All required tables present")
        
        # Show table summary
        print("\n=== Database Summary ===")
        print(f"Total tables: {len(tables)}")
        for table in sorted(tables):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} records")
        
        print("\n[SUCCESS] Migration verification successful!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    verify_migration()