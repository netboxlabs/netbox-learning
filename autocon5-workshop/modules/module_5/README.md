# Module 5: Network Modeling Advanced - Config Contexts, Tags & OSPF

## Overview

In Module 4, you learned the fundamentals of intent-based networking using NetBox. You created config templates, configured interfaces and IP addresses, and saw how Jinja2 templates can automatically generate device configurations.

But we left something critical out: **routing configuration**. Without OSPF, our devices can't learn routes to reach each other's networks.

In this module, you'll learn advanced modeling techniques to configure OSPF:
- **Config Contexts** for site-wide settings (OSPF area)
- **Local Config Context Data** for device-specific settings (router IDs)
- **Tags** to mark interfaces with special properties (passive interfaces)

## Learning Objectives

By the end of this module, you will:

- Understand Config Contexts and how they provide structured data to templates
- Use global Config Contexts for site-wide settings (OSPF area)
- Use local Config Context Data for device-specific settings (router IDs)
- Apply Tags to interfaces to mark special characteristics
- Update config templates to consume Config Context data
- Generate complete device configurations including OSPF routing

## Understanding Config Contexts

> [!IMPORTANT]
> **NetBox Concept: Config Contexts**
>
> **Config Contexts** are structured JSON data associated with NetBox objects — devices, sites, roles, tags, and more. When a config template is rendered, the device's merged config context is available alongside its interface and IP data. This lets you store protocol parameters (like OSPF router IDs or BGP AS numbers) in NetBox and inject them into generated configs, keeping all configuration intent in one place.

**Config Contexts** are a powerful way to associate structured data (JSON) with devices, sites, roles, or other NetBox objects. They provide a flexible method to inject configuration data into your templates.

### Types of Config Contexts

