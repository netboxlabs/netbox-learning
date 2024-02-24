#!./venv/bin/python

# Import required libraries

from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from nornir_utils.plugins.functions import print_result

# Initialize Nornir with config file

nr = InitNornir(config_file="config.yaml")

# Define a function to get the device facts using napalm_get

def napalm_get_facts(task):
	task.run(task=napalm_get, getters=["facts"])

# Display the results

results=nr.run(task=napalm_get_facts)

print_result(results)
