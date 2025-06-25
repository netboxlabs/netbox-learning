'''
    ensure DIODE_CLIENT_ID and DIODE_CLIENT_SECRET are set before running this
'''

from netboxlabs.diode.sdk import DiodeClient
from google.protobuf.json_format import ParseDict
from netboxlabs.diode.sdk.ingester import (
    Entity,
)


def generate_entities() -> list[Entity]:
    ''' generate a list of entitles for return to Diode '''
    entities = []
    devices = [
        {
            "device": {
                "name": "Device PDU2",
                "site": {
                    "name": "Sunderland"
                },
                "role": {
                    "name": "Rack PDU"
                },
                "device_type": {
                    "manufacturer": {
                        "name": "APC"
                    },
                    "model": "AP7952"
                },
                "custom_fields": {
                    "software_version": {
                        "text": "1.2"
                    }
                }
            }
        }
    ]

    for jsonEntity in devices:
        entity = Entity()
        entity = ParseDict(jsonEntity, entity)
        entities.append(entity)

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
