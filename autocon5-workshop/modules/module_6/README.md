# Module 6: Network Validation & Drift Detection with Discovery

## Overview

Congratulations! You've come full circle:

- **Module 1**: Experienced the pain of manual configuration (and validated with observability)
- **Module 2**: Used discovery to establish a baseline in NetBox
- **Module 3**: Used Event-Driven Ansible (EDA) to automate config deployment
- **Modules 4 & 5**: Modeled intent in NetBox with branches

But here's the reality: **Networks drift**. Despite your best automation efforts, changes happen:

- Engineers SSH in to troubleshoot and forget to update NetBox
- Hardware failures cause unexpected configuration changes
- Emergency fixes bypass the proper workflow
- Misconfigurations creep in over time

In this final module, you'll close the loop by using **NetBox Discovery** to detect drift and **automation** to self-correct. This is what makes your automation system truly **closed-loop**: it can detect when reality doesn't match intent and automatically fix it.

## Learning Objectives

By the end of this module, you will:

- Understand operational drift and why it's inevitable
- Use NetBox Discovery to detect configuration changes
- Run discovery results into NetBox branches for safe inspection
- Simulate a rogue network change and detect it via discovery
- Use observability to confirm the network is broken
- Self-heal the network by re-deploying intent from NetBox
- Understand the complete closed-loop automation workflow

## Why Drift Detection Matters

**The Problem:**
Even with automation, networks drift from their intended state. A well-intentioned engineer might:

1. SSH into a device to troubleshoot an outage
2. Make a "quick fix" to restore service
3. Forget to update NetBox
4. Your automation now has incorrect data

**The Solution:**
Continuous discovery creates a feedback loop:

```text
┌─────────────┐
│   NetBox    │ ─────> Deploy configs ─────> Network
│  (Intent)   │                                  │
└─────────────┘                                  │
       ▲                                         │
       │                                         │
       └───── Discovery detects drift ───────────┘
```

With this loop, you can:

- Detect unauthorized changes
- Identify configuration drift
- Validate that deployments actually worked
- Build self-correcting automation

---

## Your Observability Stack

Now is a good time to get familiar with the monitoring tools running in your lab — you'll rely on them shortly to detect the failure you're about to simulate.

### How Orb Monitors the Network

The Orb agent (192.168.1.2) continuously performs HTTP health checks against the web server (192.168.2.2). Because this check traverses the entire data path — through srl1's transit link, over OSPF to srl2, and out to the web server — a single alert tells you the whole path is broken.

```text
Orb agent ──> srl1 eth-1/2 ──> srl1 eth-1/1 ──> OSPF ──> srl2 eth-1/1 ──> srl2 eth-1/2 ──> Web Server
(192.168.1.2)                                                                               (192.168.2.2)
```

### Grafana Dashboard

Grafana visualises the Orb metrics and surfaces the **WebServer_HttpCheckError** alert. The dashboard's **Web Server Status** panel shows **Reachable** (green) or **Unreachable** (red) based on the underlying PromQL rule:

```promql
httpcheck_error{http_url="http://192.168.2.2"} == 1
```

> [!TIP]
> **Grafana Access**
>
> - URL: `https://grafana-<YOUR_ID>.autocon5.netboxlabs.tech`
> - Username: `admin` / Password: `netboxlabs`
>
> Keep the **Workshop Network Observability** dashboard open in a tab — you'll watch the **Web Server Status** panel change state throughout this module.

---

## Step 1: Create a Discovery Branch in NetBox

NetBox Discovery can detect the current state of your network, but that state might be very different from your intended state. Rather than immediately overwriting NetBox with discovered data (which might include mistakes!), we'll send discovery results to a **branch** where we can inspect them first.

### Create the Branch

1. In NetBox, navigate to **Branching** → **Branches**
2. Click **+ Add** (top right)
3. Give your branch a name: `module-6-discovery`
4. Click **Create**

You'll be taken to the branch detail page. The status will initially show as `Provisioning`.

