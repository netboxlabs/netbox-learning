#!/bin/bash

CREDS_FILE="diode_creds"
JSON_FILE="./diode/oauth2/client/client-credentials.json"

# Check if the credentials file exists
if [ -f "$CREDS_FILE" ]; then
    echo "Credentials file found. Using existing variables."
else
    echo "Credentials file not found. Generating new variables."

    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        echo "Error: jq is required but not installed. Please install jq."
        exit 1
    fi

    # Check if the JSON credentials file exists
    if [ ! -f "$JSON_FILE" ]; then
        echo "Error: Required file $JSON_FILE not found."
        exit 1
    fi

    # Extract secrets from the JSON file
    NETBOX_TO_DIODE_CLIENT_SECRET=$(jq -r '.[] | select(.client_id == "netbox-to-diode") | .client_secret' "$JSON_FILE")
    DIODE_CLIENT_SECRET=$(jq -r '.[] | select(.client_id == "diode-ingest") | .client_secret' "$JSON_FILE")
    
    # Verify that the secrets were extracted successfully
    if [ -z "$NETBOX_TO_DIODE_CLIENT_SECRET" ]; then
        echo "Error: Unable to extract client_secret for 'netbox-to-diode'."
        exit 1
    fi
    
    if [ -z "$DIODE_CLIENT_SECRET" ]; then
        echo "Error: Unable to extract client_secret for 'diode-ingest'."
        exit 1
    fi

    # Hardcode the client ID
    DIODE_CLIENT_ID="diode-ingest"

    # Write variables to the credentials file
    cat <<EOF > "$CREDS_FILE"
NETBOX_TO_DIODE_CLIENT_SECRET=$NETBOX_TO_DIODE_CLIENT_SECRET
DIODE_CLIENT_ID=$DIODE_CLIENT_ID
DIODE_CLIENT_SECRET=$DIODE_CLIENT_SECRET
EOF
fi

# Export variables from the credentials file
while IFS='=' read -r line; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    
    # Skip lines that don't contain '='
    [[ "$line" != *"="* ]] && continue

    # Split on first '=' only
    key="${line%%=*}"
    value="${line#*=}"

    export "$key=$value"
done < "$CREDS_FILE"

# Debug information to communicate values being used
echo
echo "--- Diode Credentials Set ---"
echo "NETBOX_TO_DIODE_CLIENT_SECRET: $NETBOX_TO_DIODE_CLIENT_SECRET"
echo "DIODE_CLIENT_ID: $DIODE_CLIENT_ID"
echo "DIODE_CLIENT_SECRET: $DIODE_CLIENT_SECRET"
echo "------------------------------"

