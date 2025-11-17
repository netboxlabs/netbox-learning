## Prerequisites
1. Ensure containerlab is started and netbox is accessible
2. Devices in NetBox must be named "srl1" and "srl2"

## Run Ansible Playbook

### Using the Script (Recommended)

Run the playbook using the provided script:

```bash
./run-ansible-playbook.sh --branch <branch_schema_id>
```

Or without a branch (will prompt for confirmation to run against main branch):

```bash
./run-ansible-playbook.sh
```

### Manual Command

Alternatively, run the following command directly, with your API token and branch id created in the previous steps:

```bash
ansible-playbook -i ansible/inventory.yaml ansible/deploy-configs.yaml -e "MY_EXTERNAL_IP=${MY_EXTERNAL_IP}" -e "NETBOX_PORT=${NETBOX_PORT}" -e "NETBOX_API_TOKEN=${NETBOX_API_TOKEN}" -e "NETBOX_BRANCH_ID=c9fpfpmj"
```
