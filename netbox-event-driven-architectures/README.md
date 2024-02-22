# Clone the repo
```
# git clone https://github.com/netboxlabs/netbox-learning.git
```


# Installation instructions

- Install ContainerLab

- Create and activate a virtual environment
```
# python3 -m venv venv
# source venv/bin/activate
(venv) #
```

- Install requirements.txt
```
(venv) # pip install -r requirements.txt
```



- Pull NATs Server Docker image and run it in daemon mode
```
(venv) # docker pull nats:latest
(venv) # docker run -p 4222:4222 -d nats:latest
```

- Install the NATs CLI (Official documentation: [https://github.com/nats-io/natscli](https://github.com/nats-io/natscli))
```
(venv) # cd /tmp
(venv) # curl -sf https://binaries.nats.dev/nats-io/natscli/nats@latest | sh
(venv) # mv ./nats /usr/bin # Or wherever you want to binary to live
```

- Create and confirm Nats contexts
```
(venv) #  nats context add localhost --description "Localhost"
(venv) #  nats context ls
╭──────────────────────────╮
│      Known Contexts      │
├────────────┬─────────────┤
│ Name       │ Description │
├────────────┼─────────────┤
│ localhost* │ Localhost   │
╰────────────┴─────────────╯

# Nats stored its config in here
~/.config/nats/context
```

# Test the facts backup agent
```
nats pub devices.facts '{"hostname": "TST-ROUTER-1", "fqdn": "TST-ROUTER-2", "vendor": "Nokia", "model": "7220 IXR-D3", serial_number": "Sim Serial No.", "os_version": "v23.10.1-218-ga3fc1bea5a", "uptime": -1.0, "interface_list": ["ethernet-1/", "ethernet-1/2", "ethernet-1/3", "ethernet-1/4", "ethernet-1/5", "ethernet-1/6", "ethernet-1/7", "ethernet-1/8", "ethernet-1/9", "ethernet-1/10", "ethernet-1/11", "ethernet-1/12", "ethernet-1/13", "ethernet-1/14", "ethernet-1/15", "ethernet-1/16", "ethernet-1/17", "ethernet-1/18", "ethernet-1/19", "ethernet-1/20", "ethernet-1/21", "ethernet-1/22", "ethernet-1/23", ethernet-1/24", "ethernet-1/25", "ethernet-1/26", "ethernet-1/27", "ethernet-1/28", "ethernet-1/29", "ethernet-1/30", "ethernet-1/31", "ethernet-1/32", "ethernet-1/33", "ethernet-1/34", "mgmt0"]}'
```

# Start the lab

```
(venv) # cd lab
(venv) # clab deploy
```

# Start the message bus (NATs)



