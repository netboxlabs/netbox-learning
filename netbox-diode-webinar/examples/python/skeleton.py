'''
    ensure DIODE_CLIENT_ID and DIODE_CLIENT_SECRET are set before running this
'''

from netboxlabs.diode.sdk import DiodeClient
from netboxlabs.diode.sdk.ingester import (
    Entity,
)


def generate_entities() -> list[Entity]:
    ''' generate a list of entitles for return to Diode '''
    entities = []
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
