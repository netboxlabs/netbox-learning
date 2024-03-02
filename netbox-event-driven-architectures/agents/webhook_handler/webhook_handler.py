from fastapi import FastAPI, HTTPException, APIRouter
import os
from nats.aio.client import Client as NATS
from dotenv import load_dotenv

class WebhookHandler():

    # Class Variables
    nats_server = ""
    publish_subject = ""
    nc = None
    router = None
    app = None

    def __init__(self):
        
        # Load Environment Variables
        load_dotenv()
        self.nats_server = os.getenv("NATS_SERVER")
        self.publish_subject = os.getenv("PUBLISH_SUBJECT")

        # Create a NATS client
        self.nc = NATS()

        # Create Fast API API Router
        self.router = APIRouter()
        self.router.add_api_route("/webhook", self.handle_webhook, methods=["POST"])

        self.app = FastAPI()
        self.app.include_router(self.router)

        # Report environment
        print(f"""Loaded environment for {os.path.basename(__file__)}
NATs Server: {self.nats_server}
Publishing to subject: {self.publish_subject}""")

    async def handle_webhook(self, payload: dict):
        try:
            # Process the webhook payload as needed
            print(f"Received webhook. Data: {payload}")
            print(f"Action Type: {payload['action']}")
            action = payload['action']

            # Perform actions based on the webhook data
            # Connect to the NATS server
            await self.nc.connect(self.nats_server)

            # Publish the event
            await self.nc.publish(action, str(payload).encode())

            # Send a response back to the sender (optional)
            return {'status': 'success'}

        except Exception as e:
            # Handle exceptions or errors
            print(f"Exception: {e}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn

    webhook_handler = WebhookHandler()

    # Run the FastAPI application using Uvicorn on a specified port (e.g., 5000)
    uvicorn.run(webhook_handler.app, host='0.0.0.0', port=5000)