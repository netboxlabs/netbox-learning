import os, asyncio, json
from nats.aio.client import Client as NATS
from dotenv import load_dotenv
from slack_sdk import WebClient

class ReachacbilityAlerter():

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
        
         # Set up a Slack WebClient with the Slack OAuth token
        self.slack_webclient = WebClient(self.slack_token)

        # Report environment
        print(f"""Loaded environment for {os.path.basename(__file__)}
NATs Server: {self.nats_server}
Writing ping alerts to Slack channel: {self.slack_channel} with username: {self.slack_username}""")
        
    async def message_handler(self, msg) -> None:
        subject = msg.subject
        data = msg.data.decode()
        data = json.loads(data)
        print(f"Received a message on '{subject}':{data}")
        hostname = data["hostname"]
        ip = data["ip"]
        reachable = data["reachable"]

        if reachable == False:
            try:
                # Send a message to Slack
                alert = f"Device unreachable ⚠️ Hostname: {hostname} IP: {ip}"
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
    reachability_alerter = ReachacbilityAlerter()
    asyncio.run(reachability_alerter.main_loop())