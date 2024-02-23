import os, asyncio, nmap, time
from nats.aio.client import Client as NATS
from dotenv import load_dotenv

class ScanNetwork():

    # Class Variables
    nats_server = ""
    publish_subject = ""
    network_cidr = ""

    # Class Functions
    def load_environment(self):
        
        # Load Environment Variables
        load_dotenv()
        self.nats_server = os.getenv("NATS_SERVER")
        self.publish_subject = os.getenv("PUBLISH_SUBJECT")
        self.network_cidr = os.getenv("NETWORK_CIDR")

        # Report environment
        print(f"""Loaded environment for {os.path.basename(__file__)}.
                  NATs Server: {self.nats_server}
                  Publishing to subject: {self.publish_subject}""")

    async def main_loop(self) -> None:
        # Create a NATS client
        nc = NATS()
        
        # Connect to the NATS server
        await nc.connect(self.nats_server)

        # Enter main loop
        while True:
            # Initialise nmap PortScanner
            nm = nmap.PortScanner()

            # Scan the subnet
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f"{current_time}: Scanning {self.network_cidr}...")
            nm.scan(hosts=self.network_cidr, arguments='-n -sP -PE -PA21,22,23,80,3389')

            # Write the output to the bus
            for host in nm.all_hosts():
                print(f"Publishing found host: {host}")
                await nc.publish(self.publish_subject, str(host).encode())

            # Wait for the delay period
            await asyncio.sleep(30)

# Run the subscriber
if __name__ == "__main__":
    device_facts_poller = ScanNetwork()
    device_facts_poller.load_environment()
    asyncio.run(device_facts_poller.main_loop())