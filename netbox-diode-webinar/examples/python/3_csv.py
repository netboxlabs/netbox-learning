'''
    ensure DIODE_CLIENT_ID and DIODE_CLIENT_SECRET are set before running this
'''

from netboxlabs.diode.sdk import DiodeClient
from netboxlabs.diode.sdk.ingester import (
    Entity,
    Device,
    IPAddress,
    Interface,
    CustomFieldValue
)
import csv


def load_from_csv(filename: str) -> list:
    ''' function to read a csv file and return it as a list '''
    pdu_list = []

    ''' read the csv file and look through creating a dict for each row,
        then append to our list '''
    with open(filename, newline='') as csvfile:
        ''' use a dict reader so we can reference via column names '''
        reader = csv.DictReader(csvfile)
        for row in reader:
            pdu = {
                'name': row['name'],
                'serial': row['serial'],
                'model': row['model'],
                'manufacturer': row['manufacturer'],
                'management_ip': row['management_ip'],
                'software_version': row['software_version']
            }
            pdu_list.append(pdu)
    return pdu_list


def generate_entities() -> list[Entity]:
    ''' generate a list of entitles for return to Diode '''

    pdu_list = load_from_csv("ourdata.csv")

    entities = []
    for pdu in pdu_list:
        ''' create Device Entity, an IP Address and an Interface '''
        device = Device(
            name=pdu['name'],
            device_type=pdu['model'],
            manufacturer=pdu['manufacturer'],
            site='Prague',
            role='pdu',
            serial=pdu['serial'],
            status='active',
            custom_fields={
                "software_version": CustomFieldValue(
                    text=pdu['software_version']
                )
            },
            primary_ip4=IPAddress(
                address=pdu['management_ip'],
                status='active',
                description='loaded from csv',
                assigned_object_interface=Interface(
                    name='eth0',
                    type='1000base-t',
                    device=Device(
                        name=pdu['name'],
                        device_type=pdu['model'],
                        manufacturer=pdu['manufacturer'],
                        site='Prague',
                        role='pdu',
                        serial=pdu['serial'],
                        status='active',
                    )
                )
            )
        )

        entities.append(Entity(device=device))
    return entities


if __name__ == "__main__":
    ''' main function '''

    entities = generate_entities()

    with DiodeClient(
        target="grpc://<diode.ip:diode.port>/diode",
        app_name="my-app",
        app_version="1",

    ) as client:
        try:
            response = client.ingest(entities=entities)
        except Exception as exc:
            print(f"\n!! An Exception Happened: {exc}")
