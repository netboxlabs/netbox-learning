# netbox-ansible-webinar

Ansible code to accompany the **Webinar: Getting Started with Network Automation: 
NetBox & Ansible** hosted by **NetBox Labs** on 30th Jan 2024.

[![netbox ansible webinar](https://img.youtube.com/vi/BtzKX3Unuu0/0.jpg)](https://www.youtube.com/watch?v=BtzKX3Unuu0)

## Get Access to a NetBox instance

For hassle-free access to NetBox you can either use the NetBox Labs demo site, or request a free 14 Day Trial of NetBox Cloud: 

- [Demo Site](https://netboxlabs.com/netbox-demo/)
- [Free Trial of NetBox Cloud](https://netboxlabs.com/trial/)

## Getting Started With The Ansible Playbooks

1. Clone the Git repo and change into the `netbox-ansible-webinar` directory:
    ```
    git clone https://github.com/netboxlabs/netbox-learning.git
    cd netbox-learning/netbox-ansible-webinar
    ```
2. Create and activate Python 3 virtual environment:
    ```
    python3 -m venv ./venv
    source venv/bin/activate
    ```
3. Upgrade pip:
    ```
    python3 -m pip install --upgrade pip
    ```
4. Install required Python packages:

    **option 1** - Install individual packages: 
    ```
    pip install pynetbox
    pip install ansible
    pip install pytz
    pip install ansible-pylibssh
    ```
    **option 2** - Install from `requirements.txt` file: 
    ```
    pip install -r requirements.txt
    ```
5. Install Ansible Galaxy Collection for NetBox
    ```
    ansible-galaxy collection install netbox.netbox
    ```
6. Set environment variables for the NetBox API token and URL:
    ```
    export NETBOX_API=<YOUR_NETBOX_URL> (note - must include http:// or https://) 
    export NETBOX_TOKEN=<YOUR_NETBOX_API_TOKEN>
    ```
7. List the devices and host variables retrieved from NetBox using the dynamic inventory: 
    ```
    ansible-inventory -i netbox_inv.yml --list
    ```
7. Run a playbook, for example: 
    ```
    ansible-playbook get_facts.yml
    ```
8. When you have finished working you can deactivate the Python virtual environment:
    ```
    deactivate
    ```

## Building the Virtual Network With Containerlab

Follow these [instructions](./containerlab/README.md) to install containerlab, and build the lab network

Alternatively you use the official [Containerlab documenation](https://containerlab.dev/install/)