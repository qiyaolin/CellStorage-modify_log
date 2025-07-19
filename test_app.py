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
    response = requests.get('http://127.0.0.1:5000/', timeout=10, allow_redirects=False)
    print(f'Status Code: {response.status_code}')
    print(f'Response Headers: {dict(response.headers)}')
    if response.status_code != 200:
        print(f'Response Text: {response.text[:500]}')
except Exception as e:
    print(f'Error: {e}')