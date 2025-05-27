# Getting Hands On with NetBox Discovery and Assurance

This section provides a practical, hands-on experience with NetBox Discovery and Assurance features. Participants will learn how to spin up local containerlab devices, run network and device discovery, and interact with the results in NetBox Assurance.

## Instructions

### Getting set up

First, ensure you are in the Section 3 directory.

```bash
cd sections/Section-3/
```

#### Generating your Diode credentials

In order to send the results of our discovery to NetBox Assurance, via Diode, we first need Diode credentials.

To generate these, do the following:

> [!TIP]
>  
> You can find your NetBox instance at `http://${INFRA_IP}:8000/netbox`  
> Your credentials are `admin:admin`


1. Go to your NetBox instance
2. In left hand pane navigate to `Diode` -> `Client Credentials`
3. Click on `+ Add a Credential`
4. For `Client Name` enter: `discovery-workshop` and click `Create`
5. **IMPORTANT** Copy the `Client ID` and the `Client Secret` and paste them somewhere you can retrieve them in a moment
6. Click `Return to List`

You have now created your credentials.


#### Exporting the correct environment variables

Now we need to set up the environment so that the tools we're going to use can access the variables they need. We've automated most of this for you, but there are a couple of manual steps.

1. Export `DIODE_CLIENT_ID` with the `client-id` you just generated: `export DIODE_CLIENT_ID=<client-id>`
2. Export `DIODE_CLIENT_SECRET` with the `client-secret` you just generated: `export DIODE_CLIENT_SECRET=<client-secret>`
3. And now source the helper script to configure the rest:

```bash
source ./scripts/1_set_envvars.sh
```

Your environment is now ready.

#### Starting your network lab

In order to do some initial discovery we need a network to test against. For this we will use ContainerLab, which is preinstalled on your workshop VM. Let's take a look at our ContainerLab topology file by running `cat network/srl.clab.yml`

```yaml
name: discovery-quickstart-nokia

mgmt:
  network: discovery-quickstart
  ipv4-subnet: 172.24.0.0/24

topology:
  nodes:
    srl1:
      kind: nokia_srlinux
      type: ixrd3
      image: ghcr.io/nokia/srlinux:24.7.2
      mgmt-ipv4: 172.24.0.100
```

The topology is very simple, containing one SR Linux device, but it is ideal for our purposes. Now let's start the ContainerLab lab:

```bash
./scripts/2_start_network.sh network/srl.clab.yml
```

When it completes you should see something like this:

```yaml
╭───────────────────────────────┬──────────────────────────────┬─────────┬────────────────╮
│              Name             │          Kind/Image          │  State  │ IPv4/6 Address │
├───────────────────────────────┼──────────────────────────────┼─────────┼────────────────┤
│ clab-discovery-assurance-srl1 │ nokia_srlinux                │ running │ 172.24.0.100   │
│                               │ ghcr.io/nokia/srlinux:24.7.2 │         │ N/A            │
╰───────────────────────────────┴──────────────────────────────┴─────────┴────────────────╯
```

Your lab network is now ready.

> [!TIP]
>  
> If you're interested you can SSH into the SR Linux device and take a look around:  
> `ssh admin@172.24.0.100`  
> password: `NokiaSrl1!`


### Network Discovery

Now we're ready to try out Network Discovery. We will point our network discovery at the subnet that our ContainerLab devices are in, and then interact with the results in NetBox Assurance.

This step is also automated for you, but first lets look at some of what is going on under the hood. First we'll take a look at the `config.yaml` for our network discovery agent:

> [!TIP]
>  
> Our helper scripts actually substitutes all the variables below, _before_ sending the config to the agent  
> You'll see more ways to manage configs later in the workshop

```yaml
orb:
  config_manager:
    active: local
  backends:
    network_discovery:
    common:
      diode:
        target: grpc://${INFRA_IP}:${DIODE_PORT}/diode
        client_id: ${DIODE_CLIENT_ID}
        client_secret: ${DIODE_CLIENT_SECRET}
        agent_name: network-discovery
  policies:
    network_discovery:
      policy_1:
        config:
          timeout: 5
        scope:
          targets: [${DOCKER_SUBNET}]
```

Let's highlight some key sections in each discovery configuration:

- `backends` can be thought of as different types of discovery that the agent can run. In this case we that we are including `network_discovery` which is specific to this section and also `common` which is used in all configurations
- `policies` are used to configured the `backends` so in this case we are telling our `network_discovery` backend target the subnet we've created for our ContainerLab devices (`${DOCKER_SUBNET}`)

Next let's preview the command that is used to start the agent (**don't run yet**):

```
docker run -v $(pwd):/opt/orb/ \
   -e DIODE_CLIENT_SECRET=${DIODE_CLIENT_SECRET} \
   --network ${DOCKER_NETWORK} \
   mrmrcoleman/orb-agent:with_ccc run -c /opt/orb/agent.yaml
```

If you're unfamiliar with Docker this can look like a lot, but in practice it's quite straightforward:
- First we mount the local directory into the discovery agent container with `-v $(pwd):/opt/orb/`
- Then we tell the agent which DIODE_CLIENT_SECRET to use with `-e DIODE_CLIENT_SECRET=${DIODE_CLIENT_SECRET}`
- Then we tell the agent which Docker Network to run in with `--network ${DOCKER_NETWORK}` (**NOTE**: This is only necessary in our lab environment so that the agent can see the ContainerLab devices)
- And finally we ask the discovery agent to run using our `agent.yaml` configuration file with `netboxlabs/orb-agent:latest run -c /opt/orb/agent.yaml`

Now let's run the agent via our helper script and see what we get: 
```bash
./scripts/3_start_network_discovery.sh
```

