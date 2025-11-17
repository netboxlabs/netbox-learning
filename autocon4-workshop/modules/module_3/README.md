# Module 3: Network Discovery & Baseline with NetBox Discovery

## Overview

In Module 2, you set up observability to monitor your network. Now let's pivot and setup NetBox. To get started using it as a source of truth for automation, you first need to **populate it with accurate data**.

For greenfield networks (building from scratch), you can populate NetBox as you build. But most networks are **brownfield** - they already exist, with devices running, interfaces configured, and IPs assigned. Manually documenting hundreds or thousands of existing devices is tedious and error-prone.

**This is where NetBox Discovery can really help.** It automatically scans your network and populates NetBox with:
- Devices and their details (manufacturer, model, serial numbers)
- Interfaces and their configurations
- IP addresses and subnets

In this module, you'll use the Orb agent to run device discovery, establishing a baseline of your network in NetBox (safely, using branches).

## Learning Objectives

By the end of this module, you will:

- Use NetBox branches to safely ingest discovery data
- Configure Orb agent policies via Git (Gitea)
- Run device discovery to populate NetBox automatically
- Inspect discovered data before merging to production
- Merge discovery results into NetBox's main branch
- Understand how discovery provides a baseline for automation

## Why Discovery + Branching?

Discovery can save countless hours of manual data entry, but there's a risk: **what if discovery finds incorrect or stale data?** In production NetBox instances with valuable existing data, you don't want discovery to blindly overwrite what's already there.

**The Solution: NetBox Branching**

