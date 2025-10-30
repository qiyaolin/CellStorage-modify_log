"""
Quick database fix to add batch_id column to print_jobs table
"""

import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def add_batch_id_column():
    """Add batch_id column to print_jobs table"""
    try:
        from app import create_app, db
        
        # Create Flask app
        app = create_app()
        
        with app.app_context():
            print("Adding batch_id column to print_jobs table...")
            
            # Check if column already exists
            inspector = db.inspect(db.engine)
            
            # Check current columns
            print_job_columns = inspector.get_columns('print_jobs')
            column_names = [col['name'] for col in print_job_columns]
            
            if 'batch_id' in column_names:
                print("batch_id column already exists")
                return True
            
            # Add the batch_id column
            print("Adding batch_id column...")
            
            # Use raw SQL to add the column
            sql_commands = [
                "ALTER TABLE print_jobs ADD COLUMN batch_id INTEGER;",
                "ALTER TABLE print_jobs ADD CONSTRAINT fk_print_jobs_batch_id FOREIGN KEY (batch_id) REFERENCES vial_batches(id);"
            ]
            
            for sql in sql_commands:
                try:
                    print(f"Executing: {sql}")
                    db.session.execute(sql)
                    db.session.commit()
                    print("SUCCESS")
                except Exception as e:
                    print(f"ERROR: {e}")
                    db.session.rollback()
                    return False
            
            # Verify the column was added
            inspector = db.inspect(db.engine)
            updated_columns = inspector.get_columns('print_jobs')
            updated_column_names = [col['name'] for col in updated_columns]
            
            if 'batch_id' in updated_column_names:
                print("batch_id column added successfully!")
                return True
            else:
                print("Failed to add batch_id column")
                return False
                
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Adding batch_id column to print_jobs table")
    print("=" * 50)
    
    success = add_batch_id_column()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1)