# Module 1: Configuring the Network the Old Fashioned Way

## Overview

Despite the availability of automation tools, it's still common for many network teams to SSH directly into devices to configure them manually. This approach is both laborious and error-prone, but experiencing it firsthand helps us appreciate why automation is so valuable—and why doing it right matters.

In this module, you'll manually configure network devices using the CLI, feeling the pain points that automation aims to solve. This sets the stage for the automated solutions we'll build in later modules.

## Learning Objectives

By the end of this module, you will:

- Understand the lab network topology and how devices connect
- Experience manual network configuration using SSH and CLI commands
- Configure interfaces, IP addressing, and OSPF routing manually
- Validate network connectivity using ping
- Recognize the challenges and risks of manual configuration at scale

## Lab Network Topology

Throughout this workshop, we'll work with a simple but realistic network topology:

```
┌──────────────────┐                             ┌──────────────────┐
│   Orb Agent      │                             │   Web Server     │
│                  │                             │                  │
│  (Monitoring)    │                             │    (Target)      │
└────────┬─────────┘                             └────────┬─────────┘
         │ 192.168.1.2/30                                 │ 192.168.2.2/30
         │                                                │ 
         │ 192.168.1.1/30                                 │ 192.168.2.1/30
         │ ethernet-1/2                                   │ ethernet-1/2
┌────────┴─────────┐             OSPF            ┌────────┴─────────┐
│      srl1        │            Area 0           │      srl2        │
│                  │◄───────────────────────────►│                  │
│   Router ID:     │ 10.0.0.1/30     10.0.0.2/30 │   Router ID:     │
│    1.1.1.1       │ ethernet-1/1   ethernet-1/1 │    2.2.2.2       │
└──────────────────┘                             └──────────────────┘
```

### Topology Details

**Devices:**
- **srl1**: Nokia SR Linux router (Management IP: 172.24.0.101)
- **srl2**: Nokia SR Linux router (Management IP: 172.24.0.102)
- **web-server**: Nginx web server (192.168.2.2)
- **orb-agent**: Monitoring agent (Management IP: 172.24.0.100)

**Network Design:**
- **Transit Link**: srl1 (10.0.0.1) ↔ srl2 (10.0.0.2) via ethernet-1/1
- **Routing Protocol**: OSPF v2, Area 0
- **Web Server Access**: Connected to srl2 via 192.168.2.0/30 subnet
- **Goal**: Enable srl1 to reach the web server (192.168.2.2) via OSPF routing through srl2

### Initial State

The network starts in a **broken state**:
- Interfaces are not configured
- IP addresses are not assigned
- OSPF is not enabled
- Connectivity to the web server does not work

Your task: Fix it manually (so you appreciate automation later!).

## Setting Up the Lab Environment

Before we start configuring devices, we need to ensure our lab environment is running.

### Step 1: Set Up Environment Variables

First, set up your shell environment variables:

```bash
source ./1_set_envvars.sh
```

```bash
source 3_set_diode_creds.sh
```

This script sets various environment variables including `$MY_EXTERNAL_IP` which you'll use throughout the workshop.

### Step 2: Start the ContainerLab Network

Launch the network topology:

```bash
./7_start_network.sh network/workshop.clab.yaml
```

> [!TIP]
> If prompted to remove existing labs, type `y` to confirm.

This script will:
1. Create the necessary Docker networks
2. Deploy all containers (srl1, srl2, web-server, orb-agent)
3. Leave devices unconfigured (other than management intefaces)

After a couple of minutes, you should see the lab deployment complete:

```bash
╭──────────────────────────┬──────────────────────────────┬─────────┬────────────────╮
│           Name           │          Kind/Image          │  State  │ IPv4/6 Address │
├──────────────────────────┼──────────────────────────────┼─────────┼────────────────┤
│ clab-workshop-orb-agent  │ linux                        │ running │ 172.24.0.100   │
│                          │ netboxlabs/orb-agent:develop │         │ N/A            │
├──────────────────────────┼──────────────────────────────┼─────────┼────────────────┤
│ clab-workshop-srl1       │ nokia_srlinux                │ running │ 172.24.0.101   │
│                          │ ghcr.io/nokia/srlinux:24.7.2 │         │ N/A            │
├──────────────────────────┼──────────────────────────────┼─────────┼────────────────┤
│ clab-workshop-srl2       │ nokia_srlinux                │ running │ 172.24.0.102   │
│                          │ ghcr.io/nokia/srlinux:24.7.2 │         │ N/A            │
├──────────────────────────┼──────────────────────────────┼─────────┼────────────────┤
│ clab-workshop-web-server │ linux                        │ running │ N/A            │
│                          │ nginx:alpine                 │         │ N/A            │
╰──────────────────────────┴──────────────────────────────┴─────────┴────────────────╯
```

