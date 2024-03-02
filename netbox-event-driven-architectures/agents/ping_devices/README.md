# NetBox Event-Driven Architectures Webinar 🚀

## Ping Devices Agent

By default the Ping Agent waits for messages to appear on the `$SUBSCRIBE_SUBJECT` subject and then pulls all devices from NetBox that are in the `Active` state and have a `mgmt-ipv4` address. The agent then uses `ping` to check if the devices are reachable and publishes the results to the `$PUBLISH_SUBJECT` subject on the message bus.

### Configuration

The agent is configured on start up by the `.env` file in the agent's directory.

```
cat agents/ping_devices/example.env 
NATS_SERVER="127.0.0.1:4222"                            # NATs server to connect to
PUBLISH_SUBJECT="network.devices.reachable"             # NATs subject to publish ping results to
SUBSCRIBE_SUBJECT="network.actions.ping_devices"        # NATs subject to subscribe to. The agent runs when a message is receieved
NETBOX_URL="https://yournetbox.instance.com/"           # NetBox instance to pull device inventory from
NETBOX_TOKEN="YOUR NETBOX TOKEN"                        # NetBox API token. Must have at least `read` permission on `dcim/device`
```

### Start the agent

```
python agents/ping_devices/ping_devices.py
Loaded environment for ping_devices.py
NATs Server: 127.0.0.1:4222
Publishing to: network.devices.reachable
Pulling inventory from NetBox: https://sxtc8225.cloud.netboxapp.com/
Subscribed to network.actions.ping_devices
```