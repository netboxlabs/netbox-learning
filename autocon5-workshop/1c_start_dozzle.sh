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

DOZZLE_DIR="$(pwd)/dozzle"

mkdir -p "${DOZZLE_DIR}"

echo
echo "--- Generating Dozzle users.yml ---"
echo

docker run --rm amir20/dozzle generate admin --password netboxlabs --name "Admin" \
  > "${DOZZLE_DIR}/users.yml"

cp config-templates/dozzle/docker-compose.yaml "${DOZZLE_DIR}/docker-compose.yaml"

echo
echo "--- Starting Dozzle ---"
echo

docker rm -f dozzle 2>/dev/null || true

pushd "${DOZZLE_DIR}"
docker compose up -d
popd

echo
echo "✅ Done. Dozzle is available at: https://docker-${PARTICIPANT_ID}.autocon5.netboxlabs.tech"
echo "   Username: admin"
echo "   Password: netboxlabs"
echo
