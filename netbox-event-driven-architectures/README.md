# NetBox Event-Driven Architectures Webinar 🚀

> ⚠️ These instructions have been tested on Ubuntu 22.04, YMMV.
> If you need support running the demo join the **#netbox-learning** channel in the [NetDev Slack](https://netdev.chat/)

You can run this demo against Open Source NetBox or NetBox Cloud. If you don't have a NetBox testing instance to hand, you can spin up a free NetBox Cloud instance in about 90 seconds over here: [https://signup.netboxlabs.com/](https://signup.netboxlabs.com/)

# Follow along with the webinar

On March 1 2024 we ran a webinar in which you can see a walk through of this repo. Jump to [21:45 over here on YouTube](https://www.youtube.com/watch?v=K3qaLc8CYO8) to see it in action.

You can also follow along with the slide deck here: [Event Driven Architectures with NetBox](https://docs.google.com/presentation/d/1aWogRiM182vM_mM7Ty8lp7vJpEVqCYSzCDqYyZ5s64I/)

# Getting started

This README will get you the core requirements for running the demo. Individual agents have their own installation instructions that you can find below under **Agents**.

## Install tooling

### Docker
```
apt install docker.io
```

### ContainerLab
```
bash -c "$(curl -sL https://get.containerlab.dev)"
```

### NATs

Pull NATs Server Docker image and run it in daemon mode exposing the relevant ports: 4222 for client connections, and 8222 for HTTP management reporting in case you'd later like to use tools like `nats-top`
```
docker pull nats:latest
docker run -p 4222:4222 -p 8222:8222 --name nats-server -d nats:latest
```

Create and confirm Nats context
```
nats context add event_driven_webinar --description "Event Driven Webinar"
nats context ls
╭─────────────────────────────────────────────╮
│                Known Contexts               │
├──────────────────────┬──────────────────────┤
│ Name                 │ Description          │
├──────────────────────┼──────────────────────┤
│ event_driven_webinar │ Event Driven Webinar │
╰──────────────────────┴──────────────────────╯
```

### Install `nmap`

```
apt install nmap
```


## Set up the local environment

### Clone the repo
```
git clone https://github.com/netboxlabs/netbox-learning.git
cd netbox-learning/netbox-event-driven-architectures/
```

### Start the ContainerLab network

```
(venv) cd lab
(venv) clab deploy
+---+-----------------------------------+--------------+-----------------------+---------------+---------+----------------+----------------------+
| # |               Name                | Container ID |         Image         |     Kind      |  State  |  IPv4 Address  |     IPv6 Address     |
+---+-----------------------------------+--------------+-----------------------+---------------+---------+----------------+----------------------+
| 1 | clab-event-driven-webinar-RCM-WR1 | 9f8272a79e5b | ghcr.io/nokia/srlinux | nokia_srlinux | running | 172.20.20.2/24 | 2001:172:20:20::2/64 |
| 2 | clab-event-driven-webinar-RCM-WR2 | beaa0713e857 | ghcr.io/nokia/srlinux | nokia_srlinux | running | 172.20.20.3/24 | 2001:172:20:20::4/64 |
| 3 | clab-event-driven-webinar-RCM-WR3 | 4dd31d8bccb9 | ghcr.io/nokia/srlinux | nokia_srlinux | running | 172.20.20.4/24 | 2001:172:20:20::3/64 |
+---+-----------------------------------+--------------+-----------------------+---------------+---------+----------------+----------------------+
(venv) cd ..
```

### Create and activate a virtual environment

```
apt install python3.10-venv
python3 -m venv venv
source venv/bin/activate
(venv)
```

### Install package requirements and make the local available as Python packages
 
```
(venv) pip install -r requirements.txt
(venv) pip install -e .
```

### Install the SR Linux driver for NAPALM
```
git clone https://github.com/napalm-automation-community/napalm-srlinux.git
cd napalm-srlinux
pip install -r requirements.txt
python3 setup.py install
cd ..
```
# Agents

The nature of event-driven architectures means that all agents are independent of each other in terms of startup orders. However some agents only act when they observe events on the message bus that are created by other agents. For example, the Reachability Alerter Agent reacts to messages on the `network.devices.reachable` subject, which is populated by the Ping Device Agent. The **Subscribes to** and **Publishes to** columns are useful in understanding these relationships.

Each agent reads from a `.env` file on in its local directory on startup in order to function. For example the Discover Network Agent will look for `.agents/discover_network/.env`. Each agent has an `example.env` file in its local directory. Populate these with the values for your environment and then copy them over. For example:

```
cp agents/discover_network/example.env agents/discover_network/.env
```

> ⚠️ Your populated `.env` file will contain confidential information. Do not push it to GitHub! `.env` is already added in `.gitignore` to help prevent this.

|Agent|Function|Subcribes to|Publishes to|External Dependencies|Instructions|
|---|---|---|---|---|---|
|Discover Network|Scans a subnet for devices|network.actions.discover_network|network.devices|Network|[README](./agents/discover_network/README.md)|
|Ping Devices|Pings devices found in NetBox|network.actions.ping_devices|network.devices.reachable|Network, NetBox|[README](./agents/ping_devices/README.md)|
|Get Running Config|Pulls running config from devices found in NetBox|network.actions.get_running_config|network.devices.running_config|Network, NetBox|[README](./agents/get_running_config/README.md)|
|Reachability Alerter|Creates an alert in Slack whenever a device is unreachable|network.devices.reachable|n/a|Slack|[README](./agents/reachability_alerter/README.md)|
|Device Alerter|Creates an alert in Slack whenever an unknown device is found in the network|network.devices|n/a|Slack, NetBox|[README](./agents/device_alerter/README.md)|
|Config Backuper|Commits device running config to GitHub|network.devices.running_config|n/a|GitHub|[README](./agents/config_backuper/README.md)|
