import asyncio
from nats.aio.client import Client as NATS

async def message_handler(msg):
    subject = msg.subject
    data = msg.data.decode()
    print(f"Received a message on '{subject}': {data}")

async def subscribe_to_subject():
    # Create a NATS client
    nc = NATS()
    
    # Connect to the NATS server
    await nc.connect("nats://localhost:4222")

    # Subscribe to a subject
    subject = "devices.facts"
    await nc.subscribe(subject, cb=message_handler)
    print(f"Subscribed to {subject}")

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
    asyncio.run(subscribe_to_subject())