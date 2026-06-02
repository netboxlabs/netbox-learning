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

# Clone netbox-docker (idempotent)
if [ ! -d netbox-docker ]; then
  git clone --branch 4.0.2 https://github.com/netbox-community/netbox-docker.git
else
  echo "netbox-docker already exists, skipping clone."
fi
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
# Disable the new-release banner — not relevant in a workshop environment
RELEASE_CHECK_URL = None

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

DEFAULT_USER_PREFERENCES = {
    "ui": {
        "copilot_enabled": "true",
    }
}
EOF

cat <<EOF > Dockerfile-Plugins
FROM netboxcommunity/netbox:v4.5.10

RUN uv pip install netboxlabs-diode-netbox-plugin==1.12.0
RUN uv pip install netboxlabs-netbox-branching==1.0.3
EOF

cat <<EOF > docker-compose.override.yml
services:
  netbox:
    image: netbox:v4.5.10-plugins
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
      SUPERUSER_PASSWORD: "netboxlabs"
      EDA_HOST: "${MY_EXTERNAL_IP}"
    healthcheck:
      test: curl -f http://localhost:8080/login/ || exit 1
      start_period: 600s
      timeout: 3s
      interval: 15s
  netbox-worker:
    image: netbox:v4.5.10-plugins
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

echo
echo "--- Waiting for NetBox to be healthy ---"
echo

until [ "$(
  docker inspect -f '{{.State.Health.Status}}' netbox-docker-netbox-1 2>/dev/null || echo "starting"
)" = "healthy" ]; do
  sleep 5
done

echo
echo "--- Starting NetBox worker ---"
echo

docker compose up -d netbox-worker

until [ "$(
  docker inspect -f '{{.State.Health.Status}}' netbox-docker-netbox-worker-1 2>/dev/null || echo "starting"
)" = "healthy" ]; do
  sleep 5
done

# Replace the auto-created v2 token with a v1 token using the known NETBOX_TOKEN value.
# v2 tokens store only a hashed secret — unusable with "Authorization: Token <value>".
# v1 tokens store the plaintext and work with all workshop tooling (curl, nb_inventory, Diode).
echo
echo "--- Provisioning v1 API token for admin ---"
echo

docker exec netbox-docker-netbox-1 python3 /opt/netbox/netbox/manage.py shell -c "
from users.models import Token
from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.get(username='admin')
Token.objects.filter(user=admin).delete()
t = Token(user=admin, version=1, write_enabled=True, description='Workshop token (v1)', token='${NETBOX_TOKEN}')
t.save()
print(f'Token provisioned: {t.plaintext}')
"

# Configure admin dashboard
echo
echo "--- Configuring NetBox admin dashboard ---"
echo

# Read HTTPS URLs from environment file if set, otherwise fall back to HTTP
ENV_FILE="$(pwd)/../environment"
GRAFANA_URL=$(grep "^GRAFANA_URL=" "${ENV_FILE}" 2>/dev/null | cut -d= -f2 || echo "http://${MY_EXTERNAL_IP}:3100")
GITEA_URL=$(grep "^GITEA_URL=" "${ENV_FILE}" 2>/dev/null | cut -d= -f2 || echo "http://${MY_EXTERNAL_IP}:3000")
DOZZLE_URL=$(grep "^DOZZLE_URL=" "${ENV_FILE}" 2>/dev/null | cut -d= -f2 || echo "http://${MY_EXTERNAL_IP}:8888")
WETTY_URL=$(grep "^WETTY_URL=" "${ENV_FILE}" 2>/dev/null | cut -d= -f2 || echo "http://${MY_EXTERNAL_IP}:3001")

docker exec netbox-docker-netbox-1 python3 /opt/netbox/netbox/manage.py shell -c "
from extras.models.dashboard import Dashboard
from extras.dashboard.widgets import NoteWidget, ObjectListWidget
from django.contrib.auth import get_user_model

GRAFANA_URL = '${GRAFANA_URL}'
GITEA_URL   = '${GITEA_URL}'
DOZZLE_URL  = '${DOZZLE_URL}'
WETTY_URL   = '${WETTY_URL}'

User = get_user_model()
user = User.objects.get(username='admin')
dashboard, _ = Dashboard.objects.get_or_create(user=user)
dashboard.layout = []
dashboard.config = {}

INSTRUCTIONS_BASE = GITEA_URL + '/admin/workshop-resources/src/branch/main/modules'

# Row 1 (y=0, height=3): Modules 1-3
m1 = NoteWidget(
    title='Module 1 — Getting Started',
    width=4, height=3, color='teal',
    config={'content': (
        'Experience the pain of manual network configuration — and why automation matters.\n\n'
        '[📖 Module instructions](%s/module_1/README.md)\n\n'
        '**Workshop tools:**\n\n'
        '- [Grafana](%s)\n'
        '- [Gitea](%s)\n'
        '- [Container logs (via Dozzle)](%s)\n'
        '- [Terminal (via WeTTY)](%s)'
    ) % (INSTRUCTIONS_BASE, GRAFANA_URL, GITEA_URL, DOZZLE_URL, WETTY_URL)},
)
dashboard.add_widget(m1, x=0, y=0)

