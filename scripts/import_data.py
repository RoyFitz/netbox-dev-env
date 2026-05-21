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

def get_auth_header(token: str) -> dict:
    """Return appropriate Authorization header based on token format.

    v2 tokens start with 'nbt_' and use Bearer auth.
    v1 tokens use Token auth (deprecated in NetBox 4.6+).
    """
    if token.startswith('nbt_'):
        return {'Authorization': f'Bearer {token}'}
    else:
        return {'Authorization': f'Token {token}'}

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

    # Special update operations
    'interface_updates': '/api/dcim/interfaces/',
    'device_updates': '/api/dcim/devices/',
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
            **get_auth_header(token),
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

    def update_interfaces(self, interface_configs: list[dict]) -> dict:
        """Update existing device interfaces with VLAN assignments."""
        results = {'updated': 0, 'failed': 0, 'errors': []}

        for config in interface_configs:
            device_ref = config.get('device', {})
            device_name = device_ref.get('name')
            iface_name = config.get('name')

            if not device_name or not iface_name:
                print(f"  ✗ Missing device or interface name")
                results['failed'] += 1
                continue

            # Look up the interface
            iface_id = self._find_interface(device_name, iface_name)
            if not iface_id:
                print(f"  ✗ Interface not found: {device_name} / {iface_name}")
                results['failed'] += 1
                continue

            # Build the update payload
            payload = {}

            if 'mode' in config:
                payload['mode'] = config['mode']

            # Resolve tagged VLANs to IDs
            if 'tagged_vlans' in config:
                vlan_ids = []
                for vlan_ref in config['tagged_vlans']:
                    vlan_id = self._find_vlan(vlan_ref.get('vid'))
                    if vlan_id:
                        vlan_ids.append(vlan_id)
                payload['tagged_vlans'] = vlan_ids

            # Resolve untagged VLAN to ID
            if 'untagged_vlan' in config:
                vlan_id = self._find_vlan(config['untagged_vlan'].get('vid'))
                if vlan_id:
                    payload['untagged_vlan'] = vlan_id

            # PATCH the interface
            try:
                url = f"{self.base_url}/api/dcim/interfaces/{iface_id}/"
                response = self.session.patch(url, json=payload)

                if response.status_code == 200:
                    results['updated'] += 1
                    print(f"  ✓ Updated: {device_name} / {iface_name}")
                else:
                    results['failed'] += 1
                    error = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                    results['errors'].append({'interface': f"{device_name}/{iface_name}", 'error': error})
                    print(f"  ✗ Failed: {device_name} / {iface_name} - {error}")
            except Exception as e:
                results['failed'] += 1
                print(f"  ✗ Error: {device_name} / {iface_name} - {e}")

        return results

    def _find_interface(self, device_name: str, iface_name: str) -> int | None:
        """Find interface ID by device name and interface name."""
        url = f"{self.base_url}/api/dcim/interfaces/"
        try:
            response = self.session.get(url, params={'device': device_name, 'name': iface_name})
            if response.status_code == 200:
                data = response.json()
                if data.get('count', 0) > 0:
                    return data['results'][0]['id']
        except Exception:
            pass
        return None

    def _find_vlan(self, vid: int) -> int | None:
        """Find VLAN ID by VID."""
        url = f"{self.base_url}/api/ipam/vlans/"
        try:
            response = self.session.get(url, params={'vid': vid})
            if response.status_code == 200:
                data = response.json()
                if data.get('count', 0) > 0:
                    return data['results'][0]['id']
        except Exception:
            pass
        return None

    def _find_device(self, name: str) -> int | None:
        """Find device ID by name."""
        url = f"{self.base_url}/api/dcim/devices/"
        try:
            response = self.session.get(url, params={'name': name})
            if response.status_code == 200:
                data = response.json()
                if data.get('count', 0) > 0:
                    return data['results'][0]['id']
        except Exception:
            pass
        return None

    def _find_ip_address(self, address: str) -> int | None:
        """Find IP address ID by address."""
        url = f"{self.base_url}/api/ipam/ip-addresses/"
        try:
            response = self.session.get(url, params={'address': address})
            if response.status_code == 200:
                data = response.json()
                if data.get('count', 0) > 0:
                    return data['results'][0]['id']
        except Exception:
            pass
        return None

    def preprocess_ip_addresses(self, ip_list: list[dict]) -> list[dict]:
        """Resolve interface references in IP address objects."""
        processed = []
        for ip in ip_list:
            ip_copy = ip.copy()

            # Handle assigned_object reference
            if 'assigned_object' in ip_copy and 'assigned_object_type' in ip_copy:
                obj_type = ip_copy.pop('assigned_object_type')
                obj_ref = ip_copy.pop('assigned_object')

                if obj_type == 'dcim.interface':
                    device_name = obj_ref.get('device', {}).get('name')
                    iface_name = obj_ref.get('name')
                    if device_name and iface_name:
                        iface_id = self._find_interface(device_name, iface_name)
                        if iface_id:
                            ip_copy['assigned_object_type'] = 'dcim.interface'
                            ip_copy['assigned_object_id'] = iface_id
                        else:
                            print(f"  ⚠ Interface not found: {device_name}/{iface_name}")

            processed.append(ip_copy)
        return processed

    def update_devices(self, device_configs: list[dict]) -> dict:
        """Update existing devices (e.g., set primary IP)."""
        results = {'updated': 0, 'failed': 0, 'errors': []}

        for config in device_configs:
            device_name = config.get('name')
            if not device_name:
                print(f"  ✗ Missing device name")
                results['failed'] += 1
                continue

            device_id = self._find_device(device_name)
            if not device_id:
                print(f"  ✗ Device not found: {device_name}")
                results['failed'] += 1
                continue

            payload = {}

            # Handle primary_ip4 reference
            if 'primary_ip4' in config:
                ip_ref = config['primary_ip4']
                if isinstance(ip_ref, dict) and 'address' in ip_ref:
                    ip_id = self._find_ip_address(ip_ref['address'])
                    if ip_id:
                        payload['primary_ip4'] = ip_id
                    else:
                        print(f"  ⚠ IP not found: {ip_ref['address']}")

            # Handle primary_ip6 reference
            if 'primary_ip6' in config:
                ip_ref = config['primary_ip6']
                if isinstance(ip_ref, dict) and 'address' in ip_ref:
                    ip_id = self._find_ip_address(ip_ref['address'])
                    if ip_id:
                        payload['primary_ip6'] = ip_id

            if not payload:
                print(f"  - Skipped (nothing to update): {device_name}")
                continue

            try:
                url = f"{self.base_url}/api/dcim/devices/{device_id}/"
                response = self.session.patch(url, json=payload)

                if response.status_code == 200:
                    results['updated'] += 1
                    print(f"  ✓ Updated: {device_name}")
                else:
                    results['failed'] += 1
                    error = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                    print(f"  ✗ Failed: {device_name} - {error}")
            except Exception as e:
                results['failed'] += 1
                print(f"  ✗ Error: {device_name} - {e}")

        return results

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

            # Handle interface updates specially (PATCH instead of POST)
            if object_type == 'interface_updates':
                print(f"\n► Updating {len(objects)} interfaces...")
                results = importer.update_interfaces(objects)
                total_created += results['updated']
                total_failed += results['failed']
                continue

            # Handle device updates specially (PATCH instead of POST)
            if object_type == 'device_updates':
                print(f"\n► Updating {len(objects)} devices...")
                results = importer.update_devices(objects)
                total_created += results['updated']
                total_failed += results['failed']
                continue

            # Preprocess IP addresses to resolve interface references
            if object_type == 'ip_addresses':
                objects = importer.preprocess_ip_addresses(objects)

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
