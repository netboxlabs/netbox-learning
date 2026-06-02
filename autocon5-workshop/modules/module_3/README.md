# Module 3: Event-Driven Ansible — Automating Network Operations

## Overview

In Module 2 you built a complete design in NetBox: site, rack, devices, cables, and management IPs. The source of truth is ready. Now it's time to put it to work.

This module introduces **Event-Driven Ansible (EDA)** — the automation layer that listens for events from NetBox, evaluates rules, and runs Ansible playbooks automatically. You'll see how Ansible reads its inventory dynamically from NetBox (no static host files), validate your network against NetBox as the source of truth, and then extend that validation yourself by editing a live playbook in Gitea.

## Learning Objectives

By the end of this module, you will:

- Understand how EDA turns a NetBox webhook into an automated playbook run
- Understand how the NetBox dynamic inventory plugin builds Ansible's host list from the source of truth
- Validate your network against NetBox as the source of truth and interpret the output
- Edit a live playbook in Gitea, sync it into EDA, and see your change take effect immediately

## How Event-Driven Ansible Works

> [!IMPORTANT]
> **Ansible Concept: Event-Driven Ansible & Rulebooks**
>
> Traditional Ansible requires a human to decide *when* to run a playbook. **Event-Driven Ansible (EDA)** removes that decision by processing incoming events — webhooks, alerts, state changes — through a **rulebook**. A rulebook is a YAML file that maps event conditions to actions: "if the event payload contains `event_type == device.validate`, run `validate_network.yml`." EDA runs continuously in the background, so automation fires the moment something happens — not the next time someone remembers to check.

EDA adds a rules engine on top of traditional Ansible. Instead of a human deciding when to run a playbook, an event (a webhook, an alert, a state change) does. Here's the full flow in this workshop:

```text
  NetBox Script           EDA (port 5000)           Ansible Playbook
  ─────────────          ─────────────────          ────────────────
  Trigger EDA  ──POST──► Webhook listener           
  Event Script            │                         
                          ▼                         
                    Evaluate rulebook               
                          │                         
                    Rule matches?                   
                          │ yes                     
                          ▼                         
                    run_playbook: ──────────────────► Query NetBox
                    validate_network.yml              SSH to devices
                                                      Build report
                          ◄──────────────────────────
                    POST result to callback URL     
                          │                         
                          ▼                         
  NetBox Script  ◄── Poll result server             
  displays result          (port 5001)              
```

**Key components:**

| Component | What it does |
|-----------|-------------|
| `ansible-rulebook` | Listens on port 5000, evaluates rules, triggers playbooks |
| `rulebook.yml` | Maps event types to playbook filenames |
| `result_server.py` | Receives playbook output on port 5001 and holds it for polling |
| `trigger_eda.py` | NetBox custom script that fires the webhook and displays the result |

**Where EDA runs:** EDA was started automatically when your workshop VM was provisioned. The `ansible-rulebook` process cloned the `ansible-playbooks` Gitea repo and is listening on port 5000.

### Verify EDA is Running

Before using EDA, confirm the two processes are up:

```bash
ps aux | grep -E 'ansible-rulebook|result_server' | grep -v grep
```

You should see two lines — one for `ansible-rulebook` (the webhook listener) and one for `result_server.py` (the result relay):

```
root  ... python3 ansible-playbooks/result_server.py
root  ... ansible-rulebook --rulebook rulebook.yml --inventory inventory/ --verbose
```

If either is missing, restart EDA from the workshop directory:

```bash
cd ~/workspace/product-internal-skunkworks/autocon5-workshop
source ./1_set_envvars.sh
bash 7_start_eda.sh
```

## How Ansible Knows Where to Connect: nb_inventory

> [!IMPORTANT]
> **Ansible Concept: Dynamic Inventory**
>
> Ansible needs to know *which hosts* to connect to and *how* to connect to them. A **static inventory** is a hand-maintained file of hostnames and IPs — it drifts the moment a device is added, renamed, or re-addressed. A **dynamic inventory** queries a live data source at run time and builds the host list fresh on every execution. The `netbox.netbox.nb_inventory` plugin used here queries the NetBox API directly — so the moment you add a device to NetBox, Ansible knows about it.

Traditional Ansible uses a static inventory file listing hostnames and IPs. That breaks as soon as a device is added or renamed. This workshop uses the **NetBox dynamic inventory plugin** (`netbox.netbox.nb_inventory`) instead.

When Ansible needs an inventory, it queries the NetBox API — using the same `NETBOX_URL` and `NETBOX_TOKEN` environment variables you set in the workshop setup — and builds a real-time picture of your devices, their IPs, and how they're grouped.

