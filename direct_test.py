#!/usr/bin/env python3
"""Direct test that manually checks for template and routing errors"""

import requests
import subprocess
import time
import threading
import sys
import re
from urllib.parse import urljoin

def test_direct():
    base_url = 'http://127.0.0.1:5000'
    
    # Start app
    def run_app():
        subprocess.run([sys.executable, 'run.py'], 
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL)
    
    app_thread = threading.Thread(target=run_app, daemon=True)
    app_thread.start()
    time.sleep(3)
    
    print("Direct Page Error Detection Test")
    print("=" * 40)
    
    # Test pages that don't require authentication
    public_pages = [
        '/auth/login'
    ]
    
    # Test pages after login (we'll use a simple session)
    session = requests.Session()
    
    # Quick login
    try:
        login_url = urljoin(base_url, '/auth/login')
        response = session.get(login_url, timeout=10)
        csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)
        
        if csrf_match:
            csrf_token = csrf_match.group(1)
            login_data = {
                'username': 'admin',
                'password': 'admin',
                'csrf_token': csrf_token,
                'submit': 'Sign In'
            }
            session.post(login_url, data=login_data, timeout=10)
        
        print("Login attempt completed")
    except:
        print("Login attempt failed, continuing with tests...")
    
    # Test all pages for errors
    test_pages = [
        '/auth/login',
        '/',
        '/cell-storage/',
        '/cell-storage/cell_lines',
        '/cell-storage/inventory', 
        '/cell-storage/locations',
        '/cell-storage/cryovial/add',
        '/cell-storage/cell_line/add',
        '/inventory/',
        '/inventory/items',
    ]
    
    errors_found = []
    
    for path in test_pages:
        try:
            url = urljoin(base_url, path)
            response = session.get(url, timeout=10)
            
            page_name = path.replace('/', ' ').strip() or 'root'
            
            # Check for specific error types
            if response.status_code == 500:
                # Get error details
                error_type = "Unknown Error"
                if 'jinja2.exceptions.TemplateSyntaxError' in response.text:
                    error_type = "Jinja2 Template Syntax Error"
                elif 'werkzeug.routing.exceptions.BuildError' in response.text:
                    error_type = "URL Building Error (missing endpoint)"
                elif 'Could not build url for endpoint' in response.text:
                    # Extract the specific endpoint error
                    endpoint_match = re.search(r"Could not build url for endpoint '([^']+)'", response.text)
                    if endpoint_match:
                        error_type = f"Missing endpoint: {endpoint_match.group(1)}"
                elif 'AttributeError' in response.text:
                    error_type = "Attribute Error (missing variable/function)"
                elif 'NameError' in response.text:
                    error_type = "Name Error (undefined variable)"
                
                print(f"FAILED: {page_name} - {error_type}")
                errors_found.append((path, error_type))
                
            elif response.status_code == 404:
                print(f"FAILED: {page_name} - Page Not Found (404)")
                errors_found.append((path, "404 Not Found"))
                
            elif response.status_code == 200:
                # Check content for client-side errors
                if len(response.text) < 100:
                    print(f"FAILED: {page_name} - Empty response")
                    errors_found.append((path, "Empty Response"))
                elif 'Internal Server Error' in response.text:
                    print(f"FAILED: {page_name} - Contains error message")
                    errors_found.append((path, "Error in content"))
                else:
                    print(f"SUCCESS: {page_name}")
                    
            elif response.status_code == 302:
                print(f"REDIRECT: {page_name} (redirect is normal)")
                
            else:
                print(f"FAILED: {page_name} - Status {response.status_code}")
                errors_found.append((path, f"Status {response.status_code}"))
                
        except Exception as e:
            print(f"FAILED: {page_name} - Exception: {e}")
            errors_found.append((path, f"Exception: {e}"))
    
    print("\\n" + "=" * 40)
    print("SUMMARY")
    print("=" * 40)
    
    if errors_found:
        print(f"Found {len(errors_found)} errors:")
        for path, error in errors_found:
            print(f"  {path}: {error}")
        return False
    else:
        print("No errors found! All pages accessible.")
        return True

if __name__ == "__main__":
    success = test_direct()
    print(f"\\nTest result: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)