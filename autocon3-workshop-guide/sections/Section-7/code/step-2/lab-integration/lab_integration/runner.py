#!/usr/bin/env python
import json
import csv
import logging
from netboxlabs.diode.sdk.ingester import Device, Interface, IPAddress
from collections.abc import Iterable
from netboxlabs.diode.sdk.ingester import Entity
from worker.backend import Backend
from worker.models import Metadata, Policy


class LabIntegration(Backend):

    def setup(self) -> Metadata:
        return Metadata(name="lab_integration", app_name="lab_integration_app", app_version="1.0.0")
    
    def load_from_csv(self, filename: str) -> list:
        ''' function to read a csv file and return it as a list '''
        pdu_list = []

        ''' read the csv file and look through creating a dict for each row, then append to our list '''
        with open(filename, newline='') as csvfile:
            ''' use a dict reader so we can reference via column names '''
            reader = csv.DictReader(csvfile)
            for row in reader:
                pdu = {
                    'name': row['name'],
                    'serial': row['serial'],
                    'model': row['model'],
                    'manufacturer': row['manufacturer'],
                    'management_ip': row['management_ip']
                }
                pdu_list.append(pdu)
        return pdu_list

    def transform_to_diode(self, pdu_list: list) -> list:
        entities = []
        for pdu in pdu_list:
            ''' create Device Entity, an IP Address and an Interface '''
            device = Device(
                name = pdu['name'],
                device_type=pdu['model'],
                manufacturer=pdu['manufacturer'],
                site='Prague',
                role='pdu',
                serial=pdu['serial'],
                status='active',
                primary_ip4=IPAddress(
                    address=pdu['management_ip'],
                    status='active',
                    description='loaded from csv',
                    assigned_object_interface=Interface(
                        name='eth0',
                        type='1000base-t',
                        device=Device(
                            name = pdu['name'],
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

    def run(self, policy_name: str, policy: Policy) -> Iterable[Entity]:
        entities = []

        p = json.loads(policy.model_dump_json())
        method = p.get('config', {}).get('method')
        logging.info(f"Integration method: {method.upper()}")

        pdu_list = []
        ''' load method depends on our environment '''
        if method == 'csv':
            filename = p.get('config', {}).get('csv_filename')
            pdu_list = self.load_from_csv(filename)

        if pdu_list:
            entities=self.transform_to_diode(pdu_list)

        logging.info(f"{len(entities)} entities to be ingested")
        return entities