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
# load .env; it wins over the shell, so credentials exported for another NetBox or Diode cannot leak in
while IFS='=' read -r k v; do
  [[ -z "$k" || "$k" == \#* ]] && continue
  export "$k=$v"
done < .env
export DIODE_CLIENT_ID DIODE_CLIENT_SECRET LAB_DEVICE_USERNAME LAB_DEVICE_PASSWORD LAB_SNMP_COMMUNITY 2>/dev/null || true

if [ -z "${LAB_DEVICE_HOST:-}" ] && [ -z "${LAB_SNMP_TARGETS:-}" ]; then
  echo "Set LAB_DEVICE_HOST (SSH) or LAB_SNMP_TARGETS (SNMP) in .env, or use ./4_discover_simulated.py"; exit 1
fi

mkdir -p run
# JSON is valid YAML, and writing it from Python quotes every value correctly.
# Credentials stay as ${...} placeholders: the agent reads them from its environment.
.venv/bin/python - <<'PY' > run/agent.yaml
import json, os
E = os.environ.get
defaults = {"site": E("LAB_SITE") or "NYC-DC1", "role": E("LAB_ROLE") or "Access Switch", "tags": ["webinar-demo"]}
if E("LAB_LOCATION"):
    defaults["location"] = E("LAB_LOCATION")
backends, policies = {}, {}
if E("LAB_DEVICE_HOST"):
    backends["device_discovery"] = None
    policies["device_discovery"] = {"webinar_device": {
        "config": {
            "defaults": {**defaults,
                "if_type": "other",
                "interface_patterns": [{"match": "^Ethernet[0-9]+/[0-9]+$", "type": "1000base-t"},
                                       {"match": "^Loopback[0-9]+$", "type": "virtual"}],
                "interface_exclude_patterns": ["^Null[0-9]*$"],
                "device": {"manufacturer": "Cisco", "model": "IOL-XE", "platform": "IOS-XE"}},
            "options": {"discovery_drivers": [E("LAB_DEVICE_DRIVER") or "ios"],
                        "capture_running_config": False, "capture_startup_config": False,
                        "emit_host_prefixes": False, "propagate_defaults_to_prefix_scope": False,
                        "create_unknown_vlans": False, "discover_vrfs": False, "platform_omit_version": True}},
        "scope": [{"driver": E("LAB_DEVICE_DRIVER") or "ios", "hostname": E("LAB_DEVICE_HOST"), "timeout": 90,
                   "username": "${LAB_DEVICE_USERNAME}", "password": "${LAB_DEVICE_PASSWORD}"}]}}
if E("LAB_SNMP_TARGETS"):
    backends["snmp_discovery"] = None
    policies["snmp_discovery"] = {"webinar_snmp": {
        "config": {"timeout": 300, "defaults": defaults},
        "scope": {"targets": [{"host": h.strip()} for h in E("LAB_SNMP_TARGETS").split(",") if h.strip()],
                  "authentication": {"protocol_version": "SNMPv2c", "community": "${LAB_SNMP_COMMUNITY}"}}}}
backends["common"] = {"diode": {"target": E("DIODE_TARGET"), "client_id": "${DIODE_CLIENT_ID}",
                                "client_secret": "${DIODE_CLIENT_SECRET}", "agent_name": E("AGENT_NAME") or "webinar-agent"}}
print(json.dumps({"orb": {"config_manager": {"active": "local"}, "backends": backends, "policies": policies}}, indent=2))
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
