import requests
import subprocess
import time
import threading
import sys

def run_app():
    subprocess.run([sys.executable, 'run.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

app_thread = threading.Thread(target=run_app, daemon=True)
app_thread.start()

time.sleep(3)

try:
    response = requests.get('http://127.0.0.1:5000/auth/login', timeout=10)
    print(f'Status Code: {response.status_code}')
    if response.status_code == 500:
        print(f'ERROR: Internal Server Error')
        print(f'Response Text: {response.text[:1000]}')
    elif response.status_code == 200:
        print('Login page loads successfully')
        if 'login' in response.text.lower():
            print('Login form detected')
    else:
        print(f'Unexpected status: {response.status_code}')
        print(f'Response Text: {response.text[:500]}')
except Exception as e:
    print(f'Error accessing login page: {e}')