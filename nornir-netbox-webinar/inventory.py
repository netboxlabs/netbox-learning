#!./venv/bin/python

# Import required libraries

from nornir import InitNornir
import json

# Initialize Nornir with config file

nr = InitNornir(config_file="config.yaml")

# Loop over all hosts from NetBox and print the output

for host in nr.inventory.hosts.values():
    host_data = host.dict()
    formatted_json = json.dumps(host_data, indent=4)
    print(formatted_json)
