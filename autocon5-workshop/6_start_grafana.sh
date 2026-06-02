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
mkdir -p grafana
pushd grafana

echo
echo "--- Copying config files from config-templates/grafana/ ---"
echo

cp ../config-templates/grafana/docker-compose.yaml .
rm -rf provisioning
cp -r ../config-templates/grafana/provisioning provisioning

echo
echo "--- Ensuring data dirs exist ---"
echo

rm -rf prometheus-data grafana-data
mkdir -p prometheus-data grafana-data

echo
echo "--- Starting Prometheus and Grafana (detached) ---"
echo

$DOCKER_COMPOSE up -d

echo
echo "--- Waiting for Prometheus to be healthy ---"
echo

until [ "$(
  docker inspect -f '{{.State.Health.Status}}' prometheus 2>/dev/null || echo "starting"
)" = "healthy" ]; do
  sleep 1
done

echo
echo "--- Waiting for Grafana to be healthy ---"
echo

until [ "$(
  docker inspect -f '{{.State.Health.Status}}' grafana 2>/dev/null || echo "starting"
)" = "healthy" ]; do
  sleep 1
done

popd
echo
echo "✅ Done."
echo
echo "Grafana is ready at:     http://${MY_EXTERNAL_IP}:3100"
echo "   Username: admin"
echo "   Password: netboxlabs"
echo
