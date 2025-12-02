# Closed-Loop Network Automation - Zero to Hero

_This workshop was originaly delivered as a hands-on, in-person workshop at Autocon4 ([WS:D3](https://networkautomation.forum/autocon4#workshops))_

Welcome to the Closed-Loop Network Automation - Zero to Hero! In this workshop we will build a fully functioning closed-loop network automation stack, including observability and network discovery feedback loops.

This workshop is intended to introduce you to the high-level concepts around closed-loop network automation, while also delivering you a fully functioning stack you can continue to experiment with. The workshop is split into sections covering different elements of the story. You should follow them sequentially.

## Modules

This workshop is split into various learning modules.

- Module 0 - [Introduction](./modules/module_0/README.md)
- Module 1 - [Configuring the network the old fashioned way](./modules/module_1/README.md)
- Module 2 - [Observability in support of network automation](./modules/module_2/README.md)
- Module 3 - [Using Discovery to get a baseline of your network](./modules/module_3/README.md)
- Module 4a - [Expressing network design through modeling (basic)](./modules/module_4a/README.md)
- Module 4b - [Expressing network design through modeling (advanced)](./modules/module_4b/README.md)
- Module 5 - [Configuring the network through automation](./modules/module_5/README.md)
- Module 6 - [Using Discovery to validate the state of the network](./modules/module_6/README.md)


## Setup & Installation

### Workshop Requirements

The following is the _minimum_ recommended environment for this workshop:
- Ubuntu 25.04
- 4 vCPUs
- 8 GB RAM 

The workshop has been tested on Ubuntu up to 25.04 (Plucky Puffin). It _should_ work on other Linux distros but if you hit any problems please create an [issue](https://github.com/netboxlabs/netbox-learning/issues) in GitHub.

The workshop can be run on a server or virtual machine with a private IPv4 address. Please see the additional step for private IP below.

> [!WARNING]
> Unfortunately MacOS is not supported. The workshop requires ContainerLab, which does not have native support for MacOS  


### Install the required tooling on the host and set up users

```bash
./0_install_host_tooling.sh
```

### Generate and export the necessary environment variables

#### Set the private IPv4 address (only if required)

If this machine does not have a public IPv4 address assigned on a local interface, the private IP must be explicitly set. In the command below, replace `<IP address>` with the IP address assigned to the local machine (e.g. `10.1.1.1`). Do not use `127.0.0.1` or `localhost` as it will cause the NetBox healthcheck to fail and connections to get stuck in containers.

```bash
export MY_EXTERNAL_IP=<IP address>
```

#### Export the environment variables

```bash
source ./1_set_envvars.sh
```

> [!TIP]
>   
> `1_set_envvars.sh` writes the variables it generates to a file in the root directory called `environment`  
> This is so that you can run `1_set_envvars.sh` in separate terminals and get the same results  
> If you need to recreate the envirionment variables, just delete `environment` and run the script again  

### Start Diode

```bash
./2_start_diode.sh
```

Once Diode has finished installing you need to export some credentials to your environment for the following steps.

> [!TIP]
>   
> `./3_set_diode_creds.sh` writes the variables it generates to a file in the root directory called `diode_creds`  
> This is so that you can run `./3_set_diode_creds.sh` in separate terminals and get the same results  
> If you need to recreate the envirionment variables, just delete `diode_creds` and run the script again 

```bash
source ./3_set_diode_creds.sh
```

### Start NetBox with the Diode plugin installed and configured and NetBox Branching enabled

> [!TIP]
>   
> NetBox runs a lot of database migrations when starting up for the first time so this can take a few minutes  

```bash
./4_start_netbox.sh
```

When this step finishes you can check that NetBox is working by logging into NetBox using the URL and credentials provided in the command line output.

### Start local Git server and create initial agent config

```bash
./5_start_gitea.sh
```

When this step finishes you can check that NetBox is working by logging into Gitea using the URL and credentials provided in the command line output.

### Start local Prometheus server

```bash
./6_start_prometheus.sh
```

When this step finishes you can check that Prometheus is working by using the URL and credentials provided in the command line output.

## What's Next?

Now that we've setup the workshop environment, you're ready to begin!

In **Module 0**, we'll get oriented with the workshop lab environment and learn the fundamentals of closed-loop network automation. We'll also introduce why discovery and observability feedback loops are critical to help create self-correcting automation systems.

---

**Continue to:** [Module 0 - Introduction](../module_0/README.md)