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

WETTY_DIR="$(pwd)/wetty"

mkdir -p "${WETTY_DIR}"

echo
echo "--- Creating workshop admin user ---"
echo

if ! id "admin" &>/dev/null; then
  # Use -N to avoid conflict if the admin group already exists
  useradd -m -s /bin/bash -N admin
  usermod -aG admin admin 2>/dev/null || true
  echo "User 'admin' created."
else
  echo "User 'admin' already exists — skipping creation."
fi

echo "admin:netboxlabs" | chpasswd
usermod -aG docker admin

WORKSHOP_DIR="/root/workspace/product-internal-skunkworks/autocon5-workshop"

# Suppress terminal color probing (prevents escape sequences leaking into output via WeTTY)
echo 'export NO_COLOR=1' >> /home/admin/.bashrc
# Land in the workshop directory on login so participants don't need to navigate there
echo "cd ${WORKSHOP_DIR}" >> /home/admin/.bashrc
chmod +x "${WORKSHOP_DIR}/reset_network.sh"
# Allow admin to traverse (but not list) /root so the workshop dir is reachable
chmod o+x /root
cat > /home/admin/reset_network.sh <<EOF
#!/usr/bin/env bash
exec sudo ${WORKSHOP_DIR}/reset_network.sh
EOF
chmod +x /home/admin/reset_network.sh
chown admin:admin /home/admin/reset_network.sh

echo
echo "--- Enabling SSH password authentication for admin ---"
echo

SSHD_CONF="/etc/ssh/sshd_config.d/workshop-admin.conf"
cat > "${SSHD_CONF}" <<EOF
Match User admin
    PasswordAuthentication yes
EOF
systemctl reload ssh
echo "SSH password auth enabled for admin."

echo
echo "--- Configuring sudoers for clab ---"
echo

SUDOERS_FILE="/etc/sudoers.d/workshop-admin"
cat > "${SUDOERS_FILE}" <<EOF
# Allow workshop admin user to run containerlab and the network reset script without a password
admin ALL=(ALL) NOPASSWD: /usr/bin/clab, /usr/local/bin/clab, /usr/bin/containerlab, /usr/local/bin/containerlab, ${WORKSHOP_DIR}/reset_network.sh
EOF
chmod 440 "${SUDOERS_FILE}"
echo "Sudoers entry written for clab."

echo
echo "--- Starting WeTTY ---"
echo

cp config-templates/wetty/docker-compose.yaml "${WETTY_DIR}/docker-compose.yaml"

pushd "${WETTY_DIR}"
docker compose up -d
popd

echo
echo "✅ Done. Terminal is available at: https://ssh-${PARTICIPANT_ID}.autocon5.netboxlabs.tech"
echo "   Username: admin"
echo "   Password: netboxlabs"
echo
