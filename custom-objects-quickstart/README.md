# NetBox Custom Objects - Quickstart

This simple repo is intended to get you up and running with NetBox Custom Objects quickly, using NetBox Docker.

## Quick Setup

## Prerequisites
- Docker
- Python 3.8 or higher

### Setup

1. Clone this repository:
```bash
git clone https://github.com/netboxlabs/netbox-learning.git
cd custom-object-testing
```

2. Set up your environment:

[!NOTE]
> By default NetBox will be exposed on your **external** IP address which will not work in most home environments.  
> To override this set the `EXTERNAL_IP` variable as shown below. `127.0.0.1` usually works, otherwise choose a local interface IP.

```bash
# OPTIONAL: Set IP address
export EXTERNAL_IP=127.0.0.1

# Set up environment variables
source 1_set_envvars.sh
```


3. Start NetBox with Custom Objects

```bash
# Start NetBox instance
./2_start_netbox.sh
```

### Notes

- Environment variables are written into `environment`. To start from fresh:

```bash
# delete the environment file
rm environment

# Stop NetBox and clean up temporary files
cd netbox-docker
docker compose down
cd ..
rm -fr netbox-docker

# Then go to step 2
```

- The time taken for NetBox to start up depends greatly on the available hardware. The timeout is set to 600 seconds. You can change this in `2_start_netbox.sh`.
- The latest available version of NetBox Custom Objects will be used. You can edit `2_start_netbox.sh` to change this behaviour.