**1. Global Config Contexts** (What we'll create now)
- Apply to multiple devices based on criteria (site, role, platform, etc.)
- Great for site-wide or role-wide settings
- Example: All devices in a site share the same OSPF area

**2. Local Config Context Data** (We'll use this for router IDs)
- Stored directly on a device
- Device-specific overrides or unique values
- Example: Each router needs a unique router ID

**How Templates Access Config Context Data:**
```jinja2
{% set context = device.get_config_context() -%}
{{ context.ospf_area }}  {# Accesses the ospf_area value #}
{{ context.router_id }}  {# Accesses the router_id value #}
```

Config Context data is **merged** (global + local), with local data taking precedence over global.

---

### Before You Start: Create a Branch

OSPF configuration is a meaningful change to your source of truth — it deserves its own branch so you can review and merge it independently of the IP addressing work in Module 4.

1. Navigate to **Branching** → **Branches** → **+ Add**
2. **Name**: `module-5-ospf-config`
3. Click **Create**
4. Wait until **Status** shows `Ready` (30–60 seconds, refresh as needed)
5. Use the branch selector at the top of NetBox to activate `module-5-ospf-config`
6. Confirm the branch indicator is visible in the NetBox header before continuing

## Step 1: Define the OSPF Area (Global Config Context)

Since all devices in our workshop are in OSPF Area 0.0.0.0, we'll use a global Config Context to set this site-wide.

### Create the Config Context

1. Navigate to **Provisioning** → **Config Contexts**
2. Click **+ Add** (top right)
3. Enter the following:
   - **Name**: `OSPF Area 0.0.0.0`
   - **Data** section:
   ```json
   {
     "ospf_area": "0.0.0.0"
   }
   ```
4. Under **Assignment** → **Sites**, select `autocon-lab`
5. Click **Create**

**What This Does:**
- Assigns `ospf_area = "0.0.0.0"` to **all devices** in the `autocon-lab` site
- Templates can now access this value via `context.ospf_area`
- If you had multiple sites with different OSPF areas, you'd create multiple Config Contexts

## Step 2: Define OSPF Router IDs (Local Config Context Data)

Each OSPF router needs a unique router ID. Since this is device-specific, we'll use **Local Config Context Data** stored directly on each device.

### Configure srl1

1. Navigate to **Devices** → **Devices**
2. Click the orange pencil icon to edit `srl1`
3. Scroll to **Local Config Context Data** section
4. Enter:
   ```json
   {
     "router_id": "1.1.1.1"
   }
   ```
5. Click **Save**

### Configure srl2

1. Click the orange pencil icon to edit `srl2`
2. Scroll to **Local Config Context Data** section
3. Enter:
   ```json
   {
     "router_id": "2.2.2.2"
   }
   ```
4. Click **Save**

**What This Does:**
- Assigns unique router IDs to each device
- Config Context merges global (`ospf_area`) + local (`router_id`) data
- Templates access both via `device.get_config_context()`

**Why Use Local Config Context?**
Router IDs must be unique per device, so they can't be set globally. This is a perfect use case for local config context data.

### Verify the Merged Context

With both devices configured, navigate to the **Config Context** tab on either device to see how NetBox merges global and local data:

1. Navigate to **Devices** → **Devices** → `srl2`
2. Click the **Config Context** tab

You'll see three panels:

- **Rendered Context** (left) — the final merged result that templates receive:

  ```json
  {
      "ospf_area": "0.0.0.0",
      "router_id": "2.2.2.2"
  }
  ```

- **Local Context** (top right) — the router ID you just set directly on the device:

  ```json
  {
      "router_id": "2.2.2.2"
  }
  ```

- **Source Contexts** (bottom right) — the `OSPF Area 0.0.0.0` global Config Context assigned to the `autocon-lab` site:

  ```json
  {
      "ospf_area": "0.0.0.0"
  }
  ```

> [!NOTE]
> NetBox notes that *"The local config context overwrites all source contexts."* This is how `router_id` (local) and `ospf_area` (global) end up combined in the Rendered Context — and if both sources defined the same key, local would win.

## Step 3: Mark Passive OSPF Interfaces with Tags

Some interfaces should be included in OSPF (so the subnet is advertised) but should **not** form OSPF adjacencies. These are called **passive interfaces**.

In our topology:
- `ethernet-1/2.0` on both routers connects to stub networks (web server, orb agent)
- These interfaces should be passive - advertise the subnet but don't try to form OSPF neighbors

We'll use **NetBox Tags** to mark these interfaces. The config template will check for this tag and configure the interface as passive.

### Create the Tag

1. Navigate to **Customization** → **Tags**
2. Click **+ Add** (top right)
3. Enter:
   - **Name**: `ospf-passive`
   - **Slug**: Hit tab to autocomplete with `ospf-passive`
4. Click **Create**

### Tag Interface on srl1

1. Navigate to **Devices** → **Devices** → `srl1`
2. Select the **Interfaces** tab
3. Find interface `ethernet-1/2.0` and click the orange pencil icon
4. Under **Tags**, add the `ospf-passive` tag
5. Click **Save**

### Tag Interface on srl2

1. Navigate to **Devices** → **Devices** → `srl2`
2. Select the **Interfaces** tab
3. Find interface `ethernet-1/2.0` and click the orange pencil icon
4. Under **Tags**, add the `ospf-passive` tag
5. Click **Save**

**What This Does:**

- Tags act as metadata on interfaces
- Templates can check if an interface has a specific tag
- This approach is flexible - you could have tags for different OSPF areas, interface types, security zones, etc.

**Why Use Tags?**
Tags are lightweight and flexible. They're perfect for marking interfaces with special characteristics without needing to add custom fields or complex data structures.

## Step 4: Update the Config Template for OSPF

Now we need to update our config template to point to the OSPF-capable version. In Gitea, there are two template files:

- `config-templates/srl_linux.j2` — interface and IP configuration only (used in Module 4)
- `config-templates/srl_linux_ospf.j2` — full template including OSPF (used in this module)

We just need to update the config template in NetBox to use the new file — the data source handles the rest.

### Update the Template

1. Navigate to **Provisioning** → **Config Templates**
2. Edit `SR Linux` by clicking the orange pencil icon
3. Change the **Data File** from `config-templates/srl_linux.j2` to `config-templates/srl_linux_ospf.j2`
4. Click **Save**

### Understanding the OSPF Configuration

Let's break down the new OSPF section:

#### 1. Access Config Context Data

```jinja2
{% set context = device.get_config_context() -%}
{% if context.ospf_area and context.router_id -%}
```

- Retrieves the merged config context (global + local)
- Only generates OSPF config if both `ospf_area` and `router_id` are present
- This makes the template safe - it won't break if OSPF data is missing

#### 2. Configure OSPF Instance

```jinja2
set / network-instance {{ network_instance }} protocols ospf instance main admin-state enable
set / network-instance {{ network_instance }} protocols ospf instance main version ospf-v2
set / network-instance {{ network_instance }} protocols ospf instance main router-id {{ context.router_id }}
```

- Enables OSPF instance named "main"
- Sets OSPF version to v2
- Uses `router_id` from local config context (unique per device)

#### 3. Loop Through Interfaces for OSPF

```jinja2
{% for interface in device.interfaces.all() -%}
{% if interface.ip_addresses.all() and not interface.name.startswith('mgmt') and not interface.name.startswith('lo0') -%}
```

- Loops through all interfaces with IP addresses
- Skips management and loopback interfaces
- Only configures OSPF on relevant data plane interfaces

#### 4. Check for Passive Interface Tag

```jinja2
{% set tag_slugs = interface.tags.all() | map(attribute='slug') | list -%}
set / network-instance {{ network_instance }} protocols ospf instance main area {{ context.ospf_area }} interface {{ interface.name }} admin-state enable
set / network-instance {{ network_instance }} protocols ospf instance main area {{ context.ospf_area }} interface {{ interface.name }} interface-type point-to-point
{% if 'ospf-passive' in tag_slugs -%}
set / network-instance {{ network_instance }} protocols ospf instance main area {{ context.ospf_area }} interface {{ interface.name }} passive true
{% endif -%}
```

- Gets all tags on the interface
- Enables the interface in OSPF area (from global config context)
- Sets interface type to point-to-point
- If interface has `ospf-passive` tag, marks it as passive

**Result:** The template now generates complete configurations including OSPF based on Config Contexts and Tags!

## Step 5: Review the Results

Now let's verify that everything is working correctly. We'll check both the Config Context (data) and the Rendered Config (generated commands).

### Verify Config Context for srl1

1. Navigate to **Devices** → **Devices** → `srl1`
2. Click the **Config Context** tab

You should see the **Rendered Context**:

```json
{
    "ospf_area": "0.0.0.0",
    "router_id": "1.1.1.1"
}
```

**Notice:**
- `router_id` comes from **Local Context** (device-specific)
- `ospf_area` comes from **Source Contexts** (global Config Context assigned to the `autocon-lab` site)

### Verify Config Context for srl2

Repeat the same process for srl2 - you should see:

```json
{
    "ospf_area": "0.0.0.0",
    "router_id": "2.2.2.2"
}
```

✅ **Config Context is working!** Both devices have the merged context data.

### Inspect the Rendered Config for srl1

Now for the moment of truth - let's see the complete, production-ready configuration!

1. Navigate to **Devices** → **Devices** → `srl1`
2. Click the **Render Config** tab

You should see the complete device configuration:

```text
# Enter configuration mode
enter candidate

# Configure network instance
set / network-instance default type default

# Configure interfaces
set / interface ethernet-1/1 admin-state enable
set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.0.1/30
set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable

set / interface ethernet-1/2 admin-state enable
set / interface ethernet-1/2 subinterface 0 ipv4 address 192.168.1.1/30
set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable

# Add interfaces to default network instance
set / network-instance default interface ethernet-1/1.0
set / network-instance default interface ethernet-1/2.0

# Configure OSPF
set / network-instance default protocols ospf instance main admin-state enable
set / network-instance default protocols ospf instance main version ospf-v2
set / network-instance default protocols ospf instance main router-id 1.1.1.1

# OSPF area 0.0.0.0
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/1.0 admin-state enable
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/1.0 interface-type point-to-point
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/2.0 admin-state enable
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/2.0 interface-type point-to-point
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/2.0 passive true

# Commit
commit now
```

**Key Observations:**

- ✅ Interfaces configured (from Module 4)
- ✅ OSPF instance with router ID `1.1.1.1`
- ✅ Both interfaces added to OSPF area `0.0.0.0`
- ✅ `ethernet-1/2.0` is marked as **passive** (because of the `ospf-passive` tag!)

### Inspect the Rendered Config for srl2

Repeat for srl2 - you should see similar output but with `router_id 2.2.2.2`.

🎉 **Congratulations!** You now have complete, deployable network configurations generated automatically from NetBox!

## Step 6: Deploy the Complete Configuration with EDA

The rendered configs now include both interfaces and OSPF. Push them to the devices.

1. Navigate to **Customization** → **Scripts** → **Trigger EDA Event**
2. **Event Type**: `Push Device Config`
3. **Branch**: select `module-5-ospf-config`
4. Click **Run Script**

Watch the Ansible output as it applies the full config — interfaces, OSPF instance, router IDs, area membership, and passive interfaces — to both devices from a single trigger.

## Step 7: All Checks Green — Run the Final Validation

This is the moment everything has been building towards. With OSPF deployed, all five checks should pass.

1. Navigate to **Customization** → **Scripts** → **Trigger EDA Event**
2. **Event Type**: `Network Validation Report`
3. **Branch**: select `module-5-ospf-config`
4. Leave **Target Device** blank
5. Click **Run Script**

You should see a fully green validation report for both devices:

```text
[srl1] (172.24.0.101)

  CHECK 0 — Hostname Drift            : PASS — srl1 confirmed on device
  CHECK 1 — Device Reachable          : PASS
  CHECK 2 — LLDP Neighbors (cables)   : PASS — srl2
  CHECK 3 — Interface IPs             : PASS — 10.0.0.1/30, 192.168.1.1/30
  CHECK 4 — OSPF Neighbors            : PASS — 1/1 neighbors FULL
  CHECK 5 — Web Server Route          : PASS — 192.168.2.0/30 via 10.0.0.2

[srl2] (172.24.0.102)

  CHECK 0 — Hostname Drift            : PASS — srl2 confirmed on device
  CHECK 1 — Device Reachable          : PASS
  CHECK 2 — LLDP Neighbors (cables)   : PASS — srl1
  CHECK 3 — Interface IPs             : PASS — 10.0.0.2/30, 192.168.2.1/30
  CHECK 4 — OSPF Neighbors            : PASS — 1/1 neighbors FULL
  CHECK 5 — Web Server Route          : PASS — 192.168.2.0/30 via 192.168.2.1
```

> [!NOTE]
> **This is what intent-based networking looks like end-to-end.** You designed the network in NetBox, templates rendered the config, EDA deployed it, and the validator — using NetBox itself as the source of truth — confirmed that reality matches intent. Every PASS is backed by a specific NetBox record.

### Optional: Deep-Dive OSPF Verification

The validation report confirms OSPF is up — but if you want to see the raw neighbor state and learned routes directly from the devices, there's a dedicated OSPF verification playbook that gives you that detail.

You can view the playbook source in Gitea — navigate to **admin / ansible-playbooks** → `verify_ospf.yml`.

To run it:

1. Navigate to **Customization** → **Scripts** → **Trigger EDA Event**
2. **Event Type**: `Verify OSPF`
3. Leave **Target Device** blank (runs against both devices)
4. Click **Run Script**

Expected output:

```text
=== OSPF Verification Report ===

[srl1] (172.24.0.101)
  OSPF Neighbors:
    • 2.2.2.2  interface ethernet-1/1.0  state FULL
  OSPF Routes:
    • 192.168.2.0/30  via 10.0.0.2  metric 20

[srl2] (172.24.0.102)
  OSPF Neighbors:
    • 1.1.1.1  interface ethernet-1/1.0  state FULL
  OSPF Routes:
    • 192.168.1.0/30  via 10.0.0.1  metric 20
```

Each neighbor at `FULL` state confirms a stable OSPF adjacency. The routes show that each router has learned the other's stub network via OSPF — exactly what enables the web server to be reachable from the orb agent.

## Step 8: Merge the Branch

The network is working and the validation report confirms it. Merge the branch to promote the OSPF configuration to main.

1. Navigate to **Branching** → **Branches** → `module-5-ospf-config`
2. Click **Merge** → check **Commit Changes** → **Merge Branch**

> [!NOTE]
> You may see **1 conflict** on the `SR Linux` config template. This is expected — the branch updated the template to use `srl_linux_ospf.j2`, while main recorded a data sync timestamp change on the same object. The branch version is correct. **Tick the checkbox** next to the conflict row to confirm it, then proceed with the merge.

Main now reflects exactly what's running on the network.

## Key Takeaways

### What You Accomplished

In Modules 4 and 5, you've built a complete intent-based network configuration system:

**Module 4 (Basics):**

- ✅ Created NetBox branches for safe changes
- ✅ Built config templates with Jinja2
- ✅ Configured interfaces and IP addresses
- ✅ Generated basic interface configurations

**Module 5 (Advanced):**

- ✅ Used global Config Contexts for site-wide settings (OSPF area)
- ✅ Used local Config Context Data for device-specific settings (router IDs)
- ✅ Applied Tags to mark interface characteristics (passive interfaces)
- ✅ Updated templates to generate complete OSPF configurations

## Other Playbooks to Explore

The `ansible-playbooks` repo in Gitea contains several other playbooks beyond what the workshop uses directly. They're there as working examples you can read, adapt, or run:

```bash
echo "$GITEA_URL/admin/ansible-playbooks"
```

| Playbook | Event Type | What it does |
|---|---|---|
| `verify_reachability.yml` | `Verify Reachability` | Ping-based reachability check between devices |
| `health_check.yml` | `device.health_check` | Interface error counters and CPU/memory on each device |
| `connectivity_test.yml` | `device.connectivity_test` | End-to-end connectivity test across the topology |
| `compliance_check.yml` | `device.compliance_check` | Checks device config against a baseline policy |
| `network_audit.yml` | `device.audit` | Full inventory snapshot — interfaces, IPs, neighbors |

All of these are already wired into the EDA rulebook, so they can be triggered the same way as the playbooks you've used in the workshop.

## What's Next?

You've modeled intent in NetBox, deployed it with EDA, and validated it — all six checks are green. The network matches the source of truth.

In **Module 6**, you'll close the remaining loop: simulate a rogue change that breaks the network, use NetBox Discovery to detect the drift, and self-heal by re-deploying intent from main.

---

**Continue to:** [Module 6 - Network Validation & Drift Detection](../module_6/README.md)
