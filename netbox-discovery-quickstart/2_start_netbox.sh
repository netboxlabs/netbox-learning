#!/usr/bin/env bash
set -euo pipefail

# Check if all required environment variables are set
REQUIRED_VARS=("MY_EXTERNAL_IP" "NETBOX_PORT" "NETBOX_TO_DIODE_CLIENT_SECRET")

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    exit 1
  fi
done

echo
echo "--- Cloning NetBox Docker ---"
echo

# Clone netbox-docker
git clone --branch 3.3.0 https://github.com/netbox-community/netbox-docker.git
pushd netbox-docker

echo
echo "--- Generating configuration files ---"
echo

cat <<EOF > Dockerfile-Plugins
FROM netboxcommunity/netbox:v4.3.7

RUN uv pip install netboxlabs-diode-netbox-plugin
EOF

cat <<EOF > docker-compose.override.yml
services:
  netbox:
    image: netbox:v4.3.7-plugins
    pull_policy: never
    ports:
      - "${NETBOX_PORT}:8080"
    build:
      context: .
      dockerfile: Dockerfile-Plugins
    environment:
      SKIP_SUPERUSER: "false"
      SUPERUSER_API_TOKEN: "1234567890"
      SUPERUSER_EMAIL: ""
      SUPERUSER_NAME: "admin"
      SUPERUSER_PASSWORD: "admin"
    healthcheck:
      test: curl -f http://${MY_EXTERNAL_IP}:${NETBOX_PORT}/login/ || exit 1
      start_period: 600s
      timeout: 3s
      interval: 15s
  netbox-worker:
    image: netbox:v4.3.7-plugins
    pull_policy: never
  netbox-housekeeping:
    image: netbox:v4.3.7-plugins
    pull_policy: never
EOF

# Add the Diode plugin and its configuration to configuration.py
cat <<EOF > configuration/plugins.py
PLUGINS = ["netbox_diode_plugin"]

PLUGINS_CONFIG = {
    "netbox_diode_plugin": {
        # Diode gRPC target for communication with Diode server
        "diode_target_override": "grpc://host.docker.internal:8080/diode",
        # NetBox username associated with changes applied via plugin
        "diode_username": "diode",
        # netbox-to-diode client secret from earlier step
        "netbox_to_diode_client_secret": "${NETBOX_TO_DIODE_CLIENT_SECRET}"
    },
}
EOF

echo
echo "--- Building NetBox ---"
echo

docker compose build --no-cache

echo
echo "--- Starting NetBox Docker ---"
echo

docker compose up -d

# End
popd
echo "You can now access NetBox here: http://${MY_EXTERNAL_IP}:${NETBOX_PORT}"
echo "username: admin"
echo "password: admin"