#!/bin/bash

ENV_FILE="environment"

# Function to generate random keys
generate_random_key() {
    head -c20 </dev/urandom | xxd -p
}

generate_random_base64_key() {
    openssl rand -base64 40 | head -c 40
}

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
    DOCKER_NETWORK="discovery-quickstart"
    DIODE_TO_NETBOX_API_KEY=$(generate_random_key)
    NETBOX_TO_DIODE_API_KEY=$(generate_random_key)
    DIODE_API_KEY=$(generate_random_key)
    INGESTER_TO_RECONCILER_API_KEY=$(generate_random_base64_key)

    # Write variables to the environment file
    cat <<EOF > "$ENV_FILE"
MY_EXTERNAL_IP=$MY_EXTERNAL_IP
NETBOX_PORT=$NETBOX_PORT
DOCKER_SUBNET=$DOCKER_SUBNET
DOCKER_NETWORK=$DOCKER_NETWORK
DIODE_TO_NETBOX_API_KEY=$DIODE_TO_NETBOX_API_KEY
NETBOX_TO_DIODE_API_KEY=$NETBOX_TO_DIODE_API_KEY
DIODE_API_KEY=$DIODE_API_KEY
INGESTER_TO_RECONCILER_API_KEY=$INGESTER_TO_RECONCILER_API_KEY
EOF
fi

# Export variables from the environment file
while IFS='=' read -r key value; do
    export "$key=$value"
done < "$ENV_FILE"

# Debug information to communicate values being used
echo
echo "--- Environment Variables Set ---"
echo "External IP: $MY_EXTERNAL_IP"
echo "NetBox will be deployed at: http://$MY_EXTERNAL_IP:$NETBOX_PORT"
echo "Docker subnet: $DOCKER_SUBNET"
echo "Docker network: $DOCKER_NETWORK"
echo "DIODE_TO_NETBOX_API_KEY: $DIODE_TO_NETBOX_API_KEY"
echo "NETBOX_TO_DIODE_API_KEY: $NETBOX_TO_DIODE_API_KEY"
echo "DIODE_API_KEY: $DIODE_API_KEY"
echo "INGESTER_TO_RECONCILER_API_KEY: $INGESTER_TO_RECONCILER_API_KEY"
echo "-----------------------------------"