m2 = NoteWidget(
    title='Module 2 — Planning',
    width=4, height=3, color='secondary',
    config={'content': (
        'Plan your network deployment by modeling intent in NetBox before touching a device.\n\n'
        '[📖 Module instructions](%s/module_2/README.md)\n\n'
        '**NetBox menus used:**\n\n'
        '- [Branches](/plugins/branching/branches/)\n'
        '- [Sites](/dcim/sites/)\n'
        '- [Devices](/dcim/devices/)\n'
        '- [Device Types](/dcim/device-types/)\n'
        '- [Device Roles](/dcim/device-roles/)\n'
        '- [IP Addresses](/ipam/ip-addresses/)\n'
        '- [Scripts](/extras/scripts/)\n'
        '- [Diode Settings](/plugins/diode/settings/)'
    ) % INSTRUCTIONS_BASE},
)
dashboard.add_widget(m2, x=4, y=0)

m3 = NoteWidget(
    title='Module 3 — Deploying Ansible',
    width=4, height=3, color='teal',
    config={'content': (
        'Configure Ansible to read from NetBox, laying the groundwork for automated deployments.\n\n'
        '[📖 Module instructions](%s/module_3/README.md)\n\n'
        '**NetBox menus used:**\n\n'
        '- [Branches](/plugins/branching/branches/)\n'
        '- [Scripts](/extras/scripts/)\n'
        '- [Diode Settings](/plugins/diode/settings/)'
    ) % INSTRUCTIONS_BASE},
)
dashboard.add_widget(m3, x=8, y=0)

# Row 2 (y=3, height=3): Modules 4-6
m4 = NoteWidget(
    title='Module 4 — Basic Config Rendering',
    width=4, height=3, color='secondary',
    config={'content': (
        'Model interfaces and IP addresses in NetBox and render device configurations.\n\n'
        '[📖 Module instructions](%s/module_4/README.md)\n\n'
        '**NetBox menus used:**\n\n'
        '- [Branches](/plugins/branching/branches/)\n'
        '- [Devices](/dcim/devices/)\n'
        '- [IP Addresses](/ipam/ip-addresses/)\n'
        '- [Config Templates](/extras/config-templates/)\n'
        '- [Data Sources](/core/data-sources/)'
    ) % INSTRUCTIONS_BASE},
)
dashboard.add_widget(m4, x=0, y=3)

m5 = NoteWidget(
    title='Module 5 — Advanced Config Rendering',
    width=4, height=3, color='teal',
    config={'content': (
        'Add OSPF routing intent to NetBox and generate full device configurations.\n\n'
        '[📖 Module instructions](%s/module_5/README.md)\n\n'
        '**NetBox menus used:**\n\n'
        '- [Branches](/plugins/branching/branches/)\n'
        '- [Devices](/dcim/devices/)\n'
        '- [Config Templates](/extras/config-templates/)\n'
        '- [Config Contexts](/extras/config-contexts/)'
    ) % INSTRUCTIONS_BASE},
)
dashboard.add_widget(m5, x=4, y=3)

m6 = NoteWidget(
    title='Module 6 — Drift Detection',
    width=4, height=3, color='secondary',
    config={'content': (
        'Detect configuration drift and self-heal the network from NetBox.\n\n'
        '[📖 Module instructions](%s/module_6/README.md)\n\n'
        '**NetBox menus used:**\n\n'
        '- [Branches](/plugins/branching/branches/)\n'
        '- [Scripts](/extras/scripts/)\n'
        '- [Diode Settings](/plugins/diode/settings/)'
    ) % INSTRUCTIONS_BASE},
)
dashboard.add_widget(m6, x=8, y=3)

# Row 3 (y=6, height=4): Change log (full width)
try:
    changelog = ObjectListWidget(
        title='Change Log',
        width=12, height=4, color='secondary',
        config={'model': 'core.objectchange'},
    )
    dashboard.add_widget(changelog, x=0, y=6)
except Exception as e:
    print(f'Note: Could not add Change Log widget: {e}')

dashboard.save()
print('Dashboard configured.')
"

# Enable Copilot for admin user
echo
echo "--- Enabling NetBox Copilot for admin ---"
echo

docker exec netbox-docker-netbox-1 python3 /opt/netbox/netbox/manage.py shell -c "
from users.models import UserConfig
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='admin')
uc, _ = UserConfig.objects.get_or_create(user=user)
uc.data.setdefault('ui', {})['copilot_enabled'] = 'true'
uc.save()
print('Copilot enabled for admin.')
"

# End
popd
echo "You can now access NetBox here: http://${MY_EXTERNAL_IP}:${NETBOX_PORT}"
echo "username: admin"
echo "password: netboxlabs"