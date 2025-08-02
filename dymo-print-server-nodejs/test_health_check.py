#!/usr/bin/env python3
"""
Test the health check functionality
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from production_print_agent import ProductionPrintAgent

def test_health_check():
    """Test the health check function"""
    print("Testing health check...")
    
    agent = ProductionPrintAgent()
    status = agent.health_check()
    
    print(f"Health check result: {status}")
    
    if status['backend_api']:
        print("✓ Backend API connection: OK")
    else:
        print("✗ Backend API connection: FAILED")
    
    if status['template_file']:
        print("✓ Template file: OK")
    else:
        print("✗ Template file: MISSING")
    
    if status['dymo_framework']:
        print("✓ DYMO framework: OK")
    else:
        print("✗ DYMO framework: MISSING")
    
    all_ok = all([status['backend_api'], status['template_file'], status['dymo_framework']])
    print(f"\nOverall status: {'PASS' if all_ok else 'FAIL'}")
    
    return all_ok

if __name__ == "__main__":
    success = test_health_check()
    sys.exit(0 if success else 1)