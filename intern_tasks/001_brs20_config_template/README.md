# Task 001 - BRS20 NetBox Config Template

## Goal

Create a first-pass NetBox config template for the preloaded Hirschmann BRS20 field switch in this development environment.

The template should use NetBox data to render a readable draft switch configuration.

This is not expected to be production-ready yet. The goal is to learn how NetBox device, VLAN, IP, and interface data can become a generated config.

---

## What You Need To Do

1. Start the NetBox dev environment.
2. Import the test data.
3. Log into NetBox.
4. Find the preloaded field switch device (`FSW-01`).
5. Review its:
   - device name
   - site
   - interfaces
   - assigned IP address
   - VLANs
   - tagged and untagged VLAN assignments
6. Fill out `data_mapping.md` as you verify each data source.
7. Create a NetBox config template for the switch.
   - Go to **Provisioning > Config Templates** in NetBox
   - Click **Add** to create a new template
   - Use Jinja2 syntax with the device context
8. Assign the template to the device.
   - Go to **Devices > Devices** and click on `FSW-01`
   - Click **Edit** and set the **Config Template** field to your template
   - Save the device
9. Render the template against the test switch.
   - On the device page, click the **Render Config** tab
10. Save the rendered output to `rendered_example.txt`.
11. Document questions and assumptions in `questions.md`.

---

## Minimum Template Requirements

The first version of the template must render:

- Device name / hostname
- Site name
- Device model and role
- Primary management IP, if assigned
- VLAN list (discovered from interface assignments)
- Interface list (management and physical separated)
- Interface descriptions
- Interface mode (access or trunk)
- Access VLANs
- Tagged VLANs
- Clear comments when data is missing

---

## Template Hints

- Use Jinja2 whitespace control (`{%-` and `-%}`) to prevent blank lines in output
- VLANs should be collected from interface assignments, not queried directly from site
- Management interfaces (`mgmt_only=true`) should be handled separately from switchports
- The device `local_context_data` contains useful info (ring config, interface roles)

---

## Do Not Do Yet

Do not worry about:

- Spanning tree tuning
- SNMPv3
- NTP
- Syslog
- User accounts
- Passwords
- Production deployment
- Pushing configs to switches
- Perfect Hirschmann syntax

For this task, readable and logically correct is more important than production syntax.

---

## Stretch Goals (Optional)

If time permits:

- Use `local_context_data` to render MRP ring configuration
- Map interface roles (ring_up, ring_down) from local_context_data
- Add generation timestamp to output

---

## Deliverables

When finished, provide:

1. `brs20_template.j2` - The Jinja2 config template
2. `rendered_example.txt` - Output from rendering the template against FSW-01
3. `data_mapping.md` - Completed data mapping worksheet (fill in Yes/No columns)
4. `questions.md` - Questions, assumptions, and missing data notes

The `questions.md` file should list:
- Open questions (syntax, data model, requirements)
- Assumptions made during development
- Missing data in NetBox that would be needed for production
- Resources needed (documentation, examples)

See `expected_deliverables.md` for the evaluation checklist.

---

## Resources

- [How to Generate Device Configurations with NetBox](https://netboxlabs.com/blog/how-to-generate-device-configurations-with-netbox/) - NetBox Labs guide on config templates
- `example_output.txt` - Sample output to work towards