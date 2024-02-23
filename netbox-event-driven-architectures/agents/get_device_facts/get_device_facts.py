import os, json, asyncio
from nats.aio.client import Client as NATS
from dotenv import load_dotenv
from device_helper import NetworkDeviceHelper

class DeviceType:
    manufacturer = "Nokia"

class Device():
    device_type = DeviceType()
    primary_ip4 = "172.20.20.2/24"
    

class GetDeviceFacts():

    # Class Variables
    nats_server = ""
    publish_subject = ""

    # Class Functions
    def load_environment(self):
        
        # Load Environment Variables
        load_dotenv()
        self.nats_server = os.getenv("NATS_SERVER")
        self.publish_subject = os.getenv("PUBLISH_SUBJECT")

        # Report environment
        print(f"Loaded environment for {os.path.basename(__file__)}. \n NATs Server: {self.nats_server} \n Publishing to subject: {self.publish_subject}")

    async def main_loop(self) -> None:
        # Create a NATS client
        nc = NATS()
        
        # Connect to the NATS server
        await nc.connect(self.nats_server)

        # Enter main loop
        while True:
            # Get the list of devices
            print("Checking for devices...")
            device = Device()
            print(f"Found device: {device}")

            # Get the device facts from each one
            print("Pulling device facts...")
            napalm_device_connection = NetworkDeviceHelper(device)
            if napalm_device_connection == None:
                print(f"Unable to initiate connection to device: {device}")
            facts = napalm_device_connection.get_config(NetworkDeviceHelper.TYPE_FACTS)

            # Create a valid JSON string from the NAPALM output
            valid_facts = str(facts).replace("'", "\"")

            # Write them to the NATs Subject
            # Publish a message to a subject
            #facts = '{"hostname": "TST-ROUTER-1", "fqdn": "TST-ROUTER-2", "vendor": "Nokia", "model": "7220 IXR-D3", "serial_number": "Sim Serial No.", "os_version": "v23.10.1-218-ga3fc1bea5a", "uptime": -1.0, "interface_list": ["ethernet-1/1", "ethernet-1/2", "ethernet-1/3", "ethernet-1/4", "ethernet-1/5", "ethernet-1/6", "ethernet-1/7", "ethernet-1/8", "ethernet-1/9", "ethernet-1/10", "ethernet-1/11", "ethernet-1/12", "ethernet-1/13", "ethernet-1/14", "ethernet-1/15", "ethernet-1/16", "ethernet-1/17", "ethernet-1/18", "ethernet-1/19", "ethernet-1/20", "ethernet-1/21", "ethernet-1/22", "ethernet-1/23", "ethernet-1/24", "ethernet-1/25", "ethernet-1/26", "ethernet-1/27", "ethernet-1/28", "ethernet-1/29", "ethernet-1/30", "ethernet-1/31", "ethernet-1/32", "ethernet-1/33", "ethernet-1/34", "mgmt0"]}'
            
            print(f"Publishing device fact: {valid_facts}")
            await nc.publish(self.publish_subject, valid_facts.encode())

            # Wait for the delay period
            await asyncio.sleep(30)

# Run the subscriber
if __name__ == "__main__":
    device_facts_poller = GetDeviceFacts()
    device_facts_poller.load_environment()
    asyncio.run(device_facts_poller.main_loop())