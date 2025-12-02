#!/bin/bash
set -euo pipefail

# Check if all required environment variables are set
REQUIRED_VARS=("MY_EXTERNAL_IP" "NETBOX_PORT")

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    exit 0
  fi
done

echo
echo "--- Configuring environment ---"
echo

pushd ansible
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
ansible-galaxy install -r roles/requirements.yml
ansible-galaxy collection install git+https://github.com/nokia/srlinux-ansible-collection.git

# Insert the correct NetBox server
sed -i "s/MY_EXTERNAL_IP/$MY_EXTERNAL_IP/g; s/NETBOX_PORT/$NETBOX_PORT/g" inventory/netbox.yml

echo
echo "--- Deploying changes to the network ---"
echo

ansible-playbook playbooks/set-ntp.yml

echo
echo "--- Cleaning up ---"
echo

#deactivate
#rm -fr venv/
#popd