# NetBox Event-Driven Architectures Webinar 🚀

## Webhook Handler Agent

By default the Webhook Handler Agent accepts HTTP POST requests on `http://0.0.0.0:5000/webhook` and expects to find the payload in the format:

```
{"action":"$ACTION"}
```

Where `$ACTION` can be one of:

```
network.actions.discover_network
network.actions.ping_devices
network.actions.get_running_config
```

When the agent receices a payload that fits the above expectations it then puts a message on the corresponding subject determined by the action, to start other agents.

### Configuration

The agent is configured on start up by the `.env` file in the agent's directory.

```
cat  agents/webhook_handler/example.env 
NATS_SERVER="127.0.0.1:4222"                            # NATs server to connect to
```

### Start the agent

```
python agents/webhook_handler/webhook_handler.py 
Loaded environment for webhook_handler.py
NATs Server: 127.0.0.1:4222
Publishing to subject: None
INFO:     Started server process [605005]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```