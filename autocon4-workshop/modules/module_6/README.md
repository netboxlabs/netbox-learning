# Module 6: Network Validation & Drift Detection with Discovery

## Overview

Congratulations! You've come full circle:
- **Module 1**: Experienced the pain of manual configuration
- **Module 2**: Set up observability to detect failures
- **Module 3**: Used discovery to establish a baseline
- **Module 4**: Modeled intent in NetBox with branches
- **Module 5**: Deployed configurations automatically via Ansible

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
```
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

## Step 1: Create a Discovery Branch in NetBox

NetBox Discovery can detect the current state of your network, but that state might be very different from your intended state. Rather than immediately overwriting NetBox with discovered data (which might include mistakes!), we'll send discovery results to a **branch** where we can inspect them first.

### Create the Branch

> [!TIP]
> **NetBox Access**
> - URL: `echo "http://$MY_EXTERNAL_IP:8000"`
> - Username: `admin`
> - Password: `admin`

1. In NetBox, navigate to **Branching** → **Branches**
2. Click **+ Add** (top right)
3. Give your branch a name: `Module 6 Discovery`
4. Click **Create**

You'll be taken to the branch detail page. The status will initially show as `Provisioning`.

> [!NOTE]
> You may need to refresh the page a couple of times. Wait until the **Status** field shows `Ready` before proceeding.

### Configure Diode to Use the Branch

Now we need to tell Diode to send discovery results to this branch instead of main.

1. In NetBox, navigate to **Diode** → **Settings**
2. Click the pen icon (top right) to edit
3. Under the **Branch** dropdown, select `Module 6 Discovery`
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

Exit the SSH session:

```bash
quit
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

Exit srl1:

```bash
quit
```

## Step 3: Confirm Observability Detected the Failure

Now let's check if our monitoring system (from Module 2) detected the problem.

> [!TIP]
> **Prometheus URL:** `echo "http://$MY_EXTERNAL_IP:9090"`
> No authentication required.

1. Open Prometheus in your browser
2. Navigate to **Alerts** in the top menu
3. Click on the **WebServer_NotReachable** alert

The alert should be **red (Firing)**, confirming that the Orb agent detected the failure and Prometheus triggered the alert.

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

### Trigger a New Discovery Run

We've already configured device discovery in Module 3. The Orb agent watches for changes to policy files in Gitea. By updating the policy file, we trigger a new discovery run.

> [!TIP]
> **Gitea Access**
> - URL: `echo "http://$MY_EXTERNAL_IP:3000"`
> - Username: `admin`
> - Password: `admin123`

1. Open Gitea in your browser
2. Navigate to the **admin/orb-policies** repository
3. Click on `srl_devices.yaml`
4. Click the **edit** icon (small pen, top right)
5. On line 1, increment the `#--- version` number
   - Example: `#--- version: 1` → `#--- version: 2`
6. Scroll to the bottom and click **Commit Changes**

**What Happens Next:**
- Orb agent polls Gitea and detects the policy change
- Orb runs discovery against srl1 and srl2
- Discovery results are sent to Diode
- Diode ingests the data into the `Module 6 Discovery` branch

This takes about 1-2 minutes. Let's inspect the results!

### Inspect the Discovery Results

1. In NetBox, navigate to **Branching** → **Branches**
2. Click on `Module 6 Discovery`
3. Click the **Changes Ahead** tab

You should see discovery results showing changes detected across the network. Scroll through the list—you'll see many different types of NetBox objects that were discovered.

**Look for the smoking gun:**
Find a line showing **Updated** for `ethernet-1/1`. In the **BEFORE** and **AFTER** columns, you'll see:

| BEFORE        | AFTER          |
|---------------|----------------|
| enabled: None | enabled: False |

🎯 **Bingo!** Discovery detected that `ethernet-1/1` was disabled. Now you know exactly what changed and why the alerts are firing.

**Why This is Powerful:**
- You didn't need to SSH into devices to investigate
- Discovery automatically compared actual state vs. NetBox's expected state
- You have audit trail of what changed
- This works at scale (imagine 100 devices instead of 2)


## Step 5: Self-Heal by Re-Deploying Intent

Now that we know what broke (ethernet-1/1 was disabled), we could SSH in and fix it manually. But there's a better way: **re-deploy the known-good intent from NetBox**.

Since our automation already deployed the correct configuration in Module 5, we can simply re-run it. The automation will:
1. Query NetBox for the correct configuration
2. Deploy it to the devices
3. Overwrite the rogue change

This is **self-healing automation**: use the source of truth to correct drift.

### Re-Deploy the Configuration

Run the Ansible playbook to re-apply the intended configuration:

```bash
./run_ansible.sh
```

When prompted:

```
Warning: No branch specified. This will run against the main branch.
Do you want to continue? (yes/no): yes
```

Type `yes` and press Enter.

**What Happens:**
- Ansible queries NetBox's **main branch** for rendered configs
- Ansible connects to srl1 and srl2 via SSH
- Ansible deploys the configurations
- The interface is re-enabled automatically
- Network connectivity is restored

### Verify the Network is Healed

Check Prometheus to confirm the network is back online:

> [!TIP]
> **Prometheus URL:** `echo "http://$MY_EXTERNAL_IP:9090"`

1. Navigate to **Alerts**
2. Click on **WebServer_NotReachable**

