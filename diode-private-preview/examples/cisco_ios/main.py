import argparse
import sys

from ciscoconfparse2 import CiscoConfParse
from netboxlabs.diode.sdk import DiodeClient
from netboxlabs.diode.sdk.ingester import (
    Device,
    Entity,
    Interface,
    IPAddress,
)


def parse_cisco_config(config_file: str, site: str = "Site A") -> list[Entity]:
    """
    Parses a Cisco configuration file and returns a list of entities.

    This function reads a Cisco IOS configuration file and extracts information
    about the device and its interfaces, including IP addresses. It returns this
    information as a list of `Entity` objects.

    Args:
    ----
        config_file (str): The path to the Cisco configuration file.
        site (str): The name of the site where the device is located. Default is "Site A".

    Returns:
    -------
        list[Entity]: A list of `Entity` objects representing the parsed configuration.

    Raises:
        ValueError: If the configuration file does not contain required information
                    such as 'hostname' or 'version'.
    """

    parse = CiscoConfParse(config_file, syntax='ios')

    # Extract device name (hostname), end processing if not found
    if parse.find_objects(r'^hostname'):
        hostname = " ".join(parse.find_objects(r'hostname')[0].text.split()[1:])
    else:
        raise ValueError(f"failed to find 'hostname' in {config_file}")

    # Extract IOS version, if present
    if parse.find_objects(r'^version'):
        version = " ".join(parse.find_objects(r'version')[0].text.split()[1:])
    else:
        version = 'unknown'

    # Add device information
    entities = [
        Entity(
            device=Device(
                name=hostname,
                device_type='unknown',
                manufacturer='Cisco',
                platform=f'IOS {version}',
                site=site,
            )
        )
    ]

    # Process interfaces, if present
    if parse.find_objects(r'^interface'):
        for interface in parse.find_objects(r'^interface'):
            name = " ".join(interface.text.split()[1:])
            description = interface.re_match_iter_typed(r'description (.+)', result_type=str)

            # Add the interface
            entities.append(Entity(
                interface=Interface(
                    name=name,
                    description=description,
                    device=hostname,
                    site=site,
                    device_type='unknown',
                    manufacturer='Cisco'
                )
            ))

            # Extract lists of IPv4 and IPv6 addresses for this interface
            ipv4 = interface.re_match_iter_typed(r'ip address ([\d./]+).*', result_type=str)
            ipv6 = interface.re_match_iter_typed(r'ipv6 address .+ (.+)', result_type=str)

            # Add interface IP addresses, if present
            if ipv4 or ipv6:
                for ip in [ipv4, ipv6]:
                    entities.append(Entity(
                        ip_address=IPAddress(
                            address=ip,
                            interface=name,
                            device=hostname,
                            site=site,
                            device_type='unknown',
                            manufacturer='Cisco'
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
        entities = parse_cisco_config("cisco_ios.txt")
    except ValueError as e:
        print(f"FAIL: {e}")
        sys.exit(1)

    if args.apply is False:
        print("INFO: dry-run mode, no changes will be applied")
        print(f"INFO: entities to ingest: {entities}")
        sys.exit(0)

    with DiodeClient(target=args.target, app_name="cisco-ios-config-parser", app_version="0.0.1",
                     tls_verify=args.tls_verify) as client:
        response = client.ingest(entities=entities)
        if response.errors:
            print(f"FAIL: response errors: {response.errors}")
        else:
            print("INFO: data ingested successfully")


if __name__ == "__main__":
    main()
