#!/bin/bash

ENV_FILE="environment"

# Check if the environment file exists
if [ -f "$ENV_FILE" ]; then
    echo "Environment file found. Using existing variables."
else
    echo "Environment file not found. Generating new variables."

    if [[ -z "${MY_EXTERNAL_IP}" ]]; then
	# Attempt to fetch the external IPv4 address
    	EXTERNAL_IP=$(curl -4 -s ifconfig.me)  # Use -4 to ensure IPv4 is returned
    	# Check if the IP was retrieved successfully
    	if [ -z "$EXTERNAL_IP" ]; then
        	echo "Error: Unable to determine external IPv4 address."
        	exit 1
    	fi
    else
	EXTERNAL_IP=${MY_EXTERNAL_IP}
    fi

    # Generate new variables
    MY_EXTERNAL_IP=$EXTERNAL_IP
    NETBOX_PORT="8000"
    DOCKER_SUBNET="172.24.0.0/24"
    DOCKER_NETWORK="autocon5-workshop"
    NETBOX_TOKEN="1234567890"
    SRL_USERNAME="admin"
    SRL_PASSWORD="NokiaSrl1!"

    # Write variables to the environment file
    cat <<EOF > "$ENV_FILE"
MY_EXTERNAL_IP=$MY_EXTERNAL_IP
NETBOX_PORT=$NETBOX_PORT
DOCKER_SUBNET=$DOCKER_SUBNET
DOCKER_NETWORK=$DOCKER_NETWORK
NETBOX_TOKEN=$NETBOX_TOKEN
SRL_USERNAME=$SRL_USERNAME
SRL_PASSWORD=$SRL_PASSWORD
EOF
fi

# Ensure SRL credentials are present (may be missing from older environment files)
if ! grep -q "^SRL_USERNAME=" "$ENV_FILE"; then
    echo "SRL_USERNAME=admin" >> "$ENV_FILE"
    echo "SRL_PASSWORD=NokiaSrl1!" >> "$ENV_FILE"
fi

# Export variables from the environment file
while IFS='=' read -r key value; do
    export "$key=$value"
done < "$ENV_FILE"

# Derive convenience URLs from base vars (not persisted to file — always computed fresh)
export NETBOX_URL="http://${MY_EXTERNAL_IP}:${NETBOX_PORT}"
export GITEA_URL="http://${MY_EXTERNAL_IP}:3000"
export GRAFANA_URL="http://${MY_EXTERNAL_IP}:3001"

# Debug information to communicate values being used
echo
echo "--- Environment Variables Set ---"
echo "External IP: $MY_EXTERNAL_IP"
echo "NetBox will be deployed at: $NETBOX_URL"
echo "Docker subnet: $DOCKER_SUBNET"
echo "Docker network: $DOCKER_NETWORK"
echo "NetBox token: $NETBOX_TOKEN"
echo "-----------------------------------"

# Load Diode credentials if available
DIODE_JSON="./diode/oauth2/client/client-credentials.json"
if [ -f "$DIODE_JSON" ] || [ -f "diode_creds" ]; then
    source ./3_set_diode_creds.sh
fi