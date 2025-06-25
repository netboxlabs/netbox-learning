'''
    ensure DIODE_CLIENT_ID and DIODE_CLIENT_SECRET are set before running this
'''

from netboxlabs.diode.sdk import DiodeClient
from netboxlabs.diode.sdk.ingester import (
    Device,
    DeviceRole,
    DeviceType,
    Site,
    Entity,
    CustomFieldValue,
)


def generate_entities() -> list[Entity]:
    ''' generate a list of entitles for return to Diode '''
    entities = []

    device = Device(
        name="PDU 1",
        device_type=DeviceType(
            manufacturer="APC",
            model="7951"
        ),
        role=DeviceRole(
            name="Rack PDU"
        ),
        site=Site(
            name="Sunderland"
        ),
        custom_fields={
            'software_version': CustomFieldValue(
                text="1.1"
            )
        }
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
            print(response)
        except Exception as exc:
            print(f"\n!! An Exception Happened: {exc}")
