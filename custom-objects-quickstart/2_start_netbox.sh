#!/bin/bash
set -euo pipefail

# Check if all required environment variables are set
REQUIRED_VARS=("MY_EXTERNAL_IP" "NETBOX_PORT" "NETBOX_TOKEN")

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    exit 0
  fi
done

echo
echo "--- Cloning NetBox Docker ---"
echo

# Clone netbox-docker
git clone --branch 3.4.0 https://github.com/netbox-community/netbox-docker.git
pushd netbox-docker

echo
echo "--- Generating configuration files ---"
echo

# Create Dockerfile for plugins
cat <<EOF > Dockerfile-Plugins
FROM netboxcommunity/netbox:v4.4.0

RUN uv pip install netboxlabs-netbox-custom-objects
EOF

cat <<EOF > docker-compose.override.yml
services:
  netbox:
    image: netbox:v4.4.0-plugins
    pull_policy: never
    ports:
      - "${NETBOX_PORT}:8080"
    build:
      context: .
      dockerfile: Dockerfile-Plugins
    environment:
      SKIP_SUPERUSER: "false"
      SUPERUSER_API_TOKEN: ${NETBOX_TOKEN}
      SUPERUSER_EMAIL: ""
      SUPERUSER_NAME: "admin"
      SUPERUSER_PASSWORD: "admin"
    healthcheck:
      test: curl -f http://${MY_EXTERNAL_IP}:${NETBOX_PORT}/login/ || exit 1
      start_period: 600s
      timeout: 3s
      interval: 15s
  netbox-worker:
    image: netbox:v4.4.0-plugins
    pull_policy: never
EOF

# Add the NetBox Service Mappings plugin
cat <<EOF > configuration/plugins.py
PLUGINS = ["netbox_custom_objects"]
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