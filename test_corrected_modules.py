#!/usr/bin/env python3
"""
Corrected comprehensive test with proper URL paths
"""

import requests
import subprocess
import time
import threading
import sys
import re
from urllib.parse import urljoin

class CellStorageTester:
    def __init__(self, base_url='http://127.0.0.1:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        
    def start_app(self):
        def run_app():
            subprocess.run([sys.executable, 'run.py'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        
        self.app_thread = threading.Thread(target=run_app, daemon=True)
        self.app_thread.start()
        time.sleep(3)
        
    def login(self, username='admin', password='admin'):
        try:
            login_url = urljoin(self.base_url, '/auth/login')
            response = self.session.get(login_url, timeout=10)
            
            if response.status_code != 200:
                return False, f"Login page error: {response.status_code}"
            
            csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)
            if not csrf_match:
                return False, "Could not find CSRF token"
            
            csrf_token = csrf_match.group(1)
            
            login_data = {
                'username': username,
                'password': password,
                'csrf_token': csrf_token,
                'submit': 'Sign In'
            }
            
            response = self.session.post(login_url, data=login_data, 
                                       timeout=10, allow_redirects=False)
            
            if response.status_code == 302:
                return True, "Login successful"
            else:
                return False, f"Login failed: {response.status_code}"
                
        except Exception as e:
            return False, f"Login error: {e}"
    
    def test_url(self, path, description):
        try:
            url = urljoin(self.base_url, path)
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return True, f"SUCCESS: {description}"
            elif response.status_code == 302:
                return True, f"REDIRECT: {description} (redirected)"
            elif response.status_code == 500:
                return False, f"ERROR: {description} - Internal Server Error"
            else:
                return False, f"ERROR: {description} - Status {response.status_code}"
                
        except Exception as e:
            return False, f"ERROR: {description} - {e}"
    
    def run_all_tests(self):
        print("Starting Comprehensive CellStorage Test Suite")
        print("=" * 50)
        
        # Start app and login
        print("Starting Flask application...")
        self.start_app()
        
        print("Logging in...")
        success, message = self.login()
        if not success:
            print(f"FAILED: {message}")
            return False
        print(f"SUCCESS: {message}")
        
        # Define all test cases with correct paths
        test_cases = [
            # Core Dashboard
            ('/', 'Main Dashboard'),
            ('/cell-storage/', 'Cell Storage Dashboard'),
            ('/inventory/', 'Inventory Dashboard'),
            
            # Cell Storage Core
            ('/cell-storage/cell_lines', 'Cell Lines List'),
            ('/cell-storage/cell_line/add', 'Add Cell Line Form'),
            ('/cell-storage/locations', 'Storage Locations Overview'),
            ('/cell-storage/tower/add', 'Add Tower Form'),
            ('/cell-storage/inventory', 'Cryovial Inventory'),
            ('/cell-storage/cryovial/add', 'Add Cryovial Form'),
            ('/cell-storage/audit_logs', 'Audit Logs'),
            
            # Inventory Management
            ('/inventory/items', 'Inventory Items'),
            ('/inventory/orders', 'Purchase Orders'),
            ('/inventory/suppliers', 'Suppliers Management'),
            ('/inventory/locations', 'Storage Locations'),
            
            # Authentication
            ('/auth/create_user', 'Create User Form'),
            ('/auth/users', 'User Management'),
            ('/auth/reset_password', 'Reset Password Form'),
            
            # Advanced Features (corrected paths)
            ('/cell-storage/admin/batch_edit_vials', 'Batch Edit Vials'),
            ('/cell-storage/admin/manage_batch', 'Batch Management'),
            ('/cell-storage/admin/import_csv', 'CSV Import'),
            ('/cell-storage/admin/backup_database', 'Database Backup'),
            ('/cell-storage/admin/restore_database', 'Database Restore'),
            ('/cell-storage/admin/clear_all', 'Clear All Data'),
        ]
        
        # Run tests
        results = []
        
        print("\\nRunning module tests...")
        for path, desc in test_cases:
            success, message = self.test_url(path, desc)
            results.append((success, message))
            print(f"  {message}")
        
        # Summary
        print("\\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(results)
        successful_tests = sum(1 for success, _ in results if success)
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\\nFAILED TESTS:")
            for success, message in results:
                if not success:
                    print(f"  - {message}")
        else:
            print("\\nALL TESTS PASSED! Application is working correctly.")
        
        return failed_tests == 0

def main():
    tester = CellStorageTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\\nUnexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())