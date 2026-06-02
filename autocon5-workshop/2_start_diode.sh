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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIODE_TEMPLATE_DIR="${SCRIPT_DIR}/config-templates/diode"

mkdir -p diode/nginx
pushd diode

echo
echo "--- Copying pinned Diode configuration ---"
echo

cp "${DIODE_TEMPLATE_DIR}/docker-compose.yaml" docker-compose.yaml
cp "${DIODE_TEMPLATE_DIR}/nginx/nginx.conf"    nginx/nginx.conf

echo
echo "--- Running quickstart script to generate credentials and env ---"
echo

curl -sSfLo quickstart.sh https://raw.githubusercontent.com/netboxlabs/diode/release/diode-server/docker/scripts/quickstart.sh
chmod +x quickstart.sh
# Run quickstart for env/credential generation only — docker-compose.yaml is overwritten below
./quickstart.sh "http://${MY_EXTERNAL_IP}:${NETBOX_PORT}"
# Restore our pinned docker-compose (quickstart overwrites it)
cp "${DIODE_TEMPLATE_DIR}/docker-compose.yaml" docker-compose.yaml
cp "${DIODE_TEMPLATE_DIR}/nginx/nginx.conf"    nginx/nginx.conf

echo
echo "--- Bringing up Diode ---"
echo

docker compose up -d

# End
popd