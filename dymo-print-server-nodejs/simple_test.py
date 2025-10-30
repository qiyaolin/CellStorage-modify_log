#!/usr/bin/env python3
import json
import requests
import os

def test_connection():
    # Load config
    config_path = os.path.join(os.path.dirname(__file__), 'src', 'print_agent_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    backend_url = config['backend_url']
    api_token = config['api_token']
    
    print(f"Testing connection to: {backend_url}")
    
    # Test API
    headers = {'Authorization': f'Bearer {api_token}'}
    url = f"{backend_url}/api/print/fetch-pending-job?server_id=test"
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code == 200:
            print("SUCCESS: API connection working!")
            return True
        else:
            print("ERROR: API connection failed!")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_connection()