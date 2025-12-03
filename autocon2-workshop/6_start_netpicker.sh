#!/bin/bash
set -euo pipefail

# Check if all required environment variables are set
REQUIRED_VARS=("MY_EXTERNAL_IP" "NETPICKER_PORT" "NETPICKER_API_PORT")

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    exit 0
  fi
done

echo
echo "--- Starting Netpicker ---"
echo

pushd netpicker
docker compose up -d
popd

echo
echo "--- Configuring Policies, Rules and Vault ---"
echo

pushd workshop_setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python netpicker/setup.py
deactivate
rm -fr venv/
popd

echo "you can get to netpicker on http://${MY_EXTERNAL_IP}:${NETPICKER_PORT}"
echo "username: admin@admin.com"
echo "password: 12345678"
