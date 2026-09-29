#!/usr/bin/env bash
# Demo 2, step 1 (Discover), real version: run the Orb agent once against the lab.
#
# Writes run/agent.yaml from the LAB_* settings in .env, then starts netboxlabs/orb-agent in Docker
# with an SNMP discovery policy and, if LAB_NETWORK_TARGETS is set, a network (NMAP) policy.
# Results go through Diode, so with Assurance on they arrive as deviations.
# No lab reachable? Use ./4_discover_simulated.py instead.
#
#   ./4_discover_orb.sh          run until you press Ctrl+C (the policies run once at start)
#   ./4_discover_orb.sh --dry    write agent.yaml and show it, do not start the agent
set -euo pipefail
cd "$(dirname "$0")"
# load .env, keeping anything already set in the shell (same rule as common.py)
while IFS='=' read -r k v; do
  [[ -z "$k" || "$k" == \#* ]] && continue
  [ -z "${!k:-}" ] && export "$k=$v"
done < .env
export DIODE_CLIENT_ID DIODE_CLIENT_SECRET

: "${LAB_SNMP_TARGETS:?Set LAB_SNMP_TARGETS in .env, for example 10.0.0.1,10.0.0.2 or 10.0.0.0/28}"
export LAB_SNMP_COMMUNITY="${LAB_SNMP_COMMUNITY:-public}"
LAB_SITE="${LAB_SITE:-NYC-DC1}"
AGENT_NAME="${AGENT_NAME:-webinar-agent}"

mkdir -p run
{
  echo "orb:"
  echo "  config_manager:"
  echo "    active: local"
  echo "  backends:"
  echo "    snmp_discovery:"
  [ -n "${LAB_NETWORK_TARGETS:-}" ] && echo "    network_discovery:"
  echo "    common:"
  echo "      diode:"
  echo "        target: ${DIODE_TARGET}"
  echo "        client_id: \${DIODE_CLIENT_ID}"
  echo "        client_secret: \${DIODE_CLIENT_SECRET}"
  echo "        agent_name: ${AGENT_NAME}"
  echo "  policies:"
  echo "    snmp_discovery:"
  echo "      webinar_snmp:"
  echo "        config:"
  echo "          timeout: 300"
  echo "          defaults:"
  echo "            site: ${LAB_SITE}"
  echo "            tags: [webinar-demo]"
  echo "        scope:"
  echo "          targets:"
  IFS=',' read -ra T <<< "$LAB_SNMP_TARGETS"; for t in "${T[@]}"; do echo "            - host: \"${t// /}\""; done
  echo "          authentication:"
  echo "            protocol_version: \"SNMPv2c\""
  echo "            community: \"\${LAB_SNMP_COMMUNITY}\""
  if [ -n "${LAB_NETWORK_TARGETS:-}" ]; then
    echo "    network_discovery:"
    echo "      webinar_sweep:"
    echo "        config:"
    echo "          defaults:"
    echo "            tags: [webinar-demo]"
    echo "        scope:"
    echo "          targets: [${LAB_NETWORK_TARGETS}]"
  fi
} > run/agent.yaml

echo "== Demo 2 · 1 Discover: the Orb agent =="
echo; cat run/agent.yaml; echo
[ "${1:-}" = "--dry" ] && exit 0

docker info >/dev/null 2>&1 || { echo "Docker is not running. Start it, or use ./4_discover_simulated.py"; exit 1; }
echo "Starting the agent. Watch for 'ingest' lines, then open ${NETBOX_URL}/plugins/assurance/deviations/"
echo "Press Ctrl+C to stop it once the results are in."
exec docker run --rm -u root --name orb-webinar \
  -v "$PWD/run:/opt/orb/" \
  -e DIODE_CLIENT_ID -e DIODE_CLIENT_SECRET -e LAB_SNMP_COMMUNITY \
  netboxlabs/orb-agent:latest run -c /opt/orb/agent.yaml
