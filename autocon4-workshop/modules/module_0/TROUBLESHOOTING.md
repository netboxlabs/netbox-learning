# Workshop Troubleshooting Guide

This guide helps you diagnose and fix common issues you might encounter during the workshop. Issues are organized by category and include step-by-step solutions.

## Quick Diagnostics

Credentials

**Nokia SR Linux Credentials**
- Username: `admin`
- Password: `NokiaSrl1!`


If something isn't working, start here:

```bash
# Check all containers are running
docker ps

# Check environment variables are set
echo $MY_EXTERNAL_IP

# Check ContainerLab network status
sudo clab inspect

# Check Orb agent logs
docker logs clab-workshop-orb-agent --tail 50
```

---

## Table of Contents

1. [Environment Setup Issues](#environment-setup-issues)
2. [Service Access Issues](#service-access-issues)
3. [ContainerLab Network Issues](#containerlab-network-issues)
4. [NetBox Issues](#netbox-issues)
5. [Discovery Issues](#discovery-issues)
6. [Ansible Deployment Issues](#ansible-deployment-issues)
7. [Observability Issues](#observability-issues)
8. [Gitea Issues](#gitea-issues)

---

## Environment Setup Issues

### Issue: `$MY_EXTERNAL_IP` is not set

**Symptoms:**
- Commands using `$MY_EXTERNAL_IP` return empty URLs
- Cannot access web interfaces

**Solution:**

```bash
# Set environment variables
source 1_set_envvars.sh

# Verify it's set
echo $MY_EXTERNAL_IP
```

**Expected output:** An IP address (e.g., `192.168.1.100`)

If still not set:

```bash
# Manually export your machine's IP
export MY_EXTERNAL_IP=<your-machine-ip>

# Example:
export MY_EXTERNAL_IP=192.168.1.100
```

> **Note:** Do NOT use `127.0.0.1` or `localhost` - use your actual network IP.

---

## Service Access Issues

### Issue: Cannot access NetBox web interface

**Symptoms:**
- Browser shows "Connection refused" or timeout
- URL `http://$MY_EXTERNAL_IP:8000` doesn't load

**Diagnosis:**

```bash
# Check if NetBox container is running
docker ps | grep netbox

# Check NetBox logs
docker logs netbox --tail 50
```

**Solution 1: NetBox not started**

```bash
# Start NetBox
./4_start_netbox.sh

# Wait 2-3 minutes for database migrations
# Check when ready
docker logs netbox --tail 20
```

**Solution 2: NetBox is starting (migrations running)**

NetBox runs database migrations on first startup. This can take 3-5 minutes.

```bash
# Watch the logs
docker logs netbox -f

# Look for: "Listening at: http://0.0.0.0:8080"
```

**Solution 3: Port conflict**

```bash
# Check if port 8000 is in use
sudo lsof -i :8000

# If another service is using it, stop that service
```

### Issue: Cannot access Prometheus

**Symptoms:**
- URL `http://$MY_EXTERNAL_IP:9090` doesn't load

**Diagnosis:**

```bash
# Check if Prometheus container is running
docker ps | grep prometheus

# Check Prometheus logs
docker logs prometheus --tail 50
```

**Solution:**

```bash
# Start Prometheus
./6_start_prometheus.sh

# Verify it's running
curl -s http://localhost:9090/-/healthy
```

**Expected output:** `Prometheus is Healthy.`

### Issue: Cannot access Gitea

**Symptoms:**
- URL `http://$MY_EXTERNAL_IP:3000` doesn't load

**Diagnosis:**

```bash
# Check if Gitea container is running
docker ps | grep gitea

# Check Gitea logs
docker logs gitea --tail 50
```

**Solution:**

```bash
# Start Gitea
./5_start_gitea.sh

# Wait 30-60 seconds, then verify
curl -s http://localhost:3000
```

---

## ContainerLab Network Issues

### Issue: ContainerLab devices not running

**Symptoms:**
- `sudo clab inspect` shows no devices
- Cannot SSH to devices
- Devices show as not running

**Diagnosis:**

```bash
# Check lab status
sudo clab inspect

# If no labs running:
sudo clab inspect --all
```

**Solution:**

```bash
# Start the network
./7_start_network.sh network/workshop.clab.yaml

# Verify devices are running
sudo clab inspect
```

**Expected output:**
```
╭──────────────────────────┬──────────────────────────────┬─────────┬────────────────╮
│           Name           │          Kind/Image          │  State  │ IPv4/6 Address │
├──────────────────────────┼──────────────────────────────┼─────────┼────────────────┤
│ clab-workshop-orb-agent  │ linux                        │ running │ 172.24.0.100   │
│ clab-workshop-srl1       │ nokia_srlinux                │ running │ 172.24.0.101   │
│ clab-workshop-srl2       │ nokia_srlinux                │ running │ 172.24.0.102   │
│ clab-workshop-web-server │ linux                        │ running │ N/A            │
╰──────────────────────────┴──────────────────────────────┴─────────┴────────────────╯
```

### Issue: Cannot SSH to SR Linux devices

**Symptoms:**
- SSH connection times out or refused
- `ssh admin@clab-workshop-srl1` fails

**Diagnosis:**

```bash
# Check if device container is running
docker ps | grep srl1

# Check device is reachable
ping -c 2 172.24.0.101

# Try to get device logs
docker logs clab-workshop-srl1 --tail 20
```

**Solution 1: Device not ready yet**

SR Linux devices take 30-60 seconds to fully boot after starting.

```bash
# Wait and retry
sleep 30
ssh admin@clab-workshop-srl1
```

**Solution 2: Correct SSH syntax**

```bash
# Use the full container name or IP
ssh admin@clab-workshop-srl1
# OR
ssh admin@172.24.0.101

# Password: NokiaSrl1!
```

**Solution 3: SSH key conflicts**

```bash
# Remove old SSH keys if you've rebuilt the lab
ssh-keygen -R clab-workshop-srl1
ssh-keygen -R 172.24.0.101

# Try connecting again
ssh admin@clab-workshop-srl1
```

### Issue: ContainerLab network won't start

**Symptoms:**
- `./7_start_network.sh` fails with errors
- Docker network conflicts

**Solution:**

```bash
# Clean up existing labs
sudo clab destroy --all --cleanup

# Remove Docker networks
docker network prune -f

# Restart the network
./7_start_network.sh network/workshop.clab.yaml
```

---

## NetBox Issues

### Issue: NetBox branch status stuck on "Provisioning"

**Symptoms:**
- Created a branch but status never changes to "Ready" or "Active"
- Branch is unusable

**Diagnosis:**

```bash
# Check NetBox logs for errors
docker logs netbox --tail 50 | grep -i error

# Check database connectivity
docker logs netbox-postgres --tail 20
```

**Solution:**

1. Wait 60-90 seconds and refresh the page
2. If still stuck after 2 minutes:

```bash
# Check NetBox background worker
docker logs netbox-worker --tail 50

# Restart NetBox services
docker restart netbox netbox-worker

# Wait 60 seconds, then refresh NetBox UI
```

### Issue: Cannot activate a branch

**Symptoms:**
- Click "Activate" but branch doesn't activate
- No branch indicator shown at top of NetBox

**Solution:**

1. Ensure branch status is "Ready" or "Active"
2. Refresh the NetBox page
3. Try activating again
4. Check browser console for JavaScript errors (F12)

### Issue: Rendered configs are empty or missing

**Symptoms:**
- Device shows "Render Config" tab but no content
- Expected configuration commands not appearing

**Diagnosis:**

Check what's missing:

1. Is the config template assigned to the device?
   - Navigate to device → Edit → Check "Config Template" field

2. Are interfaces and IPs configured?
   - Navigate to device → Interfaces tab
   - Check that child interfaces exist (e.g., `ethernet-1/1.0`)
   - Check that IPs are assigned to interfaces

3. Is the template correct?
   - Navigate to Provisioning → Config Templates
   - Check for syntax errors in the Jinja2 template

**Solution:**

```bash
# For Module 4a issues:
# 1. Ensure config template is assigned to device
# 2. Ensure child interfaces exist (e.g., ethernet-1/1.0)
# 3. Ensure IP addresses are assigned to child interfaces

# For Module 4b issues:
# 4. Ensure Config Context is created and assigned
# 5. Ensure Local Config Context Data is set on devices
# 6. Ensure tags are applied to interfaces
```

### Issue: Config Context not showing data

**Symptoms:**
- Device → Config Context tab shows empty `{}`
- Missing `ospf_area` or `router_id`

**Diagnosis:**

1. Check global Config Context:
   - Navigate to Provisioning → Config Contexts
   - Ensure "OSPF Area 0.0.0.0" exists
   - Check Assignment → Sites includes "Workshop"

2. Check local Config Context:
   - Navigate to device → Edit
   - Check "Local Config Context Data" field has JSON

**Solution:**

Re-create missing Config Context or Local Config Context Data (see Module 4b).

---

## Discovery Issues

### Issue: Discovery not running / No discovery results

**Symptoms:**
- Branch shows 0 "Changes Ahead"
- No devices discovered after several minutes
- Orb agent not discovering devices

**Diagnosis:**

```bash
# Check Orb agent is running
docker ps | grep orb-agent

# Check Orb agent logs for errors
docker logs clab-workshop-orb-agent --tail 100

# Look for discovery-related messages
docker logs clab-workshop-orb-agent | grep -i discovery
```

**Solution 1: Discovery not enabled**

Verify the `selector.yaml` in Gitea has `srlinux_discovery` enabled:

```yaml
srlinux_discovery:
  selector:
    agent_name: orb-agent
  policies:
    srl_devices:
      path: srl_devices.yaml
      enabled: true    # Must be true!
```

**Solution 2: Orb agent not polling Gitea**

```bash
# Check Orb agent can reach Gitea
docker exec clab-workshop-orb-agent curl -s http://gitea:3000

# Restart Orb agent to force re-sync
docker restart clab-workshop-orb-agent

# Watch logs
docker logs clab-workshop-orb-agent -f
```

**Solution 3: Diode not configured correctly**

1. In NetBox, navigate to Diode → Settings
2. Ensure the correct branch is selected
3. Ensure Diode URL and API key are configured
4. Click Save

**Solution 4: Devices not reachable from Orb agent**

```bash
# Test connectivity from Orb agent to devices
docker exec clab-workshop-orb-agent ping -c 2 172.24.0.101
docker exec clab-workshop-orb-agent ping -c 2 172.24.0.102

# If ping fails, check network connectivity
docker network inspect autocon4-workshop
```

### Issue: Discovery results not appearing in branch

**Symptoms:**
- Orb logs show discovery running
- But NetBox branch shows 0 changes

**Diagnosis:**

```bash
# Check Diode logs
docker logs diode --tail 100

# Look for ingestion errors
docker logs diode | grep -i error
```

**Solution:**

1. Verify Diode configuration in NetBox
2. Check Diode has correct API token
3. Restart Diode:

```bash
docker restart diode

# Wait 30 seconds, then re-trigger discovery
```

---

## Ansible Deployment Issues

### Issue: Ansible deployment fails

**Symptoms:**
- `./run_ansible.sh` fails with errors
- Devices show as unreachable
- Tasks fail

**Diagnosis:**

Look at the error output carefully. Common issues:

**Error: "Could not fetch rendered config from NetBox"**

```bash
# Check NetBox is accessible
curl -s http://localhost:8000/api/

# Check branch ID is correct
# In NetBox, verify the SCHEMA ID matches what you used
```

**Error: "unreachable=2"**

Devices cannot be reached via SSH.

```bash
# Test SSH manually
ssh admin@172.24.0.101
# Password: NokiaSrl1!

# If SSH fails, check device status
docker ps | grep srl
sudo clab inspect
```

**Error: "Authentication failed"**

```bash
# Verify SSH credentials are correct
# Default password: NokiaSrl1!

# Check if devices have different credentials
docker exec clab-workshop-srl1 cat /etc/ssh/sshd_config
```

**Solution:**

```bash
# For most Ansible issues:
# 1. Verify all containers are running: docker ps
# 2. Verify environment variables: echo $MY_EXTERNAL_IP
# 3. Verify devices are reachable: ping 172.24.0.101
# 4. Verify SSH works: ssh admin@172.24.0.101
# 5. Check NetBox branch exists and has rendered configs
```

### Issue: Ansible says "changed=0" but should have deployed

**Symptoms:**
- Ansible completes but shows no changes
- Configurations not actually applied

**Diagnosis:**

This might be correct! Ansible is idempotent. If the configuration is already applied, it won't make changes.

```bash
# Check current device configuration
ssh admin@clab-workshop-srl1
show running-config
exit
```

**If configuration should be different:**

1. Check rendered config in NetBox matches what you expect
2. Verify you're deploying from the correct branch
3. Check Ansible playbook is fetching latest config

---

## Observability Issues

### Issue: Prometheus alerts not showing or stuck

**Symptoms:**
- WebServer_NotReachable alert missing
- Alert not changing color (green/red)
- No alerts visible

**Diagnosis:**

```bash
# Check Prometheus is running
docker ps | grep prometheus

# Check Prometheus configuration
curl -s http://localhost:9090/api/v1/status/config

# Check targets are being scraped
curl -s http://localhost:9090/api/v1/targets
```

**Solution 1: Alert not configured**

```bash
# Check alert rules are loaded
# In Prometheus UI: Status → Rules

# If no rules, check Prometheus config mounted correctly
docker inspect prometheus | grep -i volume
```

**Solution 2: Metrics not being collected**

```bash
# Check Orb agent is exposing metrics
docker exec clab-workshop-orb-agent curl -s http://localhost:8080/metrics

# Check Prometheus can scrape Orb agent
curl -s http://localhost:9090/api/v1/targets | grep orb
```

**Solution 3: Alert evaluation delay**

Prometheus evaluates alerts periodically (every 30-60 seconds). Wait 2-3 minutes and refresh.

### Issue: Prometheus shows "WebServer_NotReachable" is red but network works

**Symptoms:**
- Can ping web server from devices
- But alert still firing

**Diagnosis:**

The Orb agent performs HTTP checks, not just ping.

```bash
# Test HTTP from Orb agent perspective
docker exec clab-workshop-orb-agent curl -v http://192.168.2.2

# Check Orb agent routing
docker exec clab-workshop-orb-agent ip route
```

**Solution:**

Orb agent needs routing to reach the web server. If OSPF is not configured or interfaces are down, HTTP checks will fail even if direct ping works from devices.

---

## NetBox Issues

### Issue: Diode settings not saving

**Symptoms:**
- Select branch in Diode settings
- Click Save but branch doesn't persist

**Solution:**

```bash
# Check Diode container is running
docker ps | grep diode

# Restart Diode
docker restart diode

# Wait 30 seconds, try again in NetBox UI
```

### Issue: Changes not appearing in branch

**Symptoms:**
- Made changes in NetBox
- Branch doesn't show changes
- Changes Ahead count is 0

**Diagnosis:**

1. Verify you've activated the branch
   - Look for branch indicator at top of NetBox UI
   - Should show branch name (e.g., "Module 4 SRL Config")

2. Ensure you're not on main branch
   - Check branch dropdown at top

**Solution:**

1. Navigate to Branching → Branches
2. Click on your branch
3. Click "Activate"
4. Make changes again

---

## Discovery Issues

### Issue: Discovery takes too long or never completes

**Symptoms:**
- Enabled discovery in Gitea
- After 5+ minutes, still no results

**Diagnosis:**

```bash
# Check Orb agent logs for discovery activity
docker logs clab-workshop-orb-agent --tail 100 | grep -i discovery

# Check for errors
docker logs clab-workshop-orb-agent | grep -i error
```

**Common errors and solutions:**

**Error: "Failed to connect to device"**

```bash
# Test connectivity from Orb agent
docker exec clab-workshop-orb-agent ping -c 2 172.24.0.101

# Test SSH from Orb agent
docker exec clab-workshop-orb-agent ssh -o StrictHostKeyChecking=no admin@172.24.0.101
# Should prompt for password
```

**Error: "Authentication failed"**

Check the discovery policy has correct credentials:
1. In Gitea, open `srl_devices.yaml`
2. Verify username and password match device credentials

**Solution: Force discovery to re-run**

```bash
# In Gitea, edit srl_devices.yaml
# Increment the version number on line 1
# Example: #--- version: 1 → #--- version: 2

# Commit the change

# Wait 30 seconds, check Orb logs
docker logs clab-workshop-orb-agent --tail 50
```

### Issue: Discovery finds fewer objects than expected

**Symptoms:**
- Discovery completes but only shows 50 changes instead of 366
- Missing devices or interfaces

**Diagnosis:**

This might be correct if:
- Only one device is reachable
- Devices are not fully configured
- Discovery is still running (wait longer)

**Solution:**

```bash
# Wait longer - discovery can take 2-3 minutes
# Keep refreshing the NetBox branch page

# If still incomplete after 5 minutes:
# Check Orb agent logs
docker logs clab-workshop-orb-agent --tail 200

# Look for errors connecting to specific devices
```

---

## Gitea Issues

### Issue: Orb agent not picking up Gitea policy changes

**Symptoms:**
- Changed `selector.yaml` in Gitea
- Orb agent doesn't react
- Discovery doesn't start

**Diagnosis:**

```bash
# Check Orb agent is polling Gitea
docker logs clab-workshop-orb-agent | grep -i git

# Check Orb agent can reach Gitea
docker exec clab-workshop-orb-agent curl -s http://gitea:3000
```

**Solution:**

```bash
# Restart Orb agent to force policy sync
docker restart clab-workshop-orb-agent

# Watch logs to see it pick up policies
docker logs clab-workshop-orb-agent -f

# Look for: "Successfully fetched policies from Git"
```

### Issue: Cannot commit changes in Gitea

**Symptoms:**
- Edit file in Gitea
- "Commit Changes" button doesn't work or shows error

**Solution:**

1. Ensure you're logged in to Gitea
2. Ensure you have write permissions (you should as admin)
3. Try refreshing the Gitea page
4. Clear browser cache

---

## General Troubleshooting Steps

### Complete System Reset

If everything is broken and you need to start fresh:

```bash
# Stop everything
sudo clab destroy --all --cleanup
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)

# Clean Docker networks
docker network prune -f

# Restart from scratch
source 1_set_envvars.sh
./2_start_diode.sh
source ./3_set_diode_creds.sh
./4_start_netbox.sh
./5_start_gitea.sh
./6_start_prometheus.sh
./7_start_network.sh network/workshop.clab.yaml
```

> **Warning:** This deletes all data and configurations. Use only as last resort.

### Check All Services Health

```bash
# Create a health check script
cat > check_health.sh << 'EOF'
#!/bin/bash
echo "Checking Workshop Environment Health..."
echo

echo "1. Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "netbox|diode|prometheus|gitea|orb|srl|web"
echo

echo "2. Environment Variables:"
echo "MY_EXTERNAL_IP: $MY_EXTERNAL_IP"
echo

echo "3. ContainerLab Status:"
sudo clab inspect 2>/dev/null || echo "No labs running"
echo

echo "4. Service Accessibility:"
echo -n "NetBox: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 && echo " ✓" || echo " ✗"
echo -n "Prometheus: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:9090 && echo " ✓" || echo " ✗"
echo -n "Gitea: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 && echo " ✓" || echo " ✗"
echo

echo "5. Device Connectivity:"
echo -n "srl1: "
ping -c 1 -W 1 172.24.0.101 >/dev/null 2>&1 && echo "✓" || echo "✗"
echo -n "srl2: "
ping -c 1 -W 1 172.24.0.102 >/dev/null 2>&1 && echo "✓" || echo "✗"
EOF

chmod +x check_health.sh
./check_health.sh
```

---

## Getting Help

If you've tried the troubleshooting steps above and still have issues:

### 1. Collect Diagnostic Information

```bash
# Gather logs
mkdir -p /tmp/workshop-debug
docker ps > /tmp/workshop-debug/containers.txt
docker logs netbox > /tmp/workshop-debug/netbox.log 2>&1
docker logs clab-workshop-orb-agent > /tmp/workshop-debug/orb-agent.log 2>&1
docker logs diode > /tmp/workshop-debug/diode.log 2>&1
sudo clab inspect > /tmp/workshop-debug/clab-status.txt 2>&1

# Create archive
tar -czf workshop-debug.tar.gz -C /tmp workshop-debug/

echo "Debug info saved to: workshop-debug.tar.gz"
```

### 2. Ask Workshop Facilitators

Provide:
- Which module you're working on
- What you were trying to do
- The exact error message
- Output from the diagnostic commands above

### 3. Check Workshop Repository

- [GitHub Issues](https://github.com/netboxlabs/netbox-learning/issues)
- Workshop README for additional notes

---

## Common Command Reference

Quick reference for frequently used commands:

```bash
# Environment
source 1_set_envvars.sh                    # Set environment variables
echo $MY_EXTERNAL_IP                       # Check your IP

# Services
docker ps                                   # List running containers
docker logs <container-name>               # View container logs
docker restart <container-name>            # Restart a container

# ContainerLab
sudo clab inspect                          # Check lab status
sudo clab destroy --all --cleanup          # Clean up labs
./7_start_network.sh network/workshop.clab.yaml  # Start network

# SSH to devices
ssh admin@clab-workshop-srl1              # Password: NokiaSrl1!
ssh admin@172.24.0.101                    # Alternative using IP

# Service URLs
echo "NetBox:     http://$MY_EXTERNAL_IP:8000"
echo "Prometheus: http://$MY_EXTERNAL_IP:9090"
echo "Gitea:      http://$MY_EXTERNAL_IP:3000"
```

---

## Prevention Tips

Avoid common issues:

1. **Always source environment variables** when opening a new terminal session
2. **Wait for services to fully start** (especially NetBox - takes 3-5 minutes first time)
3. **Refresh NetBox UI** after creating/merging branches
4. **Check branch is activated** before making NetBox changes
5. **Verify rendered configs** before running Ansible deployments
6. **Use correct credentials** (different for each service)
7. **Don't use `127.0.0.1`** for `MY_EXTERNAL_IP` (use actual network IP)

---

**Last Updated:** 2025-11-14
