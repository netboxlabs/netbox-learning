#!/bin/bash
# Icinga plugin to ping a specified target
# Usage: ./ping_plugin.sh -H admin@host --target <target IP/hostname>
# Function to show usage
usage() {
  echo "Usage: $0 -H admin@host --target <target IP/hostname>"
  exit 3  # Unknown status
}
# Default exit codes for Icinga plugins
OK=0
WARNING=1
CRITICAL=2
UNKNOWN=3
# Parse arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    -H) HOST="$2"; shift ;;
    --target) TARGET="$2"; shift ;;
    *) usage ;;
  esac
  shift
done
# Check if HOST and TARGET were provided
if [[ -z "$HOST" || -z "$TARGET" ]]; then
  echo "UNKNOWN: Required arguments -H and --target are missing."
  usage
fi

SSHPASS="NokiaSrl1!"
# Perform ping and check the result
sshpass -p $SSHPASS ssh -o StrictHostKeyChecking=no admin@$HOST ping -c 2 -W 2 "$TARGET" > /dev/null 2>&1
PING_STATUS=$?
if [[ $PING_STATUS -eq 0 ]]; then
  echo "OK: Ping to $TARGET from $HOST is successful."
  exit $OK
else
  echo "CRITICAL: Ping to $TARGET from $HOST failed."
  exit $CRITICAL
fi
