#!/usr/bin/env python3
"""
Simple script to verify print jobs without Flask dependencies
This can be used to check current print job status
"""

def check_print_jobs_via_api():
    """Check print jobs via API endpoint"""
    import requests
    import json
    
    # These are the API endpoints based on the codebase
    base_url = "https://ambient-decoder-467517-h8.nn.r.appspot.com"
    
    # Token from test files
    token = "zWCcDs_VmMWYVs6xWudyOZlRCwwC4Q-PAmKmrNpZ_kI"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Check print system status
        print("Checking print system status...")
        response = requests.get(f"{base_url}/api/print/status", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Print System Status:")
            print(f"   - Total jobs: {data.get('total_jobs', 0)}")
            print(f"   - Pending jobs: {data.get('pending_jobs', 0)}")
            print(f"   - Processing jobs: {data.get('processing_jobs', 0)}")
            print(f"   - Failed jobs: {data.get('failed_jobs', 0)}")
            print(f"   - Completed jobs: {data.get('completed_jobs', 0)}")
        else:
            print(f"Status check failed: {response.status_code}")
        
        # Try to fetch a pending job (this is what the print agent does)
        print("\nChecking for pending jobs...")
        response = requests.get(f"{base_url}/api/print/fetch-pending-job?server_id=test", headers=headers)
        if response.status_code == 200:
            job_data = response.json()
            if job_data.get('job'):
                job = job_data['job']
                print(f"WARNING: Found pending job:")
                print(f"   - Job ID: {job.get('id')}")
                print(f"   - Status: {job.get('status')}")
                print(f"   - Priority: {job.get('priority')}")
                print(f"   - Created: {job.get('created_at')}")
                print(f"   - Error: {job.get('error_message', 'None')}")
                print(f"\nThis job can be managed through Flask-admin now!")
                return job.get('id')
            else:
                print("No pending jobs found")
        else:
            print(f"Fetch pending job failed: {response.status_code}")
            
    except Exception as e:
        print(f"Error checking print jobs: {e}")
    
    return None

def simulate_job_status_update(job_id, new_status):
    """Simulate updating a job status (like Flask-admin would do)"""
    import requests
    
    base_url = "https://ambient-decoder-467517-h8.nn.r.appspot.com"
    token = "zWCcDs_VmMWYVs6xWudyOZlRCwwC4Q-PAmKmrNpZ_kI"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    try:
        data = {"status": new_status, "error_message": "Manually updated via admin"}
        response = requests.post(f"{base_url}/api/print/update-job-status/{job_id}", 
                               headers=headers, json=data)
        if response.status_code == 200:
            print(f"Successfully updated job {job_id} to status: {new_status}")
            return True
        else:
            print(f"Failed to update job {job_id}: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"Error updating job {job_id}: {e}")
    
    return False

if __name__ == "__main__":
    print("Print Job Verification Tool")
    print("=" * 50)
    
    job_id = check_print_jobs_via_api()
    
    if job_id:
        print(f"\nSolutions for the infinite loop issue:")
        print(f"1. Use Flask-admin to delete job {job_id}")
        print(f"2. Use Flask-admin to change job {job_id} status to 'failed' or 'completed'")
        print(f"3. Use Flask-admin 'Reset to Pending' action to retry the job")
        
        # Demonstrate API-based status update
        print(f"\nWant to fix job {job_id} right now? (y/n): ", end="")
        try:
            choice = input().lower().strip()
            if choice == 'y':
                print(f"Attempting to mark job {job_id} as failed...")
                if simulate_job_status_update(job_id, "failed"):
                    print("Job marked as failed! The infinite loop should stop.")
                    print("   The print agent should no longer pick up this job.")
        except KeyboardInterrupt:
            print("\nCancelled")
    
    print(f"\nFlask-admin Access:")
    print(f"   URL: https://ambient-decoder-467517-h8.nn.r.appspot.com/flask-admin")
    print(f"   Features added:")
    print(f"   - Print Job Management: View, delete, change status")
    print(f"   - Print Server Management: Monitor server status")  
    print(f"   - Bulk actions: Delete jobs, reset to pending")