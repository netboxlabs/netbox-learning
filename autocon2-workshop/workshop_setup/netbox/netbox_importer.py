import argparse
import json
import pynetbox

def get_arguments():
    # Initialize the parser
    parser = argparse.ArgumentParser(description="Import Netbox Data")

    # Add arguments for URL and Token
    parser.add_argument("--url", required=True, help="The URL of the NetBox instance")
    parser.add_argument("--token", required=True, help="The API token for authentication")
    parser.add_argument("--file", required=True, help="Json file containing the payload")

    # Parse the arguments
    args = parser.parse_args()

    # Return the parsed arguments
    return args

class Netbox:
    def __init__(self, url, token, payload) -> None:
        # NetBox API details
        self.netbox_url = url
        self.netbox_token = token
        self.payload = payload
        self.object_type = None
        self.obj = None
        self.required_fields = []
        self.init_api()


    def init_api(self):
        # Initialize pynetbox API connection
        self.nb = pynetbox.api(self.netbox_url, token=self.netbox_token)

    def findBy(self, key):
        self.obj = self.object_type.get(**{key: self.payload[key]})

    @property
    def hasRequired(self):
        missing = []
        for key in self.required_fields:
            if key not in self.payload:
                missing.append(key)
        if missing:
            print(f"missing required fields {', '.join(missing)}")
            return False
        else: 
            return True

    def createOrUpdate(self):
        # If object exists see if we need to update it
        if self.obj:
            # Do we need to save?
            updated = False

            for key, value in self.payload.items():
                if isinstance(value, dict):
                    if hasattr(self.obj, key):
                        child_key = next(iter(value))
                        child_value = value[child_key]
                        if not hasattr(self.obj, key) or not hasattr(getattr(self.obj, key), child_key) or getattr(getattr(self.obj, key), child_key) != child_value:
                            print(f"Updating '{key}' from '{getattr(self.obj, key)}' to '{value}'")
                            setattr(self.obj, key, value)
                            updated = True 
                else:
                    if getattr(self.obj, key) != value:
                        print(f"Updating '{key}' from '{getattr(self.obj, key)}' to '{value}'")
                        setattr(self.obj, key, value)
                        updated = True                
            if updated:
                self.obj.save()
                # TODO: error handling here
                print(f"Object '{self.payload}' updated successfully.")
            else:
                print(f"No changes detected for '{self.payload}'.")
        # If the object doesn't exist then create it
        else:
            if self.hasRequired:
                self.object_type.create(self.payload)
                print(f"Object '{self.payload['name']}' created successfully.")              

class NetBoxSite(Netbox):
    def __init__(self, url, token, payload, find_key = 'name') -> None:
        # Initialize the Netbox superclass with URL and token
        super().__init__(url, token, payload)
        self.object_type = self.nb.dcim.sites
        self.required_fields = [ 
            "name",
            "slug",
            "status",
        ]
        self.find_key = find_key
        self.findBy(self.find_key)
        self.createOrUpdate()

class NetboxDevice(Netbox):
    def __init__(self, url, token, payload, find_key = 'name') -> None:
        # Initialize the Netbox superclass with URL and token
        super().__init__(url, token, payload)
        self.object_type = self.nb.dcim.devices
        self.required_fields = [ 
            "device_type",
            "manufacturer",
            "role",
            "site",
            "status",
        ]
        self.find_key = find_key
        self.findBy(self.find_key)
        self.createOrUpdate()

class NetboxDeviceInterface(Netbox):
    def __init__(self, url, token, payload, find_key = 'name') -> None:
        # Initialize the Netbox superclass with URL and token
        super().__init__(url, token, payload)
        self.object_type = self.nb.dcim.interfaces
        self.required_fields = [ 
            "device",
            "name",
            "type"      # virtual
        ]
        self.find_key = find_key
        self.findBy(self.find_key)
        self.createOrUpdate()


class NetboxTag(Netbox):
    def __init__(self, url, token, payload, find_key = 'name') -> None:
        # Initialize the Netbox superclass with URL and token
        super().__init__(url, token, payload)
        self.object_type = self.nb.extras.tags
        self.required_fields = [ 
            "color",
            "name",
            "slug"
        ]
        self.find_key = find_key
        self.findBy(self.find_key)
        self.createOrUpdate()

class NetboxCustomFields(Netbox):
    def __init__(self, url, token, payload, find_key = 'name') -> None:
        # Initialize the Netbox superclass with URL and token
        super().__init__(url, token, payload)
        self.object_type = self.nb.extras.custom_fields
        self.required_fields = [ 
            "weight",
            "filter_logic",
            "search_weight",
            "object_types",
            "type",
            "name",
        ]
        self.find_key = find_key
        self.findBy(self.find_key)
        self.createOrUpdate()

class NetboxCustomFieldChoiceSets(Netbox):
    def __init__(self, url, token, payload, find_key = 'name') -> None:
        # Initialize the Netbox superclass with URL and token
        super().__init__(url, token, payload)
        self.object_type = self.nb.extras.custom_field_choice_sets
        self.required_fields = [ 
            "name",
            "extra_choices",

        ]
        self.find_key = find_key
        self.findBy(self.find_key)
        self.createOrUpdate()

