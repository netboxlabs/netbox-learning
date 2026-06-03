#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

set -a
source ./1_set_envvars.sh
[ -f ./diode_creds ] && source ./diode_creds
set +a

./8_start_network.sh network/workshop.clab.yaml
