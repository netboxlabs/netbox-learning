#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="./network/orb-agent/.env"

# Check if all required environment variables are set
REQUIRED_VARS=("MY_EXTERNAL_IP" "DIODE_CLIENT_ID" "DIODE_CLIENT_SECRET")

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    exit 1
  fi
done

# Generate variables needed by orb-agent
DIODE_TARGET="grpc://${MY_EXTERNAL_IP}:8080/diode"
GIT_TARGET="http://${MY_EXTERNAL_IP}:3000/admin/orb-policies"
PROMETHEUS_TARGET="http://${MY_EXTERNAL_IP}:9090/api/v1/write"

# Ensure directory exists
mkdir -p "$(dirname ${ENV_FILE})"

# Write variables to the environment file
cat <<EOF > "$ENV_FILE"
DIODE_TARGET=${DIODE_TARGET}
DIODE_CLIENT_ID=${DIODE_CLIENT_ID}
DIODE_CLIENT_SECRET=${DIODE_CLIENT_SECRET}
GIT_TARGET=${GIT_TARGET}
PROMETHEUS_TARGET=${PROMETHEUS_TARGET}
EOF

# Debug information to communicate values being used
echo
echo "--- Orb Agent ENV file created ---"
echo ${ENV_FILE}
cat $ENV_FILE
echo "----------------------------------"
echo