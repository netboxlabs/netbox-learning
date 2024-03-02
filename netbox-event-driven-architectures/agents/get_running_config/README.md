# Get Running Config Agent 🏃

By default the Get Running Agent waits for messages to appear on the `$SUBSCRIBE_SUBJECT` subject and then pulls all devices from NetBox that are in the `Active` state and have a `mgmt-ipv4` address. The agent then uses [NAPALM](https://napalm.readthedocs.io/en/latest/) to pull the running configs and publishes them to the `$PUBLISH_SUBJECT` subject on the message bus.

### Known limitations

The agent has a limited implementation which only supports Nokia SR Linux and Arista cEOS devices. It also uses hardcoded default credentials for the devices.

### Configuration

The agent is configured on start up by the `.env` file in the agent's directory.

```
cat agents/get_running_config/example.env 
NATS_SERVER="127.0.0.1:4222"                            # NATs server to connect to
PUBLISH_SUBJECT="network.devices.running_config"        # NATs subject to publish running configs to
SUBSCRIBE_SUBJECT="network.actions.get_running_config"  # NATs subject to subscribe to. The agent runs when a message is receieved
NETBOX_URL="https://yournetbox.instance.com/"           # NetBox instance to pull device inventory from
NETBOX_TOKEN="YOUR NETBOX TOKEN"                        # NetBox API token. Must have at least `read` permission on `dcim/device`
```

### Start the agent

```
python agents/get_running_config/get_running_config.py 
Loaded environment for get_running_config.py
NATs Server: 127.0.0.1:4222
Publishing to subject: network.devices.running_config
Pulling inventory from NetBox: https://sxtc8225.cloud.netboxapp.com/
Subscribed to network.actions.get_running_config
```