For this workshop, the inventory plugin:
- Finds all **Active** devices in the `sites_autocon_lab` group (all devices in site `autocon-lab`)
- Uses each device's **Primary IPv4** as `ansible_host` (the `172.24.0.x` management IPs you set in Module 2)
- Sets `ansible_network_os: nokia.srlinux.srlinux` and SSH credentials from the inventory config

This is why modeling the devices in NetBox with correct primary IPs in Module 2 mattered — Ansible reads exactly that data here.

> [!NOTE]
> **No Primary IP = Ansible can't connect.** If a device is missing its Primary IPv4 in NetBox, `nb_inventory` has nothing to put in `ansible_host` and the playbook will skip or fail for that device. Setting the primary IP is not optional — it's the bridge between the source of truth and the automation layer.

### Browse the Inventory Files in Gitea

The inventory config lives in the `ansible-playbooks` repository alongside the playbooks. Open Gitea (`https://gitea-<YOUR_ID>.autocon5.netboxlabs.tech`), navigate to the **ansible-playbooks** repository, and browse to the `inventory/` directory. You'll see two files.

---

**`inventory/nb_inventory.yml`** — tells Ansible how to query NetBox

```yaml
plugin: netbox.netbox.nb_inventory
validate_certs: false
config_context: true
interfaces: true
services: false
device_query_filters:
  - status: active
compose:
  ansible_host: primary_ip4.address | regex_replace('/.*$', '')
keyed_groups:
  - prefix: sites
    key: site.slug
    separator: "_"
```

| Line | What it does |
|------|-------------|
| `plugin: netbox.netbox.nb_inventory` | Use the official NetBox inventory plugin from the `netbox.netbox` collection |
| `device_query_filters: status: active` | Only devices marked **Active** in NetBox are included — planned or decommissioned devices are excluded automatically |
| `compose: ansible_host: primary_ip4.address \| regex_replace(...)` | Takes the Primary IPv4 address (e.g. `172.24.0.101/24`) and strips the CIDR suffix to produce the bare IP that Ansible uses for the SSH/API connection |
| `keyed_groups: key: site.slug` | Creates a dynamic Ansible group for each site. The `autocon-lab` site (slug: `autocon-lab`) becomes the group `sites_autocon_lab` — this is what playbooks target with `hosts: sites_autocon_lab` |
| `config_context: true` | Fetches each device's merged config context from NetBox as a hostvar. Used in Module 5 to pull OSPF router IDs |
| `interfaces: true` | Fetches interface data (names, types, IP assignments) for each device. Used in validation checks to compare NetBox intent against device state |

---

**`inventory/group_vars/sites_autocon_lab.yml`** — connection settings applied to every device in the group

```yaml
ansible_connection: ansible.netcommon.httpapi
ansible_network_os: nokia.srlinux.srlinux
ansible_user: admin
ansible_password: "NokiaSrl1!"
```

| Variable | What it does |
|----------|-------------|
| `ansible_connection: ansible.netcommon.httpapi` | Nokia SR Linux uses an HTTP/JSON-RPC API rather than traditional SSH for automation. This connection plugin handles that transport |
| `ansible_network_os: nokia.srlinux.srlinux` | Loads Nokia's SR Linux-specific Ansible modules (`nokia.srlinux` collection). These translate Ansible tasks into SR Linux CLI or gNMI operations |
| `ansible_user / ansible_password` | The admin credentials baked into the ContainerLab topology |

> [!NOTE]
> `group_vars/sites_autocon_lab.yml` applies to **every host in the group** — no per-device config needed. Add a new device to the `autocon-lab` site in NetBox and it inherits these settings automatically on the next Ansible run.

---

### Register the Trigger EDA Script

The `trigger_eda.py` script is the glue between NetBox and EDA — it fires webhook events and streams results back into the script output panel. Register it now before using it below:

1. Navigate to **Customization** → **Scripts**
2. Click **+ Add** (top right)
3. Fill in:
   - **Data Source**: `workshop-resources`
   - **File Path**: `scripts/trigger_eda.py`
   - Check **Auto sync enabled**
4. Click **Create**

---

### See It Live: Show Inventory

Before validating the network, you can inspect exactly what nb_inventory built from your NetBox data. The **Show Inventory** event renders a summary of every host in `sites_autocon_lab` — the IP Ansible will use, the OS, the site, and whether a config context is set.

1. In NetBox, navigate to **Customization** → **Scripts** → **Trigger EDA Event**
2. **Event Type**: `Show Inventory`
3. Leave **Target Device** blank
4. Click **Run Script**

You should see something like:

