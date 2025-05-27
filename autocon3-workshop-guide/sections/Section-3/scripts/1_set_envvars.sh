#!/bin/bash

ENV_FILE="environment"

# Check if the environment file exists
if [ -f "$ENV_FILE" ]; then
    echo "Environment file found. Using existing variables."
else
    echo "First run, will generate new variables."

    # Fail is INFRA_IP is not set
    if [ -z "$INFRA_IP" ]; then
        echo "INFRA_IP is not set. Please set it and try again."
        exit 1
    fi

    # Fail is DIODE_CLIENT_ID is not set
    if [ -z "$DIODE_CLIENT_ID" ]; then
        echo "DIODE_CLIENT_ID is not set. Please set it and try again."
        exit 1
    fi
    
    # Fail is DIODE_CLIENT_SECRET is not set
    if [ -z "$DIODE_CLIENT_SECRET" ]; then
        echo "DIODE_CLIENT_SECRET is not set. Please set it and try again."
        exit 1
    fi
    
    # Generate new variables
    INFRA_IP=$INFRA_IP
    NETBOX_PORT="8000"
    DIODE_PORT="8080"
    DOCKER_SUBNET="172.24.0.0/24"
    DOCKER_NETWORK="discovery-quickstart"

    # Write variables to the environment file
    cat <<EOF > "$ENV_FILE"
INFRA_IP=$INFRA_IP
NETBOX_PORT=$NETBOX_PORT
DIODE_PORT=$DIODE_PORT
DOCKER_SUBNET=$DOCKER_SUBNET
DOCKER_NETWORK=$DOCKER_NETWORK
EOF
fi

# Export variables from the environment file
while IFS='=' read -r key value; do
    export "$key=$value"
done < "$ENV_FILE"

# Debug information to communicate values being used
echo
echo "--- Environment Variables Set ---"
echo "Infra IP: $INFRA_IP"
echo "DIODE_CLIENT_ID: $DIODE_CLIENT_ID"
echo "DIODE_CLIENT_SECRET: $DIODE_CLIENT_SECRET"
echo "NetBox instance is at: http://$INFRA_IP:$NETBOX_PORT/netbox"
echo "Diode instance is at: http://$INFRA_IP:$DIODE_PORT/diode"
echo "Docker subnet: $DOCKER_SUBNET"
echo "Docker network: $DOCKER_NETWORK"
echo "-----------------------------------"