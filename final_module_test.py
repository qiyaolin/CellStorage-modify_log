#!/usr/bin/env python3
"""Final comprehensive test with correct paths"""

import requests
import subprocess
import time
import threading
import sys
import re
from urllib.parse import urljoin

def test_final():
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
            print("Login failed")
            return
        
        print("Login successful")
        
        # Test remaining problematic routes
        test_routes = [
            ('/cell-storage/admin/backup', 'Database Backup'),
            ('/cell-storage/admin/restore', 'Database Restore'),
        ]
        
        for path, desc in test_routes:
            url = urljoin(base_url, path)
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"SUCCESS: {desc}")
            elif response.status_code == 302:
                print(f"REDIRECT: {desc}")
            else:
                print(f"ERROR: {desc} - Status {response.status_code}")
        
        print("\\nFinal functionality test:")
        
        # Test a few key workflows
        workflows = [
            # Core navigation
            ('/', 'Main Dashboard'),
            ('/cell-storage/', 'Cell Storage Module'),
            ('/inventory/', 'Inventory Module'),
            
            # Key features
            ('/cell-storage/cell_lines', 'Cell Lines Management'),
            ('/cell-storage/inventory', 'Cryovial Inventory'),
            ('/cell-storage/locations', 'Storage Locations'),
            ('/inventory/items', 'Inventory Items'),
            ('/auth/users', 'User Management'),
        ]
        
        all_success = True
        for path, desc in workflows:
            url = urljoin(base_url, path)
            response = session.get(url, timeout=10)
            
            if response.status_code in [200, 302]:
                print(f"✓ {desc}")
            else:
                print(f"✗ {desc} - Status {response.status_code}")
                all_success = False
        
        if all_success:
            print("\\n🎉 ALL CORE MODULES WORKING CORRECTLY!")
        else:
            print("\\n⚠️ Some modules have issues")
    
    except Exception as e:
        print(f"Test error: {e}")

if __name__ == "__main__":
    test_final()