```
=== NetBox Dynamic Inventory ===

Plugin  : netbox.netbox.nb_inventory
Group   : sites_autocon_lab  (Active devices in site autocon-lab)

srl1  →  172.24.0.101
  Network OS  : nokia.srlinux.srlinux
  Connection  : ansible.netcommon.httpapi
  User        : admin
  Site        : autocon-lab
  Config Ctx  : (none — added in Module 5)
  Interfaces  : ethernet-1/1, ethernet-1/2, mgmt0, mgmt0.0

srl2  →  172.24.0.102
  Network OS  : nokia.srlinux.srlinux
  Connection  : ansible.netcommon.httpapi
  User        : admin
  Site        : autocon-lab
  Config Ctx  : (none — added in Module 5)
  Interfaces  : ethernet-1/1, ethernet-1/2, mgmt0, mgmt0.0

ansible_host resolved as:
  primary_ip4.address | strip CIDR suffix → bare IP for SSH
```

Everything here came from NetBox — the IPs you assigned to `mgmt0.0` in Module 2, the device names, the site. If a device is missing or shows the wrong IP, fix it in NetBox and re-run; Ansible picks it up automatically.

## Step 1: Validate Your Network Against the Source of Truth

> [!IMPORTANT]
> **Ansible Concept: Playbooks**
>
> An Ansible **playbook** is a YAML file that defines automation tasks — what to do, on which hosts, and in what order. Each task calls an Ansible **module**: a built-in function such as "run a CLI command on a network device" or "make an HTTP API call." Playbooks are **idempotent** by design — running the same playbook twice produces the same result as running it once, making them safe to re-run after a failure or a partial change. In this workshop, playbooks are stored in Gitea and triggered by EDA in response to NetBox events.

Let's see what the validator says about the network right now, given what's been modeled in NetBox so far.

1. In NetBox, navigate to **Customization** → **Scripts** → **Trigger EDA Event**
2. **Event Type**: `Network Validation Report`
3. Leave **Target Device** blank (runs against all workshop devices)
4. Click **Run Script**

The script fires a webhook to EDA on port 5000. EDA matches the `device.validate` event type in the rulebook and runs `validate_network.yml`. The playbook queries NetBox for expected state, SSHes into each device for actual state, and posts the result back. After a few seconds, the script polls the result and renders it line by line.

### Reading the Output

You should see something like this:

```
[srl1] (172.24.0.101)

  CHECK 1 — Device Reachable          : PASS
  CHECK 2 — LLDP Neighbors (cables)   : PASS — srl2
  CHECK 3 — Interface IPs             : FAIL — no IPs assigned in NetBox (assign IPs in Module 4)
  CHECK 4 — OSPF Neighbors            : FAIL — no OSPF config context in NetBox (configure OSPF in Module 5)
  CHECK 5 — Web Server Route          : FAIL — 192.168.2.x not in route table

[srl2] (172.24.0.102)

  CHECK 1 — Device Reachable          : PASS
  CHECK 2 — LLDP Neighbors (cables)   : PASS — srl1
  CHECK 3 — Interface IPs             : FAIL — no IPs assigned in NetBox (assign IPs in Module 4)
  CHECK 4 — OSPF Neighbors            : FAIL — no OSPF config context in NetBox (configure OSPF in Module 5)
  CHECK 5 — Web Server Route          : FAIL — 192.168.2.x not in route table
```

This is the baseline after Module 2. CHECKs 1 and 2 pass because the devices are reachable and the cables are in NetBox. CHECKs 3, 4, and 5 fail because IP addresses and OSPF haven't been deployed yet — those are the goals of Modules 4 and 5.

> [!NOTE]
> **Every FAIL message tells you exactly what to do next.** The validator uses NetBox as the source of truth: if the data isn't in NetBox, it reports why. If the data is in NetBox but not on the device, it reports that too. You'll watch each check flip to PASS as the workshop progresses.

### What the Validator Checks

| Check | Source of Truth | What it compares |
|-------|----------------|-----------------|
| CHECK 1 — Device Reachable | EDA connectivity | SSH succeeds |
| CHECK 2 — LLDP Neighbors | NetBox cables API | Expected remote devices vs. `show system lldp neighbor` |
| CHECK 3 — Interface IPs | NetBox IPAM | Assigned IPs vs. configured interfaces |
| CHECK 4 — OSPF Neighbors | NetBox config_context `router_id` | Peer's router_id from NetBox vs. active OSPF adjacencies |
| CHECK 5 — Web Server Route | Hard-coded `192.168.2.x` | Route presence in route table |

## Step 2: Interactive Exercise — Add a Hostname Check

The playbooks live in the `ansible-playbooks` Gitea repository, which EDA cloned when it started. Because EDA clones this repo, participants can push changes to Gitea, trigger a sync, and see new behaviour without restarting anything.

In this exercise you'll add **CHECK 0 — Hostname Drift** to `validate_network.yml`. Hostname drift is a real operational problem: someone SSHes in and renames a device, and suddenly your monitoring, your DNS, and your source of truth disagree. The check compares what the device reports as its own hostname against what NetBox says it should be called.

