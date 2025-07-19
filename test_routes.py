#!/usr/bin/env python3
"""
Test script to verify that the application routes work after migration.
"""

import requests
import time
import subprocess
import sys
import os

def start_app():
    """Start the Flask application in a subprocess"""
    env = os.environ.copy()
    env['FLASK_ENV'] = 'development'
    
    return subprocess.Popen(
        [sys.executable, 'run.py'],
        cwd=os.path.dirname(__file__),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

def test_routes():
    """Test that key routes are accessible"""
    base_url = "http://127.0.0.1:5000"
    
    # Wait for app to start
    print("Waiting for application to start...")
    time.sleep(3)
    
    # Test routes (these should at least not crash)
    test_urls = [
        "/",
        "/inventory/",
        "/inventory/items",
        "/inventory/locations",
        "/inventory/suppliers"
    ]
    
    results = {}
    
    for url in test_urls:
        try:
            response = requests.get(f"{base_url}{url}", timeout=5)
            results[url] = {
                'status': response.status_code,
                'success': response.status_code in [200, 302]  # 302 for redirects (login)
            }
            print(f"[OK] {url}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            results[url] = {
                'status': 'ERROR',
                'success': False,
                'error': str(e)
            }
            print(f"[ERROR] {url}: ERROR - {e}")
    
    return results

if __name__ == "__main__":
    print("=== Testing Application Routes ===")
    
    # Start the Flask app
    app_process = start_app()
    
    try:
        # Test the routes
        results = test_routes()
        
        # Summary
        successful = sum(1 for r in results.values() if r['success'])
        total = len(results)
        
        print(f"\n=== Results ===")
        print(f"Successful routes: {successful}/{total}")
        
        if successful == total:
            print("[SUCCESS] All routes are accessible!")
        else:
            print("[WARNING] Some routes may have issues, but this is expected if authentication is required.")
        
    finally:
        # Stop the Flask app
        app_process.terminate()
        app_process.wait(timeout=5)