# Module 4a: Network Modeling Basics - Config Templates & Device Configuration

## Overview

In Module 1, we experienced the pain of manually configuring devices one by one. As your team grows and more people make changes, this problem compounds. When you SSH into a device, you never know exactly what you'll find—that simple 1-hour change window can turn into a research project, forcing you to postpone planned work.

The traditional approach of "change first, document later" is fundamentally broken. After a busy change window or a late-night troubleshooting session, documentation is the last thing engineers want to deal with. The result? Outdated documentation that can't be trusted.

**Intent-based networking flips this model**: Update NetBox first, then deploy. This approach provides:

- **Clear visibility**: Everyone sees what changes are planned before they happen
- **Accurate documentation**: Documentation is created before implementation, not after
- **Automation-ready**: As you'll see in Module 5, defining intent in NetBox enables automated deployment
- **Better collaboration**: Teams can review and discuss changes before they hit production

In this module, you'll learn the fundamentals of modeling network intent in NetBox using config templates and basic device attributes.

## Learning Objectives

By the end of this module, you will:

- Understand the concept of intent-based networking and NetBox as a source of truth
- Learn about workflows and modeling approaches in NetBox
- Create and use NetBox branches for safe change management
- Build config templates using Jinja2 to generate device configurations
- Configure devices with interfaces and IP addresses in NetBox
- Inspect rendered configurations before deployment

> [!NOTE]
> Because we're only configuring a couple of devices in the workshop, sections 4a and 4b step can appear like a lot of overhead. With only two devices in our network, this _is_ a lot of overhead, but in a normal network the ROI on these steps is _much_ greater.  

## Key Concepts: Workflows and Modeling

When using NetBox to drive automation, you need to consider two audiences:
1. **People** using NetBox to manage the network
2. **Automation systems** consuming NetBox data

This requires thinking about both **workflows** (how to generate configs) and **modeling** (what data to capture).

### Workflows: Two Approaches to Configuration Generation

