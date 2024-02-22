import os
import asyncio
import json
from nats.aio.client import Client as NATS
from dotenv import load_dotenv
from github_helper import GitHubRepoHelper

class FactsBackup():

    # Class Variables
    nats_server = ""
    subscribe_subject = ""
    github_token = ""
    github_org = ""
    github_repo = ""
    commit_filename = "facts"

    # Class Functions
    def load_environment(self):
        load_dotenv()

        self.nats_server = os.getenv("NATS_SERVER")
        self.subscribe_subject = os.getenv("SUBSCRIBE_SUBJECT")
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.github_org = os.environ.get("GITHUB_ORG")
        self.github_repo = os.environ.get("GITHUB_REPO")

    def write_to_github(self, device_name, facts):
        # Initialise the GitHub Helper
        gh = GitHubRepoHelper(self.github_token, self.github_org, self.github_repo)
        print(f"Created GitHub Helper object: {gh}")

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
        print(f"'msg.data' has type {type(msg.data)}")
        print(f"'data' has type {type(data)}")
        print(f"Received a message on '{subject}': {data}")

        # Extract the device name
        device_name = json.loads(data)["hostname"]

        self.write_to_github(device_name, data)

    async def subscribe_loop(self) -> None:
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
    facts_backup = FactsBackup()
    facts_backup.load_environment()
    asyncio.run(facts_backup.subscribe_loop())