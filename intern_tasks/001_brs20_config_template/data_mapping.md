# Data Mapping - BRS20 Config Template

This file documents where each rendered configuration value should come from in NetBox.

The purpose of this file is to prove that every dynamic value in `brs20_template.j2` has a known source of truth.

Do not guess production values. If a value is missing from NetBox, mark it as missing and explain what is needed.

---

## Test Device

| Item | Value |
|---|---|
| Device Name | `FSW-01` |
| Device Type | Hirschmann BRS20 |
| Purpose | Field switch config template test device |
| Environment | NetBox dev/test environment |

---

## Required Data Mapping

| Config Item | NetBox Source | Found in Test Data? | Notes |
|---|---|---:|---|
| Hostname | `device.name` | Yes/No | Used for the switch hostname. |
| Site | `device.site.name` | Yes/No | Used in the generated config header. |
| Device Model | `device.device_type.model` | Yes/No | Used in the generated config header. |
| Device Manufacturer | `device.device_type.manufacturer.name` | Yes/No | Used in the generated config header. |
| Device Role | `device.role.name` | Yes/No | Used in the generated config header. |
| Management IP | `device.primary_ip4.address` or management interface IP | Yes/No | Confirm whether the template should use the device primary IP or an IP assigned to the management interface. |
| Management Interface | Interface named `Management`, `mgmt`, or defined by role/tag/custom field | Yes/No | Confirm how the management interface is identified in NetBox. |
| VLAN ID | `vlan.vid` | Yes/No | Used to render VLAN database entries. |
| VLAN Name | `vlan.name` | Yes/No | Used to render VLAN names. |
| VLAN Description | `vlan.description` | Yes/No | Optional. May be useful for comments. |
| Interface Name | `interface.name` | Yes/No | Used to render each interface section. |
| Interface Description | `interface.description` | Yes/No | Used for interface description/comment. |
| Interface Enabled State | `interface.enabled` | Yes/No | Used to decide whether to render shutdown/disabled comments. |
| Interface Mode | `interface.mode` | Yes/No | Used to determine access vs tagged/trunk behavior. |
| Access/Untagged VLAN | `interface.untagged_vlan` | Yes/No | Used for access port VLAN assignment. |
| Tagged VLANs | `interface.tagged_vlans` | Yes/No | Used for trunk/tagged VLAN assignment. |
| Interface Role/Purpose | Interface tag, custom field, or `local_context_data` | Yes/No | Used later for uplink, ring, management, spare, or field-device role logic. |
| Ring/MRP Role | `device.local_context_data` or interface custom fields | Yes/No | Stretch goal only. Not required for Task 001. |
| NTP Servers | Config context or `local_context_data` | Yes/No | Out of scope for Task 001. |
| DNS Servers | Config context or `local_context_data` | Yes/No | Out of scope for Task 001. |
| Syslog Server | Config context or `local_context_data` | Yes/No | Out of scope for Task 001. |
| SNMP Settings | Config context or `local_context_data` | Yes/No | Out of scope for Task 001. |

---

## Expected VLANs

Confirm these VLANs exist in NetBox and identify where they are assigned.

| VLAN ID | VLAN Name | Expected Use | Found in NetBox? | Notes |
|---:|---|---|---:|---|
| 40 | `pv-pcs` | PCS / inverter field devices | Yes/No | |
| 50 | `tracker` | Tracker devices | Yes/No | |
| 60 | `met-station` | Meteorological station devices | Yes/No | |
| 90 | `pv-field-mgmt` | Field switch / device management | Yes/No | |
| 101 | `mrp-ckt-a` | MRP ring redundancy VLAN | Yes/No | Used for MRP ring protocol traffic. |

---

## Expected Interface Mapping

Confirm these interfaces exist on `FSW-01` and that the VLAN assignments match NetBox.

