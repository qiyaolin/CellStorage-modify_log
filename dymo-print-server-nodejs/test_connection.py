#!/usr/bin/env python3
"""
Test script to verify print server connection to backend
"""

import json
import requests
import sys
import os

def load_config():
    """Load configuration from print_agent_config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'src', 'print_agent_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return None

def get_auth_headers(api_token):
    """Return HTTP headers for authenticated requests"""
    headers = {'Content-Type': 'application/json'}
    if api_token:
        headers['Authorization'] = f'Bearer {api_token}'
    return headers

def test_backend_connection():
    """Test connection to backend API"""
    print("Testing DYMO Print Server Connection")
    print("=" * 50)
    
    # Load config
    config = load_config()
    if not config:
        return False
    
    backend_url = config.get('backend_url')
    api_token = config.get('api_token')
    
    print(f"Backend URL: {backend_url}")
    print(f"API Token: {'Configured' if api_token else 'Missing'}")
    
    if not api_token:
        print("ERROR: No API token configured!")
        return False
    
    # Test 1: Health check (fetch-pending-job)
    print("\nTest 1: Health Check")
    try:
        url = f"{backend_url}/api/print/fetch-pending-job?server_id=test-connection"
        headers = get_auth_headers(api_token)
        
        print(f"   Calling: {url}")
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"   SUCCESS: Health check passed: {data}")
        else:
            print(f"   ERROR: Health check failed: HTTP {resp.status_code}")
            print(f"   Response: {resp.text}")
            return False
    except Exception as e:
        print(f"   ERROR: Health check error: {e}")
        return False
    
    # Test 2: Server heartbeat
    print("\nTest 2: Server Heartbeat")
    try:
        url = f"{backend_url}/api/print/heartbeat"
        headers = get_auth_headers(api_token)
        payload = {
            "server_id": "test-connection",
            "server_name": "Test Connection Script",
            "location": "Local Test"
        }
        
        print(f"   📞 Calling: {url}")
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ Heartbeat successful: {data}")
        else:
            print(f"   ❌ Heartbeat failed: HTTP {resp.status_code}")
            print(f"   Response: {resp.text}")
            return False
    except Exception as e:
        print(f"   ❌ Heartbeat error: {e}")
        return False
    
    # Test 3: Server registration
    print("\n📝 Test 3: Server Registration")
    try:
        url = f"{backend_url}/api/print/register-server"
        headers = get_auth_headers(api_token)
        payload = {
            "server_id": "test-connection",
            "name": "Test Connection Script",
            "location": "Local Test Environment",
            "capabilities": {
                "printer_types": ["DYMO"],
                "max_concurrent_jobs": 1
            }
        }
        
        print(f"   📞 Calling: {url}")
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if resp.status_code in [200, 201]:
            data = resp.json()
            print(f"   ✅ Registration successful: {data}")
        else:
            print(f"   ❌ Registration failed: HTTP {resp.status_code}")
            print(f"   Response: {resp.text}")
            return False
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        return False
    
    print("\n🎉 All tests passed! Print server can communicate with backend.")
    print("\n📋 Next Steps:")
    print("   1. Start the print agent: python src/production_print_agent.py")
    print("   2. Create print jobs through the Cell Storage web interface")
    print("   3. Watch the agent process and print the jobs")
    
    return True

if __name__ == "__main__":
    success = test_backend_connection()
    sys.exit(0 if success else 1)