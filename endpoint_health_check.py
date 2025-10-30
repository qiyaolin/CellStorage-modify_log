#!/usr/bin/env python3
"""
Endpoint Health Check - Run this script to verify all endpoints are working
"""

import sys
sys.path.append('.')

def check_endpoints():
    try:
        from app import create_app
        app = create_app()

        with app.app_context():
            print("Endpoint Health Check")
            print("=" * 30)

            # Critical endpoints that must exist
            critical_endpoints = [
                'cell_storage.index',
                'cell_storage.cryovial_inventory',
                'cell_storage.locations_overview',
                'cell_storage.backup_database',
                'admin.index',
                'inventory.index'
            ]

            all_routes = {rule.endpoint for rule in app.url_map.iter_rules()}

            for endpoint in critical_endpoints:
                if endpoint in all_routes:
                    print(f"OK: {endpoint}")
                else:
                    print(f"ERROR: {endpoint} missing")

            print(f"\nTotal endpoints registered: {len(all_routes)}")

    except Exception as e:
        print(f"Health check failed: {e}")
        return False

    return True

if __name__ == "__main__":
    check_endpoints()
