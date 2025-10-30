#!/usr/bin/env python3
"""
Systematic Flask Endpoint Validation Tool
=========================================

This tool systematically validates all Flask endpoint references in templates
against the actual registered routes to prevent BuildError exceptions.
"""

import re
import os
import sys
from pathlib import Path
from collections import defaultdict

def extract_url_for_calls(file_path):
    """Extract all url_for calls from a template file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pattern to match url_for calls: url_for('endpoint.name')
        pattern = r"url_for\(['\"]([^'\"]+)['\"]\)"
        matches = re.findall(pattern, content)

        return matches
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def get_available_routes():
    """Get all available routes from the Flask application."""
    try:
        # Add current directory to Python path
        sys.path.insert(0, '.')

        from app import create_app
        app = create_app()

        routes = {}
        with app.app_context():
            for rule in app.url_map.iter_rules():
                routes[rule.endpoint] = rule.rule

        return routes
    except Exception as e:
        print(f"Error getting routes: {e}")
        return {}

def scan_templates_directory(templates_dir="app/templates"):
    """Scan all template files for url_for calls."""
    template_endpoints = defaultdict(list)

    templates_path = Path(templates_dir)
    if not templates_path.exists():
        print(f"Templates directory not found: {templates_dir}")
        return template_endpoints

    # Find all HTML templates
    for template_file in templates_path.rglob("*.html"):
        endpoints = extract_url_for_calls(template_file)
        if endpoints:
            template_endpoints[str(template_file)] = endpoints

    return template_endpoints

def validate_endpoints():
    """Main validation function."""
    print("Flask Endpoint Validation Tool")
    print("=" * 50)

    # Get available routes
    print("Loading Flask application and extracting routes...")
    available_routes = get_available_routes()

    if not available_routes:
        print("ERROR: Failed to load routes. Check Flask application configuration.")
        return False

    print(f"OK: Found {len(available_routes)} registered routes")

    # Scan templates
    print("\nScanning template files...")
    template_endpoints = scan_templates_directory()

    if not template_endpoints:
        print("ERROR: No template files found.")
        return False

    print(f"OK: Scanned {len(template_endpoints)} template files")

    # Validate endpoints
    print("\nValidating endpoint references...")
    missing_endpoints = []
    valid_count = 0

    for template_file, endpoints in template_endpoints.items():
        for endpoint in endpoints:
            if endpoint in available_routes:
                valid_count += 1
            else:
                missing_endpoints.append((template_file, endpoint))
                print(f"ERROR: Missing endpoint: {endpoint} in {template_file}")

    # Summary
    print(f"\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    print(f"OK: Valid endpoints: {valid_count}")
    print(f"ERROR: Missing endpoints: {len(missing_endpoints)}")

    if missing_endpoints:
        print(f"\nMISSING ENDPOINTS FOUND:")
        print("-" * 30)
        for template_file, endpoint in missing_endpoints:
            # Suggest similar endpoints
            suggestions = find_similar_endpoints(endpoint, available_routes.keys())
            suggestion_text = f" (Suggestions: {', '.join(suggestions)})" if suggestions else ""
            print(f"  • {endpoint} in {template_file}{suggestion_text}")

        print(f"\nRECOMMENDATIONS:")
        print("- Remove unused endpoint references")
        print("- Replace with existing similar endpoints")
        print("- Implement missing endpoint routes if needed")
        return False
    else:
        print("SUCCESS: All endpoint references are valid!")
        return True

def find_similar_endpoints(missing_endpoint, available_endpoints):
    """Find similar endpoint names."""
    # Extract the function name part (after the dot)
    if '.' in missing_endpoint:
        blueprint, function = missing_endpoint.split('.', 1)

        # Look for similar function names in the same blueprint
        similar = []
        for endpoint in available_endpoints:
            if endpoint.startswith(blueprint + '.'):
                endpoint_func = endpoint.split('.', 1)[1]
                if function.lower() in endpoint_func.lower() or endpoint_func.lower() in function.lower():
                    similar.append(endpoint)

        return similar[:3]  # Return top 3 suggestions

    return []

def generate_fix_suggestions():
    """Generate specific fix suggestions for missing endpoints."""
    template_endpoints = scan_templates_directory()
    available_routes = get_available_routes()

    print("\nGENERATING FIX SUGGESTIONS:")
    print("=" * 40)

    # Define endpoint mapping based on functionality
    endpoint_mappings = {
        'backup_database': 'audit_logs',  # Backup functionality -> Admin logs
        'manage_batch_lookup': 'batch_edit_vials',  # Already fixed
        'export_data': 'batch_export_vials',  # Data export -> Batch export
        'system_settings': 'locations_overview',  # Settings -> Locations admin
    }

    for template_file, endpoints in template_endpoints.items():
        for endpoint in endpoints:
            if endpoint not in available_routes:
                suggested_endpoint = endpoint_mappings.get(endpoint.split('.')[-1])
                if suggested_endpoint:
                    full_suggested = f"cell_storage.{suggested_endpoint}"
                    if full_suggested in available_routes:
                        print(f"FIX: Replace '{endpoint}' with '{full_suggested}' in {template_file}")

if __name__ == "__main__":
    print("Starting endpoint validation...\n")

    # Run validation
    is_valid = validate_endpoints()

    # Generate fix suggestions if there are issues
    if not is_valid:
        generate_fix_suggestions()

    sys.exit(0 if is_valid else 1)