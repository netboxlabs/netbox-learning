#!/bin/bash
set -euo pipefail

# Check if clab.yaml file path is provided
if [ $# -eq 0 ]; then
    echo "Error: No clab.yaml file path provided."
    echo "Usage: $0 <path-to-clab.yaml> [additional-clab-args]"
    exit 1
fi

CLAB_FILE="$1"
shift  # Remove the first argument so we can pass the rest to clab deploy

# Check if all required environment variables are set
REQUIRED_VARS=("DOCKER_NETWORK" "DOCKER_SUBNET")

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    echo "Please run: source ./1_set_envvars.sh"
    exit 1
  fi
done

# Create the docker network if it doesn't already exist
if ! docker network inspect "$DOCKER_NETWORK" &>/dev/null; then
    echo "Creating Docker network: $DOCKER_NETWORK with subnet: $DOCKER_SUBNET"
    docker network create \
        --driver=bridge \
        --subnet="$DOCKER_SUBNET" \
        "$DOCKER_NETWORK"
else
    echo "Docker network '$DOCKER_NETWORK' already exists."
fi

# Check if the specified clab file exists
if [ ! -f "$CLAB_FILE" ]; then
  echo "Error: File '$CLAB_FILE' does not exist."
  exit 1
fi

# Destroy all existing containerlab labs
echo
echo "--- Destroying all existing labs ---"
echo

set +e  # Temporarily disable exit on error
sudo clab destroy --all --cleanup
DESTROY_EXIT_CODE=$?
set -e  # Re-enable exit on error

if [ $DESTROY_EXIT_CODE -ne 0 ]; then
  echo "Warning: No existing labs were destroyed or an error occurred."
fi

# Restore ownership of the network directory after container teardown
# (ContainerLab may leave files owned by root that the admin user can't overwrite)
sudo chown -R "$(whoami):" "./network" 2>/dev/null || true

# Create the Orb env file
./create_orb_env_file.sh

# Starting network
echo
echo "--- Starting network from '$CLAB_FILE' ---"
echo

sudo clab deploy --reconfigure --topo "$CLAB_FILE" "$@"

# Verify SR Linux JSON-RPC API is reachable on both nodes
echo
echo "--- Verifying SR Linux JSON-RPC API (port 443) ---"
echo

SRL_NODES=("172.24.0.101" "172.24.0.102")
SRL_NAMES=("srl1" "srl2")
TIMEOUT=60
ALL_OK=true

for i in "${!SRL_NODES[@]}"; do
  IP="${SRL_NODES[$i]}"
  NAME="${SRL_NAMES[$i]}"
  echo -n "Waiting for $NAME ($IP) port 443"
  ELAPSED=0
  OK=false
  while [ $ELAPSED -lt $TIMEOUT ]; do
    if nc -zw2 "$IP" 443 &>/dev/null; then
      echo " ✓"
      OK=true
      break
    fi
    echo -n "."
    sleep 2
    ELAPSED=$((ELAPSED + 2))
  done
  if [ "$OK" = false ]; then
    echo " ✗ TIMED OUT"
    ALL_OK=false
  fi
done

if [ "$ALL_OK" = false ]; then
  echo
  echo "WARNING: One or more SR Linux nodes did not expose their JSON-RPC API within ${TIMEOUT}s."
  echo "EDA playbooks and Ansible tasks will fail until port 443 is reachable."
  echo "Try re-running this script: $0 $CLAB_FILE"
  exit 1
fi

echo
echo "✅ Network is up. SR Linux JSON-RPC API is reachable on all nodes."
echo