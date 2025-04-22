#!/usr/bin/env python
# Copyright 2025 NetBox Labs Inc
"""NetBox Labs - Mock Impl."""

from collections.abc import Iterable
from typing import Any
import json
import random
import string

# Try importing the required modules, but provide mock implementations if they're not available
try:
    from netboxlabs.diode.sdk.ingester import Device, Interface, Entity
    from worker.backend import Backend
    from worker.models import Metadata, Policy
except ImportError:
    # Mock implementations for standalone mode
    class Device:
        def __init__(self, name=None, device_type=None, manufacturer=None, site=None, role=None, **kwargs):
            self.name = name
            self.device_type = device_type
            self.manufacturer = manufacturer
            self.site = site
            self.role = role
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class Interface:
        def __init__(self, name=None, device=None, **kwargs):
            self.name = name
            self.device = device
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class Entity:
        def __init__(self, device=None, interface=None):
            self.device = device
            self.interface = interface
    
    class Backend:
        def setup(self):
            pass
        
        def run(self, policy_name, policy):
            pass
    
    class Metadata:
        def __init__(self, name=None, app_name=None, app_version=None):
            self.name = name
            self.app_name = app_name
            self.app_version = app_version
    
    class Policy:
        def __init__(self, scope=None):
            self.scope = scope or {}


class WorkerExample(Backend):

    def setup(self) -> Metadata:
        return Metadata(name="worker_example", app_name="worker_example_app", app_version="1.0.0")


    def run(self, policy_name: str, policy: Policy) -> Iterable[Entity]:
        """Process the policy and generate device entities.
        
        Args:
            policy_name: The name of the policy being executed
            policy: Policy object containing configuration details
            
        Returns:
            Iterable of Entity objects representing devices
        
        Raises:
            ValueError: If required scope parameters are missing
        """
        # Extract scope from policy
        scope = getattr(policy, 'scope', {})
        
        # Get required values with validation
        required_fields = ['name', 'device_type', 'manufacturer', 'site', 'role']
        device_params = {}
        
        for field in required_fields:
            value = scope.get(field)
            if not value:
                # You might want to log this instead of raising an error
                # depending on your requirements
                raise ValueError(f"Missing required field: {field}")
            device_params[field] = value
        
        # Create and return the device entity
        return [Entity(device=Device(**device_params))]


if __name__ == "__main__":
    import argparse
    import sys
    from datetime import datetime
    
    def create_sample_policy(device_name=None):
        """Create a sample policy for testing purposes."""
        sample_scope = {
            "name": device_name or f"test-device-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "device_type": "Router",
            "manufacturer": "Cisco",
            "site": "Test Site",
            "role": "Core"
        }
        
        # Create a simple Policy object with the sample scope
        policy = Policy(scope=sample_scope)
                
        return "sample_policy", policy
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run WorkerExample standalone')
    parser.add_argument('--device-name', '-d', help='Device name to use in the sample policy')
    args = parser.parse_args()
    
    # Create an instance of the worker and run it
    worker = WorkerExample()
    worker.setup()
    
    try:
        # Create a sample policy and run the worker
        policy_name, sample_policy = create_sample_policy(args.device_name)
        results = worker.run(policy_name, sample_policy)
        
        # Display the results
        print("\nGenerated Entities:")
        for i, entity in enumerate(results, 1):
            print(f"\nEntity {i}:")
            if entity.device:
                device = entity.device
                print(f"  Device: {device.name}")
                print(f"  Type: {device.device_type}")
                print(f"  Manufacturer: {device.manufacturer}")
                print(f"  Site: {device.site}")
                print(f"  Role: {device.role}")
            else:
                print("  No device data")
                
        print("\nExecution completed successfully.")
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)