### Open the Playbook in Gitea

1. Open Gitea in your browser (`https://gitea-<YOUR_ID>.autocon5.netboxlabs.tech`)
2. Navigate to the `admin / ansible-playbooks` repository then click `validate_network.yml`
3. Click the **edit file icon** (pencil) in the top right of the file view

### Add the Report Block

The `show version` command already runs for CHECK 1 and returns the hostname inside its result — no extra CLI task is needed. All you need to add is the report block that reads from the existing `check_reachable` variable.

Find this block inside the `Build per-device validation report` task:

> [!TIP]
> Use your browser's **Find on Page** (Ctrl+F / Cmd+F) and search for `CHECK 1` — it should be the third result in the file.

```
          {# ── CHECK 1: Device reachable ── #}
            CHECK 1 — Device Reachable          : PASS
```

Replace it with:

```
          {# ── CHECK 0: Hostname matches NetBox ── #}
          {% set device_hostname = check_reachable.result[0]['basic system info']['Hostname'] | default('') %}
          {% if inventory_hostname == device_hostname %}
            CHECK 0 — Hostname Drift            : PASS — {{ inventory_hostname }} confirmed on device
          {% else %}
            CHECK 0 — Hostname Drift            : FAIL — device reports '{{ device_hostname }}', NetBox expects '{{ inventory_hostname }}'
          {% endif %}

          {# ── CHECK 1: Device reachable ── #}
            CHECK 1 — Device Reachable          : PASS
```

**Copy-paste this block rather than typing it** — YAML is whitespace-sensitive and a single misaligned space will cause the playbook to fail silently.

### Commit in Gitea

1. Scroll to the bottom of the edit page
2. Leave the commit message as the default or enter something descriptive like `Add CHECK 0 hostname drift validation`
3. Click **Commit Changes**

### Sync the Playbooks into EDA

EDA cloned the repo when it started and will keep running its original copy until you tell it to sync. The `git.sync` event type triggers `git_sync.yml`, which runs `git pull` inside the playbook directory.

1. Back in NetBox: **Customization** → **Scripts** → **Trigger EDA Event**
2. **Event Type**: `Sync Playbooks from Gitea`
3. Click **Run Script**

You should see a confirmation like:

```
Playbooks synced successfully. Latest commit: a1b2c3d Add CHECK 0 hostname drift validation
```

### Re-Run the Validation

1. **Customization** → **Scripts** → **Trigger EDA Event**
2. **Event Type**: `Network Validation Report`
3. Click **Run Script**

CHECK 0 should now appear in the output, and it should **PASS** — both devices are correctly named `srl1` and `srl2`, matching their NetBox names exactly.

> [!NOTE]
> **If the script times out after 90 seconds**, the most likely cause is a YAML indentation error in the playbook — ansible-rulebook fails to parse it and never posts a result back. SSH to the VM and run `tail -50 /root/workspace/product-internal-skunkworks/autocon5-workshop/eda.log` to see the exact error. Fix the indentation in Gitea, commit, re-sync, and try again.

```
[srl1] (172.24.0.101)

  CHECK 0 — Hostname Drift            : PASS — srl1 confirmed on device
  CHECK 1 — Device Reachable          : PASS
  CHECK 2 — LLDP Neighbors (cables)   : PASS — srl2
  ...
```

> [!TIP]
> **Try breaking it.** SSH into `srl1` (`ssh admin@clab-workshop-srl1`), run `enter candidate` then `set / system name host-name srl1-renamed` and `commit now`. Re-run the validation — CHECK 0 will flip to FAIL. Then fix the hostname (`set / system name host-name srl1`, `commit now`) and watch it pass again.

## Key Takeaways

1. **EDA replaces the "who decides when to run the playbook" problem.** Events drive playbooks. A click in NetBox, an alert from monitoring, or a change in Git are all valid triggers — no human polling required.

2. **nb_inventory makes NetBox the single source of inventory truth.** Devices added to NetBox are automatically included in the next Ansible run. No static host files to maintain.

3. **FAIL messages are actionable, not just error codes.** The validator always explains whether the gap is in NetBox (data not entered yet) or on the device (config not deployed yet). This is the difference between a monitoring check and a compliance check.

4. **Playbooks in Git are live-editable.** Pushing to Gitea and triggering a sync is all it takes to change automation behaviour — no restarts, no redeployments, no config management for the config management tool.

## What's Next?

In **Module 4** you'll assign IP addresses to the device interfaces in NetBox, deploy them using EDA's `Push Device Config` event, and run the validator to watch CHECK 3 flip from FAIL to PASS.

---

**Continue to:** [Module 4 — Config Templates & Device Configuration](../module_4/README.md)
