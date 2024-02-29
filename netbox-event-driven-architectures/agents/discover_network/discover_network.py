import os, asyncio, nmap, time, ipaddress, json
from nats.aio.client import Client as NATS
from dotenv import load_dotenv
from agents.helpers.netbox import NetBoxHelper

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
        self.subnet_cidr = os.getenv("SUBNET_CIDR")
        self.ignore_ips = [ip.strip() for ip in os.getenv("IGNORE_IPS").split(',')]

        # Report environment
        print(f"""Loaded environment for {os.path.basename(__file__)}
NATs Server: {self.nats_server}
Publishing to subject: {self.publish_subject}
Monitoring subnet: {self.subnet_cidr}
Ignoring IPs: {self.ignore_ips}""")
            
    async def message_handler(self, msg) -> None:
        subject = msg.subject
        data = msg.data.decode()
        print(f"Received a message on '{subject}': {data}")

        ### Scan the subnet and figure out if any devices are there that shouldn't be
        # Initialise nmap PortScanner
        nm = nmap.PortScanner()

        # Scan the subnet
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"{current_time}: Scanning {self.subnet_cidr}...")
        nm.scan(hosts=self.subnet_cidr, arguments='-sn')

        print(f"Found hosts: {nm.all_hosts()}")

        for host in nm.all_hosts():
            if host in self.ignore_ips:
                print(f"Ignoring host {host} as it is present in the IP ignore list {self.ignore_ips}")
            else:
                # We do not know about this IP so alert on it
                device = {}
                device["hostname"] = f"{nm[host].hostname()}"
                device["ip"] = f"{host}"
                device["source"] = "network"
                # Create a valid JSON string from the NAPALM output
                valid_json_device = str(device).replace("'", "\"")

                await self.nc.publish(self.publish_subject, str(valid_json_device).encode())



        
        #print(table)

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