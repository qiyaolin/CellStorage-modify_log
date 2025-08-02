#!/usr/bin/env python3
"""
Test script to create a print job directly through the database
"""

import os
import sys
import json
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.cell_storage.models import PrintJob, User

def create_test_print_job():
    """Create a test print job directly in the database"""
    
    app = create_app()
    
    with app.app_context():
        print("Creating test print job...")
        
        # Find a user (or create one if needed)
        user = User.query.first()
        if not user:
            print("No users found - creating test user")
            user = User(username='test_user', role='admin')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
        
        print(f"Using user: {user.username} (ID: {user.id})")
        
        # Create test label data
        label_data = {
            "batch_name": "TEST-BATCH-001",
            "batch_id": "B999",
            "vial_number": 1,
            "location": "Tower1/Drawer1/Box1",
            "position": "R1C1",
            "date_created": datetime.now().strftime('%Y-%m-%d')
        }
        
        # Create print job
        print_job = PrintJob(
            label_data=json.dumps(label_data),
            priority='normal',
            requested_by=user.id,
            status='pending'
        )
        
        db.session.add(print_job)
        db.session.commit()
        
        print(f"✓ Created print job #{print_job.id}")
        print(f"  Label data: {label_data}")
        print(f"  Status: {print_job.status}")
        print(f"  Priority: {print_job.priority}")
        
        # Verify the job can be queried
        pending_jobs = PrintJob.query.filter_by(status='pending').all()
        print(f"✓ Total pending jobs in database: {len(pending_jobs)}")
        
        print("\nNow the print agent should pick up this job!")
        print("Check the print agent logs to see if it processes this job.")
        
        return print_job.id

if __name__ == "__main__":
    try:
        job_id = create_test_print_job()
        print(f"\nTest job created with ID: {job_id}")
        print("Run the print agent to see if it processes this job.")
    except Exception as e:
        print(f"Error creating test job: {e}")
        import traceback
        traceback.print_exc()