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
echo "--- Cloning Custom Objects ---"
echo

git clone -b main https://github.com/netboxlabs/netbox-custom-objects.git

echo
echo "--- Cloning NetBox Branching Plugin ---"
echo

git clone -b v0.7.0 https://github.com/netboxlabs/netbox-branching.git


echo
echo "--- Generating configuration files ---"
echo

# Create Dockerfile for plugins
cat <<EOF > Dockerfile-Plugins
FROM netboxcommunity/netbox:v4.4.0

COPY netbox-custom-objects /opt/netbox/netbox/plugins/netbox-custom-objects
RUN uv pip install -e /opt/netbox/netbox/plugins/netbox-custom-objects

COPY netbox-branching /opt/netbox/netbox/plugins/netbox-branching
RUN uv pip install -e /opt/netbox/netbox/plugins/netbox-branching

COPY local_settings.py /opt/netbox/netbox/netbox/local_settings.py
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
      test: curl -f http://localhost:8080/login/ || exit 1
      start_period: 600s
      timeout: 3s
      interval: 15s
  postgres:
    ports:
      - "5432:5432"
  netbox-worker:
    image: netbox:v4.4.0-plugins
    pull_policy: never
EOF

# Add the NetBox Service Mappings plugin
cat <<EOF > configuration/plugins.py
PLUGINS = ["netbox_custom_objects", "netbox_branching"]
EOF

#local_settings.py
cat <<EOF > local_settings.py
from netbox_branching.utilities import DynamicSchemaDict

DATABASES = DynamicSchemaDict({
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'netbox',               # Database name
        'USER': 'netbox',               # PostgreSQL username
        'PASSWORD': 'J5brHrAXFLQSif0K',         # PostgreSQL password
        'HOST': 'postgres',             # Database server
        'PORT': '',                     # Database port (leave blank for default)
        'CONN_MAX_AGE': 300,            # Max database connection age
    }
})

DATABASE_ROUTERS = [
    'netbox_branching.database.BranchAwareRouter',
]
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