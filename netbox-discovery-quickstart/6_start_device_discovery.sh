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

WORKING_DIR="device_discovery"

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
    device_discovery:
    common:
      diode:
        target: grpc://${MY_EXTERNAL_IP}:8080/diode
        client_id: ${DIODE_CLIENT_ID}
        client_secret: ${DIODE_CLIENT_SECRET}
        agent_name: agent2
  policies:
    device_discovery:
      discovery_1:
        config:
          schedule: "* * * * *"
          defaults:
            site: New York NY
        scope:
          - driver: srl
            hostname: 172.24.0.100
            username: admin
            password: NokiaSrl1!
            optional_args:
               insecure: True
          - driver: srl
            hostname: 172.24.0.101
            username: admin
            password: NokiaSrl1!
            optional_args:
               insecure: True
EOF

cat agent.yaml

echo
echo "--- Adding SR Linux driver ---"
echo

cat <<EOF > drivers.txt
napalm-srl==1.0.5
EOF

echo
echo "--- Starting agent ---"
echo

docker run -v $(pwd):/opt/orb/ \
   -e DIODE_CLIENT_ID=${DIODE_CLIENT_ID} \
   -e DIODE_CLIENT_SECRET=${DIODE_CLIENT_SECRET} \
   -e INSTALL_DRIVERS_PATH=/opt/orb/drivers.txt \
   --network ${DOCKER_NETWORK} \
   netboxlabs/orb-agent:latest run -c /opt/orb/agent.yaml

# End
popd

echo "Now go and check the disocvered device details in NetBox: http://${MY_EXTERNAL_IP}:${NETBOX_PORT}/dcim/devices/"