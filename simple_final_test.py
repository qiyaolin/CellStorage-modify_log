#!/usr/bin/env python3
"""Simple final test without unicode characters"""

import requests
import subprocess
import time
import threading
import sys
import re
from urllib.parse import urljoin

def test_simple():
    base_url = 'http://127.0.0.1:5000'
    session = requests.Session()
    
    # Start app
    def run_app():
        subprocess.run([sys.executable, 'run.py'], 
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL)
    
    app_thread = threading.Thread(target=run_app, daemon=True)
    app_thread.start()
    time.sleep(3)
    
    # Login
    try:
        login_url = urljoin(base_url, '/auth/login')
        response = session.get(login_url, timeout=10)
        csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)
        csrf_token = csrf_match.group(1)
        
        login_data = {
            'username': 'admin',
            'password': 'admin',
            'csrf_token': csrf_token,
            'submit': 'Sign In'
        }
        
        response = session.post(login_url, data=login_data, timeout=10, allow_redirects=False)
        
        if response.status_code != 302:
            print("FAILED: Login failed")
            return
        
        print("SUCCESS: Login successful")
        
        # Test core workflows
        workflows = [
            ('/', 'Main Dashboard'),
            ('/cell-storage/', 'Cell Storage Module'),
            ('/inventory/', 'Inventory Module'),
            ('/cell-storage/cell_lines', 'Cell Lines Management'),
            ('/cell-storage/inventory', 'Cryovial Inventory'),
            ('/cell-storage/locations', 'Storage Locations'),
            ('/inventory/items', 'Inventory Items'),
            ('/auth/users', 'User Management'),
            ('/cell-storage/admin/backup', 'Database Backup'),
            ('/cell-storage/admin/restore', 'Database Restore'),
        ]
        
        success_count = 0
        total_count = len(workflows)
        
        for path, desc in workflows:
            url = urljoin(base_url, path)
            response = session.get(url, timeout=10)
            
            if response.status_code in [200, 302]:
                print(f"SUCCESS: {desc}")
                success_count += 1
            else:
                print(f"FAILED: {desc} - Status {response.status_code}")
        
        print(f"\\nTest Results: {success_count}/{total_count} modules working")
        
        if success_count == total_count:
            print("ALL CORE MODULES WORKING CORRECTLY!")
            return True
        else:
            print("Some modules have issues")
            return False
    
    except Exception as e:
        print(f"Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_simple()
    sys.exit(0 if success else 1)