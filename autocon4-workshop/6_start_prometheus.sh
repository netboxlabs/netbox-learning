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
mkdir -p prometheus/alerts
pushd prometheus

echo "Copying config files from config-templates/prometheus/"
cp ../config-templates/prometheus/docker-compose.yaml .
cp ../config-templates/prometheus/prometheus.yaml .
cp ../config-templates/prometheus/alerts/httpcheck.yaml alerts/

echo
echo "--- Ensuring data dirs exist ---"
echo

rm -rf prometheus-data
mkdir -p prometheus-data

echo
echo "--- Starting Prometheus (detached) ---"
echo

$DOCKER_COMPOSE up -d

echo
echo "--- Waiting for container health=healthy ---"
echo

# Wait for health to be "healthy"
until [ "$(
  docker inspect -f '{{.State.Health.Status}}' prometheus 2>/dev/null || echo "starting"
)" = "healthy" ]; do
  sleep 1
done

popd
echo
echo "✅ Done. Prometheus is ready at:  http://${MY_EXTERNAL_IP}:9090"
echo