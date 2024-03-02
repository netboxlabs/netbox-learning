# Device Alerter Agent 📢

By default the Reachability Agent waits for messages to appear on the `$SUBSCRIBE_SUBJECT` subject and then the device reported in the message is not present in the NetBox inventory, the agent publishes a message to Slack.

### Configuration

The agent is configured on start up by the `.env` file in the agent's directory. We assume that you have already created a Slack app.

```
cat agents/device_alerter/example.env 
NATS_SERVER="127.0.0.1:4222"                    # NATs server to connect to
SUBSCRIBE_SUBJECT="network.devices"             # NATs subject to subscribe to. The agent runs when a message is receieved
SLACK_TOKEN="YOUR SLACK BOT"                    # Slack App Token
SLACK_USERNAME="YOUR SLACK BOT USERNAME"        # Slack username to publish as
SLACK_CHANNEL="YOUR SLACK CHANNEL"              # Slack channel to publish to
NETBOX_URL="https://yournetbox.instance.com/"   # NetBox instance to pull device inventory from
NETBOX_TOKEN="YOUR NETBOX TOKEN"                # NetBox API token. Must have at least `read` permission on `dcim/device`
```

### Start the agent

```
python agents/device_alerter/device_alerter.py 
Loaded environment for device_alerter.py
NATs Server: 127.0.0.1:4222
Reading inventory from NetBox: https://sxtc8225.cloud.netboxapp.com/
Writing device alerts to Slack channel: event-driven-webinar with username: Slack Alert Bot
Subscribed to network.devices
```