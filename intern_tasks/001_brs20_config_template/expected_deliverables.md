# Expected Deliverables - BRS20 Config Template

By the end of this task, submit these files:

```text
intern_tasks/
  001_brs20_config_template/
    brs20_template.j2
    rendered_example.txt
    data_mapping.md
    questions.md
```

---

## 1. `brs20_template.j2`

This is the NetBox/Jinja2 configuration template.

### Required Elements

- [ ] Header with device name, site, model, and role
- [ ] Hostname command
- [ ] Management IP configuration or warning if missing
- [ ] VLAN database section with all required VLANs
- [ ] Management interface configuration
- [ ] Physical interface configurations
- [ ] Access VLAN assignments for access ports
- [ ] Tagged VLAN assignments for trunk ports
- [ ] Warning comments for missing or incomplete data

### Code Quality

- [ ] Uses Jinja2 whitespace control where helpful to avoid blank line spam
- [ ] Rendered output has readable indentation
- [ ] Uses clear section separators/comments
- [ ] Handles missing data gracefully
- [ ] Does not crash if a field is empty
- [ ] Does not hard-code values that should come from NetBox unless clearly marked as a temporary placeholder

---

## 2. `rendered_example.txt`

This is the rendered output from the template using the preloaded `FSW-01` device.

### Required Content

- [ ] Rendered output from the `FSW-01` device
- [ ] No Jinja2 syntax errors
- [ ] No blank line spam
- [ ] All 10 physical interfaces present
- [ ] Management interface present
- [ ] VLANs 40, 50, 60, 90, and 101 defined
- [ ] Trunk ports `1/1` and `1/2` show tagged VLANs
- [ ] Access ports show correct VLAN assignments
- [ ] Unassigned interfaces show a warning comment

### Expected Interface Assignments

| Interface | Mode | VLAN(s) |
|---|---|---|
| 1/1 | Trunk | 40, 50, 60, 90, 101 |
| 1/2 | Trunk | 40, 50, 60, 90, 101 |
| 1/3 | Access | 40, pv-pcs |
| 1/4 | Access | 60, met-station |
| 1/5 | Access | 50, tracker |
| 1/6 | Access | 50, tracker |
| 1/7 | Access | 50, tracker |
| 1/8 | Access | 50, tracker |
| 1/9 | None | Warning comment |
| 1/10 | Access | 90, pv-field-mgmt |
| Management | Access | 90, pv-field-mgmt |

Do not manually clean up the rendered output. If the output looks wrong, fix the template or document the issue in `questions.md`.

---

## 3. `data_mapping.md`

This file explains where every rendered value comes from in NetBox.

Use this format:

| Config Item | NetBox Source | Found in Test Data? | Notes |
|---|---|---:|---|
| Hostname | `device.name` | Yes/No | |
| Site | `device.site.name` | Yes/No | |
| Device model | `device.device_type.model` | Yes/No | |
| Device role | `device.role.name` | Yes/No | |
| Management IP | `device.primary_ip4.address` or management interface IP | Yes/No | |
| VLAN ID | `vlan.vid` | Yes/No | |
| VLAN Name | `vlan.name` | Yes/No | |
| Interface Name | `interface.name` | Yes/No | |
| Interface Description | `interface.description` | Yes/No | |
| Access VLAN | `interface.untagged_vlan` | Yes/No | |
| Tagged VLANs | `interface.tagged_vlans` | Yes/No | |
| Interface Enabled State | `interface.enabled` | Yes/No | |
| Interface Role/Purpose | custom field, tag, or local context data | Yes/No | |

Every dynamic value used in `brs20_template.j2` should have a matching row in this file.

---

## 4. `questions.md`

This file should list anything you are unsure about.

### Required Sections

- [ ] Open questions, at least 3 to 5 items
- [ ] Assumptions made
- [ ] Missing data identified
- [ ] Resources needed
- [ ] Items that need engineer review

### Example Topics to Cover

- Hirschmann HiOS syntax differences
- How to retrieve VLANs from NetBox correctly
- Whether to render all site VLANs or only VLANs used by this switch
- MRP ring configuration requirements
- Management interface handling
- What happens to unassigned interfaces
- Whether interface role/purpose should come from tags, custom fields, or local context data

Use this format:

```markdown
# Questions / Issues

## Question 1
**Topic:** VLAN rendering  
**Question:** Should the template render all site VLANs or only VLANs assigned to this switch?  
**Why it matters:** Rendering all site VLANs may add VLANs that do not belong on this switch.

## Question 2
**Topic:** Management IP  
**Question:** Should the management IP come from `device.primary_ip4` or a specific management interface?  
**Why it matters:** The template needs a consistent source of truth.
```

---

# Acceptance Criteria

This task is complete when:

- [ ] The NetBox dev environment starts successfully
- [ ] The test data imports successfully
- [ ] The `FSW-01` device can be found in NetBox
- [ ] `brs20_template.j2` exists
- [ ] `brs20_template.j2` renders without errors
- [ ] `rendered_example.txt` contains the rendered output
- [ ] `data_mapping.md` explains where the rendered values came from
- [ ] `questions.md` lists open questions and assumptions
- [ ] No production devices are touched
- [ ] No configs are pushed to real equipment

---

# Out of Scope for This Task

Do not work on these yet:

- Production Hirschmann syntax validation
- MRP ring final configuration
- STP/RSTP tuning
- SNMPv3
- NTP
- Syslog
- User accounts
- Passwords
- Firewall rules
- Production deployment
- Automatic config push
- Multiple switch models

---

# Stretch Goals

These are optional bonus items only after the required deliverables are complete.

- [ ] Uses `local_context_data` for ring information
- [ ] Shows interface role mapping from `local_context_data`
- [ ] Includes placeholder MRP configuration
- [ ] Adds warnings for interfaces that are enabled but have no VLAN assignment
- [ ] Adds comments showing where future NTP, SNMP, and syslog settings would come from
