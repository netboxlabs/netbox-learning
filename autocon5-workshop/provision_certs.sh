#!/usr/bin/env bash
# Facilitator script — run once before running terraform apply in autocon5_infra/.
# Obtains the *.autocon5.netboxlabs.tech wildcard TLS certificate via Let's Encrypt
# DNS-01 challenge. DNS A records for participants are managed by Terraform.
#
# Usage:
#   DO_API_TOKEN=<token> bash provision_certs.sh
set -euo pipefail

REQUIRED_VARS=("DO_API_TOKEN")
for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "Error: Required environment variable '$var' is not set."
    exit 1
  fi
done

DOMAIN="autocon5.netboxlabs.tech"
CERT_DIR="$(cd "$(dirname "$0")/../autocon5_infra" && pwd)/certs"

# Note: DNS A records (netbox-<name>.autocon5, grafana-<name>.autocon5,
# gitea-<name>.autocon5) are managed by Terraform in autocon5_infra/.
# This script only obtains the wildcard TLS certificate.

# --- Obtain wildcard cert ---
echo
echo "--- Installing certbot and DigitalOcean DNS plugin ---"
echo

if ! command -v certbot &>/dev/null; then
  apt-get install -y certbot python3-certbot-dns-digitalocean
fi

DO_CREDS_FILE="$(mktemp)"
cat > "${DO_CREDS_FILE}" <<EOF
dns_digitalocean_token = ${DO_API_TOKEN}
EOF
chmod 600 "${DO_CREDS_FILE}"

echo
echo "--- Requesting wildcard certificate for *.${DOMAIN} ---"
echo

certbot certonly \
  --dns-digitalocean \
  --dns-digitalocean-credentials "${DO_CREDS_FILE}" \
  --dns-digitalocean-propagation-seconds 30 \
  -d "*.${DOMAIN}" \
  --non-interactive \
  --agree-tos \
  --email info@netboxlabs.com \
  --cert-name "${DOMAIN}"

rm -f "${DO_CREDS_FILE}"

mkdir -p "${CERT_DIR}"
cp /etc/letsencrypt/live/${DOMAIN}/fullchain.pem "${CERT_DIR}/cert.pem"
cp /etc/letsencrypt/live/${DOMAIN}/privkey.pem   "${CERT_DIR}/key.pem"
chmod 644 "${CERT_DIR}/cert.pem"
chmod 600 "${CERT_DIR}/key.pem"

echo
echo "✅ Done."
echo
echo "Wildcard cert written to:"
echo "  ${CERT_DIR}/cert.pem"
echo "  ${CERT_DIR}/key.pem"
echo "Expires: $(openssl x509 -enddate -noout -in ${CERT_DIR}/cert.pem)"
echo
echo "Run 'terraform apply' in autocon5_infra/ to provision participant droplets."
echo "Terraform will upload the cert to each droplet automatically."
echo
