import os
import asyncio
import json
from nats.aio.client import Client as NATS
from dotenv import load_dotenv
from agents.helpers.github_helper import GitHubRepoHelper

class ConfigBackuper():

    # Class Variables
    nats_server = ""
    subscribe_subject = ""
    github_token = ""
    github_org = ""
    github_repo = ""
    commit_filename = "facts"

    def __init__(self):
        load_dotenv()

        self.nats_server = os.getenv("NATS_SERVER")
        self.subscribe_subject = os.getenv("SUBSCRIBE_SUBJECT")
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.github_org = os.environ.get("GITHUB_ORG")
        self.github_repo = os.environ.get("GITHUB_REPO")

        # Report environment
        print(f"""Loaded environment for {os.path.basename(__file__)}
NATs Server: {self.nats_server}
Writing device configs to: {self.github_org}/{self.github_repo}""")

    def write_to_github(self, device_name, facts):
        # Initialise the GitHub Helper
        gh = GitHubRepoHelper(self.github_token, self.github_org, self.github_repo)
        print(f"Created GitHub Helper object: {gh}")

        # Create commit message
        commit_message = f"Device facts for {device_name} backed up by facts_backup agent 🚀"

        # Write to GitHub
        commit = gh.write_config_to_gh(file_path=device_name,
                                       file_name=self.commit_filename,
                                       file_contents=str(facts),
                                       commit_message=commit_message)
        print(f"Wrote device facts to GitHub. Commit: {commit}")

    async def message_handler(self, msg) -> None:
        subject = msg.subject
        data = msg.data.decode()
        print(f"Received a message on '{subject}': {data}")

        # Extract the device name
        device_name = json.loads(data)["hostname"]

        # Write the device config to GitHub
        self.write_to_github(device_name, data)

    async def main_loop(self) -> None:
        # Create a NATS client
        nc = NATS()
        
        # Connect to the NATS server
        await nc.connect(self.nats_server)

        # Subscribe to a subject
        await nc.subscribe(self.subscribe_subject, cb=self.message_handler)
        print(f"Subscribed to {self.subscribe_subject}")

        # Keep the script running to receive messages
        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            print("Disconnecting...")
            await nc.close()
        except Exception as e:
            print(e)

# Run the subscriber
if __name__ == "__main__":
    config_backuper = ConfigBackuper()
    asyncio.run(config_backuper.main_loop())