| Interface | Expected Mode | Expected VLAN(s) | NetBox Source | Found/Correct? | Notes |
|---|---|---|---|---:|---|
| `1/1` | Trunk/Tagged | 40, 50, 60, 90, 101 | `interface.tagged_vlans` | Yes/No | Uplink/ring port. |
| `1/2` | Trunk/Tagged | 40, 50, 60, 90, 101 | `interface.tagged_vlans` | Yes/No | Uplink/ring port. |
| `1/3` | Access/Untagged | 40 `pv-pcs` | `interface.untagged_vlan` | Yes/No | |
| `1/4` | Access/Untagged | 60 `met-station` | `interface.untagged_vlan` | Yes/No | |
| `1/5` | Access/Untagged | 50 `tracker` | `interface.untagged_vlan` | Yes/No | |
| `1/6` | Access/Untagged | 50 `tracker` | `interface.untagged_vlan` | Yes/No | |
| `1/7` | Access/Untagged | 50 `tracker` | `interface.untagged_vlan` | Yes/No | |
| `1/8` | Access/Untagged | 50 `tracker` | `interface.untagged_vlan` | Yes/No | |
| `1/9` | None/Unassigned | Warning comment | Missing VLAN assignment | Yes/No | Template should show a warning. |
| `1/10` | Access/Untagged | 90 `pv-field-mgmt` | `interface.untagged_vlan` | Yes/No | |
| `Management` | Access/Untagged | 90 `pv-field-mgmt` | `interface.untagged_vlan` or management interface IP | Yes/No | Confirm how this should be rendered. |

---

## Dynamic Values Used by Template

List every variable used in `brs20_template.j2`.

| Template Variable | What It Renders | NetBox Source | Required? | Fallback/Warning Behavior |
|---|---|---|---:|---|
| `{{ device.name }}` | Hostname/header device name | `device.name` | Yes | Template should fail or warn if missing. |
| `{{ device.site.name }}` | Site name | `device.site.name` | Yes | Render `NO SITE ASSIGNED` if missing. |
| `{{ device.device_type.model }}` | Device model | `device.device_type.model` | No | Render `UNKNOWN` if missing. |
| `{{ device.role.name }}` | Device role | `device.role.name` | No | Render `UNKNOWN` if missing. |
| `{{ device.primary_ip4.address }}` | Management IP with mask | `device.primary_ip4.address` | No | Render warning if missing. |
| `{{ device.primary_ip4.address.ip }}` | Management IP only | `device.primary_ip4.address.ip` | No | Use with `.netmask` for ip address command. |
| `{{ device.primary_ip4.address.netmask }}` | Management subnet mask | `device.primary_ip4.address.netmask` | No | Used with `.ip` for ip address command. |
| `{{ vlan.vid }}` | VLAN ID | `vlan.vid` | Yes | Skip or warn if missing. |
| `{{ vlan.name }}` | VLAN name | `vlan.name` | Yes | Render `UNNAMED VLAN` if missing. |
| `{{ interface.name }}` | Interface name | `interface.name` | Yes | Template should fail or warn if missing. |
| `{{ interface.description }}` | Interface description | `interface.description` | No | Render `NO DESCRIPTION` if missing. |
| `{{ interface.enabled }}` | Interface admin state | `interface.enabled` | No | Render `shutdown` if false. |
| `{{ interface.mgmt_only }}` | Management interface flag | `interface.mgmt_only` | No | Use to separate mgmt from physical ports. |
| `{{ interface.untagged_vlan.vid }}` | Access VLAN ID | `interface.untagged_vlan.vid` | Conditional | Only render for access/untagged ports. |
| `{{ interface.untagged_vlan.name }}` | Access VLAN name | `interface.untagged_vlan.name` | Conditional | Use in comments. |
| `{{ interface.tagged_vlans.all() }}` | Tagged VLAN list | `interface.tagged_vlans` | Conditional | Only render for trunk/tagged ports. |
| `{{ device.local_context_data }}` | Device config context | `device.local_context_data` | No | Check if exists before accessing. |
| `{{ device.local_context_data.ring_topology_field_ring.protocol }}` | MRP protocol type | `local_context_data` | No | Stretch goal - ring config. |
| `{{ device.local_context_data.ring_topology_field_ring.role }}` | MRP ring role | `local_context_data` | No | Stretch goal - ring config. |
| `{{ device.local_context_data.ring_topology_field_ring.vlan }}` | MRP ring VLAN | `local_context_data` | No | Stretch goal - ring config. |
| `{{ device.local_context_data.ring_topology_field_ring.priority }}` | MRP manager priority | `local_context_data` | No | Stretch goal - ring config. |
| `{{ device.local_context_data.interfaces.physical_map }}` | Interface role mapping | `local_context_data` | No | Stretch goal - maps role to port. |

---

## Questions / Data Gaps Found During Mapping

Use this section while reviewing the test device.

| Topic | Question or Gap | Impact | Proposed Fix |
|---|---|---|---|
| Management IP |  |  |  |
| VLAN Source |  |  |  |
| Management Interface |  |  |  |
| Interface Role |  |  |  |
| Hirschmann Syntax |  |  |  |

---

## Review Notes

Use this section to record findings after comparing the NetBox data to the rendered config.

```text
Reviewer Notes:

- 
- 
- 
```
