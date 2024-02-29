import os, json, asyncio, ipaddress
from nats.aio.client import Client as NATS
from dotenv import load_dotenv
from agents.helpers.device_helper import NetworkDeviceHelper
from agents.helpers.netbox import NetBoxHelper

#class DeviceType:
#    manufacturer = "Nokia"

#class Device():
#    device_type = DeviceType()
#    primary_ip4 = "172.20.20.2/24"


class GetDeviceFacts():

    # Class Functions
    def __init__(self):
        
        # Load Environment Variables
        load_dotenv()
        self.nats_server = os.getenv("NATS_SERVER")
        self.subscribe_subject = os.getenv("SUBSCRIBE_SUBJECT")
        self.publish_subject = os.getenv("PUBLISH_SUBJECT")
        self.netbox_url = os.getenv("NETBOX_URL")
        self.netbox_token = os.getenv("NETBOX_TOKEN")

        # Report environment
        print(f"Loaded environment for {os.path.basename(__file__)}. \n NATs Server: {self.nats_server} \n Publishing to subject: {self.publish_subject}")

    def load_devices_from_netbox(self) -> {str, str}:
        # Create NetBox Helper object
        nb = NetBoxHelper.getInstance(self.netbox_url, self.netbox_token)
        
        print(f"Loading devices from NetBox instance at {self.netbox_url}")
        return nb.get_active_devices_with_a_mgmt_ipv4()
    
    def get_running_config(self, device):
        print(f"Pulling running config for {device}")

        # Create NAPALM connection
        napalm_device_connection = NetworkDeviceHelper(device)
        if napalm_device_connection == None:
            print(f"Unable to initiate connection to device: {device}")

        # Pull the running config for the devices
        running_config = napalm_device_connection.get_config(NetworkDeviceHelper.TYPE_RUNNING_CONFIG)

        # Create a valid JSON string from the NAPALM output
        valid_running_config = str(running_config).replace("'", "\"")

        return valid_running_config
    
    async def message_handler(self, msg) -> None:
        # Get all active devices with an IPv4 management IP from NetBox
        print(f"Loading devices from NetBox instance at {self.netbox_url}")
        total_devices_count, elligible_devices_count, devices = self.load_devices_from_netbox()
        print(f"Found {total_devices_count} devices. {elligible_devices_count} of which are elligible for monitoring.")

        # Get the running config for each device and publish it
        for device in devices:
            running_config = self.get_running_config(device)
            running_config_message = {}
            running_config_message["hostname"] = device.name
            running_config_message["ip"] = str(ipaddress.ip_interface(str(device.primary_ip4)).ip)
            running_config_message["running_config"] = running_config
            await self.nc.publish(self.publish_subject, json.dumps(running_config_message).encode())

    async def main_loop(self) -> None:
        # Create a NATS client
        self.nc = NATS()
        
        # Connect to the NATS server
        await self.nc.connect(self.nats_server)

        # Subscribe to subject
        await self.nc.subscribe(self.subscribe_subject, cb=self.message_handler)
        print(f"Subscribed to {self.subscribe_subject}")

        # Keep the script running to receive messages
        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            print("Disconnecting...")
            await self.nc.close()
        except Exception as e:
            print(e)        

# Run the subscriber
if __name__ == "__main__":
    device_facts_poller = GetDeviceFacts()
    asyncio.run(device_facts_poller.main_loop())