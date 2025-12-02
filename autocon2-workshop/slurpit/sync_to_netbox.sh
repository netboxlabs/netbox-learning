#!/bin/bash

# Enable flags to exit on errors, unset variables, and pipeline failures
set -euo pipefail

# Check if required environment variables are set
if [[ -z "${MY_EXTERNAL_IP:-}" || -z "${SLURPIT_PORT:-}" ]]; then
    echo "Error: Environment variables MY_EXTERNAL_IP and SLURPIT_PORT must be set."
    exit 1
fi

# Construct the URLs using the environment variables
URL_SYNC="http://${MY_EXTERNAL_IP}:${SLURPIT_PORT}/run/plugin/sync"
URL_SYNC_QUEUE="http://${MY_EXTERNAL_IP}:${SLURPIT_PORT}/run/plugin/sync_queue"

# Curl the URLs, with -f to fail on HTTP errors
echo "Navigating to $URL_SYNC..."
curl -fsS "$URL_SYNC"

sleep 5

echo "Navigating to $URL_SYNC_QUEUE..."
curl -fsS "$URL_SYNC_QUEUE"

echo "Both URLs accessed successfully."