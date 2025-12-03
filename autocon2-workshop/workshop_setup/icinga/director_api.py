import requests
import json
import argparse

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def create_service_apply_rule(server, username, password, rule):
    """
    Creates a service apply rule in Icinga Director if it doesn't already exist.

    Parameters:
        server (str): The URL of the Icinga server.
        username (str): The username for Icinga API authentication.
        password (str): The password for Icinga API authentication.
        rule (dict): The dictionary containing the service apply rule details.
        
    Returns:
        dict: The response JSON if the rule was created successfully, or an error message otherwise.
    """
    rule_url = f"{server}/icingaweb2/director/serviceapplyrules"
    service_url = f"{server}/icingaweb2/director/service"

    # Check if the rule already exists
    existing_rules_response = requests.get(
        rule_url,
        auth=(username, password),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        verify=False  # Set to True if you have a valid SSL certificate
    )

    if existing_rules_response.status_code == 200:
        existing_rules = existing_rules_response.json().get('objects', [])
        for existing_rule in existing_rules:
            if existing_rule.get('object_name') == rule['object_name']:
                print(f"Service apply rule '{rule['object_name']}' already exists. Existing filter is {existing_rule.get('assign_filter', 'no filter')}")
                requests.delete(
                    f"{service_url}?name={rule['object_name']}",
                    auth=(username, password),
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                )
                # return


    # Create the service apply rule if it does not exist
    response = requests.post(
        service_url,
        auth=(username, password),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        data=json.dumps(rule),
        verify=False  # Set to True if you have a valid SSL certificate
    )
    
    if response.status_code in [200, 201, 202]:
        print("Service apply rule created successfully")
        return response.json()
    else:
        print("Failed to create service apply rule")
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return {"error": response.text, "status_code": response.status_code}

def main():
    parser = argparse.ArgumentParser(description="Create a service apply rule in Icinga Director.")
    parser.add_argument("-s", "--server", type=str, required=True, help="The URL of the Icinga server")
    parser.add_argument("-u", "--username", type=str, required=True, help="The username for Icinga API authentication")
    parser.add_argument("-p", "--password", type=str, required=True, help="The password for Icinga API authentication")

    args = parser.parse_args()

    # Example service apply rule data (this can be customized as needed)
    service_apply_rules = [
        # {
        #     "object_name": "HTTP",
        #     "object_type": "apply",
        #     "imports": ["srvt http"],
        #     "assign_filter": "host.vars.model=%227220 IXR-D2L%22",
        #     "vars": {}
        # },
        {
            "object_name": "SNMP",
            "object_type": "apply",
            "imports": ["srvt snmpv3"],
            "assign_filter": "host.vars.model=%227220 IXR-D2L%22",
            "vars": {
                "snmpv3_auth_key": "snmppassword",
                "snmpv3_label": "Uptime is",
                "snmpv3_oid": "1.3.6.1.2.1.1.3.0",
                "snmpv3_priv_key": "snmpprivpassword",
                "snmpv3_user": "snmpuser"
            }
        },
        {
            "object_name": "SSL - ",
            "object_type": "apply",
            "imports": ["srvt ssl certificate"],
            "assign_filter": "host.vars.ssl=true",
            "apply_for": "host.vars.ssl",
            "vars": {
                "ssl_cert_hostname": "$config$"
            }
        },
        {
            "object_name": "SSH",
            "object_type": "apply",
            "imports": ["srvt ssh"],
            "assign_filter": "host.vars.model=%227220 IXR-D2L%22",
            "vars": {}
        },
        {
            "object_name": "Icinga2",
            "object_type": "apply",
            "imports": ["srvt icinga service"],
            "assign_filter": "%22icinga-endpoint%22=host.vars.tags",
            "vars": {}
        },
        {
            "object_name": "Icinga2 Cluster",
            "object_type": "apply",
            "imports": ["srvt icinga cluster"],
            "assign_filter": "%22icinga-endpoint%22=host.vars.tags",
            "vars": {}
        },
        {
            "object_name": "Load",
            "object_type": "apply",
            "imports": ["srvt load linux"],
            "assign_filter": "%22icinga-endpoint%22=host.vars.tags",
            "vars": {}
        },
        {
            "object_name": "Ping",
            "object_type": "apply",
            "imports": ["srvt ping linux"],
            "assign_filter": "host.address=true",
            "vars": {}
        },
            {
            "object_name": "Ping the other Nokia",
            "object_type": "apply",
            "imports": ["srvt nokia ping"],
            "assign_filter": "host.vars.ping_target=true",
            "vars": {
                "nokia_ping_target": "$host.vars.ping_target$"
            }
        },
        {
            "object_name": "Icinga TCP",
            "object_type": "apply",
            "imports": ["srvt tcp Icinga"],
            "assign_filter": "%22workshop_software%22=host.vars.tags",
            "vars": {}
        },
        {
            "object_name": "Meerkat TCP",
            "object_type": "apply",
            "imports": ["srvt tcp Meerkat"],
            "assign_filter": "%22workshop_software%22=host.vars.tags",
            "vars": {}
        },
        {
            "object_name": "Netbox TCP",
            "object_type": "apply",
            "imports": ["srvt tcp Netbox"],
            "assign_filter": "%22workshop_software%22=host.vars.tags",
            "vars": {}
        },
        {
            "object_name": "Netpicker TCP",
            "object_type": "apply",
            "imports": ["srvt tcp Netpicker"],
            "assign_filter": "%22workshop_software%22=host.vars.tags",
            "vars": {}
        },
        {
            "object_name": "Slurpit TCP",
            "object_type": "apply",
            "imports": ["srvt tcp Slurpit"],
            "assign_filter": "%22workshop_software%22=host.vars.tags",
            "vars": {}
        }
    ]

    for service_apply_rule in service_apply_rules:
        response = create_service_apply_rule(args.server, args.username, args.password, service_apply_rule)
    

if __name__ == "__main__":
    main()
