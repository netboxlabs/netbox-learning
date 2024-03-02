# NetBox Event-Driven Architectures Webinar 🚀

## Discover Network Agent

By default the Discover Network Agent waits for messages to appear on the `$SUBSCRIBE_SUBJECT` subject and then uses `nmap` to discover devices in the `$SUBNET_CIDR` specified subnet, ignoring IPs in `$IGNORE_IPS` and publishes the devices it finds to the `$PUBLISH_SUBJECT` subject on the message bus.

### Configuration

The agent is configured on start up by the `.env` file in the agent's directory

```
cat agents/discover_network/example.env
NATS_SERVER="127.0.0.1:4222"                            # NATs server to connect to
PUBLISH_SUBJECT="network.devices"                       # NATs subject to publish discovered devices to
SUBSCRIBE_SUBJECT="network.actions.discover_network"    # NATs subject to subscribe to. The agent runs when a message is receieved. 
SUBNET_CIDR="172.20.20.0/24"                            # Which subnet to scan for devices. 172.20.20.0/24 is the ContainerLab default
IGNORE_IPS="172.20.20.1"                                # Specify multiple comma separated IPs to ignore. 172.20.20.1 is the default ContainerLab gateway (Docker bridge), so we ignore it
```

### Start the agent

```
python agents/discover_network/discover_network.py
Loaded environment for discover_network.py
NATs Server: 127.0.0.1:4222
Publishing to subject: network.devices
Monitoring subnet: 172.20.20.0/24
Ignoring IPs: ['172.20.20.1']
Subscribed to network.actions.discover_network
```