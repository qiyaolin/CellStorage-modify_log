import requests
import subprocess
import time
import threading
import sys
import re

def run_app():
    subprocess.run([sys.executable, 'run.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

app_thread = threading.Thread(target=run_app, daemon=True)
app_thread.start()

time.sleep(3)

session = requests.Session()

try:
    # Get login page to extract CSRF token
    login_page = session.get('http://127.0.0.1:5000/auth/login', timeout=10)
    
    # Extract CSRF token using regex
    csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', login_page.text)
    if not csrf_match:
        print('Could not find CSRF token')
        sys.exit(1)
    
    csrf_token = csrf_match.group(1)
    print(f'Found CSRF token: {csrf_token[:10]}...')
    
    # Try to login with admin user - let's first check what password it might have
    print('Attempting login with admin/admin...')
    login_data = {
        'username': 'admin',
        'password': 'admin',  
        'csrf_token': csrf_token,
        'submit': 'Sign In'
    }
    
    response = session.post('http://127.0.0.1:5000/auth/login', data=login_data, timeout=10, allow_redirects=False)
    print(f'Login attempt status: {response.status_code}')
    
    if response.status_code == 302:
        print('Login successful - redirected')
        location = response.headers.get('Location', '')
        print(f'Redirect location: {location}')
        
        # Follow redirect to dashboard
        dashboard = session.get('http://127.0.0.1:5000/', timeout=10)
        print(f'Dashboard status: {dashboard.status_code}')
        if dashboard.status_code == 500:
            print('ERROR: Internal Server Error on dashboard after login')
            print(f'Dashboard response: {dashboard.text[:1000]}')
        elif dashboard.status_code == 200:
            print('Dashboard loads successfully after login')
    elif response.status_code == 200:
        # Login failed, likely wrong password
        if 'Invalid username or password' in response.text:
            print('Wrong password - will try common passwords')
            for pwd in ['password', '123456', 'admin123', '']:
                login_data['password'] = pwd
                resp = session.post('http://127.0.0.1:5000/auth/login', data=login_data, timeout=10, allow_redirects=False)
                if resp.status_code == 302:
                    print(f'Success with password: "{pwd}"')
                    break
                print(f'Failed with password: "{pwd}"')
        else:
            print('Login page returned, but no error message found')
    else:
        print(f'Unexpected status: {response.status_code}')
        print(f'Response: {response.text[:500]}')
        
except Exception as e:
    print(f'Error: {e}')