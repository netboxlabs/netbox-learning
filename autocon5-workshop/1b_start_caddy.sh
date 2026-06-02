#!/usr/bin/env bash
set -euo pipefail

REQUIRED_VARS=("PARTICIPANT_ID")
for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    echo "  export PARTICIPANT_ID=<your number e.g. 01>"
    exit 1
  fi
done

DOMAIN="autocon5.netboxlabs.tech"
CERT_DIR="$(pwd)/certs"
CADDY_DIR="$(pwd)/caddy"

if [ ! -f "${CERT_DIR}/cert.pem" ] || [ ! -f "${CERT_DIR}/key.pem" ]; then
  echo "Error: Certificate files not found in ${CERT_DIR}/"
  echo "Ensure certs/cert.pem and certs/key.pem were included in the workshop files."
  exit 1
fi

echo
echo "--- Generating Caddyfile for participant ${PARTICIPANT_ID} ---"
echo

mkdir -p "${CADDY_DIR}"
sed "s/PARTICIPANT_ID/${PARTICIPANT_ID}/g" \
  config-templates/caddy/Caddyfile.template > "${CADDY_DIR}/Caddyfile"

cp config-templates/caddy/docker-compose.yaml "${CADDY_DIR}/docker-compose.yaml"

echo "NetBox  → https://netbox-${PARTICIPANT_ID}.${DOMAIN}"
echo "Grafana → https://grafana-${PARTICIPANT_ID}.${DOMAIN}"
echo "Gitea   → https://gitea-${PARTICIPANT_ID}.${DOMAIN}"
echo "Dozzle  → https://docker-${PARTICIPANT_ID}.${DOMAIN}"
echo "WeTTY   → https://ssh-${PARTICIPANT_ID}.${DOMAIN}"

echo
echo "--- Starting Caddy ---"
echo

pushd "${CADDY_DIR}"
docker compose up -d
popd

echo
echo "--- Blocking direct port access via firewall ---"
echo

# Block external access to service ports — all traffic must go through Caddy
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5000/tcp
ufw allow 5001/tcp
ufw deny 8000/tcp
ufw deny 3000/tcp
ufw deny 3100/tcp
ufw deny 8888/tcp
ufw deny 3001/tcp


echo
echo "--- Updating environment with HTTPS URLs ---"
echo

ENV_FILE="environment"
# Remove any existing URL entries and append new HTTPS ones
grep -v "^NETBOX_URL=\|^GRAFANA_URL=\|^GITEA_URL=\|^DOZZLE_URL=\|^WETTY_URL=" "${ENV_FILE}" > "${ENV_FILE}.tmp"
cat >> "${ENV_FILE}.tmp" <<EOF
NETBOX_URL=https://netbox-${PARTICIPANT_ID}.${DOMAIN}
GRAFANA_URL=https://grafana-${PARTICIPANT_ID}.${DOMAIN}
GITEA_URL=https://gitea-${PARTICIPANT_ID}.${DOMAIN}
DOZZLE_URL=https://docker-${PARTICIPANT_ID}.${DOMAIN}
WETTY_URL=https://ssh-${PARTICIPANT_ID}.${DOMAIN}
EOF
mv "${ENV_FILE}.tmp" "${ENV_FILE}"

# Update NetBox dashboard links to use HTTPS URLs (if NetBox is running)
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "netbox-docker-netbox-1"; then
  echo
  echo "--- Updating NetBox dashboard links to HTTPS ---"
  echo
  docker exec netbox-docker-netbox-1 python3 /opt/netbox/netbox/manage.py shell -c "
from extras.models.dashboard import Dashboard
from extras.dashboard.widgets import NoteWidget, ObjectCountsWidget
from django.contrib.auth import get_user_model

GRAFANA_URL = 'https://grafana-${PARTICIPANT_ID}.${DOMAIN}'
GITEA_URL   = 'https://gitea-${PARTICIPANT_ID}.${DOMAIN}'
DOZZLE_URL  = 'https://docker-${PARTICIPANT_ID}.${DOMAIN}'
WETTY_URL   = 'https://ssh-${PARTICIPANT_ID}.${DOMAIN}'

User = get_user_model()
user = User.objects.get(username='admin')
dashboard, _ = Dashboard.objects.get_or_create(user=user)
dashboard.layout = []
dashboard.config = {}

links = NoteWidget(
    title='Workshop Links',
    width=4, height=2,
    config={'content': '### Quick Links\n- [Grafana](%s)\n- [Gitea](%s)\n- [Dozzle](%s)\n- [Terminal](%s)' % (GRAFANA_URL, GITEA_URL, DOZZLE_URL, WETTY_URL)},
)
dashboard.add_widget(links, x=0, y=0)

counts = ObjectCountsWidget(
    title='Devices',
    width=4, height=2,
    config={'models': ['dcim.device', 'dcim.site', 'dcim.interface']},
)
dashboard.add_widget(counts, x=4, y=0)

dashboard.save()
print('Dashboard links updated to HTTPS.')
" 2>/dev/null || echo "  (NetBox not ready yet — dashboard will use HTTPS URLs when step 4 runs)"
fi

echo
echo "✅ Done. Services are available at:"
echo "   NetBox:   https://netbox-${PARTICIPANT_ID}.${DOMAIN}"
echo "   Grafana:  https://grafana-${PARTICIPANT_ID}.${DOMAIN}"
echo "   Gitea:    https://gitea-${PARTICIPANT_ID}.${DOMAIN}"
echo "   Dozzle:   https://docker-${PARTICIPANT_ID}.${DOMAIN}"
echo "   Terminal: https://ssh-${PARTICIPANT_ID}.${DOMAIN}"
echo
