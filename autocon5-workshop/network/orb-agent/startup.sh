#!/bin/sh

# Source environment variables
set -a  # automatically export all variables
. /opt/orb/.env
set +a

# Install napalm-srl
pip install napalm-srl==1.0.5 --break-system-packages -q

# Install iproute2 for network configuration
apt-get update -qq && apt-get install -y -qq iproute2 > /dev/null 2>&1

# Wait for eth1 interface to be available (containerlab attaches it after container starts)
echo "Waiting for eth1 interface..."
for i in $(seq 1 30); do
    if ip link show eth1 > /dev/null 2>&1; then
        echo "eth1 interface found"
        break
    fi
    sleep 1
done

# Configure data plane interface
ip addr add 192.168.1.2/30 dev eth1 2>/dev/null || true
ip link set eth1 up

# Add route to web server network via srl1
ip route add 192.168.2.0/30 via 192.168.1.1 2>/dev/null || true

echo "Network configuration complete"
ip addr show eth1
ip route

# Start orb-agent with config file
exec /usr/local/bin/orb-agent run --config /opt/orb/agent.yaml