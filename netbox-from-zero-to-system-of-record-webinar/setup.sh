#!/usr/bin/env bash
# One-time setup: a Python 3.12 environment with pynetbox, the Diode SDK and Ansible, plus the
# netbox.netbox collection. The Diode SDK needs Python 3.10 or later.
set -euo pipefail
cd "$(dirname "$0")"
if command -v uv >/dev/null; then
  uv venv -q --python 3.12 .venv && uv pip install -q --python .venv/bin/python -r requirements.txt
else
  python3.12 -m venv .venv && .venv/bin/pip install -q -r requirements.txt
fi
# the NetBox collection for the Ansible example, installed next to the playbook
.venv/bin/ansible-galaxy collection install -r ansible/requirements.yml -p ansible/collections </dev/null
[ -f .env ] || { cp .env.example .env; echo "Created .env: fill it in."; }
echo "Done. Run scripts with .venv/bin/python, or: source .venv/bin/activate"
