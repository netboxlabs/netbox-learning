# Self-Healing Networks: Managing Drift with NetBox and EDA

_Delivered as a hands-on, in-person workshop at AutoCon5 ([WS:C3](https://networkautomation.forum/autocon5#workshops)) by [NetBox Labs](https://netboxlabs.com)._

In this workshop you'll build a complete closed-loop network automation stack from scratch — configuring NetBox as the source of truth, deploying device configurations via Event-Driven Ansible, using discovery and observability to detect configuration drift, and re-deploying intent to self-heal the network. Real tools, simulated lab environment, designed for engineers who are new to automation or to NetBox.

## Modules

Work through the modules in order — each one builds on the last.

| Module | Title |
| --- | --- |
| [Module 0](./modules/module_0/README.md) | Introduction & Setup |
| [Module 1](./modules/module_1/README.md) | Configuring the Network the Old Fashioned Way |
| [Module 2](./modules/module_2/README.md) | Planning Your Deployment in NetBox |
| [Module 3](./modules/module_3/README.md) | Event-Driven Ansible — Automating Network Operations |
| [Module 4](./modules/module_4/README.md) | Network Modeling Basics — Config Templates & Device Configuration |
| [Module 5](./modules/module_5/README.md) | Network Modeling Advanced — Config Contexts, Tags & OSPF |
| [Module 6](./modules/module_6/README.md) | Network Validation & Drift Detection |

## Workshop Environment

Each participant receives a dedicated cloud VM with all services pre-installed and running. Your facilitator will give you your participant ID at the start of the session — all your service URLs are derived from it. Start with **Module 0** for connection details and a walkthrough of the tools.

## Self-Hosting

If you want to run this workshop on your own infrastructure, the provisioning scripts in this repository set up the full stack on an Ubuntu VM:

```bash
./1_set_envvars.sh     # Set environment variables
./2_start_diode.sh     # Start Diode (NetBox data ingestion)
./3_set_diode_creds.sh # Export Diode credentials
./4_start_netbox.sh    # Start NetBox + branching plugin
./5_start_gitea.sh     # Start Gitea + populate workshop repos
./6_start_grafana.sh   # Start Grafana
./7_start_eda.sh       # Start Event-Driven Ansible
./8_start_network.sh network/workshop.clab.yaml  # Start ContainerLab topology
```

**Minimum requirements:** Ubuntu 22.04+, 4 vCPUs, 8 GB RAM.

> [!WARNING]
> macOS is not supported. ContainerLab requires Linux.

Issues and contributions welcome — please open an [issue](https://github.com/netboxlabs/netbox-learning/issues) on GitHub.

---

**Start here:** [Module 0 — Introduction & Setup](modules/module_0/README.md)
