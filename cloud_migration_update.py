"""
Cloud SQL Database Migration for Printing System
For existing deployment at: https://ambient-decoder-467517-h8.nn.r.appspot.com/

This script connects to your existing Cloud SQL instance and adds the printing tables.
"""

import os
import sys
from datetime import datetime

def run_cloud_migration():
    """Run migration on existing Cloud SQL database"""
    try:
        # Set up Google Cloud environment
        print("🌐 Connecting to Google Cloud SQL...")
        print(f"🕐 Migration started at: {datetime.now()}")
        
        # Import after setting up environment
        from app import create_app, db
        from app.cell_storage.models import PrintJob, PrintServer
        
        # Create Flask app with Cloud SQL config
        app = create_app()
        
        with app.app_context():
            print("🔗 Connected to Cloud SQL database")
            
            # Check current database info
            try:
                # Test connection
                result = db.engine.execute("SELECT 1 as test").fetchone()
                print("✅ Database connection successful")
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False
            
            # Get current tables
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            print(f"📋 Current tables in database: {len(existing_tables)}")
            print("   Existing tables:", ", ".join(existing_tables))
            
            # Check if printing tables already exist
            if 'print_jobs' in existing_tables:
                print("⚠️  print_jobs table already exists - skipping creation")
                jobs_created = False
            else:
                print("➕ Will create print_jobs table")
                jobs_created = True
            
            if 'print_servers' in existing_tables:
                print("⚠️  print_servers table already exists - skipping creation")
                servers_created = False
            else:
                print("➕ Will create print_servers table")
                servers_created = True
                
            if not jobs_created and not servers_created:
                print("ℹ️  All printing tables already exist. No migration needed.")
                return verify_existing_tables(db)
            
            # Create new tables
            print("\n🏗️  Creating printing system tables...")
            
            try:
                # This will only create missing tables
                db.create_all()
                print("✅ Tables created successfully")
                
                # Verify tables were created
                inspector = db.inspect(db.engine)
                updated_tables = inspector.get_table_names()
                
                if 'print_jobs' in updated_tables and 'print_servers' in updated_tables:
                    print("✅ All printing tables are now present in database")
                    
                    # Show new table structures
                    show_table_info(inspector)
                    
                    # Test the new tables
                    return test_printing_tables(db)
                    
                else:
                    print("❌ Some tables may not have been created properly")
                    return False
                    
            except Exception as e:
                print(f"❌ Error creating tables: {e}")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_existing_tables(db):
    """Verify existing printing tables are working"""
    try:
        from app.cell_storage.models import PrintJob, PrintServer
        
        print("\n🔍 Verifying existing printing tables...")
        
        # Test queries
        job_count = PrintJob.query.count()
        server_count = PrintServer.query.count()
        
        print(f"✅ PrintJob table: {job_count} existing records")
        print(f"✅ PrintServer table: {server_count} existing servers")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying existing tables: {e}")
        return False

def show_table_info(inspector):
    """Show information about the printing tables"""
    print("\n📊 Printing Tables Structure:")
    
    # Print Jobs table
    if 'print_jobs' in inspector.get_table_names():
        print("\n🖨️  print_jobs table:")
        columns = inspector.get_columns('print_jobs')
        for col in columns:
            nullable = "nullable" if col['nullable'] else "required"
            print(f"   📄 {col['name']}: {col['type']} ({nullable})")
    
    # Print Servers table  
    if 'print_servers' in inspector.get_table_names():
        print("\n🖥️  print_servers table:")
        columns = inspector.get_columns('print_servers')
        for col in columns:
            nullable = "nullable" if col['nullable'] else "required"
            print(f"   📄 {col['name']}: {col['type']} ({nullable})")

def test_printing_tables(db):
    """Test the printing tables functionality"""
    try:
        from app.cell_storage.models import PrintJob, PrintServer, User
        
        print("\n🧪 Testing printing system functionality...")
        
        # Test basic queries
        job_count = PrintJob.query.count()
        server_count = PrintServer.query.count()
        user_count = User.query.count()
        
        print(f"✅ Query tests passed")
        print(f"   - Print jobs: {job_count}")
        print(f"   - Print servers: {server_count}")  
        print(f"   - Users (for FK test): {user_count}")
        
        if user_count == 0:
            print("⚠️  No users found - cannot test foreign key relationship")
            return True
        
        # Test creating a sample record
        print("\n🔬 Testing record creation...")
        
        # Get first user for FK test
        first_user = User.query.first()
        
        # Create test print job
        test_job = PrintJob(
            label_data='{"test": "migration_test", "created_at": "' + datetime.now().isoformat() + '"}',
            priority='normal',
            requested_by=first_user.id,
            status='pending'
        )
        
        db.session.add(test_job)
        db.session.flush()  # Get ID without committing
        
        test_id = test_job.id
        print(f"✅ Test PrintJob created with ID: {test_id}")
        
        # Test relationship
        print(f"✅ User relationship working: {test_job.user.username}")
        
        # Clean up test record
        db.session.delete(test_job)
        db.session.commit()
        print("✅ Test record cleaned up")
        
        print("\n🎉 All printing system tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_next_steps():
    """Show what to do after migration"""
    print("\n" + "="*60)
    print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("1. 🚀 Deploy updated code to App Engine:")
    print("   gcloud app deploy")
    
    print("\n2. ⚙️  Enable printing in your config:")
    print("   Set CENTRALIZED_PRINTING_ENABLED=true in app.yaml")
    
    print("\n3. 🌐 Your updated app will be available at:")
    print("   https://ambient-decoder-467517-h8.nn.r.appspot.com/")
    
    print("\n4. 🖨️  To use printing features:")
    print("   - Users can now select 'Print labels after saving' when creating vials")
    print("   - Print jobs will be stored in the database")
    print("   - Set up a print server (optional) to process jobs automatically")
    
    print("\n5. 📊 Monitor printing system:")
    print("   - Check /admin for print jobs and servers")
    print("   - Visit /api/print/status for system status")
    
    print("\n6. 🖥️  Optional - Set up print server:")
    print("   - Deploy dymo-print-server-nodejs on a Windows machine")
    print("   - Configure it to connect to your Cloud SQL backend")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    print("🌐 Google Cloud SQL Printing System Migration")
    print("🔗 For: https://ambient-decoder-467517-h8.nn.r.appspot.com/")
    print("=" * 60)
    
    # Check if running in correct environment
    instance_connection = os.environ.get('INSTANCE_CONNECTION_NAME')
    if instance_connection:
        print(f"✅ Cloud SQL connection detected: {instance_connection}")
    else:
        print("⚠️  No INSTANCE_CONNECTION_NAME found - make sure you're in the right environment")
        
    confirm = input("\n🤔 Ready to update the Cloud SQL database? (yes/no): ")
    
    if confirm.lower() in ['yes', 'y']:
        print("\n🚀 Starting migration...")
        success = run_cloud_migration()
        
        if success:
            show_next_steps()
        else:
            print("\n❌ Migration failed!")
            print("💡 Troubleshooting tips:")
            print("   - Make sure you have database connection permissions")
            print("   - Check that your Google Cloud credentials are set up")
            print("   - Verify the INSTANCE_CONNECTION_NAME is correct")
            sys.exit(1)
    else:
        print("Migration cancelled.")