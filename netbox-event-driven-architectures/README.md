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


# Start the lab

```
(venv) # cd lab
(venv) # clab deploy
```

# Start the message bus (NATs)



