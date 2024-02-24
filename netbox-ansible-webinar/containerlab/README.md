# Containerlab Quick Start Guide

## Introduction
Follow this guide to build a 3 node Arista cEOS network using containerlab (https://containerlab.dev/). 

Containerlab provides a CLI for orchestrating and managing container-based networking labs. It starts the containers, builds a virtual wiring between them to create lab topologies of users choice and manages labs lifecycle.

This guide gives a quick overview to get started and build a lab with the following elements: 

- 3 x Arista cEOS virtual devices connected to each other
- all nodes are connected to the same virtual management network 

This guide is based on using an Ubuntu 22.04 VM, but in general the requirements for containerlab to run are: 

- A user should have sudo privileges to run containerlab.
- A Linux server/VM and Docker installed.
- Load container images (e.g. Nokia SR Linux, Arista cEOS) that are not downloadable from a container registry. Containerlab will try to pull images at runtime if they do not exist locally. 

## Topology definition file
Lab topologies are defined in YAML files named in the format {lab-name}.clab.yaml they define the hosts, the image types and the connections. This lab uses the following file called `webinar.clab.yaml`:

```
name: webinar

mgmt:
  network: webinar-net
  ipv4-subnet: 172.21.21.0/24

topology:

  nodes:
    ceos-sw-1:
      kind: ceos
      image: ceos:4.29.0.2F
      mgmt-ipv4: 172.21.21.2
    ceos-sw-2:
      kind: ceos
      image: ceos:4.29.0.2F
      mgmt-ipv4: 172.21.21.3
    ceos-sw-3:
      kind: ceos
      image: ceos:4.29.0.2F
      mgmt-ipv4: 172.21.21.4

  links:
    - endpoints: ["ceos-sw-1:eth1", "ceos-sw-2:eth1"]
    - endpoints: ["ceos-sw-1:eth2", "ceos-sw-3:eth1"]
    - endpoints: ["ceos-sw-2:eth2", "ceos-sw-3:eth2"]
```

## Spinning Up The Lab
Follow these steps (based on Ubuntu 22.04 and Arista cEOS version 4.29.0.2F)

1. install docker: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04
2. install containerlab: 
`sudo bash -c "$(curl -sL https://get.containerlab.dev)"`
3. Follow these [instructions](https://netlab.tools/labs/ceos/) to install the Arista EOS Container
4. import the cEOS docker image: 
`sudo docker import cEOS-lab-4.29.0.2F.tar.xz ceos:4.29.0.2F`
6. If you have cloned this Git repo, then cd into the `containerlab` directory (or make dirctory of your choosing): 
`cd containerlab`
8. deploy the lab: 
`containerlab deploy`

After a few minutes the status will update showing the deployed lab: 
```
ubuntu@ip-172-31-32-145:~/netbox-ansible-webinar/containerlab$ sudo containerlab deploy
INFO[0000] Containerlab v0.45.1 started                 
INFO[0000] Parsing & checking topology file: webinar.clab.yaml 
INFO[0000] Creating docker network: Name="webinar-net", IPv4Subnet="172.21.21.0/24", IPv6Subnet="", MTU="1500" 
INFO[0000] Creating lab directory: /home/ubuntu/netbox-ansible-webinar/containerlab/clab-webinar 
INFO[0000] Creating container: "ceos-sw-1"              
INFO[0000] Creating container: "ceos-sw-2"              
INFO[0000] Creating container: "ceos-sw-3"              
INFO[0000] Creating link: ceos-sw-1:eth1 <--> ceos-sw-2:eth1 
INFO[0001] Creating link: ceos-sw-1:eth2 <--> ceos-sw-3:eth1 
INFO[0001] Creating link: ceos-sw-2:eth2 <--> ceos-sw-3:eth2 
INFO[0001] Running postdeploy actions for Arista cEOS 'ceos-sw-3' node 
INFO[0001] Running postdeploy actions for Arista cEOS 'ceos-sw-1' node 
INFO[0001] Running postdeploy actions for Arista cEOS 'ceos-sw-2' node 
INFO[0102] Adding containerlab host entries to /etc/hosts file 
INFO[0102] 🎉 New containerlab version 0.50.0 is available! Release notes: https://containerlab.dev/rn/0.50/
Run 'containerlab version upgrade' to upgrade or go check other installation options at https://containerlab.dev/install/ 
+---+------------------------+--------------+----------------+------+---------+----------------+--------------+
| # |          Name          | Container ID |     Image      | Kind |  State  |  IPv4 Address  | IPv6 Address |
+---+------------------------+--------------+----------------+------+---------+----------------+--------------+
| 1 | clab-webinar-ceos-sw-1 | 0924756ca24c | ceos:4.29.0.2F | ceos | running | 172.21.21.2/24 | N/A          |
| 2 | clab-webinar-ceos-sw-2 | 22352d3225cf | ceos:4.29.0.2F | ceos | running | 172.21.21.3/24 | N/A          |
| 3 | clab-webinar-ceos-sw-3 | dc7c58511cda | ceos:4.29.0.2F | ceos | running | 172.21.21.4/24 | N/A          |
+---+------------------------+--------------+----------------+------+---------+----------------+--------------+
```
8. connect to devices using docker exec
```
ubuntu@ip-172-31-32-145:~/netbox-ansible-webinar/containerlab$ sudo docker exec -it clab-webinar-ceos-sw-3 Cli
ceos-sw-3>
```
OR ssh (admin/admin for Arista cEOS devices)
```
ssh admin@172.21.21.4
(admin@172.21.21.4) Password: 
Last login: Tue Jan 30 11:11:15 2024 from 172.21.21.1
ceos-sw-3>
```

## Useful Commands

### Containerlab

- show the topology: `containerlab inspect`
- destroy the lab: `containerlab destroy --topo webinar.clab.yaml`

### Docker

- list containers: `docker ps`
- list images: `docker images`