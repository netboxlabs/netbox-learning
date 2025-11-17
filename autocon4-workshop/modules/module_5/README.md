# Module 5: Automated Configuration Deployment with Ansible

## Overview

This is the moment you've been building towards: **automatically deploying network configurations from NetBox to devices**.

You've done the hard work:
- **Module 3**: Established a baseline with discovery
- **Module 4**: Modeled your intended network state in NetBox
- **Generated configurations**: NetBox created complete device configs via templates

Now it's time to **deploy those configurations automatically** using Ansible.

No more:
- Copying and pasting CLI commands
- SSHing into device after device
- Worrying about typos or forgetting a device
- Manual validation after changes

Instead: Define intent in NetBox → Click deploy → Done.

## Learning Objectives

By the end of this module, you will:

- Understand the automated deployment workflow
- Deploy configurations from a NetBox branch using Ansible
- Use observability to verify deployment success
- Merge successful changes back to the main branch
- Understand branch-based deployment strategies
- See the complete intent-to-deployment pipeline in action

## Why Deploy from a Branch?

You modeled your network intent in a **branch** (Module 4: "Module 4 SRL Config"). Why not just deploy from main?

**The Branch-First Strategy:**

```
Branch (new intent) → Deploy → Verify → Merge to Main
         ↓                         ↓
    (If it breaks)        (If it works)
         ↓                         ↓
   Rollback from Main    Update main branch
```

**Benefits:**
- **Safety**: Main branch always contains last-known-good state
- **Rollback**: If deployment breaks network, re-deploy from main to recover
- **Validation**: Verify changes work before updating source of truth
- **Team workflow**: Multiple people can work on branches simultaneously

**In Production:**
- Some teams deploy from branches then merge
- Some merge first, then deploy from main
- Event-driven systems might auto-deploy on merge
- CI/CD pipelines orchestrate the workflow

For this workshop, we deploy from the branch first, verify it works, then merge.

## Understanding the Deployment Process

### What the Ansible Playbook Does

Our deployment script uses Ansible to:

1. **Query NetBox API** for the branch specified
2. **Fetch rendered configs** for each device
3. **SSH into each device**
4. **Apply configuration commands** line by line
5. **Verify success** and report results

> [!NOTE]
> **Workshop Simplification**
> Our Ansible playbook takes a straightforward approach: it applies rendered config lines directly.
>
> In production, you might use:
> - More sophisticated templating
> - Declarative modules (e.g., `cisco.ios.ios_config`)
> - Pre/post-deployment validation
> - Automated rollback on failure
> - Integration with CI/CD pipelines

### Deployment Triggers

> [!TIP]
> **In This Workshop:**
> We manually run a Bash script that invokes Ansible.
>
> **In Production, You Might Use:**
> - **CI/CD pipelines** (GitLab CI, GitHub Actions, Jenkins)
> - **Workflow orchestration** (Airflow, Temporal, Argo)
> - **Event-driven automation** (deploy automatically on branch merge)
> - **Scheduled jobs** (cron, scheduled pipelines)
> - **ChatOps** (Slack bot triggers deployment)

## Step 1: Get Your Branch ID

To deploy from your branch, Ansible needs the branch's unique identifier (Schema ID).

> [!TIP]
> **NetBox Access**
> - URL: `echo "http://$MY_EXTERNAL_IP:8000"`
> - Username: `admin`
> - Password: `admin`

### Find the Schema ID

1. In NetBox, navigate to **Branching** → **Branches**
2. Find your `Module 4 SRL Config` branch
3. Look in the **SCHEMA ID** column (should look like `3aq04puw`)
4. **Copy this ID**—you'll need it for the deployment command

**What is a Schema ID?**
It's a unique identifier for the branch. The Ansible script uses it to query the NetBox API and fetch rendered configs from that specific branch (not main).

## Step 2: Deploy Configurations to Devices

Now for the magic moment—let's deploy your NetBox intent to the actual network devices!

### Run the Deployment

From your workshop directory, run:

```bash
./run_ansible.sh --branch <SCHEMA ID>
```

Replace `<SCHEMA ID>` with the ID you copied (e.g., `./run_ansible.sh --branch 3aq04puw`)

### What You'll See

Ansible will output its progress as it:
1. Connects to the NetBox API
2. Fetches rendered configs for srl1 and srl2
3. SSH into each device
4. Applies configuration commands
5. Reports results

**Example output:**

```
TASK [Gathering Facts] *********************************************************
ok: [srl1]
ok: [srl2]

TASK [Fetch rendered config from NetBox] **************************************
ok: [srl1]
ok: [srl2]

TASK [Apply configuration to device] *******************************************
changed: [srl1]
changed: [srl2]

PLAY RECAP *********************************************************************
srl1                       : ok=8    changed=1    unreachable=0    failed=0
srl2                       : ok=8    changed=1    unreachable=0    failed=0
```

**Understanding the Output:**
- `ok=8`: 8 tasks succeeded
- `changed=1`: 1 task made changes (applied config)
- `unreachable=0`: All devices were reachable
- `failed=0`: No failures

