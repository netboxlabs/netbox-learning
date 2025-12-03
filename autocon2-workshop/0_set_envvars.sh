#!/bin/bash

# Attempt to fetch the external IPv4 address
EXTERNAL_IP=$(curl -4 -s ifconfig.me)  # Use -4 to ensure IPv4 is returned

# Check if the IP was retrieved successfully
if [ -z "$EXTERNAL_IP" ]; then
  echo "Error: Unable to determine external IPv4 address."
  exit 1
fi

export MY_EXTERNAL_IP=$EXTERNAL_IP

# Set service ports
export SLURPIT_PORT="8000"
export NETBOX_PORT="8001"
export ICINGA_PORT="8002"
export NETPICKER_PORT="8003"
export NETPICKER_API_PORT="8004"
export WORKSHOP_SUBNET="172.24.0.0/24"


# Debug information to communicate values being used
echo
echo "--- Environment Variables Set ---"
echo "External IP: $MY_EXTERNAL_IP"
echo "Slurpit will be deployed at: http://$MY_EXTERNAL_IP:$SLURPIT_PORT"
echo "NetBox will be deployed at: http://$MY_EXTERNAL_IP:$NETBOX_PORT"
echo "Icinga will be deployed at: http://$MY_EXTERNAL_IP:$ICINGA_PORT"
echo "NetPicker Frontend will be deployed at: http://$MY_EXTERNAL_IP:$NETPICKER_PORT"
echo "NetPicker API will be deployed at: $MY_EXTERNAL_IP:$NETPICKER_API_PORT"
echo "Workshop Docker network: $WORKSHOP_SUBNET"
echo "-----------------------------------"