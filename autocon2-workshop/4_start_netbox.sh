#!/bin/bash
set -euo pipefail

# Check if all required environment variables are set
REQUIRED_VARS=("MY_EXTERNAL_IP" "NETBOX_PORT")

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
git clone --branch 3.0.2 https://github.com/netbox-community/netbox-docker.git
pushd netbox-docker

echo
echo "--- Generating configuration files ---"
echo

# Create plugin files
cat <<EOF > plugin_requirements.txt
slurpit-netbox==1.0.45
EOF

cat <<EOF > Dockerfile-Plugins
FROM netboxcommunity/netbox:v4.1-3.0.2

COPY ./plugin_requirements.txt /opt/netbox/
RUN /opt/netbox/venv/bin/pip install  --no-warn-script-location -r /opt/netbox/plugin_requirements.txt
EOF

cat <<EOF > docker-compose.override.yml
services:
  netbox:
    image: netbox:v4.1-3.0.2-plugins
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
    image: netbox:v4.1-3.0.2-plugins
    pull_policy: never
  netbox-housekeeping:
    image: netbox:v4.1-3.0.2-plugins
    pull_policy: never
EOF

# Add the Slurpit plugin to configuration.py
cat <<EOF > configuration/plugins.py
PLUGINS = ["slurpit_netbox"]
EOF

# Update the healthcheck in docker-compose.yml
sed -i 's|http://localhost:8080/login/|http://${MY_EXTERNAL_IP}:${NETBOX_PORT}/login/|' docker-compose.yml

echo
echo "--- Building NetBox ---"
echo

docker compose build --no-cache

echo
echo "--- Starting NetBox Docker ---"
echo

docker compose up -d

popd

echo
echo "--- Configuring NetBox ---"
echo

pushd workshop_setup

# Create virtualenv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Preconfigure NetBox objects
python netbox/netbox_importer.py --url "http://${MY_EXTERNAL_IP}:${NETBOX_PORT}" --token 1234567890 --file netbox/icinga_infrastructure.json

# Preconfigure Slurpit plugin
python netbox/configure_slurpit.py --slurpittoken 1234567890abcdefghijklmnopqrstuvwxqz --netboxuser admin --netboxpass admin

# Remove virtualenv
deactivate
rm -fr venv/

popd

# End

echo "you can now access netbox here: http://${MY_EXTERNAL_IP}:${NETBOX_PORT}"
echo "username: admin"
echo "password: admin"
