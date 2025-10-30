"""
Database migration script to add printing system tables
For Google Cloud SQL deployment
"""

import os
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_migration():
    """Run the migration to add printing tables"""
    try:
        from app import create_app, db
        from app.cell_storage.models import PrintJob, PrintServer
        
        # Create Flask app
        app = create_app()
        
        with app.app_context():
            print("🔄 Starting printing tables migration...")
            print(f"📅 Migration started at: {datetime.now()}")
            
            # Check if tables already exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            print(f"📋 Existing tables: {len(existing_tables)}")
            
            if 'print_jobs' in existing_tables:
                print("⚠️  print_jobs table already exists")
            else:
                print("➕ Will create print_jobs table")
            
            if 'print_servers' in existing_tables:
                print("⚠️  print_servers table already exists")
            else:
                print("➕ Will create print_servers table")
            
            # Create all tables (this will only create missing ones)
            print("\n🏗️  Creating tables...")
            db.create_all()
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            updated_tables = inspector.get_table_names()
            
            if 'print_jobs' in updated_tables and 'print_servers' in updated_tables:
                print("✅ Printing tables created successfully!")
                
                # Show table info
                print("\n📊 Table Information:")
                
                # Print Jobs table info
                print("\n🖨️  print_jobs table columns:")
                print_job_columns = inspector.get_columns('print_jobs')
                for col in print_job_columns:
                    print(f"   - {col['name']}: {col['type']} {'(nullable)' if col['nullable'] else '(required)'}")
                
                # Print Servers table info
                print("\n🖥️  print_servers table columns:")
                print_server_columns = inspector.get_columns('print_servers')
                for col in print_server_columns:
                    print(f"   - {col['name']}: {col['type']} {'(nullable)' if col['nullable'] else '(required)'}")
                
                # Test basic functionality
                print("\n🧪 Testing table functionality...")
                
                # Test PrintJob model
                try:
                    job_count = PrintJob.query.count()
                    print(f"   - PrintJob queries working: {job_count} existing jobs")
                except Exception as e:
                    print(f"   ❌ PrintJob query failed: {e}")
                    return False
                
                # Test PrintServer model
                try:
                    server_count = PrintServer.query.count()
                    print(f"   - PrintServer queries working: {server_count} existing servers")
                except Exception as e:
                    print(f"   ❌ PrintServer query failed: {e}")
                    return False
                
                print(f"\n🎉 Migration completed successfully at: {datetime.now()}")
                return True
                
            else:
                print("❌ Failed to create printing tables")
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
        from app.cell_storage.models import PrintJob, PrintServer
        
        app = create_app()
        
        with app.app_context():
            print("\n🔍 Verifying migration...")
            
            # Check if we can perform basic operations
            
            # 1. Check if tables exist and are queryable
            job_count = PrintJob.query.count()
            server_count = PrintServer.query.count()
            
            print(f"✅ PrintJob table accessible: {job_count} records")
            print(f"✅ PrintServer table accessible: {server_count} records")
            
            # 2. Test creating a sample record (and then delete it)
            from flask_login import current_user
            
            # Create a sample print job (we'll delete it immediately)
            test_job = PrintJob(
                label_data='{"test": true}',
                priority='normal',
                requested_by=1  # Assume user ID 1 exists (admin)
            )
            
            db.session.add(test_job)
            db.session.flush()  # Get ID without committing
            
            test_job_id = test_job.id
            print(f"✅ Can create PrintJob records: ID {test_job_id}")
            
            # Delete the test record
            db.session.delete(test_job)
            db.session.commit()
            print("✅ Test record cleaned up")
            
            print("🎉 Migration verification successful!")
            return True
            
    except Exception as e:
        print(f"❌ Migration verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def rollback_migration():
    """Rollback the migration (drop printing tables)"""
    try:
        from app import create_app, db
        
        app = create_app()
        
        with app.app_context():
            print("⚠️  Starting migration rollback...")
            
            # Drop tables
            db.engine.execute("DROP TABLE IF EXISTS print_jobs CASCADE;")
            db.engine.execute("DROP TABLE IF EXISTS print_servers CASCADE;")
            
            print("✅ Printing tables dropped successfully")
            return True
            
    except Exception as e:
        print(f"❌ Rollback failed: {str(e)}")
        return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Printing system database migration')
    parser.add_argument('action', choices=['migrate', 'verify', 'rollback'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    print("🗄️  Cell Storage Printing System Database Migration")
    print("=" * 50)
    
    if args.action == 'migrate':
        success = run_migration()
        if success:
            print("\n✅ Migration completed successfully!")
            print("🔧 Next steps:")
            print("   1. Update your App Engine deployment")
            print("   2. Deploy print server (if using)")
            print("   3. Enable centralized printing in config")
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
        confirm = input("⚠️  Are you sure you want to rollback? This will delete all printing data. (yes/no): ")
        if confirm.lower() == 'yes':
            success = rollback_migration()
            if success:
                print("✅ Rollback completed!")
            else:
                print("❌ Rollback failed!")
                sys.exit(1)
        else:
            print("Rollback cancelled.")