> [!NOTE]
> You may need to refresh the page a couple of times. Wait until the **Status** field shows `Ready` before proceeding.

### Configure Diode to Use the Branch

Now we need to tell Diode to send discovery results to this branch instead of main.

1. In NetBox, navigate to **Diode** → **Settings**
2. Click the pen icon (top right) to edit
3. Under the **Branch** dropdown, select `module-6-discovery`
4. Click **Save**

**What This Does:**

- All future discovery data will be sent to the branch
- Main branch remains unchanged (your source of truth is protected)
- You can inspect discovery results before deciding whether to merge them

**Why This Matters:**
If discovery finds incorrect configurations (like our upcoming "rogue change"), you don't want to automatically import bad data into NetBox. Branches let you review first.

## Step 2: Simulate a Rogue Network Change

In real-world networks, automation adoption is gradual. Some parts are automated while others are still manually managed. Engineers might make emergency changes that bypass the proper workflow. Let's simulate this scenario.

**The Scenario:**
You're a network engineer responding to a late-night incident. You SSH into a device, make a "quick fix," and forget to update NetBox. Your automation now has stale data, and the network has drifted from its intended state.

Let's play the role of this rogue engineer! 😈

### Break the Network by Disabling an Interface

SSH into srl1:

> [!TIP]
> **Nokia SR Linux Credentials**
>
> - Username: `admin`
> - Password: `NokiaSrl1!`

```bash
ssh admin@clab-workshop-srl1
```

Disable the critical transit link to srl2:

```bash
enter candidate
set / interface ethernet-1/1 admin-state disable
commit now
```

### Verify the Network is Broken

Still logged into srl1, try to ping the web server:

```bash
ping -c 4 network-instance default 192.168.2.2
```

**Expected result:**

```bash
Using network instance default
PING 192.168.2.2 (192.168.2.2) 56(84) bytes of data.

--- 192.168.2.2 ping statistics ---
4 packets transmitted, 0 received, 100% packet loss, time 3071ms
```

🔴 **Network is broken!** The disabled interface prevents srl1 from reaching the web server through srl2.

Now exit srl1 by pressing `Ctrl+D`.

## Step 3: Confirm Observability Detected the Failure

Now let's check if our monitoring system detected the problem.

1. Switch to your Grafana tab (or open it at `https://grafana-<YOUR_ID>.autocon5.netboxlabs.tech`)
2. Open the **Workshop Network Observability** dashboard
3. Look at the **Web Server Status** panel

The panel should now show 🔴 **Unreachable**, confirming that the Orb agent detected the failure automatically.

**The Problem:**
The alert tells you something is broken, but **not what changed**. As an on-call engineer at 2 AM, you see:

- 🔴 Alert firing
- ❓ No context on what changed
- ❓ No idea who made changes or when

**The Question:**
*What happened to break the network?*

This is where **discovery** becomes critical.

## Step 4: Use Discovery to Detect the Drift

NetBox Discovery can tell us exactly what changed in the network by comparing the current state to what NetBox expects. This turns a vague "something is broken" into a specific "ethernet-1/1 was disabled."

### Trigger a Discovery Run

Discovery is on-demand — it runs each time you execute the **Run Orb Discovery** script. The version bump in `srl_devices.yaml` signals the Orb agent to re-run the policy against the live devices and push the results to Diode.