## Manually Configuring the Network

Let's configure the network by manually configuring each device.

### Configuring srl1

> [!TIP]
> **Don't worry if you're unfamiliar with the Nokia SR Linux CLI.**
> All commands are provided below. Just copy and paste them carefully.

You should still be connected to `clab-workshop-srl1` from the previous step. If not, reconnect:

```bash
ssh admin@clab-workshop-srl1
```

> [!TIP]
> **Nokia SR Linux Credentials**
> - Username: `admin`
> - Password: `NokiaSrl1!`

Now let's configure it step by step.

#### Enter Configuration Mode

```bash
enter candidate
```

This enters candidate configuration mode, where changes are staged but not yet applied.

#### Configure the Default Network Instance

```bash
set / network-instance default type default
```

This creates a default VRF (Virtual Routing and Forwarding) instance.

#### Configure ethernet-1/1 (Transit Link to srl2)

```bash
set / interface ethernet-1/1 admin-state enable
set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.0.1/30
set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable
```

This configures:
- Interface: `ethernet-1/1`
- IP Address: `10.0.0.1/30`
- Purpose: Point-to-point link to srl2

#### Configure ethernet-1/2 (Stub Network)

```bash
set / interface ethernet-1/2 admin-state enable
set / interface ethernet-1/2 subinterface 0 ipv4 address 192.168.1.1/30
set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable
```

This configures a stub network (not used in this topology, but shown for completeness).

#### Add Interfaces to Network Instance

```bash
set / network-instance default interface ethernet-1/1.0
set / network-instance default interface ethernet-1/2.0
```

This associates the interfaces with the default network instance.

#### Configure OSPF

```bash
set / network-instance default protocols ospf instance main admin-state enable
set / network-instance default protocols ospf instance main version ospf-v2
set / network-instance default protocols ospf instance main router-id 1.1.1.1
```

This enables OSPF version 2 with router ID `1.1.1.1`.

#### Configure OSPF Interfaces

```bash
# Enable OSPF on ethernet-1/1 (transit link)
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/1.0 admin-state enable
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/1.0 interface-type point-to-point

# Enable OSPF on ethernet-1/2 (passive - advertise but don't form adjacencies)
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/2.0 admin-state enable
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/2.0 interface-type point-to-point
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/2.0 passive true
```

