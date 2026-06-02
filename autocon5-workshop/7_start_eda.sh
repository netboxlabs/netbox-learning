#!/usr/bin/env bash
set -euo pipefail

REQUIRED_VARS=("MY_EXTERNAL_IP" "NETBOX_URL" "NETBOX_TOKEN")

# netbox.netbox.nb_inventory reads NETBOX_API (not NETBOX_URL)
export NETBOX_API="${NETBOX_URL}"

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    exit 1
  fi
done

GITEA_URL="${GITEA_URL:-http://${MY_EXTERNAL_IP}:3000}"
PLAYBOOK_DIR="ansible-playbooks"

EDA_PORT=5000
RESULT_PORT=5001
EDA_LOG="eda.log"
RESULT_LOG="eda-results.log"
EDA_PID_FILE="eda.pid"
RESULT_PID_FILE="eda-results.pid"

# Stop any existing processes
for pid_file in "${EDA_PID_FILE}" "${RESULT_PID_FILE}"; do
  if [ -f "${pid_file}" ]; then
    OLD_PID=$(cat "${pid_file}")
    if kill -0 "${OLD_PID}" 2>/dev/null; then
      echo "Stopping existing process (PID ${OLD_PID})..."
      kill "${OLD_PID}"
    fi
    rm -f "${pid_file}"
  fi
done

echo
echo "--- Pre-compiling Ansible collections to avoid first-run pyc errors ---"
echo

python3 -m compileall -q ~/.ansible/collections/ansible_collections/nokia \
  /usr/lib/python3/dist-packages/ansible_collections/ansible/netcommon \
  2>/dev/null || true

echo "Pre-compilation complete"

echo
echo "--- Cloning ansible-playbooks from Gitea ---"
echo

rm -rf "${PLAYBOOK_DIR}"
git clone "${GITEA_URL}/admin/ansible-playbooks.git" "${PLAYBOOK_DIR}"

echo
echo "--- Starting EDA result relay on port ${RESULT_PORT} ---"
echo

nohup python3 "${PLAYBOOK_DIR}/result_server.py" > "${RESULT_LOG}" 2>&1 &
echo $! > "${RESULT_PID_FILE}"
echo "Result relay started (PID $(cat ${RESULT_PID_FILE}))"

echo
echo "--- Starting Event Driven Ansible webhook listener on port ${EDA_PORT} ---"
echo

pushd "${PLAYBOOK_DIR}"
export EDA_PLAYBOOK_DIR="$(pwd)"
nohup ansible-rulebook \
  --rulebook rulebook.yml \
  --inventory inventory/ \
  --verbose \
  > "../${EDA_LOG}" 2>&1 &
echo $! > "../${EDA_PID_FILE}"
popd

echo "EDA started (PID $(cat ${EDA_PID_FILE})), waiting for listener to be ready..."

until grep -q "Waiting for events" "${EDA_LOG}" 2>/dev/null; do
  sleep 1
done

# Sidecar container that streams eda.log into Docker stdout so Dozzle can display it
docker rm -f eda-log 2>/dev/null || true
docker run -d \
  --name eda-log \
  --restart unless-stopped \
  -v "$(pwd)/${EDA_LOG}:/eda.log:ro" \
  alpine:latest \
  tail -f /eda.log

echo
echo "✅ Done. EDA webhook listener is ready at: http://${MY_EXTERNAL_IP}:${EDA_PORT}"
echo
echo "Test with:"
echo "  curl -X POST http://${MY_EXTERNAL_IP}:${EDA_PORT}/endpoint \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"message\": \"hello from webhook\", \"source\": \"test\"}'"
echo
echo "Watch logs:"
echo "  tail -f ${EDA_LOG}"
echo
