#!/usr/bin/env bash
set -euo pipefail

# Detect OS (macOS vs Linux)
OS_TYPE=$(uname)

# Ensure required environment variables are set
REQUIRED_VARS=("MY_EXTERNAL_IP" "NETBOX_PORT")

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    exit 1
  fi
done

mkdir -p diode
pushd diode

echo
echo "--- Downloading and preparing quickstart script ---"
echo

curl -sSfLo quickstart.sh https://raw.githubusercontent.com/netboxlabs/diode/release/diode-server/docker/scripts/quickstart.sh
chmod +x quickstart.sh

echo
echo "--- Running quickstart script pointing at NetBox at http://${MY_EXTERNAL_IP}:${NETBOX_PORT} ---"
echo

./quickstart.sh "http://${MY_EXTERNAL_IP}:${NETBOX_PORT}"

echo
echo "--- Bringing up Diode ---"
echo

docker compose up -d

# End
popd