class NetboxContacts(Netbox):
    def __init__(self, url, token, payload, find_key = 'name') -> None:
        # Initialize the Netbox superclass with URL and token
        super().__init__(url, token, payload)
        self.object_type = self.nb.tenancy.contacts
        self.required_fields = [ 
            "name",
        ]
        self.find_key = find_key
        self.findBy(self.find_key)
        self.createOrUpdate()

class NetboxContactGroups(Netbox):
    def __init__(self, url, token, payload, find_key = 'name') -> None:
        # Initialize the Netbox superclass with URL and token
        super().__init__(url, token, payload)
        self.object_type = self.nb.tenancy.contact_groups
        self.required_fields = [ 
            "name",
            "slug",
        ]
        self.find_key = find_key
        self.findBy(self.find_key)
        self.createOrUpdate()

class NetboxClusterTypes(Netbox):
    def __init__(self, url, token, payload, find_key = 'name') -> None:
        # Initialize the Netbox superclass with URL and token
        super().__init__(url, token, payload)
        self.object_type = self.nb.virtualization.cluster_types
        self.required_fields = [ 
            "name",
            "slug",
        ]
        self.find_key = find_key
        self.findBy(self.find_key)
        self.createOrUpdate()

class NetboxClusters(Netbox):
    def __init__(self, url, token, payload, find_key = 'name') -> None:
        # Initialize the Netbox superclass with URL and token
        super().__init__(url, token, payload)
        self.object_type = self.nb.virtualization.clusters
        self.required_fields = [ 
            "name",
            "type",
            "status",
        ]
        self.find_key = find_key
        self.findBy(self.find_key)
        self.createOrUpdate()

class NetboxVirtualMachines(Netbox):
    def __init__(self, url, token, payload, find_key = 'name') -> None:
        # Initialize the Netbox superclass with URL and token
        super().__init__(url, token, payload)
        self.object_type = self.nb.virtualization.virtual_machines
        self.required_fields = [ 
            "name",
            "status"
        ]
        self.find_key = find_key
        self.findBy(self.find_key)
        self.createOrUpdate()

class NetboxIPAddresses(Netbox):
    def __init__(self, url, token, payload, find_key = 'name') -> None:
        # Initialize the Netbox superclass with URL and token
        super().__init__(url, token, payload)
        self.object_type = self.nb.ipam.ip_addresses
        self.required_fields = [ 
            "address",
            "status"    
        ]
        self.find_key = find_key
        self.findBy(self.find_key)
        self.createOrUpdate()

class NetboxServiceTemplates(Netbox):
    def __init__(self, url, token, payload, find_key = 'name') -> None:
        # Initialize the Netbox superclass with URL and token
        super().__init__(url, token, payload)
        self.object_type = self.nb.ipam.service_templates
        self.required_fields = [ 
            "name",
            "protocol",
            "ports"
        ]
        self.find_key = find_key
        self.findBy(self.find_key)
        self.createOrUpdate()

def read_json_file(file_path):
    # Read the JSON file from disk
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
        print(data)
    return data

if __name__ == "__main__":
    args = get_arguments()
    if args.file:
        payload = read_json_file(args.file)

    for k,v in payload.items():
        if k == 'extras.tags':
            for payload in v:
                obj = NetboxTag(args.url, args.token, payload)
        if k == 'extras.custom-field-choice-sets':
            for payload in v:
                obj = NetboxCustomFieldChoiceSets(args.url, args.token, payload)
        if k == 'extras.custom-fields':
            for payload in v:
                obj = NetboxCustomFields(args.url, args.token, payload)
        if k == 'dcim.sites':
            for payload in v:
                obj = NetBoxSite(args.url, args.token, payload)
        if k == 'dcim.device':
            for payload in v:
                obj = NetboxDevice(args.url, args.token, payload)
        if k == 'tenancy.contact-groups':
            for payload in v:
                obj = NetboxContactGroups(args.url, args.token, payload)
        if k == 'tenancy.contacts':
            for payload in v:
                obj = NetboxContacts(args.url, args.token, payload)
        if k == 'virtualization.cluster-types':
            for payload in v:
                obj = NetboxClusterTypes(args.url, args.token, payload)
        if k == 'virtualization.clusters':
            for payload in v:
                obj = NetboxClusters(args.url, args.token, payload)
        if k == 'virtualization.virtual-machines':
            for payload in v:
                obj = NetboxVirtualMachines(args.url, args.token, payload)
        if k == 'dcim.interfaces':
            for payload in v:
                obj = NetboxDeviceInterface(args.url, args.token, payload)
        if k == 'ipam.ip-addresses':
            for payload in v:
                obj = NetboxIPAddresses(args.url, args.token, payload)
        if k == 'ipam.service-templates':
            for payload in v:
                obj = NetboxServiceTemplates(args.url, args.token, payload)
