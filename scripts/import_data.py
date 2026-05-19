#!/usr/bin/env python3
"""
NetBox Data Importer

Imports data from YAML/JSON files in /data directory into NetBox via API.
Files are processed in order based on their numeric prefix (01_, 02_, etc.)
to handle dependencies between object types.

Usage:
    docker compose exec netbox python /scripts/import_data.py

Or from host:
    ./import.sh
"""

import json
import os
import sys
import yaml
import requests
from pathlib import Path
from typing import Any

# Configuration
NETBOX_URL = os.getenv('NETBOX_URL', 'http://localhost:8080')
API_TOKEN = os.getenv('API_TOKEN', '0123456789abcdef0123456789abcdef01234567')
DATA_DIR = Path(os.getenv('DATA_DIR', '/data'))

# API endpoint mappings for common NetBox object types
ENDPOINT_MAP = {
    # DCIM
    'regions': '/api/dcim/regions/',
    'site_groups': '/api/dcim/site-groups/',
    'sites': '/api/dcim/sites/',
    'locations': '/api/dcim/locations/',
    'rack_roles': '/api/dcim/rack-roles/',
    'racks': '/api/dcim/racks/',
    'manufacturers': '/api/dcim/manufacturers/',
    'device_types': '/api/dcim/device-types/',
    'device_roles': '/api/dcim/device-roles/',
    'platforms': '/api/dcim/platforms/',
    'devices': '/api/dcim/devices/',
    'interfaces': '/api/dcim/interfaces/',
    'cables': '/api/dcim/cables/',

    # Device Type Components (templates)
    'interface_templates': '/api/dcim/interface-templates/',
    'console_port_templates': '/api/dcim/console-port-templates/',
    'console_server_port_templates': '/api/dcim/console-server-port-templates/',
    'power_port_templates': '/api/dcim/power-port-templates/',
    'power_outlet_templates': '/api/dcim/power-outlet-templates/',
    'rear_port_templates': '/api/dcim/rear-port-templates/',
    'front_port_templates': '/api/dcim/front-port-templates/',
    'module_bay_templates': '/api/dcim/module-bay-templates/',
    'device_bay_templates': '/api/dcim/device-bay-templates/',

    # IPAM
    'rirs': '/api/ipam/rirs/',
    'asns': '/api/ipam/asns/',
    'vrfs': '/api/ipam/vrfs/',
    'route_targets': '/api/ipam/route-targets/',
    'aggregates': '/api/ipam/aggregates/',
    'prefixes': '/api/ipam/prefixes/',
    'ip_ranges': '/api/ipam/ip-ranges/',
    'ip_addresses': '/api/ipam/ip-addresses/',
    'vlans': '/api/ipam/vlans/',
    'vlan_groups': '/api/ipam/vlan-groups/',

    # Virtualization
    'cluster_types': '/api/virtualization/cluster-types/',
    'cluster_groups': '/api/virtualization/cluster-groups/',
    'clusters': '/api/virtualization/clusters/',
    'virtual_machines': '/api/virtualization/virtual-machines/',
    'vm_interfaces': '/api/virtualization/interfaces/',

    # Tenancy
    'tenant_groups': '/api/tenancy/tenant-groups/',
    'tenants': '/api/tenancy/tenants/',
    'contacts': '/api/tenancy/contacts/',
    'contact_groups': '/api/tenancy/contact-groups/',
    'contact_roles': '/api/tenancy/contact-roles/',

    # Circuits
    'providers': '/api/circuits/providers/',
    'provider_networks': '/api/circuits/provider-networks/',
    'circuit_types': '/api/circuits/circuit-types/',
    'circuits': '/api/circuits/circuits/',

    # Extras
    'tags': '/api/extras/tags/',
    'custom_fields': '/api/extras/custom-fields/',
    'custom_links': '/api/extras/custom-links/',
    'webhooks': '/api/extras/webhooks/',
}

