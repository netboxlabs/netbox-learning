import os, json, asyncio, ipaddress
from nats.aio.client import Client as NATS
from dotenv import load_dotenv
from agents.helpers.netbox import NetBoxHelper
from pythonping import ping
from pythonping.executor import SuccessOn

#class DeviceType:
#    manufacturer = "Nokia"

#class Device():
#    device_type = DeviceType()
#    primary_ip4 = "172.20.20.2/24"


class PingDevices():

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
    
    async def message_handler(self, msg) -> None:
        # Get all active devices with an IPv4 management IP from NetBox
        print(f"Loading devices from NetBox instance at {self.netbox_url}")
        total_devices_count, elligible_devices_count, devices = self.load_devices_from_netbox()
        print(f"Found {total_devices_count} devices. {elligible_devices_count} of which are elligible for pinging.")

        # Get the running config for each device and publish it
        for device in devices:
            ping_message = {}
            ping_message["hostname"] = device.name
            ip = str(ipaddress.ip_interface(str(device.primary_ip4)).ip)
            ping_message["ip"] = ip

            print(f"Pinging {device.name} at {ip}")
            ping_message["reachable"] = ping(ip,
                                             verbose=False,
                                             timeout=1,
                                             count=1).success(option=SuccessOn.Most)
            await self.nc.publish(self.publish_subject, json.dumps(ping_message).encode())

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
    device_facts_poller = PingDevices()
    asyncio.run(device_facts_poller.main_loop())