#!/bin/bash
set -euo pipefail

# pushd to Slurpit directory
pushd slurpit

# Check if all required environment variables are set
REQUIRED_VARS=("MY_EXTERNAL_IP" "SLURPIT_PORT" "WORKSHOP_SUBNET" "NETBOX_PORT")

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    exit 0
  fi
done

echo
echo "--- Starting Slurpit ---"
echo

docker compose up -d

# Return to the original directory
popd

echo
echo "--- Configuring Finder and NetBox Plugin ---"
echo

pushd workshop_setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python slurpit/setup.py
deactivate
rm -fr venv/
popd

echo "You should be able to login to slurpit here: http://${MY_EXTERNAL_IP}:${SLURPIT_PORT}"
echo "username admin@admin.com"
echo "password 12345678"
