#!/usr/bin/env bash
# Demo 1, step 2b (Script, without Python): load ansible/data/ams-dc1.yml with Ansible.
#
# The data definition file describes the site; the playbook (ansible/load.yml) turns it into
# NetBox objects with the netbox.netbox collection. Run it twice: the second run is changed=0.
#
#   ./2b_ansible.sh                           load ansible/data/ams-dc1.yml
#   ./2b_ansible.sh -e data_file=other.yml    load another data definition file
#   ./2b_ansible.sh --check --diff            show what would change, without changing it
set -euo pipefail
cd "$(dirname "$0")"
# load .env; it wins over the shell, so credentials exported for another NetBox or Diode cannot leak in
while IFS='=' read -r k v; do
  [[ -z "$k" || "$k" == \#* ]] && continue
  export "$k=$v"
done < .env
export NETBOX_URL NETBOX_TOKEN
export ANSIBLE_COLLECTIONS_PATH="$PWD/ansible/collections" ANSIBLE_PYTHON_INTERPRETER="$PWD/.venv/bin/python"
export ANSIBLE_STDOUT_CALLBACK=default ANSIBLE_CALLBACK_RESULT_FORMAT=yaml ANSIBLE_DISPLAY_SKIPPED_HOSTS=false
export ANSIBLE_LOCALHOST_WARNING=false ANSIBLE_INVENTORY_UNPARSED_WARNING=false
echo "== Demo 1 · 2b Script without Python: Ansible =="
echo "Data definition: ansible/data/ (default ams-dc1.yml)   Playbook: ansible/load.yml"
cd ansible
exec ../.venv/bin/ansible-playbook load.yml "$@"
