#!/usr/bin/env bash
set -euo pipefail

# Check if all required environment variables are set
REQUIRED_VARS=("MY_EXTERNAL_IP")

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    exit 1
  fi
done

# You can override this if you use the legacy 'docker-compose' binary:
DOCKER_COMPOSE="${DOCKER_COMPOSE:-docker compose}"

# Fresh start directory
mkdir -p gitea
pushd gitea

echo
echo "--- Writing docker-compose.yml (rootless, SQLite, healthcheck) ---"
echo

cat > docker-compose.yml <<EOF
services:
  gitea:
    image: gitea/gitea:latest-rootless
    container_name: gitea
    restart: unless-stopped
    environment:
      - GITEA__server__ROOT_URL=http://${MY_EXTERNAL_IP}:3000/
      - GITEA__server__HTTP_PORT=3000
      - GITEA__server__SSH_DOMAIN=${MY_EXTERNAL_IP}
      - GITEA__server__SSH_PORT=2222
      - GITEA__database__DB_TYPE=sqlite3
      - GITEA__security__INSTALL_LOCK=true
      - GITEA__service__DISABLE_REGISTRATION=true
    # NOTE: rootless image expects /var/lib/gitea and /etc/gitea
    volumes:
      - ./gitea-data:/var/lib/gitea
      - ./gitea-config:/etc/gitea
    ports:
      - "3000:3000"   # HTTP
      - "2222:2222"   # SSH
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://127.0.0.1:3000/api/healthz >/dev/null || exit 1"]
      interval: 2s
      timeout: 2s
      retries: 60
      start_period: 5s
EOF

echo
echo "--- Ensuring data dirs exist and are writable by UID 1000 (rootless) ---"
echo

rm -rf gitea-data gitea-config
mkdir -p gitea-data gitea-config
# The rootless image runs as 1000:1000
chown -R 1000:1000 gitea-data gitea-config
chmod -R u+rwX gitea-data gitea-config

echo
echo "--- Starting Gitea (detached) ---"
echo

$DOCKER_COMPOSE up -d gitea

echo
echo "--- Waiting for container health=healthy ---"
echo

# Wait for health to be "healthy"
until [ "$(
  docker inspect -f '{{.State.Health.Status}}' gitea 2>/dev/null || echo "starting"
)" = "healthy" ]; do
  sleep 1
done

echo
echo "--- Creating admin user (safe to re-run) ---"
echo

$DOCKER_COMPOSE exec -T gitea gitea admin user create \
  --username admin \
  --password admin123 \
  --email admin@example.com \
  --admin || true

echo
echo "--- Generating a short-lived access token for admin ---"
echo

# Scopes: write:user,write:repository are both required to create repos via /api/v1/user/repos
TOKEN="$($DOCKER_COMPOSE exec -T gitea gitea admin user generate-access-token \
  --username admin \
  --token-name bootstrap-$(date +%s) \
  --scopes write:user,write:repository \
  --raw | tr -d '\r')"

if [ -z "${TOKEN}" ]; then
  echo "ERROR: Could not obtain access token from Gitea CLI."
  echo "Check container logs with: docker compose logs gitea"
  exit 1
fi

echo
echo "--- Creating orb-policies repo via API (idempotent) ---"
echo

# 201 Created on first run; 409 Conflict if it already exists — both are fine
set +e
HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" -X POST "http://${MY_EXTERNAL_IP}:3000/api/v1/user/repos" \
  -H "Authorization: token ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"orb-policies","private":false,"auto_init":true}')
set -e
if [ "${HTTP_CODE}" != "201" ] && [ "${HTTP_CODE}" != "409" ]; then
  echo "ERROR: Repo creation returned HTTP ${HTTP_CODE}"
  exit 1
fi

echo
echo "--- Commiting Orb config files to Gitea ---"
echo

rm -rf orb-policies
git clone "http://admin:admin123@${MY_EXTERNAL_IP}:3000/admin/orb-policies.git" orb-policies
cd orb-policies

echo "Copying policy files from config-templates/orb-policies/ to Gitea..."
cp ../../config-templates/orb-policies/selector.yaml .
cp ../../config-templates/orb-policies/clab_networks.yaml .
cp ../../config-templates/orb-policies/srl_devices.yaml .
cp ../../config-templates/orb-policies/web_monitor.yaml .

git config user.email "workshop@autocon4.example.com"
git config user.name "Workshop Participant"
git add .
git commit -m "Initial Orb policy files" || true
git push || true
cd ..

popd
echo
echo "✅ Done. Gitea is ready at:  http://${MY_EXTERNAL_IP}:3000"
echo "   Username: admin"
echo "   Password: admin123"
echo
echo "Repo URL (HTTPS): http://${MY_EXTERNAL_IP}:3000/admin/orb-policies.git"
echo "Repo URL (SSH):   ssh://git@${MY_EXTERNAL_IP}:2222/admin/orb-policies.git"
echo