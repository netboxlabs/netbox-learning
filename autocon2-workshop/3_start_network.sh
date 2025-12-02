#!/bin/bash
set -euo pipefail

# Check if directory parameter is passed
if [ $# -eq 0 ]; then
  echo "Usage: $0 <network_directory>"
  exit 1
fi

NETWORK_DIR="$1"

# Check if the specified directory exists
if [ ! -d "$NETWORK_DIR" ]; then
  echo "Error: Directory '$NETWORK_DIR' does not exist."
  exit 1
fi

TOPOLOGY_FILENAME="autocon2.clab.yml"
TOPOLOGY_FILE_PATH="$NETWORK_DIR/$TOPOLOGY_FILENAME"

# Check if the topology file exists in the specified directory
if [ ! -f "$TOPOLOGY_FILE_PATH" ]; then
  echo "Error: Topology file '$TOPOLOGY_FILENAME' not found in '$NETWORK_DIR'."
  exit 1
fi

# Prompt user for confirmation
#echo
#read -p "This will destroy all existing containerlab labs. Are you sure? (y/n): " confirm
#if [[ "$confirm" != "y" ]]; then
#  echo "Aborting."
#  exit 0
#fi

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
echo "--- Starting network from '$NETWORK_DIR' ---"
echo

pushd "$NETWORK_DIR" > /dev/null
sudo clab deploy --topo "$TOPOLOGY_FILENAME" "${@:2}"
popd > /dev/null