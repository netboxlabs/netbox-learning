#!/bin/bash
set -euo pipefail

# Check if all required environment variables are set
REQUIRED_VARS=("DOCKER_NETWORK" "DOCKER_SUBNET")

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

# Check if directory parameter is passed
if [ $# -eq 0 ]; then
  echo "Usage: $0 <network_directory>/<srl|ios>.clab.yml"
  exit 1
fi

CLAB_FILE="$1"

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

# Starting network
echo
echo "--- Starting network from '$CLAB_FILE' ---"
echo

sudo clab deploy --topo "$CLAB_FILE" "${@:2}"
