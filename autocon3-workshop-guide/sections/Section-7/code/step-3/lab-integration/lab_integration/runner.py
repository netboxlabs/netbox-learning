#!/usr/bin/env python
import requests
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

    def load_from_controller(self, controller_url: str, controller_token: str) -> list:
        ''' function to read from the controller and return a list '''
        pdu_list = []
        names = []
        headers = {'Authorization': f'Token {controller_token}' }
        r = requests.get(controller_url, headers=headers)
        ''' get the brief list '''
        if r.status_code == 200:
            for item in r.json():
                names.append(item["name"])
        ''' loop through the brief list to get the individual pdus '''
        for name in names:
            iurl = f'{controller_url}?name={name}'
            r = requests.get(iurl, headers=headers)
            if r.status_code == 200:     
                pdu_list.append(r.json())

        return pdu_list


    def load_from_csv(self, filename: str) -> list:
        ''' function to read a csv file and return it as a list '''
        pdu_list = []

        ''' read the csv file and look through creating a dict for each row, then append to our list '''
        with open(filename, newline='') as csvfile:
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
        elif method == "api":
            controller_url = p.get('config', {}).get('controller_url')
            controller_token = p.get('config', {}).get('controller_token')
            pdu_list = self.load_from_controller(controller_url, controller_token)
    
        if pdu_list:
            entities=self.transform_to_diode(pdu_list)

        logging.info(f"{len(entities)} entities to be ingested")
        return entities
