#!/usr/bin/env bash
# Demo 2, step 1 (Discover), real version: run the Orb agent once against the lab.
#
# Builds run/agent.yaml from the LAB_* settings in .env and starts netboxlabs/orb-agent in Docker.
#   LAB_DEVICE_HOST set   -> device discovery: logs in over SSH with NAPALM (driver LAB_DEVICE_DRIVER)
#   LAB_SNMP_TARGETS set  -> SNMP discovery (v2c, LAB_SNMP_COMMUNITY)
# The policy has no schedule, so it runs once when the agent starts. Results go through Diode;
# with Assurance on, they arrive as deviations. No lab reachable? Use ./4_discover_simulated.py.
#
#   ./4_discover_orb.sh          run the agent; press Ctrl+C once the results are in
#   ./4_discover_orb.sh --dry    write agent.yaml and show it, do not start the agent
set -euo pipefail
cd "$(dirname "$0")"
# load .env; it wins over the shell, so credentials exported for another NetBox or Diode cannot leak in.
# Split each line at the first "=" only: secrets can end in "=" (base64 padding), and read -r k v drops it.
while IFS= read -r line || [ -n "$line" ]; do
  [[ -z "$line" || "$line" == \#* || "$line" != *=* ]] && continue
  export "${line%%=*}=${line#*=}"
done < .env
export DIODE_CLIENT_ID DIODE_CLIENT_SECRET LAB_DEVICE_USERNAME LAB_DEVICE_PASSWORD LAB_SNMP_COMMUNITY 2>/dev/null || true

if [ -z "${LAB_DEVICE_HOST:-}" ] && [ -z "${LAB_SNMP_TARGETS:-}" ]; then
  echo "Set LAB_DEVICE_HOST (SSH) or LAB_SNMP_TARGETS (SNMP) in .env, or use ./4_discover_simulated.py"; exit 1
fi

mkdir -p run
# Written as commented YAML, so ./4_discover_orb.sh --dry is something to show and explain on screen.
# Values are quoted with json.dumps, which is valid YAML. Credentials stay as ${...} placeholders:
# the agent reads them from its environment, so the password is never written to disk.
.venv/bin/python - <<'PY' > run/agent.yaml
import json, os
E = os.environ.get
q = json.dumps
site, role, loc = E("LAB_SITE") or "NYC-DC1", E("LAB_ROLE") or "Access Switch", E("LAB_LOCATION")
L = []
w = L.append
w("# Orb agent configuration, written by 4_discover_orb.sh from .env. Show it with: ./4_discover_orb.sh --dry")
w("orb:")
w("  # Where the agent gets its policies: this file. The alternative is a Git repository.")
w("  config_manager:")
w("    active: local")
w("  backends:")
if E("LAB_DEVICE_HOST"):
    w("    # Device discovery: logs in to each device over SSH with NAPALM and reads it.")
    w("    device_discovery:")
if E("LAB_SNMP_TARGETS"):
    w("    # SNMP discovery: polls each target with SNMP (v1, v2c or v3).")
    w("    snmp_discovery:")
w("    # Shared by every backend: where the results go. Diode matches them against NetBox;")
w("    # with Assurance they arrive as deviations to review.")
w("    common:")
w("      diode:")
w(f"        target: {q(E('DIODE_TARGET'))}")
w("        # OAuth2 client credentials from NetBox > Diode > Client credentials, read from the environment.")
w("        client_id: ${DIODE_CLIENT_ID}")
w("        client_secret: ${DIODE_CLIENT_SECRET}")
w("        # The name this agent's data carries in Diode, and the source to filter by in Assurance.")
w(f"        agent_name: {q(E('AGENT_NAME') or 'webinar-agent')}")
w("  policies:")
if E("LAB_DEVICE_HOST"):
    drv = E("LAB_DEVICE_DRIVER") or "ios"
    w("    device_discovery:")
    w("      webinar_device:")
    w("        config:")
    w("          # No schedule: the policy runs once when the agent starts.")
    w('          # Add  schedule: "*/15 * * * *"  (cron) to repeat it.')
    w("          defaults:")
    w("            # A switch does not know its site, location or role, so the policy supplies them.")
    w(f"            site: {q(site)}")
    if loc:
        w(f"            location: {q(loc)}")
    w(f"            role: {q(role)}")
    w("            # Tags added to everything this policy finds.")
    w('            tags: ["webinar-demo"]')
    w("            # Interface type when none of the patterns below matches.")
    w('            if_type: "other"')
    w("            # Interface name (regular expression) to NetBox interface type.")
    w("            interface_patterns:")
    w('              - match: "^Ethernet[0-9]+/[0-9]+$"')
    w('                type: "1000base-t"')
    w('              - match: "^Loopback[0-9]+$"')
    w('                type: "virtual"')
    w("            # Interfaces to leave out entirely.")
    w('            interface_exclude_patterns: ["^Null[0-9]*$"]')
    w("            # Used for the device type and platform (the CML image does not report a real model).")
    w("            device:")
    w('              manufacturer: "Cisco"')
    w('              model: "IOL-XE"')
    w('              platform: "IOS-XE"')
    w("          options:")
    w("            # NAPALM drivers to try against each host.")
    w(f"            discovery_drivers: [{q(drv)}]")
    w("            # Do not read the running or startup configuration.")
    w("            capture_running_config: false")
    w("            capture_startup_config: false")
    w("            # No /32 prefixes for single addresses such as loopbacks.")
    w("            emit_host_prefixes: false")
    w("            # Do not scope the prefixes it derives to the default site.")
    w("            propagate_defaults_to_prefix_scope: false")
    w("            # Do not create VLAN placeholders for VLAN IDs the device only references.")
    w("            create_unknown_vlans: false")
    w("            # Do not read VRFs.")
    w("            discover_vrfs: false")
    w('            # Platform name without the software version, so it stays "IOS-XE" across upgrades.')
    w("            platform_omit_version: true")
    w("        scope:")
    w("          # One entry per device (a subnet or an IP range also works). Credentials come from the environment.")
    w(f"          - driver: {q(drv)}")
    w(f"            hostname: {q(E('LAB_DEVICE_HOST'))}")
    w("            # Seconds to wait for the device to answer.")
    w("            timeout: 90")
    w("            username: ${LAB_DEVICE_USERNAME}")
    w("            password: ${LAB_DEVICE_PASSWORD}")
if E("LAB_SNMP_TARGETS"):
    w("    snmp_discovery:")
    w("      webinar_snmp:")
    w("        config:")
    w("          # Seconds the whole policy may take.")
    w("          timeout: 300")
    w("          defaults:")
    w("            # SNMP does not tell NetBox the site, location or role either.")
    w(f"            site: {q(site)}")
    if loc:
        w(f"            location: {q(loc)}")
    w(f"            role: {q(role)}")
    w('            tags: ["webinar-demo"]')
    w("        scope:")
    w("          # Hosts, IP ranges or subnets to poll.")
    w("          targets:")
    for h in [h.strip() for h in E("LAB_SNMP_TARGETS").split(",") if h.strip()]:
        w(f"            - host: {q(h)}")
    w("          # SNMPv2c; the community string comes from the environment.")
    w("          authentication:")
    w('            protocol_version: "SNMPv2c"')
    w("            community: ${LAB_SNMP_COMMUNITY}")
print("\n".join(L))
PY

echo "== Demo 2 · 1 Discover: the Orb agent =="
echo; cat run/agent.yaml; echo
[ "${1:-}" = "--dry" ] && exit 0

docker info >/dev/null 2>&1 || { echo "Docker is not running. Start it, or use ./4_discover_simulated.py"; exit 1; }
echo "Starting the agent. Watch for the discovery and ingest lines, then open ${NETBOX_URL}/plugins/assurance/deviations/"
echo "Press Ctrl+C to stop it once the results are in."
exec docker run --rm -u root --name orb-webinar \
  -v "$PWD/run:/opt/orb/" \
  -e DIODE_CLIENT_ID -e DIODE_CLIENT_SECRET \
  -e LAB_DEVICE_USERNAME -e LAB_DEVICE_PASSWORD -e LAB_SNMP_COMMUNITY \
  netboxlabs/orb-agent:latest run -c /opt/orb/agent.yaml
