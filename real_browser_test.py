#!/usr/bin/env python3
"""
Real browser-like testing that validates actual page content rendering.
This test checks not just status codes but actual page content to ensure templates render correctly.
"""

import requests
import subprocess
import time
import threading
import sys
import re
from urllib.parse import urljoin

class RealBrowserTester:
    def __init__(self, base_url='http://127.0.0.1:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        
    def start_app(self):
        """Start the Flask application"""
        def run_app():
            subprocess.run([sys.executable, 'run.py'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        
        self.app_thread = threading.Thread(target=run_app, daemon=True)
        self.app_thread.start()
        time.sleep(3)
        
    def login(self, username='admin', password='admin'):
        """Login and return session"""
        try:
            login_url = urljoin(self.base_url, '/auth/login')
            response = self.session.get(login_url, timeout=10)
            
            if response.status_code != 200:
                return False, f"Login page failed: {response.status_code}"
            
            # Check if login page content is correct
            if 'login' not in response.text.lower() or 'csrf_token' not in response.text:
                return False, "Login page content is invalid"
            
            csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)
            if not csrf_match:
                return False, "CSRF token not found"
            
            csrf_token = csrf_match.group(1)
            
            login_data = {
                'username': username,
                'password': password,
                'csrf_token': csrf_token,
                'submit': 'Sign In'
            }
            
            response = self.session.post(login_url, data=login_data, 
                                       timeout=10, allow_redirects=True)
            
            # Check if login was successful by looking for user-specific content
            if response.status_code == 200 and username in response.text:
                return True, "Login successful"
            else:
                return False, f"Login failed - redirected to: {response.url}"
                
        except Exception as e:
            return False, f"Login error: {e}"
    
    def test_page_content(self, path, description, expected_content=None, should_not_contain=None):
        """Test a page with actual content validation"""
        try:
            url = urljoin(self.base_url, path)
            response = self.session.get(url, timeout=10)
            
            # Check status code
            if response.status_code != 200:
                if response.status_code == 500:
                    # Try to extract error details for 500 errors
                    if 'jinja2.exceptions' in response.text:
                        return False, f"ERROR: {description} - Jinja2 Template Error"
                    elif 'werkzeug.routing.exceptions' in response.text:
                        return False, f"ERROR: {description} - Routing Error"
                    else:
                        return False, f"ERROR: {description} - Internal Server Error"
                else:
                    return False, f"ERROR: {description} - Status {response.status_code}"
            
            # Check content length (empty responses are suspicious)
            if len(response.text) < 100:
                return False, f"ERROR: {description} - Response too short ({len(response.text)} chars)"
            
            # Check for common error indicators
            error_indicators = [
                'Internal Server Error',
                'jinja2.exceptions',
                'werkzeug.exceptions',
                'TemplateSyntaxError',
                'BuildError',
                'Could not build url',
                'AttributeError',
                'NameError'
            ]
            
            for error in error_indicators:
                if error in response.text:
                    return False, f"ERROR: {description} - Contains error: {error}"
            
            # Check for expected content
            if expected_content:
                for content in expected_content:
                    if content not in response.text:
                        return False, f"ERROR: {description} - Missing expected content: {content}"
            
            # Check for content that should not be present
            if should_not_contain:
                for content in should_not_contain:
                    if content in response.text:
                        return False, f"ERROR: {description} - Contains forbidden content: {content}"
            
            # Check for basic HTML structure
            if not all(tag in response.text for tag in ['<html', '<head', '<body']):
                return False, f"ERROR: {description} - Invalid HTML structure"
            
            return True, f"SUCCESS: {description}"
            
        except Exception as e:
            return False, f"ERROR: {description} - Exception: {e}"
    
    def run_comprehensive_content_test(self):
        """Run comprehensive test with actual content validation"""
        print("Starting Real Browser Content Validation Test")
        print("=" * 50)
        
        # Start application
        print("Starting Flask application...")
        self.start_app()
        
        # Test login first
        print("Testing login functionality...")
        success, message = self.login()
        if not success:
            print(f"CRITICAL: {message}")
            return False
        print(f"SUCCESS: {message}")
        
        # Define test cases with expected content
        test_cases = [
            # Core pages with expected content
            {
                'path': '/',
                'desc': 'Main Dashboard',
                'expected': ['Lab Management System', 'Cell Storage', 'Inventory'],
                'forbidden': ['Internal Server Error', 'jinja2.exceptions']
            },
            {
                'path': '/cell-storage/',
                'desc': 'Cell Storage Dashboard', 
                'expected': ['Welcome', current_user.username if 'current_user' in locals() else 'admin'],
                'forbidden': ['TemplateSyntaxError', 'BuildError']
            },
            {
                'path': '/cell-storage/cell_lines',
                'desc': 'Cell Lines List',
                'expected': ['Cell Lines', 'Add New Cell Line'],
                'forbidden': ['Could not build url']
            },
            {
                'path': '/cell-storage/inventory',
                'desc': 'Cryovial Inventory',
                'expected': ['CryoVial', 'Inventory'],
                'forbidden': ['main.cryovial_inventory']
            },
            {
                'path': '/cell-storage/locations',
                'desc': 'Storage Locations',
                'expected': ['Storage', 'Locations'],
                'forbidden': ['main.locations_overview']
            },
            {
                'path': '/inventory/',
                'desc': 'Inventory Module',
                'expected': ['Inventory'],
                'forbidden': ['Internal Server Error']
            },
            {
                'path': '/auth/users',
                'desc': 'User Management',
                'expected': ['Users', 'admin'],
                'forbidden': ['AttributeError']
            }
        ]
        
        # Run tests
        results = []
        print("\\nTesting page content rendering...")
        
        for test_case in test_cases:
            success, message = self.test_page_content(
                test_case['path'], 
                test_case['desc'],
                expected_content=test_case.get('expected'),
                should_not_contain=test_case.get('forbidden')
            )
            results.append((success, message))
            print(f"  {message}")
        
        # Test specific functionality that might cause errors
        print("\\nTesting error-prone functionality...")
        
        error_prone_tests = [
            ('/cell-storage/cryovial/add', 'Add Cryovial Form', ['Add', 'CryoVial'], ['main.']),
            ('/cell-storage/cell_line/add', 'Add Cell Line Form', ['Cell Line', 'Add'], ['main.']),
            ('/cell-storage/tower/add', 'Add Tower Form', ['Tower', 'Add'], ['main.']),
        ]
        
        for path, desc, expected, forbidden in error_prone_tests:
            success, message = self.test_page_content(path, desc, expected, forbidden)
            results.append((success, message))
            print(f"  {message}")
        
        # Summary
        print("\\n" + "=" * 50)
        print("REAL BROWSER TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(results)
        successful_tests = sum(1 for success, _ in results if success)
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\\nFAILED TESTS (with actual errors):")
            for success, message in results:
                if not success:
                    print(f"  - {message}")
        else:
            print("\\nALL TESTS PASSED! Pages render correctly with valid content.")
        
        return failed_tests == 0

def main():
    """Main test runner"""
    tester = RealBrowserTester()
    
    try:
        success = tester.run_comprehensive_content_test()
        
        if success:
            print("\\nSUCCESS: All pages render correctly!")
        else:
            print("\\nFAILED: Some pages have rendering issues.")
            
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\\nUnexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())