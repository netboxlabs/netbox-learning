#!/usr/bin/env bash
set -euo pipefail

# Check if all required environment variables are set
REQUIRED_VARS=("MY_EXTERNAL_IP" "NETBOX_PORT" "NETBOX_TO_DIODE_CLIENT_SECRET" "NETBOX_TOKEN")

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
git clone --branch 3.4.1 https://github.com/netbox-community/netbox-docker.git
pushd netbox-docker

echo
echo "--- Generating configuration files ---"
echo

# Add the Diode plugin and its configuration to configuration.py
cat <<EOF > configuration/plugins.py
PLUGINS = ["netbox_diode_plugin", "netbox_branching"]

PLUGINS_CONFIG = {
    "netbox_diode_plugin": {
        # Diode gRPC target for communication with Diode server
        "diode_target_override": "grpc://${MY_EXTERNAL_IP}:8080/diode",
        # NetBox username associated with changes applied via plugin
        "diode_username": "diode",
        # netbox-to-diode client secret from earlier step
        "netbox_to_diode_client_secret": "${NETBOX_TO_DIODE_CLIENT_SECRET}"
    },
}
EOF

#extra.py for NetBox Branching
cat <<EOF > configuration/extra.py
from netbox_branching.utilities import DynamicSchemaDict

DATABASES = DynamicSchemaDict({
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'netbox',               # Database name
        'USER': 'netbox',               # PostgreSQL username
        'PASSWORD': 'J5brHrAXFLQSif0K', # PostgreSQL password
        'HOST': 'postgres',             # Database server
        'PORT': '',                     # Database port (leave blank for default)
        'CONN_MAX_AGE': 300,            # Max database connection age
    }
})

DATABASE_ROUTERS = [
    'netbox_branching.database.BranchAwareRouter',
]
EOF

cat <<EOF > Dockerfile-Plugins
FROM netboxcommunity/netbox:v4.4.4

RUN uv pip install netboxlabs-diode-netbox-plugin==1.5.0
RUN uv pip install netboxlabs-netbox-branching==0.7.1
EOF

cat <<EOF > docker-compose.override.yml
services:
  netbox:
    image: netbox:v4.4.4-plugins
    pull_policy: never
    ports:
      - "${NETBOX_PORT}:8080"
    build:
      context: .
      dockerfile: Dockerfile-Plugins
    environment:
      SKIP_SUPERUSER: "false"
      SUPERUSER_API_TOKEN: "${NETBOX_TOKEN}"
      SUPERUSER_EMAIL: ""
      SUPERUSER_NAME: "admin"
      SUPERUSER_PASSWORD: "admin"
    healthcheck:
      test: curl -f http://${MY_EXTERNAL_IP}:${NETBOX_PORT}/login/ || exit 1
      start_period: 600s
      timeout: 3s
      interval: 15s
  netbox-worker:
    image: netbox:v4.4.4-plugins
    pull_policy: never
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