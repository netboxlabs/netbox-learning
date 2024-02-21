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
pip install -r requirements.txt
```


- Install NATs
```
docker pull nats:latest
docker run -p 4222:4222 -ti nats:latest
```


# Start the lab

```
cd lab
clab deploy
```

# Start the message bus (NATs)



