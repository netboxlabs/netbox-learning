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

    # Write variables to the environment file
    cat <<EOF > "$ENV_FILE"
MY_EXTERNAL_IP=$MY_EXTERNAL_IP
NETBOX_PORT=$NETBOX_PORT
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
echo "NetBox username: admin"
echo "NetBox password: admin"
echo "-----------------------------------"
