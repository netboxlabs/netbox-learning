import os, asyncio, json, ipaddress
from nats.aio.client import Client as NATS
from dotenv import load_dotenv
from slack_sdk import WebClient
from agents.helpers.netbox import NetBoxHelper

class SlackAlerter():

    # Class Variables
    nats_server = ""
    subscribe_subject = ""
    
    slack_token = ""
    slack_webclient = None
    slack_username = ""
    slack_channel = ""

    # Class Functions
    def __init__(self):
        # Load Environment Variables
        load_dotenv()
        self.nats_server = os.getenv("NATS_SERVER")
        self.subscribe_subject = os.getenv("SUBSCRIBE_SUBJECT")
        self.slack_token = os.getenv("SLACK_TOKEN")
        self.slack_username = os.getenv("SLACK_USERNAME")
        self.slack_channel = os.getenv("SLACK_CHANNEL")
        self.netbox_url = os.getenv("NETBOX_URL")
        self.netbox_token = os.getenv("NETBOX_TOKEN")
        
         # Set up a Slack WebClient with the Slack OAuth token
        self.slack_webclient = WebClient(self.slack_token)

        # Report environment
        print(f"""Loaded environment for {os.path.basename(__file__)}
NATs Server: {self.nats_server}
Reading inventory from NetBox: {self.netbox_url}
Writing device alerts to Slack channel: {self.slack_channel} with username: {self.slack_username}""")

    def load_devices_from_netbox(self) -> {str, str}:
        # Create NetBox Helper object
        nb = NetBoxHelper.getInstance(self.netbox_url, self.netbox_token)
        
        print(f"Loading devices from NetBox instance at {self.netbox_url}")
        return nb.get_active_devices_with_a_mgmt_ipv4()
        
    async def message_handler(self, msg) -> None:
        subject = msg.subject
        data = msg.data.decode()
        data = json.loads(data)
        print(f"Received a message on '{subject}':{data}")
        hostname = data["hostname"]
        ip = data["ip"]
        
        # Get all active devices with an IPv4 management IP from NetBox
        total_devices_count, elligible_devices_count, devices = self.load_devices_from_netbox()
        print(f"Found {elligible_devices_count} (of {total_devices_count}) devices in NetBox.")

        # If this device is NOT in NetBox, send an alert
        found_device_in_netbox = False
        for device in devices:
            if str(ipaddress.ip_interface(str(device.primary_ip4)).ip) == ip:
                found_device_in_netbox = True
                print(f"Found device {device.name} in NetBox inventory. Skipping.")
        
        if found_device_in_netbox == False:
            # Couldn't find the device in NetBox, so send a Slack lert           
            try:
                # Send a message to Slack
                alert = f"Found unknown device in network ⚠️ IP: {ip}"
                self.slack_webclient.chat_postMessage(channel=self.slack_channel,
                                                      text=alert,
                                                      username=self.slack_username
                )
            except Exception as e:
                print(f"Caught exception {type(e)} while writing message to Slack with user '{self.slack_username}'. Exception: {e}")
        

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
    network_monitor = SlackAlerter()
    asyncio.run(network_monitor.main_loop())