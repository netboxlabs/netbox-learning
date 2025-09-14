# NetBox Discovery - Quickstart

The purpose of this quickstart is to get you up and running with NetBox Discovery as quickly as possible. In a few commands you will install and pre-configure everything you need to start experimenting with NetBox Discovery:

- NetBox with the Diode Plugin
- Diode
- Lab devices in ContainerLab
- NetBox Discovery configurations

You will be able to run simple scripts to use both features of NetBox Discovery:

1. Network Diccovery
2. Device Discovery

> [!TIP]
>   
> If you hit any issues when running through this quickstart guide you can get help by posting in the #netbox channel in the NetDev Slack  
> If you don't already have an account in the NetDev Slack, you can create one here: [https://netdev.chat/](https://netdev.chat/)  

## Setup

> [!TIP]
>  
> - The workshop can be run on a server or virtual machine with a public or private IP. Please see the additional step for private IP options below.
> - We recommend using a machine with at least 4GB of RAM and 2 cores. If you're using a discount cloud or are going to run Cisco IOS images, we recommend at least 8GB of RAM and 4 cores.  
> - The workshop has been tested on Ubuntu up to 25.04 (Plucky Puffin). It _should_ work on other Linux distros but if you hit any problems please create an [issue](https://github.com/netboxlabs/netbox-learning/issues) in GitHub  
> - Unfortunately MacOS is not supported. The quickstart relies heavily on ContainerLab which does not have native support for MacOS  


### Clone the repo and go to the Discovery Quickstart

> [!TIP]
>  
> If you're using this on a fork, be sure to update the git repo URL accordingly  

```
cd /opt
git clone https://github.com/netboxlabs/netbox-learning.git
cd netbox-learning/netbox-discovery-quickstart
```

### Install the required tooling on the host and set up users

```
./0_install_host_tooling.sh
```

### Switch to the correct user

> [!TIP]
>  
> We run as a separate user so that we can correctly mount our NetBox Discovery configuration in later steps  

```
su - quickstart
```

### Generate and export the necessary environment variables for the quickstart

 Optionally set a private IP.  If this machine does not have a public ipv4 address assigned on a local interface, this option should be used. 

 Replace <IP address> with an IP address assigned to the local machine - eg: `10.1.1.1` (**NOTE:** Do not use `127.0.0.1`/`localhost` as it will cause the NetBox healthcheck to fail and connections to get stuck in containers)

```
export MY_EXTERNAL_IP=<IP address>
```

> [!TIP]
>   
> `1_set_envvars.sh` writes the variables it generates to a file in the root directory called `environment`  
> This is so that you can run `1_set_envvars.sh` in separate terminals and get the same results  
> If you need to recreate the envirionment variables, just delete `environment` and run the script again  

```
source 1_set_envvars.sh
```

### Start Diode.

```
./2_start_diode.sh
```

> [!TIP]
> Once Diode has finished installing be sure to follow the instructions to export the `NETBOX_TO_DIODE_CLIENT_SECRET` as it is required when starting NetBox.  
> `export NETBOX_TO_DIODE_CLIENT_SECRET=$(jq -r '.[] | select(.client_id == "netbox-to-diode") | .client_secret' ./diode/oauth2/client/client-credentials.json)`  

### Start NetBox with the Diode plugin installed and configured.

> [!TIP]
>   
> NetBox runs a lot of database migrations when starting up for the first time so this can take a few minutes  

```
./3_start_netbox.sh
```

When this step finishes you can check that NetBox is working by logging into NetBox using the URL and credentials provided in the command line output.

### Generate Diode Client Credentials

> [!TIP]   
> NetBox credentials:  
> username: `admin`  
> password: `admin`  

In order for the discovery agents to communicate with Diode, you need to create some client credentials.

- Go to your NetBox instance
- In the left-hand pane navigate to `Diode` -> `Client Credentials`
- Click on `+ Add a Credential`
- For the `Client Name` enter any name you like and then click `Create`
- **IMPORTANT** on your command line, export the credentials so that they can be used in the next steps:
  - `export DIODE_CLIENT_ID="<your-client-id>"`
  - `export DIODE_CLIENT_SECRET="<your-client-secret>"`

Diode is now ready to start ingesting data from NetBox Discovery into our NetBox instance!

### Start the lab network

We need some lab devices to run our device discovery against and for this we will use ContainerLab.

> [!TIP]
> 
> The default lab uses two Nokia SR Linux devices because they are freely available and don't use much memory.  

> [!TIP]
> 
> There's also a single node Cisco IOS example lab but you'll need to provide your own Cisco IOS containerized image  
> You can find the ContainerLab instructions for Cisco IOS [here](https://containerlab.dev/manual/kinds/)  
> Update `network/cisco_ios/ios.clab.yml` to point it to your Cisco IOS Docker image  

```
./4_start_network.sh network/srl.clab.yml
```

> [!TIP]
> 
> If you see an `ERROR` followed by `Warning: No existing labs were destroyed or an error occurred.` you can ignore it. This step attempts to clean up any existing ContainerLab labs and the first time round there aren't any to clean up.  

After a short while you should see a summary of your ContainerLab devices, like this:

```
╭──────────────────────────────────────┬──────────────────────────────┬─────────┬────────────────╮
│                 Name                 │          Kind/Image          │  State  │ IPv4/6 Address │
├──────────────────────────────────────┼──────────────────────────────┼─────────┼────────────────┤
│ clab-discovery-quickstart-nokia-srl1 │ nokia_srlinux                │ running │ 172.24.0.100   │
│                                      │ ghcr.io/nokia/srlinux:24.7.2 │         │ N/A            │
├──────────────────────────────────────┼──────────────────────────────┼─────────┼────────────────┤
│ clab-discovery-quickstart-nokia-srl2 │ nokia_srlinux                │ running │ 172.24.0.101   │
│                                      │ ghcr.io/nokia/srlinux:24.7.2 │         │ N/A            │
╰──────────────────────────────────────┴──────────────────────────────┴─────────┴────────────────╯
```

## NetBox Discovery

NetBox Discovery has two modes: **Network Discovery** and **Device Discovery**

> [!TIP]
> 
> You can find the full NetBox Discovery documentation here: [https://netboxlabs.com/docs/diode/?focus=community](https://netboxlabs.com/docs/diode/?focus=community)  

**Network Discovery** uses `nmap` under the hood to find active IPs and ingests them into NetBox.

**Device Discovery** uses `NAPALM` under the hood to discover network device information and ingest it to NetBox.

### Network Discovery

Network Discovery has various configuration options, but for now we will focus on discovering active IPs in a subnet. In this case we will use the subnet we pre-configured for our lab devices: `172.24.0.0/24`

Before we run our network discovery, let's take a quick look at the configuration file that will be created to define the discovery behaviour.

```
orb:
  config_manager:
    active: local
  backends:
    network_discovery:
    common:
      diode:
        target: grpc://${MY_EXTERNAL_IP}:8080/diode
        client_id: ${DIODE_CLIENT_ID}
        client_secret: ${DIODE_CLIENT_SECRET}
        agent_name: agent1
  policies:
    network_discovery:
      loopback_policy:
        config:
        scope:
          targets: 
            - ${DOCKER_SUBNET}
```

Here you can see various variables that will be populated automatically when you run the script below. Here's the most important part in which we define the `targets` for our network discovery.

```
  policies:
    network_discovery:
      loopback_policy:
        config:
        scope:
          targets: 
            - ${DOCKER_SUBNET}
```

`targets` is a list of individual IPs, IP ranges or subnets. In this case when we run the script we will insert a single subnet for our ContainerLab devices, which as mentioned above is `172.24.0.0/24`

___

Now let's run the network discovery!

```
./5_start_network_discovery.sh
```

In our lab we have two SR Linux devices with management IPs at `172.24.0.100` and `172.24.0.101`. When we run our network discovery we should expect to find those, but also a few other IPs that are being used in our quickstart guide. You can ignore those.

Now go and take a look into NetBox under `IPAM`-> `IP Addresses` and you should see the IP addresses the network discovery found.

Now exit out of network discovery with `Ctrl+C`

### Device Discovery

Using Device Discovery we will extract information from our lab devices and then ingest that information into NetBox. Device Discovery requires that we provide some information about our devices so that connections can be established.

Let's take a look at the configuration file that will be generated for Device Discovery.

```
orb:
  config_manager: 
    active: local
  backends:
    device_discovery:
    common:
      diode:
        target: grpc://${MY_EXTERNAL_IP}:8080/diode
        client_id: ${DIODE_CLIENT_ID}
        client_secret: ${DIODE_CLIENT_SECRET}
        agent_name: agent2
  policies:
    device_discovery:
      discovery_1:
        config:
          schedule: "* * * * *"
          defaults:
            site: New York NY
        scope:
          - driver: srl
            hostname: 172.24.0.100
            username: admin
            password: NokiaSrl1!
            optional_args:
               insecure: True
          - driver: srl
            hostname: 172.24.0.101
            username: admin
            password: NokiaSrl1!
            optional_args:
               insecure: True
```

Again you can see various variables that will be populated automatically when you run the script below. Here's the most important part in which we define the devices for our network discovery.

```
        scope:
          - driver: srl
            hostname: 172.24.0.100
            username: admin
            password: NokiaSrl1!
            optional_args:
               insecure: True
          - driver: srl
            hostname: 172.24.0.101
            username: admin
            password: NokiaSrl1!
            optional_args:
               insecure: True
```

You can see that we need to provide the IPs, and SSH credentials for our lab devices. We've also used NAPALM's `optional_args` functionality to specifiy `insecure: True` which tells the NAPALM driver to skip TLS so we don't need to concern ourselves with certificates in this quickstart.

Let's go ahead and run it:

```
./6_start_device_discovery.sh
```

First NetBox Discovery will load the environment and the policies we've defined in our configuration. The configuration section `schedule: "* * * * *"` tells the discovery agent to run every minute, so you'll need to wait for a minute to pass for the first device discovery run to execute.

- Keep an eye on `Devices` -> `Devices`. Eventually you'll see the discovered device details start to show up.
- You'll also notice in our configuration above that we defined the default site for devices to be `New York NY`. Go to NetBox and click on `Organization` -> `Sites` where you'll now see our `New York NY` site.
- Now click on `New York NY` and then `Devices` in the right hand pane, where you will now see our devices.
- Now click on the first device `srl1`. Here you can see that the `Device Type`, `Platform` and `Status` have all been set correctly.
- Now click on the `Interfaces` tab for `srl1`. Now you'll see that all our our device interfaces have been successfully ingested into NetBox, with the correct administrative statuses which are called `Enabled` in NetBox.
- Lastly, click on the top interface `ethernet-1/1`. Now you'll see that NetBox Discovery has correctly ingested the correct `MAC Address`, `MTU`, and `Speed/Duplex` for the interface.

## Conclusion

In this short guide you have learned the basics of NetBox Discovery's two modes of operation: network discovery and device discovery. Feel free to play around with the environment you've created, and to fork the repo to do your own experiments with NetBox Discovery.