> [!TIP]
>  
> You can use `Ctrl+C`to stop the discovery agent  

After a minute or so you should see something like this in the logs:

```bash
{"time":"2025-05-23T11:22:00.088169971Z","level":"INFO","msg":"network-discovery stdout","log":"time=2025-05-23T11:22:00.075Z level=INFO msg=\"running scanner\" targets=[172.24.0.0/24] policy=policy_1"}
{"time":"2025-05-23T11:22:14.674804014Z","level":"INFO","msg":"network-discovery stdout","log":"time=2025-05-23T11:22:14.668Z level=INFO msg=\"entities ingested successfully\" policy=policy_1"}
```

Great! Our first network discovery has run. Now let's go and look at what it found in NetBox Assurance.

- Go back to your NetBox instance (`http://$INFRA_IP:8000/netbox`, username: `admin`, password: `admin`)
- In the left pane navigate to `Assurance` -> `Active Deviations`
- You should see 4 IP addresses that were found by our network discovery
- Select all of them, then click `Apply Selected`, and the click `Apply 4 deviations`

Now we have successfully, discovered, inspected and applied our first discovery results. Let's have a look at them in NetBox:

- In the left pane of your NetBox instance, navigate to `IPAM` -> `IP Addresses`
- You'll now see that the IPs we discovered from the network are present in NetBox

You're network is now discovered.


### Device Discovery

Next we are going to look at device discovery. As we just saw, network discovery is responsible for scanning a subnet and discovering any hosts that are alive. Device discovery is responsible for interrogating devices on the network and returning detailed information about them.

This step is also automated for you, but first lets look at some of what is going on under the hood. First we'll take a look at the `config.yaml` for our device discovery agent:

```yaml
orb:
  config_manager: 
    active: local
  backends:
    device_discovery:
    common:
      diode:
        target: grpc://${INFRA_IP}:${DIODE_PORT}/diode
        client_id: ${DIODE_CLIENT_ID}
        client_secret: ${DIODE_CLIENT_SECRET}
        agent_name: device-discovery
  policies:
    device_discovery:
      discovery_1:
        config:
          defaults:
            site: New York NY
        scope:
          - driver: srl
            hostname: 172.24.0.100
            username: admin
            password: NokiaSrl1!
            optional_args:
               insecure: True
```

Let's look at some key sections in the config:

- Again we see the `backends` section but this time with `device_discovery` instead of `network_discovery`
- We also see an entry for a our device discovery `backend` under `policies` which tells the agent how to communicate with the devices, as defined in the (`scope`) section.

The `driver` parameter requires some additional explanation. Under the hood device discovery uses NAPALM. NAPALM comes with built-in support for the following network operating systems (NOSes):

- EOS
- Junos
- IOS-XR (NETCONF)
- IOS-XR (XML-Agent)
- NX-OS
- NX-OS SSH
- IOS

You may notice that our NOS, SRLinux, is not present in the above list. NAPALM also supports "community drivers" and many vendors have created their own community drivers for NAPALM, including Nokia for their SRLinux OS.

> [!TIP]
>  
> This also means you can create your own drivers for NetBox Device Discovery!

> [!TIP]
>  
> For this workshop we have already baked the SRLinux NAPALM driver into the image, so the driver.txt information is just for reference  

To include community drivers, we must tell device discovery where to find them. Let's preview the command that is used to start the agent (don't run yet):

```bash
docker run -v $(pwd):/opt/orb/ \
   -e DIODE_CLIENT_SECRET=${DIODE_CLIENT_SECRET}   \
   -e INSTALL_DRIVERS_PATH=/opt/orb/drivers.txt \
   --network ${DOCKER_NETWORK} \
   mrmrcoleman/orb-agent:with_ccc run -c /opt/orb/agent.yaml
```

You'll see that this is _almost_ identical to the command to run the network discovery agent, with one difference: `-e INSTALL_DRIVERS_PATH=/opt/orb/drivers.txt`

This line tells the agent where to find the drivers it needs, and the `drivers.txt` file just contains the following, which tells it which version of the SRLinux Community NAPALM driver to load:

```bash
% cat drivers.txt
napalm-srl==1.0.5
```

___

Now let's run the agent with the helper script and see what we get: 
```bash
./scripts/4_start_device_discovery.sh
```

> [!TIP]
>  
> You can use `Ctrl+C`to stop the discovery agent  

After a minute or so you should see something like this in the logs:

```bash
{"time":"2025-05-23T12:14:03.90164784Z","level":"INFO","msg":"device-discovery stderr","log":"INFO:apscheduler.executors.default:Job \"PolicyRunner.run (trigger: cron[month='*', day='*', day_of_week='*', hour='*', minute='*'], next run at: 2025-05-23 12:15:00 UTC)\" executed successfully"}
{"time":"2025-05-23T12:14:04.388330871Z","level":"INFO","msg":"device-discovery stderr","log":"INFO:device_discovery.client:Hostname 172.24.0.100: Successful ingestion"}
```

Great! Our first device discovery has run. Now let's go and look at what it found in NetBox Assurance.

- Go back to your NetBox instance (`http://$INFRA_IP:8000/netbox`, username: `admin`, password: `admin`)
- In the left pane navigate to `Assurance` -> `Active Deviations`
- You should see a lot of interfaces and 2 devices
- Select all of them, then click `Apply Selected`, and the click `Apply 4 deviations`

Now we have successfully, discovered, inspected and applied our first device discovery results. Let's have a look at them in NetBox:

- In the left pane of your NetBox instance, navigate to `Devices` -> `Devices`
- You'll now see that the two devices in our ContainerLab network are present in NetBox.
- Click on one of the devices and then click on `Interfaces` and you'll see that we have also discovered all of the interfaces for the devices.

You're devices have now been discovered!