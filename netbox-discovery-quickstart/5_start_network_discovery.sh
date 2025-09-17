#!/bin/bash
set -euo pipefail

# Check if all required environment variables are set
REQUIRED_VARS=("MY_EXTERNAL_IP" "DOCKER_SUBNET" "DOCKER_NETWORK" "NETBOX_PORT" "DIODE_CLIENT_ID" "DIODE_CLIENT_SECRET")

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    exit 0
  fi
done

WORKING_DIR="network_discovery"

# Remove config directory if it exists
sudo rm -fr ${WORKING_DIR}

# Recreate it and pushd in
mkdir ${WORKING_DIR}
pushd ${WORKING_DIR}

echo
echo "--- Writing agent config ---"
echo

cat <<EOF > agent.yaml
orb:
  config_manager:
    active: local
  backends:
    network_discovery:
    common:
      diode:
        target: grpc://${MY_EXTERNAL_IP}:8080/diode
        client_id: ${DIODE_CLIENT_ID}
        client_secret: ${DIODE_CLIENT_SECRET}
        agent_name: agent1
  policies:
    network_discovery:
      loopback_policy:
        config:
        scope:
          targets: 
            - ${DOCKER_SUBNET}
EOF

cat agent.yaml

echo
echo "--- Start the agent ---"
echo

docker run -v $(pwd):/opt/orb/ \
   -e DIODE_CLIENT_ID=${DIODE_CLIENT_ID} \
   -e DIODE_CLIENT_SECRET=${DIODE_CLIENT_SECRET} \
   --network ${DOCKER_NETWORK} \
   netboxlabs/orb-agent:latest run -c /opt/orb/agent.yaml

# End
popd

echo "Now go and check the discovered IPs in NetBox: http://${MY_EXTERNAL_IP}:${NETBOX_PORT}/ipam/ip-addresses/"