#!/usr/bin/env bash
set -euo pipefail

# Check if all required environment variables are set
REQUIRED_VARS=("MY_EXTERNAL_IP" "NETBOX_PORT" "DIODE_TO_NETBOX_API_KEY" "NETBOX_TO_DIODE_API_KEY" "DIODE_API_KEY" "INGESTER_TO_RECONCILER_API_KEY")

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
git clone --branch 3.0.2 https://github.com/netbox-community/netbox-docker.git
pushd netbox-docker

echo
echo "--- Generating configuration files ---"
echo

# Create plugin files
cat <<EOF > plugin_requirements.txt
netboxlabs-diode-netbox-plugin
EOF

cat <<EOF > Dockerfile-Plugins
FROM netboxcommunity/netbox:v4.1-3.0.2

COPY ./plugin_requirements.txt /opt/netbox/
RUN /opt/netbox/venv/bin/pip install --no-warn-script-location -r /opt/netbox/plugin_requirements.txt
EOF

cat <<EOF > docker-compose.override.yml
services:
  netbox:
    image: netbox:v4.1-3.0.2-plugins
    pull_policy: never
    ports:
      - "\${NETBOX_PORT}:8080"
    build:
      context: .
      dockerfile: Dockerfile-Plugins
    environment:
      SKIP_SUPERUSER: "false"
      SUPERUSER_API_TOKEN: "1234567890"
      SUPERUSER_EMAIL: ""
      SUPERUSER_NAME: "admin"
      SUPERUSER_PASSWORD: "admin"
      DIODE_TO_NETBOX_API_KEY: "\${DIODE_TO_NETBOX_API_KEY}"
      NETBOX_TO_DIODE_API_KEY: "\${NETBOX_TO_DIODE_API_KEY}"
      DIODE_API_KEY: "\${DIODE_API_KEY}"
      #INGESTER_TO_RECONCILER_API_KEY: "\${INGESTER_TO_RECONCILER_API_KEY}"
    healthcheck:
      test: curl -f http://\${MY_EXTERNAL_IP}:\${NETBOX_PORT}/login/ || exit 1
      start_period: 600s
      timeout: 3s
      interval: 15s
  netbox-worker:
    image: netbox:v4.1-3.0.2-plugins
    pull_policy: never
  netbox-housekeeping:
    image: netbox:v4.1-3.0.2-plugins
    pull_policy: never
EOF

# Add the Diode plugin and its configuration to configuration.py
cat <<EOF > configuration/plugins.py
PLUGINS = ["netbox_diode_plugin"]

PLUGINS_CONFIG = {
    "netbox_diode_plugin": {
        "auto_provision_users": False,
        "diode_target_override": "grpc://${MY_EXTERNAL_IP}:8080/diode",
        "diode_to_netbox_username": "diode-to-netbox",
        "netbox_to_diode_username": "netbox-to-diode",
        "diode_username": "diode-ingestion",
    },
}
EOF

# Detect OS and apply sed command accordingly
OS_TYPE=$(uname)
if [[ "$OS_TYPE" == "Darwin" ]]; then
  # macOS (requires '' for in-place edit)
  sed -i '' "s|http://localhost:8080/login/|http://${MY_EXTERNAL_IP}:${NETBOX_PORT}/login/|" docker-compose.yml
else
  # Linux
  sed -i "s|http://localhost:8080/login/|http://${MY_EXTERNAL_IP}:${NETBOX_PORT}/login/|" docker-compose.yml
fi

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