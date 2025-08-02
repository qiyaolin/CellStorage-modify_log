"""
Database migration script to add batch_id column to print_jobs table
For Google Cloud SQL deployment
"""

import os
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_migration():
    """Run the migration to add batch_id column to print_jobs table"""
    try:
        from app import create_app, db
        
        # Create Flask app
        app = create_app()
        
        with app.app_context():
            print("Starting batch_id column migration...")
            print(f"Migration started at: {datetime.now()}")
            
            # Check if column already exists
            inspector = db.inspect(db.engine)
            
            # Check if print_jobs table exists
            existing_tables = inspector.get_table_names()
            if 'print_jobs' not in existing_tables:
                print("❌ print_jobs table does not exist. Run printing table migration first.")
                return False
            
            # Check current columns
            print_job_columns = inspector.get_columns('print_jobs')
            column_names = [col['name'] for col in print_job_columns]
            
            print(f"📋 Current print_jobs columns: {column_names}")
            
            if 'batch_id' in column_names:
                print("⚠️  batch_id column already exists")
                return True
            
            # Add the batch_id column
            print("\n🏗️  Adding batch_id column...")
            
            # Use raw SQL to add the column
            sql_commands = [
                # Add the batch_id column as nullable integer with foreign key
                "ALTER TABLE print_jobs ADD COLUMN batch_id INTEGER;",
                
                # Add foreign key constraint
                "ALTER TABLE print_jobs ADD CONSTRAINT fk_print_jobs_batch_id FOREIGN KEY (batch_id) REFERENCES vial_batches(id);"
            ]
            
            for sql in sql_commands:
                try:
                    print(f"   Executing: {sql}")
                    db.session.execute(sql)
                    db.session.commit()
                    print("   SUCCESS")
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
                    db.session.rollback()
                    return False
            
            # Verify the column was added
            print("\n🔍 Verifying column addition...")
            inspector = db.inspect(db.engine)
            updated_columns = inspector.get_columns('print_jobs')
            updated_column_names = [col['name'] for col in updated_columns]
            
            if 'batch_id' in updated_column_names:
                print("✅ batch_id column added successfully!")
                
                # Show updated table info
                print("\n📊 Updated print_jobs table columns:")
                for col in updated_columns:
                    marker = "🆕" if col['name'] == 'batch_id' else "   "
                    print(f"{marker} - {col['name']}: {col['type']} {'(nullable)' if col['nullable'] else '(required)'}")
                
                # Test basic functionality
                print("\n🧪 Testing table functionality...")
                
                try:
                    from app.cell_storage.models import PrintJob
                    job_count = PrintJob.query.count()
                    print(f"   - PrintJob queries working: {job_count} existing jobs")
                    
                    # Test that we can access the new column
                    first_job = PrintJob.query.first()
                    if first_job:
                        batch_id_value = first_job.batch_id
                        print(f"   - batch_id column accessible: {batch_id_value}")
                    
                except Exception as e:
                    print(f"   ❌ PrintJob query failed: {e}")
                    return False
                
                print(f"\n🎉 Migration completed successfully at: {datetime.now()}")
                return True
                
            else:
                print("❌ Failed to add batch_id column")
                return False
                
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_migration():
    """Verify the migration was successful"""
    try:
        from app import create_app, db
        from app.cell_storage.models import PrintJob, VialBatch
        
        app = create_app()
        
        with app.app_context():
            print("\n🔍 Verifying batch_id migration...")
            
            # Check if we can perform basic operations with the new column
            
            # 1. Check if column exists and is queryable
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('print_jobs')
            column_names = [col['name'] for col in columns]
            
            if 'batch_id' not in column_names:
                print("❌ batch_id column not found")
                return False
            
            print("✅ batch_id column exists")
            
            # 2. Test querying with the new column
            job_count = PrintJob.query.count()
            print(f"✅ PrintJob table accessible: {job_count} records")
            
            # 3. Test that the relationship works
            if job_count > 0:
                first_job = PrintJob.query.first()
                batch_id = first_job.batch_id
                print(f"✅ Can access batch_id: {batch_id}")
                
                # Test relationship if batch_id is set
                if batch_id:
                    try:
                        batch = first_job.batch
                        batch_name = batch.name if batch else "None"
                        print(f"✅ Batch relationship works: {batch_name}")
                    except Exception as e:
                        print(f"⚠️  Batch relationship issue: {e}")
            
            # 4. Test that we can set batch_id
            try:
                # Find a vial batch to test with
                test_batch = VialBatch.query.first()
                if test_batch and job_count > 0:
                    test_job = PrintJob.query.first()
                    original_batch_id = test_job.batch_id
                    
                    # Temporarily set and restore
                    test_job.batch_id = test_batch.id
                    db.session.flush()
                    print(f"✅ Can set batch_id: {test_batch.id}")
                    
                    # Restore original value
                    test_job.batch_id = original_batch_id
                    db.session.commit()
                    print("✅ Test changes reverted")
                else:
                    print("ℹ️  No test data available for relationship testing")
            except Exception as e:
                print(f"⚠️  Batch assignment test failed: {e}")
                db.session.rollback()
            
            print("🎉 Migration verification successful!")
            return True
            
    except Exception as e:
        print(f"❌ Migration verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def rollback_migration():
    """Rollback the migration (remove batch_id column)"""
    try:
        from app import create_app, db
        
        app = create_app()
        
        with app.app_context():
            print("⚠️  Starting migration rollback...")
            
            # Drop foreign key constraint first, then column
            sql_commands = [
                "ALTER TABLE print_jobs DROP CONSTRAINT IF EXISTS fk_print_jobs_batch_id;",
                "ALTER TABLE print_jobs DROP COLUMN IF EXISTS batch_id;"
            ]
            
            for sql in sql_commands:
                try:
                    print(f"   Executing: {sql}")
                    db.session.execute(sql)
                    db.session.commit()
                    print("   SUCCESS")
                except Exception as e:
                    print(f"   ⚠️  Command failed (may be expected): {e}")
                    db.session.rollback()
            
            print("✅ batch_id column rollback completed")
            return True
            
    except Exception as e:
        print(f"❌ Rollback failed: {str(e)}")
        return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Print jobs batch_id column migration')
    parser.add_argument('action', choices=['migrate', 'verify', 'rollback'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    print("Print Jobs batch_id Column Migration")
    print("=" * 50)
    
    if args.action == 'migrate':
        success = run_migration()
        if success:
            print("\n✅ Migration completed successfully!")
            print("🔧 Next steps:")
            print("   1. Deploy the updated application")
            print("   2. Test print job functionality")
            print("   3. Verify batch linking works")
        else:
            print("❌ Migration failed!")
            sys.exit(1)
    
    elif args.action == 'verify':
        success = verify_migration()
        if success:
            print("✅ Migration verification passed!")
        else:
            print("❌ Migration verification failed!")
            sys.exit(1)
    
    elif args.action == 'rollback':
        confirm = input("⚠️  Are you sure you want to rollback? This will remove the batch_id column. (yes/no): ")
        if confirm.lower() == 'yes':
            success = rollback_migration()
            if success:
                print("✅ Rollback completed!")
            else:
                print("❌ Rollback failed!")
                sys.exit(1)
        else:
            print("Rollback cancelled.")