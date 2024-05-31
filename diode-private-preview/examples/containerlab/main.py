import argparse
import sys

import yaml
from netboxlabs.diode.sdk import DiodeClient
from netboxlabs.diode.sdk.ingester import (
    Device,
    Entity,
    Prefix
)


def parse_clab_config(config_file: str) -> list[Entity]:
    """
    Parses a Containerlab configuration file and returns a list of entities.

    This function reads a Containerlab configuration file and extracts information
    about the device and its interfaces, including IP addresses. It returns this
    information as a list of `Entity` objects.

    Args:
    ----
        config_file (str): The path to the Containerlab configuration file.

    Returns:
    -------
        list[Entity]: A list of `Entity` objects representing the parsed configuration.

    """

    entities = []
    with open(config_file, 'r') as file:
        data = yaml.safe_load(file)

        # Set the site name
        name = data.get('name', "undefined") or "undefined"
        site_name = f'Containerlab: {name}'

        # Parse mgmt network data, if present
        if data.get("mgmt"):
            mgmt = data.get("mgmt")
            entities.append(Entity(
                prefix=Prefix(
                    prefix=mgmt.get("ipv4-subnet"),
                    description=mgmt.get("network"),
                    site=site_name
                )
            ))

        # Parse node (device) data, if present
        if data.get("topology"):
            nodes = data.get("topology").get("nodes")
            for node in nodes:
                node_data = nodes.get(node)
                entities.append(Entity(
                    device=Device(
                        name=node,
                        device_type=node_data.get('kind'),
                        manufacturer=node_data.get('kind'),
                        platform=node_data.get('image'),
                        site=site_name,
                        primary_ip4=node_data.get('mgmt-ipv4')
                    )
                ))

    return entities


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=str, default="localhost:8081", help="the target address of the Diode server")
    parser.add_argument("--tls_verify", action="store_false", default=True, help="enable TLS verification")
    parser.add_argument("--apply", action="store_true", default=False, help="apply the changes")
    args = parser.parse_args()

    try:
        entities = parse_clab_config("containerlab.yaml")
    except ValueError as e:
        print(f"FAIL: {e}")
        sys.exit(1)

    if args.apply is False:
        print("INFO: dry-run mode, no changes will be applied")
        print(f"INFO: entities to ingest: {entities}")
        sys.exit(0)

    with DiodeClient(target=args.target, app_name="containerlab-config-parser", app_version="0.0.1",
                     tls_verify=args.tls_verify) as client:
        response = client.ingest(entities=entities)
        if response.errors:
            print(f"FAIL: response errors: {response.errors}")
        else:
            print("INFO: data ingested successfully")


if __name__ == "__main__":
    main()
