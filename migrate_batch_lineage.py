#!/usr/bin/env python3
"""
Batch Lineage Database Migration Script

This script adds the batch_lineage table for proper parent-child batch tracking.
Follows the existing migration pattern used in migrate_database.py.

Usage:
    python migrate_batch_lineage.py           # Interactive mode with backup
    python migrate_batch_lineage.py --force   # Skip confirmation
"""

import sqlite3
import os
import sys
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
        print(f"✅ Database backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False


def table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def create_batch_lineage_table(cursor):
    """Create the batch_lineage table"""
    if table_exists(cursor, 'batch_lineage'):
        print("✅ Table 'batch_lineage' already exists")
        return True

    try:
        # SQLite version - use INTEGER PRIMARY KEY for auto-increment
        cursor.execute("""
            CREATE TABLE batch_lineage (
                id INTEGER PRIMARY KEY,
                parent_batch_id INTEGER NOT NULL,
                child_batch_id INTEGER NOT NULL,
                relationship_type VARCHAR(50) NOT NULL DEFAULT 'passage',
                notes TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_by_user_id INTEGER,
                FOREIGN KEY (parent_batch_id) REFERENCES vial_batches(id) ON DELETE CASCADE,
                FOREIGN KEY (child_batch_id) REFERENCES vial_batches(id) ON DELETE CASCADE,
                CHECK (parent_batch_id != child_batch_id),
                UNIQUE (parent_batch_id, child_batch_id)
            )
        """)
        print("✅ Table 'batch_lineage' created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating table 'batch_lineage': {e}")
        return False


def create_indexes(cursor):
    """Create indexes for better query performance"""
    indexes = [
        ("idx_batch_lineage_parent", "CREATE INDEX IF NOT EXISTS idx_batch_lineage_parent ON batch_lineage(parent_batch_id)"),
        ("idx_batch_lineage_child", "CREATE INDEX IF NOT EXISTS idx_batch_lineage_child ON batch_lineage(child_batch_id)"),
        ("idx_batch_lineage_type", "CREATE INDEX IF NOT EXISTS idx_batch_lineage_type ON batch_lineage(relationship_type)"),
    ]

    for index_name, index_sql in indexes:
        try:
            cursor.execute(index_sql)
            print(f"✅ Index '{index_name}' created")
        except Exception as e:
            print(f"❌ Error creating index '{index_name}': {e}")
            return False

    return True


def migrate_existing_relationships(cursor):
    """
    Migrate existing string-based relationships to proper foreign keys.
    This is best-effort - some relationships may not be migratable.
    """
    print("\n📊 Migrating existing relationships...")

    migrated_count = 0
    failed_count = 0
    skipped_count = 0

    try:
        # Get all batches with their parental_cell_line info
        cursor.execute("""
            SELECT DISTINCT vb.id, vb.name, cv.parental_cell_line
            FROM vial_batches vb
            LEFT JOIN cryovials cv ON cv.batch_id = vb.id
            WHERE cv.parental_cell_line IS NOT NULL AND cv.parental_cell_line != ''
            LIMIT 1000
        """)

        batches_with_parents = cursor.fetchall()
        total_batches = len(batches_with_parents)

        if total_batches == 0:
            print("ℹ️  No batches with parental_cell_line found")
            return True

        print(f"📦 Processing {total_batches} batches...")

        for idx, (batch_id, batch_name, parental_cell_line) in enumerate(batches_with_parents, 1):
            if idx % 50 == 0:
                print(f"   Progress: {idx}/{total_batches}")

            # Try to find parent batch by name
            cursor.execute("""
                SELECT id FROM vial_batches
                WHERE name = ? AND id != ?
                LIMIT 1
            """, (parental_cell_line, batch_id))

            parent_result = cursor.fetchone()

            if not parent_result:
                skipped_count += 1
                continue

            parent_id = parent_result[0]

            # Check if relationship already exists
            cursor.execute("""
                SELECT id FROM batch_lineage
                WHERE parent_batch_id = ? AND child_batch_id = ?
            """, (parent_id, batch_id))

            if cursor.fetchone():
                skipped_count += 1
                continue

            # Create relationship
            try:
                cursor.execute("""
                    INSERT INTO batch_lineage
                    (parent_batch_id, child_batch_id, relationship_type, notes)
                    VALUES (?, ?, 'passage', ?)
                """, (parent_id, batch_id, f"Auto-migrated from parental_cell_line: {parental_cell_line}"))
                migrated_count += 1
            except Exception as e:
                failed_count += 1
                print(f"   ⚠️  Failed to create relationship {parent_id} -> {batch_id}: {e}")

        print(f"\n📈 Migration summary:")
        print(f"   ✅ Migrated: {migrated_count} relationships")
        print(f"   ⏭️  Skipped: {skipped_count} (no parent found or already exists)")
        print(f"   ❌ Failed: {failed_count}")

        return True

    except Exception as e:
        print(f"❌ Error during relationship migration: {e}")
        return False


def verify_migration(cursor):
    """Verify the migration was successful"""
    print("\n🔍 Verifying migration...")

    try:
        # Check table exists
        if not table_exists(cursor, 'batch_lineage'):
            print("❌ Table 'batch_lineage' does not exist")
            return False

        # Check relationship count
        cursor.execute("SELECT COUNT(*) FROM batch_lineage")
        lineage_count = cursor.fetchone()[0]
        print(f"✅ Found {lineage_count} batch lineage relationships")

        # Check for circular references (should be 0)
        cursor.execute("SELECT COUNT(*) FROM batch_lineage WHERE parent_batch_id = child_batch_id")
        circular = cursor.fetchone()[0]

        if circular > 0:
            print(f"⚠️  Warning: Found {circular} circular references (these should not exist)")
        else:
            print("✅ No circular references found")

        # Sample some relationships
        cursor.execute("""
            SELECT bl.id, p.name, c.name, bl.relationship_type
            FROM batch_lineage bl
            JOIN vial_batches p ON p.id = bl.parent_batch_id
            JOIN vial_batches c ON c.id = bl.child_batch_id
            LIMIT 5
        """)

        sample_lineages = cursor.fetchall()
        if sample_lineages:
            print("\n📋 Sample relationships:")
            for rel_id, parent_name, child_name, rel_type in sample_lineages:
                print(f"   {parent_name} -> {child_name} [{rel_type}]")

        # Check indexes
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='batch_lineage'
        """)
        indexes = cursor.fetchall()
        print(f"\n✅ Found {len(indexes)} indexes on batch_lineage table")

        return True

    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False


def migrate_database():
    """Perform the database migration"""
    print("=" * 80)
    print("Batch Lineage Table Migration")
    print("=" * 80)

    # Create backup
    backup_database()

    db_path = get_db_path()

    if not os.path.exists(db_path):
        print(f"\n❌ Database not found at: {db_path}")
        print("Please run the application first to create the database.")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        print("\n📋 Step 1: Creating batch_lineage table...")
        if not create_batch_lineage_table(cursor):
            return False

        print("\n📋 Step 2: Creating indexes...")
        if not create_indexes(cursor):
            return False

        print("\n📋 Step 3: Migrating existing relationships...")
        if not migrate_existing_relationships(cursor):
            print("⚠️  Data migration incomplete, but table created successfully")

        # Commit all changes
        conn.commit()

        print("\n📋 Step 4: Verifying migration...")
        if not verify_migration(cursor):
            return False

        print("\n" + "=" * 80)
        print("✅ Migration completed successfully!")
        print("=" * 80)
        print("\n📝 Next steps:")
        print("1. Review the migrated relationships in the database")
        print("2. Restart the application")
        print("3. Test the History Tree page: /cell-storage/history-tree")
        print("4. Use the batch management UI to add/edit relationships")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


def rollback_migration():
    """Rollback the migration by dropping the table"""
    print("=" * 80)
    print("Rolling Back Batch Lineage Migration")
    print("=" * 80)

    db_path = get_db_path()

    if not os.path.exists(db_path):
        print(f"\n❌ Database not found at: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DROP TABLE IF EXISTS batch_lineage")
        conn.commit()
        print("\n✅ Table 'batch_lineage' dropped successfully")
        print("Migration rolled back.")
        return True

    except Exception as e:
        print(f"❌ Rollback error: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


def main():
    """Main migration function"""
    # Check for rollback flag
    if '--rollback' in sys.argv:
        response = input("Are you sure you want to rollback the migration? (y/N): ")
        if response.lower() in ['y', 'yes']:
            rollback_migration()
        return

    # Check for force flag
    if '--force' not in sys.argv:
        print("This will add the batch_lineage table for proper batch relationship tracking.")
        print("A backup of your database will be created automatically.")
        print()
        response = input("Do you want to proceed with the migration? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Migration cancelled.")
            return

    # Perform migration
    success = migrate_database()

    if not success:
        print("\n❌ Migration failed. Please check the error messages above.")
        print("Your original database has been backed up.")
        sys.exit(1)


if __name__ == "__main__":
    main()
