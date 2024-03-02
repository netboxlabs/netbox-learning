# NetBox Event-Driven Architectures Webinar 🚀

## Discover Network Agent

By default the Discover Network Agent waits for messages to appear on the `` uses `nmap` to discover devices in a subnet and publishes the devices it finds to the `network.devices` subject on the message bus.

### Configuration

The agent is configured on start up by the `.env` file in the agent's directory.

```
cat agents/discover_network/example.env
NATS_SERVER="127.0.0.1:4222"                            # NATs server to connect to
PUBLISH_SUBJECT="network.devices"                       # NATs subject to publish discovered devices to
SUBSCRIBE_SUBJECT="network.actions.discover_network"    # NATs subject to subscribe to. The agent runs when a message is receieved. 
SUBNET_CIDR="172.20.20.0/24"                            # Which subnet to scan for devices. 172.20.20.0/24 is the ContainerLab default
IGNORE_IPS="172.20.20.1"                                # Specify multiple comma separated IPs to ignore. 172.20.20.1 is the default ContainerLab gateway (Docker bridge), so we ignore it
```

* **NATS_SERVER** tells the agent which NATs server to connect to
* PUBLI