#!/usr/bin/env python3
"""Improved test with better login handling"""

import requests
import subprocess
import time
import threading
import sys
import re
from urllib.parse import urljoin

def test_improved():
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
    
    print("Testing real page content...")
    
    try:
        # Test login page content first
        login_url = urljoin(base_url, '/auth/login')
        response = session.get(login_url, timeout=10)
        
        if response.status_code != 200:
            print(f"FAILED: Login page - Status {response.status_code}")
            return False
        
        if len(response.text) < 100:
            print(f"FAILED: Login page - Response too short")
            return False
        
        if 'Internal Server Error' in response.text or 'jinja2.exceptions' in response.text:
            print(f"FAILED: Login page - Contains error")
            return False
        
        print("SUCCESS: Login page renders correctly")
        
        # Extract CSRF and login
        csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)
        if not csrf_match:
            print("FAILED: No CSRF token found")
            return False
        
        csrf_token = csrf_match.group(1)
        
        login_data = {
            'username': 'admin',
            'password': 'admin',
            'csrf_token': csrf_token,
            'submit': 'Sign In'
        }
        
        # Try login with redirect handling
        response = session.post(login_url, data=login_data, timeout=10, allow_redirects=False)
        
        if response.status_code == 302:
            # Follow redirect
            redirect_url = response.headers.get('Location', '/')
            if redirect_url.startswith('/'):
                redirect_url = urljoin(base_url, redirect_url)
            
            response = session.get(redirect_url, timeout=10)
            
            if response.status_code == 200 and 'admin' in response.text:
                print("SUCCESS: Login successful")
            else:
                print(f"FAILED: Login redirect failed - Status {response.status_code}")
                return False
        else:
            print(f"FAILED: Login failed - Status {response.status_code}")
            return False
        
        # Now test actual page content
        test_pages = [
            ('/', 'Main Dashboard', ['Lab Management', 'Cell Storage']),
            ('/cell-storage/', 'Cell Storage Module', ['Welcome']),
            ('/cell-storage/cell_lines', 'Cell Lines', ['Cell Lines']),
            ('/cell-storage/inventory', 'Cryovial Inventory', ['CryoVial']),
            ('/inventory/', 'Inventory Module', ['Inventory']),
        ]
        
        all_passed = True
        
        for path, name, expected_content in test_pages:
            url = urljoin(base_url, path)
            response = session.get(url, timeout=10)
            
            # Check status
            if response.status_code != 200:
                print(f"FAILED: {name} - Status {response.status_code}")
                all_passed = False
                continue
            
            # Check content length
            if len(response.text) < 100:
                print(f"FAILED: {name} - Response too short")
                all_passed = False
                continue
            
            # Check for errors
            error_indicators = [
                'Internal Server Error',
                'jinja2.exceptions', 
                'TemplateSyntaxError',
                'BuildError',
                'Could not build url',
                'werkzeug.exceptions'
            ]
            
            has_error = False
            for error in error_indicators:
                if error in response.text:
                    print(f"FAILED: {name} - Contains error: {error}")
                    all_passed = False
                    has_error = True
                    break
            
            if has_error:
                continue
            
            # Check expected content
            missing_content = []
            for content in expected_content:
                if content not in response.text:
                    missing_content.append(content)
            
            if missing_content:
                print(f"FAILED: {name} - Missing content: {missing_content}")
                all_passed = False
            else:
                print(f"SUCCESS: {name}")
        
        if all_passed:
            print("\\nALL TESTS PASSED! All pages render correctly.")
            return True
        else:
            print("\\nSOME TESTS FAILED! Check the errors above.")
            return False
    
    except Exception as e:
        print(f"Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_improved()
    sys.exit(0 if success else 1)