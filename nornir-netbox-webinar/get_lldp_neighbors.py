#!./venv/bin/python

# Import required libraries

from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from nornir_utils.plugins.functions import print_result

# Initialize Nornir with config file

nr = InitNornir(config_file="config.yaml")


# Define a function to get the LLDP neighbor information using napalm_get

def napalm_get_lldp_neighbors(task):
	task.run(task=napalm_get, getters=["lldp_neighbors"])


# Display the results

results=nr.run(task=napalm_get_lldp_neighbors)

print_result(results)