**1. Config Templates and Rendered Configs** ✅ (We'll use this today)

NetBox Config Templates are Jinja2 templates that:
- Associate with devices or device groups
- Are rendered on demand by NetBox to show the latest configuration
- Can be viewed in the GUI or queried via API
- Inspect the NetBox data model to generate output

**Best for:** Teams starting with automation, or those with relatively homogeneous networks. Many organizations scale this approach successfully.

**2. NetBox API + Downstream Rendering**

Use NetBox's REST or GraphQL APIs to:
- Query the current state of any object (on main or in branches)
- Pass data to external tools for config generation

Example: Many teams use the [Certified NetBox Ansible Collection](https://docs.ansible.com/projects/ansible/latest/collections/netbox/netbox/nb_inventory_inventory.html) to extract inventory from NetBox and generate configurations via Ansible playbooks.

**Best for:** Teams with heterogeneous networks, complex requirements, or existing external config generation systems.

### Modeling: Capturing the Right Data

"Modeling" in this context means: *How do we capture sufficiently detailed data in NetBox for the needs of day-to-day users while enabling downstream automation to generate valid configurations?*

### Modeling Tools Available in NetBox

**Built-in NetBox Models and Attributes**
- Devices, interfaces, IP addresses, cables, VLANs, prefixes
- Rich data model suitable to model most networks

**Config Contexts**
- Associate structured metadata to objects
- Can be local (per device), scoped (set of devices) or global (all devices)

**Tags**
- Associate simple metadata to objects
- Lightweight and flexible

**Custom Fields**
- Add fields to extend the attributes of existing models
- Example: "Maintenance window" or "Change control number"

**Custom Objects**
- Define entirely new models in NetBox
- For complex scenarios like detailed L3 modeling or application servers

> [!NOTE]
> **For this workshop**, we'll use:
> - Module 4a: Built-in models (devices, interfaces, IPs) + Config Templates
> - Module 4b: Config Contexts + Tags (for OSPF configuration)

## Creating a Branch for Safe Changes

Just like Git workflows for code, NetBox supports branching for network changes. This provides:

- **Safety**: A "get out of jail free card" if you make mistakes—just delete the branch
- **Isolation**: Other users and API consumers see the current production state (main branch)
- **Review**: Changes can be reviewed before merging to production
- **Atomic deployment**: All changes are deployed together in Module 5

### Step 1: Create a New Branch

> [!TIP]
> **NetBox Access**
> - URL: `echo "http://$MY_EXTERNAL_IP:8000"`
> - Username: `admin`
> - Password: `admin`

1. Navigate to **Branching** → **Branches**
2. Click **+ Add** in the top right
3. Name your branch: `Module 4 SRL Config`
4. Click **Save**

> [!NOTE]
> You may need to refresh the page a couple of times until your branch status shows as **Ready**.

### Step 2: Activate the Branch

1. Once the branch status is **Ready**, click the **Activate** button
2. This ensures all changes you make are applied to the branch, not main

You should now see an indicator showing your active branch at the top of the NetBox interface.

**Why This Matters:**
- Main branch = current production state
- Your branch = proposed changes
- Automation (Module 5) will deploy from your branch, then merge to main

## Creating a Config Template

NetBox Config Templates use Jinja2 templating to generate device configurations. They:

- Are applied to NetBox devices
- Access NetBox data during rendering (interfaces, IPs, etc.)
- Can be viewed in GUI or queried via API (we'll use the API in Module 5)
- Support logic, loops, and conditionals

### Step 1: Create the Template

1. Navigate to **Provisioning** → **Config Templates**
2. Click **+ Add** (top right)
3. Give it the name: `SR Linux`
4. Paste the template code below into **Template Code**
5. Click **Create**

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

# Commit
commit now
```

### Understanding the Template

Let's break down what this Jinja2 template does:

#### 1. Determine Network Instance (VRF)

```jinja2
{% set vrf = device.primary_ip.vrf if device.primary_ip and device.primary_ip.vrf else none -%}
{% set network_instance = vrf.name if vrf else "default" -%}
```

- Checks if the device has a VRF assigned to its primary IP
- If yes, uses the VRF name; otherwise uses "default"
- This makes the template flexible for both VRF and non-VRF scenarios

#### 2. Create the Network Instance

```jinja2
set / network-instance {{ network_instance }} type default
```

- Generates a command to create the network instance (VRF)
- Example output: `set / network-instance default type default`

#### 3. Loop Through Interfaces

```jinja2
{% for interface in device.interfaces.all() -%}
{% if interface.ip_addresses.all() and not interface.name.startswith('mgmt') -%}
```

- Iterates through all interfaces on the device
- Only processes interfaces that have IP addresses AND aren't management interfaces
- This automatically skips unconfigured or management interfaces

#### 4. Configure Each Interface

```jinja2
{% set parent_name = interface.parent.name if interface.parent else interface.name.split('.')[0] -%}
{% for ip in interface.ip_addresses.all() -%}
set / interface {{ parent_name }} admin-state enable
set / interface {{ parent_name }} subinterface 0 ipv4 address {{ ip.address }}
set / interface {{ parent_name }} subinterface 0 ipv4 admin-state enable
```

- Gets the parent interface name (e.g., `ethernet-1/1` from `ethernet-1/1.0`)
- Loops through all IPs on that interface
- Generates commands to:
  - Enable the parent interface
  - Assign the IP address to subinterface 0
  - Enable IPv4 on the subinterface

#### 5. Associate Interfaces with Network Instance

```jinja2
{% for interface in device.interfaces.all() -%}
{% if interface.ip_addresses.all() and not interface.name.startswith('mgmt') -%}
{% set subif_name = interface.name if '.' in interface.name else interface.name + '.0' -%}
set / network-instance {{ network_instance }} interface {{ subif_name }}
```

- Loops through interfaces again
- Formats the subinterface name correctly (adds `.0` if needed)
- Associates each subinterface with the network instance

**Result:** The template generates complete interface configurations based solely on NetBox data (interfaces and IP addresses).

> [!NOTE]
> This template focuses on basic interface configuration. In Module 4b, we'll extend it to include OSPF routing configuration using more advanced modeling techniques.

## Configuring Device: srl1

Now let's populate NetBox with the data needed to render srl1's configuration. We'll:
1. Associate the config template with the device
2. Add child interfaces (subinterfaces)
3. Assign IP addresses to interfaces

### Step 1: Associate the Config Template

1. Navigate to **Devices** → **Devices** and click on `srl1`
2. Click **Edit**
3. Scroll down to **Config Template** and select `SR Linux` from the dropdown
4. Click **Save**

### Step 2: Configure ethernet-1/1 (Transit Link to srl2)

On the **Interfaces** tab for `srl1`:

**Create Child Interface:**
1. Use **Quick Search** to find `ethernet-1/1`
2. Click the green **+** button and select **Child Interface**
3. Give it the name: `ethernet-1/1.0`
4. Click **Create**

**Assign IP Address:**
1. Use **Quick Search** to find `ethernet-1/1.0`
2. Click the green **+** button and select **IP Address**
3. Enter address: `10.0.0.1/30`
4. Click **Create**

### Step 3: Configure ethernet-1/2 (Stub Network)

Still on the **Interfaces** tab for `srl1`:

**Create Child Interface:**
1. Use **Quick Search** to find `ethernet-1/2`
2. Click the green **+** button and select **Child Interface**
3. Give it the name: `ethernet-1/2.0`
4. Click **Create**

**Assign IP Address:**
1. Use **Quick Search** to find `ethernet-1/2.0`
2. Click the green **+** button and select **IP Address**
3. Enter address: `192.168.1.1/30`
4. Click **Create**

### Step 4: Inspect the Rendered Configuration

Now that you've added the necessary interface data, let's see the magic happen—NetBox automatically renders the configuration!

1. Navigate to **Devices** → **Devices** → `srl1`
2. Click the **Render Config** tab

You should see the generated configuration:

```yaml
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
```

**What Happened?**
- The Jinja2 template looped through srl1's interfaces
- Found ethernet-1/1.0 and ethernet-1/2.0 (with IP addresses)
- Generated SR Linux CLI commands automatically
- No OSPF configuration yet—that comes in Module 4b!

✅ **Success!** You've just generated your first automated network configuration from NetBox.

## Configuring Device: srl2

Now let's configure the second device using the same process.

### Step 1: Associate the Config Template

1. Navigate to **Devices** → **Devices** and click on `srl2`
2. Click **Edit**
3. Scroll down to **Config Template** and select `SR Linux` from the dropdown
4. Click **Save**

### Step 2: Configure ethernet-1/1 (Transit Link to srl1)

On the **Interfaces** tab for `srl2`:

**Create Child Interface:**
1. Use **Quick Search** to find `ethernet-1/1`
2. Click the green **+** button and select **Child Interface**
3. Give it the name: `ethernet-1/1.0`
4. Click **Create**

**Assign IP Address:**
1. Use **Quick Search** to find `ethernet-1/1.0`
2. Click the green **+** button and select **IP Address**
3. Enter address: `10.0.0.2/30` (peer to srl1's 10.0.0.1)
4. Click **Create**

### Step 3: Configure ethernet-1/2 (Web Server Network)

Still on the **Interfaces** tab for `srl2`:

**Create Child Interface:**
1. Use **Quick Search** to find `ethernet-1/2`
2. Click the green **+** button and select **Child Interface**
3. Give it the name: `ethernet-1/2.0`
4. Click **Create**

**Assign IP Address:**
1. Use **Quick Search** to find `ethernet-1/2.0`
2. Click the green **+** button and select **IP Address**
3. Enter address: `192.168.2.1/30` (web server is at .2)
4. Click **Create**

### Step 4: Inspect the Rendered Configuration

1. Navigate to **Devices** → **Devices** → `srl2`
2. Click the **Render Config** tab

You should see the generated configuration:

```yaml
# Configure network instance
set / network-instance default type default

# Configure interfaces
set / interface ethernet-1/1 admin-state enable
set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.0.2/30
set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable

set / interface ethernet-1/2 admin-state enable
set / interface ethernet-1/2 subinterface 0 ipv4 address 192.168.2.1/30
set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable

# Add interfaces to default network instance
set / network-instance default interface ethernet-1/1.0
set / network-instance default interface ethernet-1/2.0
```

✅ **Perfect!** Notice how the same template generates the correct configuration for srl2 with different IP addresses. This is the power of template-driven configuration.

## Key Takeaways

Let's reflect on what you've accomplished in this module:

- ✅ Created a NetBox branch for safe changes
- ✅ Built a config template that generates interface configurations
- ✅ Configured both devices with interfaces and IP addresses
- ✅ Rendered complete (partial) configurations automatically

## What's Next?

In **Module 4b**, we'll complete our network modeling by adding OSPF configuration using:
- **Config Contexts** to define global settings (OSPF area)
- **Local Config Context** for per-device settings (router IDs)
- **Tags** to mark passive interfaces

This will give you a complete, deployable network configuration ready for automation in Module 5.

---

**Continue to:** [Module 4b - Network Modeling Advanced (Config Contexts & OSPF)](../module_4b/README.md)