from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post('/webhook')
async def handle_webhook(payload: dict):
    try:
        # Process the webhook payload as needed
        print(f"Received webhook. Data: {payload}")
        print(f"Event Type: {payload['event']}")
        print(f"Object Type: {payload['model']}")

        # Perform actions based on the webhook data

        # Send a response back to the sender (optional)
        return {'status': 'success'}

    except Exception as e:
        # Handle exceptions or errors
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn

    # Run the FastAPI application using Uvicorn on a specified port (e.g., 5000)
    uvicorn.run(app, host='0.0.0.0', port=5000)