# Nested components that need to be extracted and created separately
NESTED_COMPONENTS = {
    'device_types': {
        'interfaces': 'interface_templates',
        'console_ports': 'console_port_templates',
        'console_server_ports': 'console_server_port_templates',
        'power_ports': 'power_port_templates',
        'power_outlets': 'power_outlet_templates',
        'rear_ports': 'rear_port_templates',
        'front_ports': 'front_port_templates',
        'module_bays': 'module_bay_templates',
        'device_bays': 'device_bay_templates',
    }
}


class NetBoxImporter:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        # Cache for looking up created objects
        self._cache = {}

    def get_object_id(self, endpoint: str, filters: dict) -> int | None:
        """Look up an object ID by filters (e.g., slug, name)."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=filters)
            if response.status_code == 200:
                data = response.json()
                if data.get('count', 0) > 0:
                    return data['results'][0]['id']
        except Exception:
            pass
        return None

    def import_objects(self, endpoint: str, objects: list[dict], parent_type: str = None) -> dict:
        """Import a list of objects to a NetBox endpoint."""
        url = f"{self.base_url}{endpoint}"
        results = {'created': 0, 'failed': 0, 'errors': [], 'created_objects': []}

        for obj in objects:
            # Extract nested components before creating the object
            nested_to_create = {}
            if parent_type in NESTED_COMPONENTS:
                for nested_key, template_type in NESTED_COMPONENTS[parent_type].items():
                    if nested_key in obj:
                        nested_to_create[template_type] = obj.pop(nested_key)

            try:
                # Try to create the object
                response = self.session.post(url, json=obj)

                if response.status_code == 201:
                    results['created'] += 1
                    created_obj = response.json()
                    results['created_objects'].append(created_obj)
                    obj_name = obj.get('name', obj.get('slug', obj.get('model', obj.get('address', str(obj)[:50]))))
                    print(f"  ✓ Created: {obj_name}")

                    # Create nested components (like interface templates)
                    for template_type, components in nested_to_create.items():
                        if components:
                            self._create_nested_components(
                                template_type,
                                components,
                                created_obj['id'],
                                parent_type
                            )

                elif response.status_code == 400:
                    error_detail = response.json()
                    # Check if object already exists
                    if any('already exists' in str(v).lower() for v in error_detail.values()):
                        obj_name = obj.get('name', obj.get('slug', obj.get('model', str(obj)[:50])))
                        print(f"  - Skipped (exists): {obj_name}")

                        # Still try to create nested components for existing objects
                        if nested_to_create:
                            existing_id = self._find_existing_object_id(endpoint, obj)
                            if existing_id:
                                for template_type, components in nested_to_create.items():
                                    if components:
                                        self._create_nested_components(
                                            template_type,
                                            components,
                                            existing_id,
                                            parent_type
                                        )
                    else:
                        results['failed'] += 1
                        results['errors'].append({'object': obj, 'error': error_detail})
                        obj_name = obj.get('name', obj.get('model', str(obj)[:50]))
                        print(f"  ✗ Failed: {obj_name} - {error_detail}")
                else:
                    results['failed'] += 1
                    results['errors'].append({'object': obj, 'error': response.text})
                    obj_name = obj.get('name', obj.get('model', str(obj)[:50]))
                    print(f"  ✗ Failed ({response.status_code}): {obj_name}")

            except Exception as e:
                results['failed'] += 1
                results['errors'].append({'object': obj, 'error': str(e)})
                print(f"  ✗ Error: {e}")

        return results

    def _find_existing_object_id(self, endpoint: str, obj: dict) -> int | None:
        """Find the ID of an existing object."""
        # Try different identifying fields
        for field in ['slug', 'name', 'model']:
            if field in obj:
                obj_id = self.get_object_id(endpoint, {field: obj[field]})
                if obj_id:
                    return obj_id
        return None

    def _create_nested_components(self, template_type: str, components: list, parent_id: int, parent_type: str):
        """Create nested component templates (e.g., interface templates for device types)."""
        endpoint = ENDPOINT_MAP.get(template_type)
        if not endpoint:
            print(f"    ⚠ Unknown template type: {template_type}")
            return

        # Determine the parent field name
        parent_field = 'device_type' if parent_type == 'device_types' else parent_type.rstrip('s')

        print(f"    ► Creating {len(components)} {template_type}...")

        url = f"{self.base_url}{endpoint}"
        for component in components:
            # Add parent reference
            component[parent_field] = parent_id

            # Clean up null values that the API doesn't accept
            component = {k: v for k, v in component.items() if v is not None and v != ''}

            try:
                response = self.session.post(url, json=component)
                comp_name = component.get('name', str(component)[:30])

                if response.status_code == 201:
                    print(f"      ✓ {comp_name}")
                elif response.status_code == 400:
                    error = response.json()
                    if any('already exists' in str(v).lower() for v in error.values()):
                        print(f"      - Skipped (exists): {comp_name}")
                    else:
                        print(f"      ✗ {comp_name}: {error}")
                else:
                    print(f"      ✗ {comp_name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"      ✗ {component.get('name', '?')}: {e}")

    def wait_for_netbox(self, timeout: int = 120) -> bool:
        """Wait for NetBox API to become available."""
        import time
        print(f"Waiting for NetBox API at {self.base_url}...")

        start = time.time()
        while time.time() - start < timeout:
            try:
                response = self.session.get(f"{self.base_url}/api/")
                if response.status_code == 200:
                    print("NetBox API is ready!")
                    return True
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(2)

        print("Timeout waiting for NetBox API")
        return False


def load_data_file(filepath: Path) -> dict[str, list]:
    """Load data from a YAML or JSON file."""
    with open(filepath, 'r') as f:
        if filepath.suffix in ('.yml', '.yaml'):
            return yaml.safe_load(f) or {}
        elif filepath.suffix == '.json':
            return json.load(f)
    return {}


def get_data_files(data_dir: Path) -> list[Path]:
    """Get all data files sorted by name (for ordering via numeric prefix)."""
    files = []
    for ext in ('*.yml', '*.yaml', '*.json'):
        files.extend(data_dir.glob(ext))
    return sorted(files, key=lambda p: p.name)


def main():
    print("=" * 60)
    print("NetBox Data Importer")
    print("=" * 60)

    importer = NetBoxImporter(NETBOX_URL, API_TOKEN)

    # Wait for NetBox to be ready
    if not importer.wait_for_netbox():
        sys.exit(1)

    # Find and process data files
    data_files = get_data_files(DATA_DIR)

    if not data_files:
        print(f"\nNo data files found in {DATA_DIR}")
        print("Add YAML or JSON files to the data/ directory")
        print("\nExample file structure:")
        print("  data/")
        print("    01_tenants.yml")
        print("    02_sites.yml")
        print("    03_devices.yml")
        sys.exit(0)

    print(f"\nFound {len(data_files)} data file(s):")
    for f in data_files:
        print(f"  - {f.name}")

    total_created = 0
    total_failed = 0

    for filepath in data_files:
        print(f"\n{'─' * 60}")
        print(f"Processing: {filepath.name}")
        print('─' * 60)

        try:
            data = load_data_file(filepath)
        except Exception as e:
            print(f"Error loading file: {e}")
            continue

        for object_type, objects in data.items():
            if object_type not in ENDPOINT_MAP:
                print(f"\n⚠ Unknown object type: {object_type}")
                print(f"  Available types: {', '.join(sorted(ENDPOINT_MAP.keys()))}")
                continue

            if not objects:
                continue

            endpoint = ENDPOINT_MAP[object_type]
            print(f"\n► Importing {len(objects)} {object_type}...")

            results = importer.import_objects(endpoint, objects, parent_type=object_type)
            total_created += results['created']
            total_failed += results['failed']

    print(f"\n{'=' * 60}")
    print(f"Import Complete: {total_created} created, {total_failed} failed")
    print("=" * 60)


if __name__ == '__main__':
    main()
