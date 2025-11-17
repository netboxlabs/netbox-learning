# Module 4b: Network Modeling Advanced - Config Contexts, Tags & OSPF

## Overview

In Module 4a, you learned the fundamentals of intent-based networking using NetBox. You created config templates, configured interfaces and IP addresses, and saw how Jinja2 templates can automatically generate device configurations.

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

### Step 0: Activate the Branch

We should still be in our branch from module 4a (`Module 4 SRL Config`). If not, activate the branch:

1. Using the branch selector (top right), select `Module 4 SRL Config` from the dropdown list
2. This ensures all changes you make are applied to the branch, not main

You should now see an indicator showing your active branch at the top of the NetBox interface.

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
4. Under **Assignment** → **Sites**, select `Workshop`
5. Click **Create**

**What This Does:**
- Assigns `ospf_area = "0.0.0.0"` to **all devices** in the Workshop site
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

Now we need to update our config template to consume the Config Context data and Tags we just created. We'll add OSPF configuration logic to the template.

### Update the Template

1. Navigate to **Provisioning** → **Config Templates**
2. Edit `SR Linux` by clicking the orange pencil icon
3. **Replace** the entire template code with the version below
4. Click **Save**

```yaml
# Enter configuration mode
enter candidate

# Configure network instance
{% set vrf = device.primary_ip.vrf if device.primary_ip and device.primary_ip.vrf else none -%}
{% set network_instance = vrf.name if vrf else "default" -%}
set / network-instance {{ network_instance }} type default

# Configure interfaces
{% for interface in device.interfaces.all() -%}
{% if interface.ip_addresses.all() and not interface.name.startswith('mgmt') -%}
{% set parent_name = interface.parent.name if interface.parent else interface.name.split('.')[0] -%}
{% for ip in interface.ip_addresses.all() -%}
set / interface {{ parent_name }} admin-state enable
set / interface {{ parent_name }} subinterface 0 ipv4 address {{ ip.address }}
set / interface {{ parent_name }} subinterface 0 ipv4 admin-state enable

{% endfor -%}
{% endif -%}
{% endfor -%}

# Add interfaces to {{ network_instance }} network instance
{% for interface in device.interfaces.all() -%}
{% if interface.ip_addresses.all() and not interface.name.startswith('mgmt') -%}
{% set subif_name = interface.name if '.' in interface.name else interface.name + '.0' -%}
set / network-instance {{ network_instance }} interface {{ subif_name }}
{% endif -%}
{% endfor -%}

# Configure OSPF
{% set context = device.get_config_context() -%}
{% if context.ospf_area and context.router_id -%}
set / network-instance {{ network_instance }} protocols ospf instance main admin-state enable
set / network-instance {{ network_instance }} protocols ospf instance main version ospf-v2
set / network-instance {{ network_instance }} protocols ospf instance main router-id {{ context.router_id }}

# OSPF area {{ context.ospf_area }}
{% for interface in device.interfaces.all() -%}
{% if interface.ip_addresses.all() and not interface.name.startswith('mgmt') and not interface.name.startswith('lo0') -%}
{% set tag_slugs = interface.tags.all() | map(attribute='slug') | list -%}
set / network-instance {{ network_instance }} protocols ospf instance main area {{ context.ospf_area }} interface {{ interface.name }} admin-state enable
set / network-instance {{ network_instance }} protocols ospf instance main area {{ context.ospf_area }} interface {{ interface.name }} interface-type point-to-point
{% if 'ospf-passive' in tag_slugs -%}
set / network-instance {{ network_instance }} protocols ospf instance main area {{ context.ospf_area }} interface {{ interface.name }} passive true
{% endif -%}
{% endif -%}
{% endfor -%}
{% endif -%}

# Commit
commit now
```

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
- `ospf_area` comes from **Source Contexts** (global Config Context assigned to the Workshop site)

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

```yaml
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
- ✅ Interfaces configured (from Module 4a)
- ✅ OSPF instance with router ID `1.1.1.1`
- ✅ Both interfaces added to OSPF area `0.0.0.0`
- ✅ `ethernet-1/2.0` is marked as **passive** (because of the `ospf-passive` tag!)

### Inspect the Rendered Config for srl2

Repeat for srl2 - you should see similar output but with `router_id 2.2.2.2`.

🎉 **Congratulations!** You now have complete, deployable network configurations generated automatically from NetBox!

## Key Takeaways

### What You Accomplished

In Modules 4a and 4b, you've built a complete intent-based network configuration system:

**Module 4a (Basics):**
- ✅ Created NetBox branches for safe changes
- ✅ Built config templates with Jinja2
- ✅ Configured interfaces and IP addresses
- ✅ Generated basic interface configurations

**Module 4b (Advanced):**
- ✅ Used global Config Contexts for site-wide settings (OSPF area)
- ✅ Used local Config Context Data for device-specific settings (router IDs)
- ✅ Applied Tags to mark interface characteristics (passive interfaces)
- ✅ Updated templates to generate complete OSPF configurations

## What's Next?

You've modeled your network intent in NetBox. You've generated complete, production-ready configurations. But they're still just sitting in NetBox - they haven't been deployed to the actual devices yet.

In **Module 5**, you'll use **Ansible** to:
- Query the NetBox API for rendered configurations
- Connect to devices via SSH
- Deploy configurations automatically
- Verify the deployment succeeded

This closes the loop: Intent → Configuration → Deployment. Let's automate it!

---

**Continue to:** [Module 5 - Configuring the Network Through Automation](../module_5/README.md)