This:
- Adds both interfaces to OSPF Area 0
- Sets ethernet-1/1 as an active OSPF interface
- Sets ethernet-1/2 as passive (advertises the subnet but doesn't try to form OSPF adjacencies)

#### Commit the Configuration

```bash
commit now
```

This applies all the staged changes immediately.

> [!NOTE]
> If you made any typos, the commit will fail with an error message. You can use `discard` to abandon changes and start over.

Now exit srl1 by pressing `Ctrl+D`.

### Configuring srl2

Now let's configure the second router. Notice how similar (but not identical) the configuration is—a perfect recipe for copy-paste errors.

SSH into srl2:

> [!TIP]
> **Nokia SR Linux Credentials**
> - Username: `admin`
> - Password: `NokiaSrl1!`

```bash
ssh admin@clab-workshop-srl2
```

Now configure srl2:

#### Enter Configuration Mode

```bash
enter candidate
```

#### Configure the Default Network Instance

```bash
set / network-instance default type default
```

#### Configure ethernet-1/1 (Transit Link to srl1)

```bash
set / interface ethernet-1/1 admin-state enable
set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.0.2/30
set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable
```

This configures the other end of the transit link:
- IP Address: `10.0.0.2/30` (peer to srl1's 10.0.0.1)

#### Configure ethernet-1/2 (Web Server Network)

```bash
set / interface ethernet-1/2 admin-state enable
set / interface ethernet-1/2 subinterface 0 ipv4 address 192.168.2.1/30
set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable
```

This configures the connection to the web server:
- IP Address: `192.168.2.1/30` (web server is at 192.168.2.2)

#### Add Interfaces to Network Instance

```bash
set / network-instance default interface ethernet-1/1.0
set / network-instance default interface ethernet-1/2.0
```

#### Configure OSPF

```bash
set / network-instance default protocols ospf instance main admin-state enable
set / network-instance default protocols ospf instance main version ospf-v2
set / network-instance default protocols ospf instance main router-id 2.2.2.2
```

Note the different router ID: `2.2.2.2` (vs. `1.1.1.1` on srl1).

#### Configure OSPF Interfaces

```bash
# Enable OSPF on ethernet-1/1 (transit link)
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/1.0 admin-state enable
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/1.0 interface-type point-to-point

# Enable OSPF on ethernet-1/2 (passive - web server network)
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/2.0 admin-state enable
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/2.0 interface-type point-to-point
set / network-instance default protocols ospf instance main area 0.0.0.0 interface ethernet-1/2.0 passive true
```

The ethernet-1/2 interface is passive because the web server doesn't speak OSPF—we just want to advertise the 192.168.2.0/30 subnet.

#### Commit the Configuration

```bash
commit now
```

Great! Now srl2 is configured. Let's verify everything works.

## Verifying the Configuration

Now let's test that our manual configuration actually works.

### Test 1: Ping from srl2

You should still be connected to `clab-workshop-srl2`. Let's verify it can reach the web server directly:

```bash
ping -c 4 network-instance default 192.168.2.2
```

**Expected output:**

```bash
Using network instance default
PING 192.168.2.2 (192.168.2.2) 56(84) bytes of data.
64 bytes from 192.168.2.2: icmp_seq=1 ttl=64 time=3.62 ms
64 bytes from 192.168.2.2: icmp_seq=2 ttl=64 time=4.09 ms
64 bytes from 192.168.2.2: icmp_seq=3 ttl=64 time=1.89 ms
64 bytes from 192.168.2.2: icmp_seq=4 ttl=64 time=2.03 ms

--- 192.168.2.2 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss
```

✅ **Success!** srl2 can reach the web server (as expected, since they're directly connected).

Exit srl2 by pressing `Ctrl+D`.

### Test 2: Ping from srl1

Now for the real test: Can srl1 reach the web server through the OSPF-routed path?

SSH into srl1:

```bash
ssh admin@clab-workshop-srl1
```

Ping the web server:

```bash
ping -c 4 network-instance default 192.168.2.2
```

**Expected output:**

```bash
Using network instance default
PING 192.168.2.2 (192.168.2.2) 56(84) bytes of data.
64 bytes from 192.168.2.2: icmp_seq=1 ttl=63 time=2.09 ms
64 bytes from 192.168.2.2: icmp_seq=2 ttl=63 time=1.92 ms
64 bytes from 192.168.2.2: icmp_seq=3 ttl=63 time=1.49 ms
64 bytes from 192.168.2.2: icmp_seq=4 ttl=63 time=2.03 ms

--- 192.168.2.2 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss
```

✅ **Success!** srl1 can reach the web server via OSPF routing through srl2.

### Optional: Verify OSPF Neighbors

While still on srl1, you can verify OSPF is working:

```bash
show network-instance default protocols ospf neighbor
```

You should see srl2 (10.0.0.2) as a neighbor:

```bash
Net-Inst default OSPFv2 Instance main Neighbors
+---------------------------------------------------------------------------------------+
| Interface-Name         Rtr Id            State        Pri   RetxQ    Time Before Dead |
+=======================================================================================+
| ethernet-1/1.0         2.2.2.2           full         1     0        37               |
+---------------------------------------------------------------------------------------+
No. of Neighbors: 1
```

Exit srl1 by pressing `Ctrl+D`.

## Reflection: The Pain of Manual Configuration

Take a moment to think about what you just experienced:

### What Went Wrong (or Could Have)?

1. **Repetitive and Tedious**: You typed dozens of similar commands with slight variations. This is boring, time-consuming, and mentally draining.

2. **Error-Prone**: One typo—a wrong IP address, a mismatched subnet mask, an incorrect router ID—and the network breaks. Did you catch any mistakes?

3. **Not Scalable**: This was only **two devices**. Imagine doing this for 10, 50, or 500 devices. How long would it take? How many mistakes would you make?

4. **No Version Control**: Your configuration changes aren't tracked. If something breaks tomorrow, can you remember exactly what you configured today?

5. **No Validation**: You had to manually test with ping. What if there were more complex requirements? How would you verify everything works?

6. **Context Switching**: SSH into device 1, configure, exit. SSH into device 2, configure, exit. Each context switch slows you down and increases the chance of errors.

## What's Next?

In **Module 2**, you'll see how monitoring and alerting can detect issues automatically so you don't have to manually check every device after every change. This is the first step in building a self-correcting network.

---

**Continue to:** [Module 2 - Observability in Support of Network Automation](../module_2/README.md)
  