The alert should now be **green (Inactive)**, showing that the network is functional again.

✅ **Self-healing complete!** Your automation system detected drift, identified the cause, and automatically corrected it.


## The Complete Closed-Loop Automation System

Congratulations! You've built and operated a complete closed-loop network automation system. Let's reflect on what you've accomplished and why it matters.

### The Closed Loop in Action

You experienced the complete cycle:

**1. Intent (Module 4)**
- Defined network state in NetBox (interfaces, IPs, OSPF)
- Used branches to safely model changes
- Generated configurations automatically via templates

**2. Deploy (Module 5)**
- Used Ansible to query NetBox API
- Automatically deployed configurations to devices
- No manual CLI commands needed

**3. Observe (Module 2)**
- Orb agent continuously monitors network
- Prometheus tracks metrics and fires alerts
- Detected failure immediately when interface was disabled

**4. Discover (Modules 3 & 6)**
- NetBox Discovery scans actual device state
- Compares reality vs. intent
- Identifies drift automatically

**5. Self-Heal (Module 6)**
- Re-deployed intent from NetBox
- Automatically corrected the drift
- Network restored without manual intervention

This is **true closed-loop automation**:

```
    ┌─────────────┐                    ┌─────────────┐
    │   NetBox    │ ─────Deploy──────> │   Ansible   │
    │  (Source of │                    │             │
    │   Truth)    │                    └──────┬──────┘
    └─────────────┘                           │
           ▲                                  │
           │                                  │
           │                                  ▼
           │                         ┌─────────────────┐
           │                         │    Network      │
           │                         │    Devices      │
           │                         └─────────────────┘
           │                                  │
           │                                  │
           │                                  ▼
           │                         ┌─────────────────┐
           │                         │   Orb Agent     │
           │   Discovery +           │  (Discovery &   │
           └─────Observability───────│ Observability)  │
                  Feedback           └─────────────────┘
```

### What You've Gained

**Control:**
- Update NetBox → Changes are deployed automatically
- No more manual SSH sessions for routine changes
- Consistent configurations across all devices
- Documentation always accurate (NetBox IS the documentation)

**Visibility:**
- Know what's actually running on devices (discovery)
- Know when things break (observability)
- Know what changed and when (branches + audit trail)
- Detect unauthorized changes immediately

**Resilience:**
- Automated recovery from drift
- Known-good state always available in NetBox
- Self-correcting when issues occur
- Faster mean time to recovery (MTTR)

### Real-World Benefits

**Scenario 1: Onboarding New Devices**
- Old way: Manual config, 2+ hours, error-prone
- New way: Add to NetBox, automation deploys, 15 minutes

**Scenario 2: Configuration Changes**
- Old way: SSH into each device, copy-paste, hope for the best
- New way: Update NetBox, review diff, deploy to all devices atomically

**Scenario 3: Troubleshooting Outages**
- Old way: SSH into devices, compare configs manually, investigate
- New way: Check alerts (observability), run discovery (what changed?), re-deploy intent (fix)

**Scenario 4: Compliance Audits**
- Old way: Manually collect configs, compare to standards, generate reports
- New way: Discovery shows drift from standards, automated reports available

### The Gradual Path to Automation

You don't need to automate everything overnight. Smart organizations:

**Phase 1: Observability**
- Implement monitoring first
- Get visibility before making changes
- Build confidence

**Phase 2: Source of Truth**
- Populate NetBox accurately
- Use it as documentation initially
- Engineers reference it before making changes

**Phase 3: Read-Only Automation**
- Use templates to generate configs
- Engineers review and manually deploy
- Builds trust in automation

**Phase 4: Automated Deployment**
- Automation deploys after human approval
- Start with low-risk changes
- Expand gradually

**Phase 5: Continuous Validation**
- Run discovery regularly
- Detect drift automatically
- Alert on unauthorized changes

**Phase 6: Self-Healing** (Where you are now!)
- Automatically re-deploy intent on drift detection
- Fully closed loop
- Requires high trust in your source of truth

### Key Takeaways

**1. Intent-First is Documentation-First**
Updating NetBox before deploying means documentation is always current. No more "make change now, document later (never)."

**2. Feedback Loops are Essential**
Without observability and discovery, you're automating blindly. Feedback loops make automation safe and trustworthy.

**3. Branches Enable Safe Changes**
Whether for planned changes (Module 4) or discovery results (Module 6), branches let you inspect before applying to production.

**4. Drift is Inevitable, Detection is Critical**
Networks will drift—what matters is detecting it quickly and having automated recovery.

**5. Start Small, Scale Gradually**
You don't need to automate everything at once. Pick high-value, low-risk use cases first and expand as confidence grows.

## What's Next?

You've completed the workshop, but your automation journey is just beginning. Here are some next steps:

### Learn More
- [NetBox Documentation](https://docs.netbox.dev/)
- [Orb Agent Documentation](https://github.com/netboxlabs/orb-agent)
- [NetBox Ansible Collection](https://docs.ansible.com/projects/ansible/latest/collections/netbox/netbox/)

### Join the Community
- [NetDev Community Slack](https://netdev.chat/)

---

**Thank you for participating in this workshop!** You now have the knowledge and experience to build closed-loop network automation systems. Go forth and automate! 🚀