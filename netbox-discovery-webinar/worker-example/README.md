# Worker Example

A sample implementation for NetBox Labs worker that demonstrates creating device entities.

## Requirements

- Python 3.x
- If running as part of NetBox Labs: netboxlabs.diode.sdk, worker packages

## Running Standalone

This project can be run as a standalone script for testing and development:

```bash
# Run with default device name (automatically generated)
python3 worker_example/runner.py

# Run with a custom device name
python3 worker_example/runner.py --device-name my-custom-device
```

## Features

- Creates device entities with configurable properties
- Implements required Backend interface
- Parameter validation
- Mock implementations for standalone mode

## Project Structure

- `worker_example/runner.py`: Main implementation file

## Customization

You can modify the required fields and default values in the `run` method to adapt the worker to your specific requirements.