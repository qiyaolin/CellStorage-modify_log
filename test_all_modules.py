#!/usr/bin/env python3
"""
Comprehensive browser simulation test for all CellStorage modules.
Tests each functional module end-to-end to ensure everything works.
"""

import requests
import subprocess
import time
import threading
import sys
import re
import json
from urllib.parse import urljoin

class CellStorageTester:
    def __init__(self, base_url='http://127.0.0.1:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.logged_in = False
        
    def start_app(self):
        """Start the Flask application"""
        def run_app():
            subprocess.run([sys.executable, 'run.py'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        
        self.app_thread = threading.Thread(target=run_app, daemon=True)
        self.app_thread.start()
        time.sleep(3)  # Wait for app to start
        
    def login(self, username='admin', password='admin'):
        """Login to the application"""
        try:
            # Get login page
            login_url = urljoin(self.base_url, '/auth/login')
            response = self.session.get(login_url, timeout=10)
            
            if response.status_code != 200:
                return False, f"Login page error: {response.status_code}"
            
            # Extract CSRF token
            csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)
            if not csrf_match:
                return False, "Could not find CSRF token"
            
            csrf_token = csrf_match.group(1)
            
            # Submit login
            login_data = {
                'username': username,
                'password': password,
                'csrf_token': csrf_token,
                'submit': 'Sign In'
            }
            
            response = self.session.post(login_url, data=login_data, 
                                       timeout=10, allow_redirects=False)
            
            if response.status_code == 302:
                self.logged_in = True
                return True, "Login successful"
            else:
                return False, f"Login failed: {response.status_code}"
                
        except Exception as e:
            return False, f"Login error: {e}"
    
    def test_url(self, path, description):
        """Test a specific URL path"""
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
    
    def test_dashboard_module(self):
        """Test main dashboard functionality"""
        print("\\n=== Testing Dashboard Module ===")
        
        tests = [
            ('/', 'Main Dashboard'),
            ('/cell-storage/', 'Cell Storage Dashboard'),
            ('/inventory/', 'Inventory Dashboard'),
        ]
        
        results = []
        for path, desc in tests:
            success, message = self.test_url(path, desc)
            results.append((success, message))
            print(f"  {message}")
        
        return results
    
    def test_cell_storage_module(self):
        """Test cell storage functionality"""
        print("\\n=== Testing Cell Storage Module ===")
        
        tests = [
            ('/cell-storage/cell_lines', 'Cell Lines List'),
            ('/cell-storage/cell_line/add', 'Add Cell Line Form'),
            ('/cell-storage/locations', 'Storage Locations Overview'),
            ('/cell-storage/tower/add', 'Add Tower Form'),
            ('/cell-storage/inventory', 'Cryovial Inventory'),
            ('/cell-storage/cryovial/add', 'Add Cryovial Form'),
            ('/cell-storage/audit_logs', 'Audit Logs'),
        ]
        
        results = []
        for path, desc in tests:
            success, message = self.test_url(path, desc)
            results.append((success, message))
            print(f"  {message}")
        
        return results
    
    def test_inventory_module(self):
        """Test inventory management functionality"""
        print("\\n=== Testing Inventory Module ===")
        
        tests = [
            ('/inventory/items', 'Inventory Items'),
            ('/inventory/orders', 'Purchase Orders'),
            ('/inventory/suppliers', 'Suppliers Management'),
            ('/inventory/locations', 'Storage Locations'),
        ]
        
        results = []
        for path, desc in tests:
            success, message = self.test_url(path, desc)
            results.append((success, message))
            print(f"  {message}")
        
        return results
    
    def test_auth_module(self):
        """Test authentication and user management"""
        print("\\n=== Testing Authentication Module ===")
        
        tests = [
            ('/auth/create_user', 'Create User Form'),
            ('/auth/users', 'User Management'),
            ('/auth/reset_password', 'Reset Password Form'),
        ]
        
        results = []
        for path, desc in tests:
            success, message = self.test_url(path, desc)
            results.append((success, message))
            print(f"  {message}")
        
        return results
    
    def test_advanced_features(self):
        """Test advanced features and admin functions"""
        print("\\n=== Testing Advanced Features ===")
        
        tests = [
            ('/cell-storage/batch_edit_vials', 'Batch Edit Vials'),
            ('/cell-storage/manage_batch_lookup', 'Batch Management'),
            ('/cell-storage/inventory_summary', 'Inventory Summary'),
            ('/cell-storage/import_csv', 'CSV Import'),
            ('/cell-storage/backup_database', 'Database Backup'),
            ('/cell-storage/theme_settings', 'Theme Settings'),
        ]
        
        results = []
        for path, desc in tests:
            success, message = self.test_url(path, desc)
            results.append((success, message))
            print(f"  {message}")
        
        return results
    
    def run_comprehensive_test(self):
        """Run complete test suite"""
        print("Starting Comprehensive CellStorage Test Suite")
        print("=" * 50)
        
        # Start application
        print("Starting Flask application...")
        self.start_app()
        
        # Login
        print("\\nLogging in...")
        success, message = self.login()
        if not success:
            print(f"FAILED: {message}")
            return False
        print(f"SUCCESS: {message}")
        
        # Run all module tests
        all_results = []
        
        all_results.extend(self.test_dashboard_module())
        all_results.extend(self.test_cell_storage_module())
        all_results.extend(self.test_inventory_module()) 
        all_results.extend(self.test_auth_module())
        all_results.extend(self.test_advanced_features())
        
        # Summary
        print("\\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(all_results)
        successful_tests = sum(1 for success, _ in all_results if success)
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\\nFAILED TESTS:")
            for success, message in all_results:
                if not success:
                    print(f"  - {message}")
        
        return failed_tests == 0

def main():
    """Main test runner"""
    tester = CellStorageTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("\\n🎉 ALL TESTS PASSED! Application is working correctly.")
        else:
            print("\\n⚠️ SOME TESTS FAILED. Please check the errors above.")
            
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\\nUnexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())