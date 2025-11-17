#!/usr/bin/env bash
set -euo pipefail

# Default branch to empty string
BRANCH_ID=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --branch)
      BRANCH_ID="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--branch BRANCH_SCHEMA_ID]"
      exit 1
      ;;
  esac
done

# If branch is not defined, ask for confirmation
if [ -z "$BRANCH_ID" ]; then
  echo "Warning: No branch specified. This will run against the main branch."
  read -p "Do you want to continue? (yes/no): " -r
  if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Aborted."
    exit 1
  fi
fi

# Check if required environment variables are set
REQUIRED_VARS=("MY_EXTERNAL_IP" "NETBOX_PORT" "NETBOX_TOKEN")

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    exit 1
  fi
done

# Run the ansible playbook
ansible-playbook \
  -i ansible/inventory.yaml \
  ansible/deploy-configs.yaml \
  -e "MY_EXTERNAL_IP=${MY_EXTERNAL_IP}" \
  -e "NETBOX_PORT=${NETBOX_PORT}" \
  -e "NETBOX_API_TOKEN=${NETBOX_TOKEN}" \
  -e "NETBOX_BRANCH_ID=${BRANCH_ID}"
  