#!/usr/bin/env python3
"""
Database Migration Script for Phase 1 Enhancements
Adds new columns to existing tables for inventory management system.
"""

import sqlite3
import os
from datetime import datetime

def get_db_path():
    """Get the database file path"""
    return os.path.join(os.path.dirname(__file__), 'app.db')

def backup_database():
    """Create a backup of the current database"""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print("No existing database found. Will create new one.")
        return False
    
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Database backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def add_column_if_not_exists(cursor, table_name, column_definition):
    """Add a column to a table if it doesn't exist"""
    column_name = column_definition.split()[0]
    
    if not column_exists(cursor, table_name, column_name):
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}")
            print(f"Added column '{column_name}' to table '{table_name}'")
            return True
        except Exception as e:
            print(f"Error adding column '{column_name}' to table '{table_name}': {e}")
            return False
    else:
        print(f"Column '{column_name}' already exists in table '{table_name}'")
        return True

def create_table_if_not_exists(cursor, table_sql):
    """Create a table if it doesn't exist"""
    try:
        cursor.execute(table_sql)
        print(f"Table created or already exists")
        return True
    except Exception as e:
        print(f"Error creating table: {e}")
        return False

def migrate_database():
    """Perform database migration"""
    print("Starting database migration...")
    
    # Create backup
    backup_database()
    
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        print("\n=== Phase 1.1: Adding new columns to InventoryItem ===")
        
        # Add new columns to inventory_items table
        inventory_item_columns = [
            "cas_number VARCHAR(64)",
            "lot_number VARCHAR(64)",
            "safety_document_url VARCHAR(255)",
            "qr_code VARCHAR(255)",
            "responsible_person_id INTEGER REFERENCES users(id)",
            "storage_conditions VARCHAR(128)"
        ]
        
        for column_def in inventory_item_columns:
            add_column_if_not_exists(cursor, "inventory_items", column_def)
        
        print("\n=== Phase 1.3: Adding capacity management to locations ===")
        
        # Add capacity management columns to locations table
        location_columns = [
            "max_capacity INTEGER",
            "capacity_unit VARCHAR(32) DEFAULT 'items'",
            "current_usage INTEGER DEFAULT 0"
        ]
        
        for column_def in location_columns:
            add_column_if_not_exists(cursor, "locations", column_def)
        
        print("\n=== Creating new tables ===")
        
        # Create supplier_contacts table
        supplier_contacts_sql = """
        CREATE TABLE IF NOT EXISTS supplier_contacts (
            id INTEGER PRIMARY KEY,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
            name VARCHAR(128) NOT NULL,
            title VARCHAR(64),
            email VARCHAR(128),
            phone VARCHAR(32),
            mobile VARCHAR(32),
            is_primary BOOLEAN DEFAULT FALSE,
            is_technical_contact BOOLEAN DEFAULT FALSE,
            is_sales_contact BOOLEAN DEFAULT FALSE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Create user_permissions table
        user_permissions_sql = """
        CREATE TABLE IF NOT EXISTS user_permissions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            permission VARCHAR(64) NOT NULL,
            resource_type VARCHAR(32),
            resource_id INTEGER,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            granted_by_user_id INTEGER REFERENCES users(id),
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
        """
        
        # Create shopping_cart table
        shopping_cart_sql = """
        CREATE TABLE IF NOT EXISTS shopping_cart (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            item_name VARCHAR(255) NOT NULL,
            catalog_number VARCHAR(128),
            supplier_id INTEGER REFERENCES suppliers(id),
            quantity REAL NOT NULL,
            unit VARCHAR(32),
            estimated_price REAL,
            notes TEXT,
            project_code VARCHAR(64),
            urgency VARCHAR(16) DEFAULT 'Normal',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Create the tables
        print("Creating supplier_contacts table...")
        create_table_if_not_exists(cursor, supplier_contacts_sql)
        
        print("Creating user_permissions table...")
        create_table_if_not_exists(cursor, user_permissions_sql)
        
        print("Creating shopping_cart table...")
        create_table_if_not_exists(cursor, shopping_cart_sql)
        
        print("\n=== Updating location usage counts ===")
        
        # Update current_usage for existing locations
        cursor.execute("""
        UPDATE locations 
        SET current_usage = (
            SELECT COUNT(*) 
            FROM inventory_items 
            WHERE inventory_items.location_id = locations.id
        )
        WHERE current_usage IS NULL OR current_usage = 0
        """)
        
        rows_updated = cursor.rowcount
        print(f"Updated usage counts for {rows_updated} locations")
        
        # Commit all changes
        conn.commit()
        print("\n[SUCCESS] Database migration completed successfully!")
        
        # Show summary
        print("\n=== Migration Summary ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Total tables: {len(tables)}")
        for table in tables:
            print(f"  - {table}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def verify_migration():
    """Verify that the migration was successful"""
    print("\n=== Verifying Migration ===")
    
    db_path = get_db_path()
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
        
        print("[SUCCESS] Migration verification successful!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== CellStorage Database Migration Tool ===")
    print("This will migrate your database to support Phase 1 enhancements.")
    print()
    
    response = input("Do you want to proceed with the migration? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Migration cancelled.")
        exit(0)
    
    # Perform migration
    success = migrate_database()
    
    if success:
        # Verify migration
        verify_migration()
        print("\n[SUCCESS] Migration completed! You can now restart the application.")
    else:
        print("\n[ERROR] Migration failed. Please check the error messages above.")
        print("Your original database has been backed up.")