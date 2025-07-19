import requests
import subprocess
import time
import threading
import sys
from bs4 import BeautifulSoup

def run_app():
    subprocess.run([sys.executable, 'run.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

app_thread = threading.Thread(target=run_app, daemon=True)
app_thread.start()

time.sleep(3)

session = requests.Session()

try:
    # Get login page to extract CSRF token
    login_page = session.get('http://127.0.0.1:5000/auth/login', timeout=10)
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
    
    # Try to login with admin user
    login_data = {
        'username': 'admin',
        'password': 'admin',  # Try common default password
        'csrf_token': csrf_token,
        'submit': 'Sign In'
    }
    
    response = session.post('http://127.0.0.1:5000/auth/login', data=login_data, timeout=10, allow_redirects=False)
    print(f'Login attempt status: {response.status_code}')
    
    if response.status_code == 302:
        print('Login successful - redirected')
        print(f'Redirect location: {response.headers.get("Location")}')
        
        # Follow redirect to dashboard
        dashboard = session.get('http://127.0.0.1:5000/', timeout=10)
        print(f'Dashboard status: {dashboard.status_code}')
        if dashboard.status_code == 500:
            print('ERROR: Internal Server Error on dashboard')
            print(f'Dashboard response: {dashboard.text[:1000]}')
        elif dashboard.status_code == 200:
            print('Dashboard loads successfully after login')
    else:
        print('Login failed')
        print(f'Response: {response.text[:500]}')
        
except Exception as e:
    print(f'Error: {e}')