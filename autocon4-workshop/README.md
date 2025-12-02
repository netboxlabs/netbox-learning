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


## Workshop Setup & Installation

> [!TIP]
>  
> - The workshop can be run on a server or virtual machine with a public or private IP. Please see the additional step for private IP options below.
> - We recommend using a machine with at least 4GB of RAM and 2 cores. If you're using a discount cloud or are going to run Cisco IOS images, we recommend at least 8GB of RAM and 4 cores.  
> - The workshop has been tested on Ubuntu up to 25.04 (Plucky Puffin). It _should_ work on other Linux distros but if you hit any problems please create an [issue](https://github.com/netboxlabs/netbox-learning/issues) in GitHub  
> - Unfortunately MacOS is not supported. The quickstart relies heavily on ContainerLab which does not have native support for MacOS  


### Install the required tooling on the host and set up users

```
./0_install_host_tooling.sh
```

### Generate and export the necessary environment variables for the quickstart (optional)

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

```bash
source 1_set_envvars.sh
```

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