✅ **Deployment successful!** Your NetBox intent is now running on the network devices.

## Step 3: Verify Deployment Success with Observability

Ansible says the deployment succeeded, but did it **actually work**? This is where observability proves its value. Let's check!

> [!TIP]
> **Prometheus Access**
> - URL: `echo "http://$MY_EXTERNAL_IP:9090"`
> - No authentication required

### Check the Alert Status

1. Open Prometheus in your browser
2. Navigate to **Alerts** in the top menu
3. Click on the **WebServer_NotReachable** alert

The alert should now be **green (Inactive)**, confirming:
- ✅ Network is correctly configured
- ✅ srl1 can reach the web server via OSPF
- ✅ All interfaces are up
- ✅ Routing is functional

🎉 **Success!** The network is working based on automated changes deployed from your NetBox intent.

### Compare to Module 1

Think about the difference:

**Module 1 (Manual):**
- SSHed into srl1, typed 30+ commands
- SSHed into srl2, typed 30+ commands
- Manually tested with ping
- ~15-20 minutes of tedious work
- High risk of typos

**Module 5 (Automated):**
- Ran one command: `./run_ansible.sh --branch <ID>`
- Ansible deployed to both devices simultaneously
- Observability automatically verified success
- ~2 minutes total
- Zero risk of typos (configs generated from NetBox)

**At scale (50 devices):**
- Manual: 12+ hours
- Automated: Still ~2 minutes

## Step 4: Merge the Branch to Main

The deployment worked and observability confirmed success. Now we can safely update the main branch with our new intent.

### Why Merge After Deployment?

Remember our strategy:
1. **Deploy from branch** (test in production safely)
2. **Verify it works** (observability confirms)
3. **Merge to main** (update source of truth)
4. **Main always = known-good state** (rollback target if needed)

If the deployment had **failed**, we could:
- Keep the branch active
- Fix issues in the branch
- Re-deploy from the branch
- OR rollback by deploying from main

But it worked, so let's merge!

### Merge the Branch

> [!TIP]
> **NetBox Access**
> - URL: `echo "http://$MY_EXTERNAL_IP:8000"`

1. In NetBox, navigate to **Branching** → **Branches**
2. Click on `Module 4 SRL Config`
3. Click **Merge** (top right)
4. Check the **Commit changes** checkbox
5. Click **Merge Branch**

> [!NOTE]
> The merge may take 1-2 minutes to complete.
> Refresh the page to check the branch status.

### Verify the Merge

Once complete:
- Branch status shows: `Merged`
- Main branch now contains your updated network intent
- Future deployments can use main as the source

## What Just Happened: The Complete Workflow

Let's trace the complete journey from intent to deployment:

### The Path from Intent to Reality

**1. Model Intent (Module 4)**
```
NetBox Branch → Config Template → Rendered Config
```
- You defined interfaces, IPs, OSPF in NetBox
- Templates generated device configurations
- Configs ready for deployment

**2. Deploy (Module 5)**
```
NetBox API ← Ansible → SSH → Devices
```
- Ansible queried NetBox API
- Fetched rendered configs
- SSHed into devices
- Applied configurations

**3. Verify (Observability)**
```
Devices → Orb Agent → Prometheus → Alerts (Green!)
```
- Orb checked web server reachability
- Prometheus evaluated alerts
- Confirmed network is healthy

**4. Update Source of Truth**
```
Branch → Merge → Main (Known-good state)
```
- Merged branch to main
- Main now reflects deployed reality
- Ready for next change cycle

## Key Takeaways

### The Automation Advantage

**What You Eliminated:**
- ❌ Manual SSH sessions
- ❌ Copy-paste errors
- ❌ Forgotten devices
- ❌ Inconsistent configurations
- ❌ Outdated documentation

**What You Gained:**
- ✅ One-command deployment
- ✅ Consistent configs across all devices
- ✅ Automated verification
- ✅ Self-documenting (NetBox IS the docs)
- ✅ Rollback capability
- ✅ Audit trail

### Why Branching Matters

Branches enable safe automation:
- **Test changes** without affecting main
- **Rollback** if deployment fails
- **Collaboration** - multiple teams working on different changes
- **Review** before production impact

### Idempotency: Run it Again and Again

Try running the deployment again with the same branch ID:

```bash
./run_ansible.sh --branch <SCHEMA ID>
```

**Result:** No changes made (`changed=0`)

This is **idempotency**: applying the same configuration multiple times has the same effect as applying it once. This makes automation safe and predictable.

## What's Next?

You've successfully deployed network configurations from NetBox automatically. But what happens when someone makes a manual change to the network? How do you detect it? How do you recover?

In **Module 6**, you'll:
- Simulate a rogue network change
- Use discovery to detect drift
- See observability catch the failure
- **Self-heal** by re-deploying intent from NetBox

This completes the full loop: Intent → Deploy → Monitor → Discover → Self-Heal.

---

**Continue to:** [Module 6 - Network Validation & Drift Detection](../module_6/README.md)