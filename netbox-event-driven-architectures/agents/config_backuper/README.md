# NetBox Event-Driven Architectures Webinar 🚀

## Config Backuper Agent

By default the Config Backuper Agent waits for messages to appear on the `$SUBSCRIBE_SUBJECT` subject and then commits the contents to GitHub at `github.com/$GITHUB_ORG/$GITHUB_REPO/$HOSTNAME/running_config`.

### Configuration

The agent is configured on start up by the `.env` file in the agent's directory. We assume that you have already created a Slack app.

```
cat  agents/config_backuper/example.env 
NATS_SERVER="127.0.0.1:4222"                            # NATs server to connect to
SUBSCRIBE_SUBJECT="network.devices.running_config"      # NATs subject to subscribe to. The agent runs when a message is receieved
GITHUB_TOKEN="YOUR GITHUB TOKEN"                        # GitHub API token
GITHUB_ORG="YOUR GITHUB ORG"                            # GitHub Organization that running configs will be committed to
GITHUB_REPO="YOUR GITHUB REPO"                          # GitHub Repo that running configs will be committed to
```

### Start the agent

```
python agents/config_backuper/config_backuper.py 
Loaded environment for config_backuper.py
NATs Server: 127.0.0.1:4222
Writing device configs to: mrmrcoleman/device_config_backups
Subscribed to network.devices.running_config
```