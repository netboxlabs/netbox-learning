#!/usr/bin/env bash
set -euo pipefail

# Detect OS (macOS vs Linux)
OS_TYPE=$(uname)

# Ensure required environment variables are set
REQUIRED_VARS=("MY_EXTERNAL_IP" "NETBOX_PORT" "DIODE_TO_NETBOX_API_KEY" "DIODE_API_KEY" "NETBOX_TO_DIODE_API_KEY" "INGESTER_TO_RECONCILER_API_KEY")

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    exit 1
  fi
done

mkdir -p diode
pushd diode

echo
echo "--- Fetching Diode docker-compose and .env files ---"
echo

curl -o docker-compose.yaml https://raw.githubusercontent.com/netboxlabs/diode/release/diode-server/docker/docker-compose.yaml
curl -o .env https://raw.githubusercontent.com/netboxlabs/diode/release/diode-server/docker/sample.env

echo
echo "--- Updating Diode .env file ---"
echo

# Set correct sed syntax based on OS
if [[ "$OS_TYPE" == "Darwin" ]]; then
  SED_CMD="sed -i ''"
else
  SED_CMD="sed -i"
fi

$SED_CMD "s|\(NETBOX_DIODE_PLUGIN_API_BASE_URL=http://\).*|\1${MY_EXTERNAL_IP}:${NETBOX_PORT}/api/plugins/diode|" .env
$SED_CMD "s|^\(DIODE_TO_NETBOX_API_KEY=\).*|\1${DIODE_TO_NETBOX_API_KEY}|" .env
$SED_CMD "s|^\(DIODE_API_KEY=\).*|\1${DIODE_API_KEY}|" .env
$SED_CMD "s|^\(NETBOX_TO_DIODE_API_KEY=\).*|\1${NETBOX_TO_DIODE_API_KEY}|" .env
$SED_CMD "s|^\(INGESTER_TO_RECONCILER_API_KEY=\).*|\1${INGESTER_TO_RECONCILER_API_KEY}|" .env

cat .env

echo
echo "--- Starting Diode ---"
echo

docker compose up -d

# End
popd