1. Navigate to **Customization** → **Scripts** → **Run Orb Discovery**
2. Select **Site**: `autocon-lab`
3. Select **Device Role**: `Router`
4. Leave **Activate policy** checked (it's on by default)
5. Leave **Dry run** unchecked
6. Click **Run Script**

> [!TIP]
> Watch for results in **Branching** → **Branches** → `module-6-discovery` → **Changes Ahead** tab. Refresh every 30 seconds — discovery typically completes within a minute of the script run.

### Inspect the Discovery Results

1. In NetBox, navigate to **Branching** → **Branches**
2. Click on `module-6-discovery`
3. Click the **Changes Ahead** tab

You should see discovery results showing changes detected across the network. The raw list has many entries — use the **Branch Change Summary** script to cut through the noise:

1. Navigate to **Customization** → **Scripts** → **Branch Change Summary**
2. Select **Branch**: `module-6-discovery`
3. Click **Run Script**

The script filters out routine no-op Diode updates and surfaces only meaningful changes, with before/after values for each updated field. **Look for the smoking gun** — a row in the UPDATED section for `ethernet-1/1` showing:

```text
Object Type   Name          Field    Before  After
------------  ------------  -------  ------  -----
interface     ethernet-1/1  enabled  None    False
```

🎯 **Bingo!** Discovery detected that `ethernet-1/1` was disabled. Now you know exactly what changed and why the alerts are firing.

**Why This is Powerful:**

- You didn't need to SSH into devices to investigate
- Discovery automatically compared actual state vs. NetBox's expected state
- You have an audit trail of what changed
- This works at scale (imagine 100 devices instead of 2)

## Step 5: Self-Heal by Re-Deploying Intent

Now that we know what broke (ethernet-1/1 was disabled), we could SSH in and fix it manually. But there's a better way: **re-deploy the known-good intent from NetBox via EDA** — the same mechanism you've been using throughout the workshop.

Since the correct configuration is already in NetBox's main branch, we simply push it again. EDA will query NetBox, render the config, and overwrite the rogue change.

> [!IMPORTANT]
> **Deploy from main — not the discovery branch.** The `module-6-discovery` branch contains what Diode *found on the network* — including the disabled interface. Deploying from that branch would push the broken state. Main holds your intent, which is what you want to restore.

### Re-Deploy the Configuration

1. In NetBox, navigate to **Customization** → **Scripts**
2. Click **Trigger EDA Event**
3. Set **Event Type**: `Push Device Config`
4. Leave **Target Device** blank (deploys to all workshop devices)
5. Leave **Branch** blank — this deploys from **main**, which has the correct intent
6. Click **Run Script**

**What Happens:**

- EDA receives the `device.config_push` event
- Ansible queries NetBox's **main** branch for rendered configurations
- Ansible connects to srl1 and srl2 and deploys the configurations
- The disabled interface is re-enabled automatically
- Network connectivity is restored

### Verify the Network is Healed

Check Grafana to confirm the network is back online:

1. Switch to your Grafana tab (or open it at `https://grafana-<YOUR_ID>.autocon5.netboxlabs.tech`)
2. Open the **Workshop Network Observability** dashboard
3. Watch the **Web Server Status** panel

The panel should return to 🟢 **Reachable**, showing that the network is functional again.

### Confirm with the Network Validation Report

Run the full validation to confirm all checks are green:

1. In NetBox, navigate to **Customization** → **Scripts**
2. Click **Trigger EDA Event**
3. Set **Event Type**: `Network Validation Report`
4. Leave **Target Device** and **Branch** blank
5. Click **Run Script**

**Expected output:**

```text
=== Network Validation Report ===

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

All six checks passing confirms the network is fully restored to its intended state.

## Step 6: Let Discovery Confirm the Fix

The network is healed, but the `module-6-discovery` branch is still open. Trigger one more discovery run to let Orb re-scan the devices now that the correct config has been restored.

1. Navigate to **Customization** → **Scripts** → **Run Orb Discovery**
2. Select **Site**: `autocon-lab`, **Device Role**: `Router` (leave **Activate policy** checked)
3. Click **Run Script**

Once the script completes, run **Branch Change Summary** again to review the updated results:

1. Navigate to **Customization** → **Scripts** → **Branch Change Summary**
2. Select **Branch**: `module-6-discovery`
3. Click **Run Script**

The output should show **no meaningful changes** — which is exactly what you want to see. The network now matches main, so there's nothing left to report. Discovery has confirmed the drift is resolved.

> [!NOTE]
> **The Next Step: Closing the Loop Fully**
> In this module you triggered the self-healing re-deployment manually. The final step to a truly autonomous system is wiring a Grafana alert or NetBox webhook directly to an EDA rulebook — so remediation fires automatically the moment drift is detected, with no human in the loop. The rulebook and event infrastructure are already running in your environment; the only addition is a rule that matches the alert and calls the `device.config_push` playbook.

## The Complete Closed-Loop Automation System

Congratulations! You've built and operated a complete closed-loop network automation system. Let's reflect on what you've accomplished and why it matters.

### The Closed Loop in Action

You experienced the complete cycle:

#### 1. Intent (Modules 4 & 5)

- Defined network state in NetBox (interfaces, IPs, OSPF)
- Used branches to safely model changes
- Generated configurations automatically via templates

#### 2. Deploy (Module 3)

- Used Event-Driven Ansible (EDA) to automate deployment
- EDA rulebook received NetBox events and ran Ansible playbooks
- Ansible queried NetBox API and deployed configs — no manual CLI needed

#### 3. Observe (Module 1)

- Orb agent continuously monitors network
- Grafana tracks metrics and fires alerts
- Detected failure immediately when interface was disabled

#### 4. Discover (Modules 2 & 6)

- NetBox Discovery scans actual device state
- Compares reality vs. intent
- Identifies drift automatically

#### 5. Self-Heal (Module 6)

- Re-deployed intent from NetBox via EDA
- Ansible overwrote the rogue change and restored the correct config
- Validated all checks green with the Network Validation Report

This is **true closed-loop automation**:

```text
    ┌─────────────┐   Event/Webhook   ┌─────────────┐
    │   NetBox    │ ─────────────────>│ Ansible EDA │
    │  (Source of │                   │  (Rulebook) │
    │   Truth)    │                   └──────┬──────┘
    └─────────────┘                          │ triggers
           ▲                                 ▼
           │                         ┌─────────────┐
           │                         │   Ansible   │
           │                         │  (Playbook) │
           │                         └──────┬──────┘
           │                                │
           │                                │
           │                                ▼
           │                         ┌─────────────────┐
           │                         │    Network      │
           │                         │    Devices      │
           │                         └─────────────────┘
           │                                │
           │                                │
           │                                ▼
           │                         ┌─────────────────┐
           │                         │   Orb agent     │
           │   Discovery +           │  (Discovery &   │
           └─────Observability───────│ Observability)  │
                  Feedback           └─────────────────┘
```

### Key Takeaways

**1. Intent-First is Documentation-First**
Updating NetBox before deploying means documentation is always current. No more "make change now, document later (never)."

**2. Feedback Loops are Essential**
Without observability and discovery, you're automating blindly. Feedback loops make automation safe and trustworthy.

**3. Branches Enable Safe Changes**
Whether for planned changes (Modules 4 & 5) or discovery results (Module 6), branches let you inspect before applying to production.

**4. Drift is Inevitable, Detection is Critical**
Networks will drift - what matters is detecting it quickly and having automated recovery.

**5. Start Small, Scale Gradually**
You don't need to automate everything at once. Pick high-value, low-risk use cases first and expand as confidence grows.

**6. Event-Driven Automation Closes the Final Gap**
The self-healing re-deployment in this module was still a human trigger. The final step is connecting a Grafana alert or NetBox webhook directly to EDA, so remediation fires automatically — turning reactive, human-initiated responses into proactive, self-driving remediation.

## What's Next?

Here are some resources to help you continue in your network automation journey:

### Learn More

- [NetBox Documentation](https://docs.netbox.dev/)
- [Orb agent Documentation](https://github.com/netboxlabs/orb-agent)
- [NetBox Ansible Collection](https://docs.ansible.com/projects/ansible/latest/collections/netbox/netbox/)
- [Ansible Event-Driven Ansible Documentation](https://ansible.readthedocs.io/projects/rulebook/)

### Join the Community

- [NetDev Community Slack](https://netdev.chat/)

---

**Thank you for participating in this workshop!** You now have the knowledge and experience to build closed-loop network automation systems. Go forth and automate! 🚀
