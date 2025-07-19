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
    # Get login page and extract CSRF token
    login_page = session.get('http://127.0.0.1:5000/auth/login', timeout=10)
    csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', login_page.text)
    if not csrf_match:
        print('ERROR: Could not find CSRF token')
        sys.exit(1)
    
    csrf_token = csrf_match.group(1)
    
    # Login with admin credentials
    login_data = {
        'username': 'admin',
        'password': 'admin',  
        'csrf_token': csrf_token,
        'submit': 'Sign In'
    }
    
    response = session.post('http://127.0.0.1:5000/auth/login', data=login_data, timeout=10, allow_redirects=False)
    
    if response.status_code != 302:
        print(f'ERROR: Login failed with status {response.status_code}')
        sys.exit(1)
    
    print('SUCCESS: Login successful')
    
    # Test main dashboard access
    dashboard = session.get('http://127.0.0.1:5000/', timeout=10)
    print(f'Dashboard status: {dashboard.status_code}')
    
    if dashboard.status_code == 500:
        print('ERROR: Internal Server Error on dashboard')
        print(f'Response snippet: {dashboard.text[:1000]}')
    elif dashboard.status_code == 200:
        print('SUCCESS: Dashboard loads successfully!')
        
        # Check if dashboard contains expected content
        if 'Lab Management System' in dashboard.text:
            print('SUCCESS: Dashboard content verified')
        else:
            print('WARNING: Dashboard content may be incomplete')
        
        # Test cell storage module access
        cell_storage = session.get('http://127.0.0.1:5000/cell-storage/', timeout=10)
        print(f'Cell Storage module status: {cell_storage.status_code}')
        
        if cell_storage.status_code == 200:
            print('SUCCESS: Cell Storage module loads successfully!')
        elif cell_storage.status_code == 500:
            print('ERROR: Cell Storage module has Internal Server Error')
            print(f'Response snippet: {cell_storage.text[:500]}')
        
    else:
        print(f'Unexpected dashboard status: {dashboard.status_code}')
        
except Exception as e:
    print(f'Error: {e}')