[NetBox Branching](https://github.com/netboxlabs/netbox-branching) works just like Git branches for code:
> "A discrete, static snapshot of the NetBox database which can be modified independently and later merged back into the main database. This enables users to make 'offline' changes to objects within NetBox and avoid interfering with its integrity as the network source of truth."

**The Workflow:**
```
Discovery ---> Branch ---> Inspect ---> Merge to Main (if good)
                              │
                              V 
                           Discard (if bad)
```

**Benefits:**
- **Safety**: Discovery results go to a branch, not main
- **Review**: Inspect discovered data before accepting it
- **Collaboration**: Team can review discovery results together
- **Rollback**: Discard the branch if discovery found bad data

This is especially valuable in brownfield networks where:
- Devices might be misconfigured
- Documentation might be inaccurate
- Multiple teams manage different parts of the network
- You need to validate before trusting discovered data

## Step 1: Create a Discovery Branch in NetBox

Let's create a branch where discovery results will be safely deposited.

> [!TIP]
> **NetBox Access**
> - URL: `echo "http://$MY_EXTERNAL_IP:8000"`
> - Username: `admin`
> - Password: `admin`

### Create the Branch

1. In NetBox, navigate to **Branching** → **Branches**
2. Click **+ Add** (top right)
3. Give your branch a name: `Module 3 Initial Discovery`
4. Click **Create**

You'll be taken to the branch detail page. The status will initially show as `Provisioning`.

> [!NOTE]
> Refresh the page periodically. Wait until the **Status** field shows `Ready` before proceeding. This usually takes 30-60 seconds.

### Configure Diode to Use the Branch

Now tell Diode (the ingestion service) to send discovery results to this branch instead of main.

1. In NetBox, navigate to **Diode** → **Settings**
2. Click the pen icon (top right) to edit
3. Under the **Branch** dropdown, select `Module 3 Initial Discovery`
4. Click **Save**

**What Just Happened:**
- Created an isolated branch for discovery results
- Configured Diode to route discoveries to the branch
- Main branch remains untouched and protected

Now let's configure discovery to actually run!

## Step 2: Understand Git-Based Configuration with Gitea

The Orb agent can be configured in several ways, but we're using **Git-based configuration**. The agent polls a Git repository for policy files and automatically applies changes.

**Why Git-Based?**
- **Version control**: All changes are tracked
- **GitOps**: Configuration as code
- **Rollback**: Revert bad changes easily
- **Audit trail**: Know who changed what and when

Our Orb agent watches a repository in [Gitea](https://about.gitea.com/), a self-hosted Git service running in your lab.

### Explore the Orb Policies Repository

> [!TIP]
> **Gitea Access**
> - URL: `echo "http://$MY_EXTERNAL_IP:3000"`
> - Username: `admin`
> - Password: `admin123`

1. Open Gitea in your browser
2. Click **Sign In** (top-right)
3. Under **Repositories**, click on `admin/orb-policies`

You'll see several YAML files that control the Orb agent:

**Policy Files:**

| File | Purpose | Status in Workshop |
|------|---------|-------------------|
| `srl_devices.yaml` | Device discovery for SR Linux devices | Will enable soon |
| `web_monitor.yaml` | HTTP monitoring (Module 2) | Already enabled |
| `clab_networks.yaml` | Network discovery for IP ranges | Not used today |
| `selector.yaml` | Master switch to enable/disable policies | Central control |

**How It Works:**
1. You edit a policy file in Gitea (via web UI or Git push)
2. Orb agent polls the repo periodically (every minute)
3. Agent detects changes and applies new configuration
4. Discovery runs according to the policy

Let's enable device discovery!

## Step 3: Enable Device Discovery

To enable device discovery, we simply update the `selector.yaml` file to turn on the `srlinux_discovery` policy.

### Edit the Selector File

Still in Gitea (in the `admin/orb-policies` repository):

1. Click on `selector.yaml`
2. Click the **edit** icon (small pen, top right)
3. Find the `srlinux_discovery` section
4. Change `enabled: false` to `enabled: true`
5. Scroll to the bottom and click **Commit Changes**

**Your updated `selector.yaml` should look like this:**

```yaml
web_monitor:
  selector:
    agent_name: orb-agent
  policies:
    web_monitor:
      path: web_monitor.yaml
      enabled: true

srlinux_discovery:
  selector:
    agent_name: orb-agent
  policies:
    srl_devices:
      path: srl_devices.yaml
      enabled: true        # ← Changed from false to true

clab_network_discovery:
  selector:
    agent_name: orb-agent
  policies:
    clab_networks:
      path: clab_networks.yaml
      enabled: false      # ← Leave this disabled
```

**What Happens Next:**
1. Gitea saves the commit
2. Orb agent polls the repository (within the next minute)
3. Agent detects the policy change
4. Agent starts running device discovery against srl1 and srl2
5. Discovery results are sent to Diode
6. Diode ingests data into your `Module 3 Initial Discovery` branch

This process can take up to 2-3 minutes to complete. Let's inspect the results!

## Step 4: Inspect the Discovery Results

Discovery is now running! After a minute or two, the Orb agent will have connected to both devices, gathered data, and sent it to NetBox via Diode.

### View Changes in the Branch

1. In NetBox, navigate to **Branching** → **Branches**
2. Click on `Module 3 Initial Discovery`
3. Click the **Changes Ahead** tab

You should see a list of discovered objects. The count will grow as discovery progresses.

> [!NOTE]
> **Device Discovery takes 1-2 minutes** to fully sync all data to your branch.
> Keep refreshing until you see approximately **366 Changes Ahead**.

### Explore the Discovered Data

The **Changes Ahead** list is useful for a quick overview, but let's actually explore the discovered data in NetBox.

**Activate the Branch:**
1. At the top of the screen, click **Activate**
   - You're now "inside" the branch
   - You'll see the branch name displayed at the top

**Explore the Site:**
1. In the left navigation, click **Organization** → **Sites** → **Sites**
2. You should see a site called `Workshop`

**Explore Devices:**
1. Click on the `Workshop` site
2. On the right, under **Related Objects**, click **Devices**
3. You should see both `srl1` and `srl2`

**Explore srl1 in Detail:**
1. Click on `srl1`
2. Review the discovered information:
   - Device type: Nokia SR Linux
   - Platform details
   - Serial number
   - Status
3. Click the **Interfaces** tab
4. Explore the interfaces - you'll see all physical and subinterfaces discovered
5. Click on an interface to see its details (admin status, IPs, etc.)

**What Discovery Found:**
- ✅ Site information
- ✅ Device details (manufacturer, model, serial)
- ✅ All interfaces (physical + subinterfaces)
- ✅ IP addresses assigned to interfaces
- ✅ Interface administrative states

## Step 5: Merge Discovery Results into Main

Since this is the first data going into NetBox, and we've inspected it to confirm it looks good, it's safe to merge the discovery results into the main branch.

> [!NOTE]
> In production scenarios with existing NetBox data, you'd review more carefully, potentially edit discovered data, and might even discard the branch if discovery found incorrect information. But for our baseline, we trust it!

### Merge the Branch

1. Navigate to **Branching** → **Branches** → `Module 3 Initial Discovery`
2. Click **Merge**
3. Check the **Commit Changes** checkbox
4. Click **Merge Branch**

> [!TIP]
> The merge process may take 1-2 minutes as NetBox applies all 366 changes.
> You can refresh the page to check the branch status.

### Verify the Merge

Once the merge completes:

**1. Check Branch Status:**
- Your `Module 3 Initial Discovery` branch now shows status: `Merged`
- A merged branch can no longer be edited (it's archived)

**2. Verify Data in Main:**
1. Switch to the **main** branch (use the branch dropdown at the top)
2. Navigate to **Organization** → **Sites** → **Sites**
3. You should see the `Workshop` site
4. Click through to devices - `srl1` and `srl2` are now in main!

**Success!** Your NetBox instance now has a complete, accurate baseline of your network infrastructure.

## Key Takeaways

**1. Discovery is a Time-Saver**
Automatically populating NetBox saves countless hours of manual data entry, especially in brownfield networks.

**2. Branches Enable Safe Discovery**
Ingesting into a branch lets you review before committing to main. This is critical in production environments.

**3. Discovery Provides a Baseline**
You now have a baseline of your network in your source of truth. This baseline is essential for safe and accurate automation.

## What's Next?

In **Module 4**, you'll:
- Model your **intended** network state (not just current state)
- Use config templates to generate device configurations
- Prepare configurations for automated deployment

---

**Continue to:** [Module 4a - Expressing Network Design Through Modeling (Basic)](../module_4a/README.md)