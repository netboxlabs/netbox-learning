import os, asyncio, nmap, time, sys, ipaddress, json
from nats.aio.client import Client as NATS
from dotenv import load_dotenv
from netbox import NetBoxHelper
from pythonping import ping
from pythonping.executor import SuccessOn
from prettytable import PrettyTable

class MonitorNetwork():

    # Class Variables
    nats_server = ""
    subscribe_subject = ""
    publish_subject = ""
    network_devices = {}
    netbox_url = ""
    netbox_token = ""
    nc = None

    # Class Functions
    def __init__(self):
        # Load Environment Variables
        load_dotenv()
        self.nats_server = os.getenv("NATS_SERVER")
        self.publish_subject = os.getenv("PUBLISH_SUBJECT")
        self.subscribe_subject = os.getenv("SUBSCRIBE_SUBJECT")
        self.netbox_url = os.getenv("NETBOX_URL")
        self.netbox_token = os.getenv("NETBOX_TOKEN")

        # Load devices from netbox
        self.network_devices = self.load_devices_from_netbox()

        # Report environment
        print(f"""Loaded environment for {os.path.basename(__file__)}
NATs Server: {self.nats_server}
Publishing to subject: {self.publish_subject}
Monitoring Devices: {json.dumps(self.network_devices, indent=4)}""")
    
    def load_devices_from_netbox(self) -> {str, str}:
        # Create NetBox Helper object
        nb = NetBoxHelper(self.netbox_url, self.netbox_token)

        # Get all active devices with an IPv4 management IP
        print(f"Loading devices from NetBox instance at {self.netbox_url}")
        total_devices_count, elligible_devices_count, devices = nb.get_active_devices_with_a_mgmt_ipv4()
        print(f"Found {total_devices_count} devices. {elligible_devices_count} of which are elligible for monitoring.")

        network_devices = {}
        
        # Write each of the IPs into network_devices[]
        for device in devices:
            mgmt_ip = ipaddress.ip_interface(str(device.primary_ip4)).ip
            network_devices[f"{device.name}"] = str(mgmt_ip)

        return network_devices
        
    async def message_handler(self, msg) -> None:
        subject = msg.subject
        data = msg.data.decode()
        print(f"Received a message on '{subject}': {data}")

        table = PrettyTable(["Device Name", "IP", "Pingable?"])
        

        # Ping all devices and output the results
        for device, ip in self.network_devices.items():
            device_failed = False
            ping_status = ping(ip,
                               verbose=False,
                               timeout=1,
                               count=1).success(option=SuccessOn.Most)
            table.add_row([device, ip, ping_status])
            if ping_status == False:
                device_failed = True


        await self.nc.publish(self.publish_subject, f"Device monitoring issues ⚠️ \n {table}".encode())
        
        print(table)

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
    network_monitor = MonitorNetwork()
    asyncio.run(network_monitor.main_loop())