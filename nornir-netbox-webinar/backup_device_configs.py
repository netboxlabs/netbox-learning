#!./venv/bin/python

# Import required libraries

from nornir import InitNornir
from nornir_napalm .plugins.tasks import  napalm_get
from nornir_utils.plugins.functions import print_result
from nornir_utils.plugins.tasks.files import write_file
from datetime import date
import pathlib

# Define a function to back up the device configuration and write then to a file

def backup_device_configs(task):
    backup_directory = "backups"
    pathlib.Path(backup_directory).mkdir(exist_ok=True)
    r = task.run(task=napalm_get, getters=["config"])
    task.run(
        task=write_file,
        content=r.result["config"]["running"],
        filename=f"" + str(backup_directory) + "/" + str(task.host.name) + str(date.today()) + ".cfg",
    )

# Initialize Nornir with config file

nr = InitNornir(config_file="config.yaml")

# Display the results

result = nr.run(
    name="Backing up device configurations", task=backup_device_configs
)

print_result(result)
