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
echo "--- Running quickstart script ---"
echo

./quickstart.sh "http://${MY_EXTERNAL_IP}"

echo
echo "--- Bringing up Diode ---"
echo

docker compose up -d

echo
echo "--- Extracting netbox-to-diode client secret ---"
echo

jq -r '.[] | select(.client_id == "netbox-to-diode") | .client_secret' ./oauth2/client/client-credentials.json > netbox-to-diode-client-secret

echo -e "Now you should export the netbox-to-diode client secret as an environment variable:\n"
echo "export NETBOX_TO_DIODE_CLIENT_SECRET=\$(cat ./diode/netbox-to-diode-client-secret)"

# End
popd