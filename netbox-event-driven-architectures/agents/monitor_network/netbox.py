import pynetbox
import logging
from requests.exceptions import MissingSchema

class NetBoxHelper:

    netbox = None
    logger = None
    netbox_url = ""
    netbox_token = ""
    __instance = None
    
    # Singleton ---
    @staticmethod
    def getInstance(netbox_url: str, netbox_token: str):
        if NetBoxHelper.__instance == None:
            NetBoxHelper(netbox_url, netbox_token)
        return NetBoxHelper.__instance
    
    def __init__(self, netbox_url: str, netbox_token: str):
        if NetBoxHelper.__instance != None:
            raise Exception(f"{NetBoxHelper.__name__} singleton already created. Please use {NetBoxHelper.__name__}.getInstance() instead")
        else:
            NetBoxHelper.__instance = self
        
        logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=logging.INFO)
        
        self.logger = logging.getLogger(__name__)

        self.netbox_url = netbox_url
        self.netbox_token = netbox_token
        
        try:
            self.netbox = pynetbox.api(self.netbox_url, self.netbox_token)
        except Exception as e:
            self.logger.debug(f"Unable to connect to NetBox instance: {e}")
            return None
    # --- Singleton
        
    # Functions
    def get_active_devices_with_a_mgmt_ipv4(self) -> (int, int, pynetbox.core.response.RecordSet):
        total_devices_count = 0
        elligible_devices_count = 0
        elligible_devices = None

        self.logger.info("Retrieving devices from NetBox...")
        
        try:
            total_devices_count = len(self.netbox.dcim.devices.all())
            elligible_devices = self.netbox.dcim.devices.filter(status='active', has_primary_ip='True')
            elligible_devices_count = len(elligible_devices)
            
        except (pynetbox.core.query.RequestError, MissingSchema) as e:
            self.logger.info(f"Could not establish connection with NetBox API. Please verify details. Exception details: {e}")
        except AttributeError as e:
            self.logger.critical(f"Attribute error: {e}. Did you specify an invalid API endpoint?")

        return total_devices_count, elligible_devices_count, elligible_devices