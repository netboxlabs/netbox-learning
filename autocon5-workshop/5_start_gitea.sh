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
echo "--- Copying config files from config-templates/gitea/ ---"
echo

cp ../config-templates/gitea/docker-compose.yaml docker-compose.yaml

echo
echo "--- Ensuring data dirs exist and are writable by UID 1000 (rootless) ---"
echo

if [ ! -f gitea-config/app.ini ]; then
  rm -rf gitea-data gitea-config
  mkdir -p gitea-data gitea-config
  # The rootless image runs as 1000:1000
  chown -R 1000:1000 gitea-data gitea-config
  chmod -R u+rwX gitea-data gitea-config
else
  echo "Gitea already configured — skipping data directory reset"
fi

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

$DOCKER_COMPOSE exec -T --workdir /tmp gitea gitea admin user create \
  --username admin \
  --password netboxlabs \
  --email admin@example.com \
  --admin || true

echo
echo "--- Generating a short-lived access token for admin ---"
echo

# Scopes: write:user,write:repository are both required to create repos via /api/v1/user/repos
TOKEN="$($DOCKER_COMPOSE exec -T --workdir /tmp gitea gitea admin user generate-access-token \
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
git clone "http://admin:netboxlabs@${MY_EXTERNAL_IP}:3000/admin/orb-policies.git" orb-policies
cd orb-policies

echo "Copying policy files from config-templates/orb-policies/ to Gitea..."
cp ../../config-templates/orb-policies/selector.yaml .
cp ../../config-templates/orb-policies/web_monitor.yaml .
cp ../../config-templates/orb-policies/README.md .

git config user.email "workshop@autocon5.example.com"
git config user.name "Workshop Participant"
git add .
git commit -m "Initial Orb policy files" || true
git push || true
cd ..

echo
echo "--- Creating workshop-resources repo via API (idempotent) ---"
echo

set +e
HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" -X POST "http://${MY_EXTERNAL_IP}:3000/api/v1/user/repos" \
  -H "Authorization: token ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"workshop-resources","private":false,"auto_init":true,"description":"NetBox scripts, config templates, and device types for the AutoCon5 workshop"}')
set -e
if [ "${HTTP_CODE}" != "201" ] && [ "${HTTP_CODE}" != "409" ]; then
  echo "ERROR: Repo creation returned HTTP ${HTTP_CODE}"
  exit 1
fi

echo
echo "--- Committing workshop-resources to Gitea ---"
echo

rm -rf workshop-resources
git clone "http://admin:netboxlabs@${MY_EXTERNAL_IP}:3000/admin/workshop-resources.git" workshop-resources
cd workshop-resources

mkdir -p scripts config-templates device-types/Nokia device-types/Cisco device-types/Juniper device-types/Arista device-types/Fortinet

echo "Copying scripts..."
cp ../../config-templates/workshop-resources/scripts/run_orb_discovery.py  scripts/
cp ../../config-templates/workshop-resources/scripts/trigger_eda.py          scripts/
cp ../../config-templates/workshop-resources/scripts/branch_change_summary.py scripts/

echo "Copying config templates..."
cp ../../config-templates/workshop-resources/config-templates/srl_linux.j2           config-templates/
cp ../../config-templates/workshop-resources/config-templates/srl_linux_ospf.j2       config-templates/

echo "Copying device types..."
cp ../../config-templates/workshop-resources/device-types/Nokia/7220-IXR-D2L.yaml     device-types/Nokia/
cp ../../config-templates/workshop-resources/device-types/Cisco/ASR1001-X.yaml        device-types/Cisco/
cp ../../config-templates/workshop-resources/device-types/Juniper/EX2300-24MP.yaml    device-types/Juniper/
cp ../../config-templates/workshop-resources/device-types/Arista/DCS-7050S-64.yaml    device-types/Arista/
cp ../../config-templates/workshop-resources/device-types/Fortinet/FortiGate-100F.yaml device-types/Fortinet/

echo "Copying module instructions..."
cp -r ../../modules .

git config user.email "workshop@autocon5.example.com"
git config user.name "Workshop Participant"
git add .
git commit -m "Initial workshop-resources (scripts, config templates, device types, modules)" || true
git push || true
cd ..

echo
echo "--- Creating ansible-playbooks repo via API (idempotent) ---"
echo

set +e
HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" -X POST "http://${MY_EXTERNAL_IP}:3000/api/v1/user/repos" \
  -H "Authorization: token ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"ansible-playbooks","private":false,"auto_init":true,"description":"Ansible EDA playbooks and rulebook — AutoCon5 workshop"}')
set -e
if [ "${HTTP_CODE}" != "201" ] && [ "${HTTP_CODE}" != "409" ]; then
  echo "ERROR: Repo creation returned HTTP ${HTTP_CODE}"
  exit 1
fi

echo
echo "--- Committing Ansible EDA playbooks to Gitea ---"
echo

rm -rf ansible-playbooks
git clone "http://admin:netboxlabs@${MY_EXTERNAL_IP}:3000/admin/ansible-playbooks.git" ansible-playbooks
cd ansible-playbooks

cp ../../config-templates/ansible-eda/*.yml .
cp ../../config-templates/ansible-eda/result_server.py .
mkdir -p inventory
cp ../../config-templates/ansible-eda/inventory/nb_inventory.yml inventory/
cp ../../config-templates/ansible-eda/inventory/local.yml inventory/
cp -r ../../config-templates/ansible-eda/inventory/group_vars inventory/

git config user.email "workshop@autocon5.example.com"
git config user.name "Workshop Participant"
git add .
git commit -m "Initial Ansible EDA playbooks and rulebook" || true
git push || true
cd ..

popd
echo
echo "✅ Done. Gitea is ready at:  http://${MY_EXTERNAL_IP}:3000"
echo "   Username: admin"
echo "   Password: netboxlabs"
echo
echo "Repos:"
echo "  orb-policies:       http://${MY_EXTERNAL_IP}:3000/admin/orb-policies.git"
echo "  workshop-resources:  http://${MY_EXTERNAL_IP}:3000/admin/workshop-resources.git"
echo "  ansible-playbooks:   http://${MY_EXTERNAL_IP}:3000/admin/ansible-playbooks.git"
echo