import argparse
import csv
import sys

from netboxlabs.diode.sdk import DiodeClient
from netboxlabs.diode.sdk.ingester import (
    Device,
    Entity
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=str, default="localhost:8081", help="the target address of the Diode server")
    parser.add_argument("--tls_verify", action="store_false", default=True, help="enable TLS verification")
    parser.add_argument("--apply", action="store_true", default=False, help="apply the changes")
    args = parser.parse_args()

    entities = []

    with open('inventory.csv', 'r') as file:
        reader = csv.reader(file)
        header = next(reader)

        for row in reader:
            entities.append(
                Entity(
                    device=Device(
                        name=row[header.index('Device_Name')],
                        serial=row[header.index('Serial_Number')],
                        site=row[header.index('Site_Name')],
                        role=row[header.index('Device_Type')],
                        device_type=row[header.index('Device_Model')],
                        manufacturer=row[header.index('Vendor')],
                    )
                )
            )

    if args.apply is False:
        print("INFO: dry-run mode, no changes will be applied")
        print(f"INFO: entities to ingest: {entities}")
        sys.exit(0)

    with DiodeClient(target=args.target, app_name="csv-parser", app_version="0.0.1",
                     tls_verify=args.tls_verify) as client:
        response = client.ingest(entities=entities)
        if response.errors:
            print(f"FAIL: response errors: {response.errors}")
        else:
            print("INFO: data ingested successfully")


if __name__ == "__main__":
    main()
