#!/bin/bash
set -euo pipefail

# Check if all required environment variables are set
REQUIRED_VARS=("INFRA_IP" "DOCKER_SUBNET" "DOCKER_NETWORK" "DIODE_PORT" "DIODE_CLIENT_SECRET" "DIODE_CLIENT_ID")

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
        target: grpc://${INFRA_IP}:${DIODE_PORT}/diode
        client_id: ${DIODE_CLIENT_ID}
        client_secret: ${DIODE_CLIENT_SECRET}
        agent_name: network-discovery
  policies:
    network_discovery:
      policy_1:
        config:
          timeout: 5
        scope:
          targets: [${DOCKER_SUBNET}]
EOF

cat agent.yaml

echo
echo "--- Start the agent ---"
echo

docker run -v $(pwd):/opt/orb/ \
   -e DIODE_CLIENT_SECRET=${DIODE_CLIENT_SECRET} \
   --network ${DOCKER_NETWORK} \
   mrmrcoleman/orb-agent:with_ccc run -c /opt/orb/agent.yaml

# End
popd

echo "Now go and check out NetBox Assurance: http://${INFRA_IP}:${NETBOX_PORT}/netbox/"