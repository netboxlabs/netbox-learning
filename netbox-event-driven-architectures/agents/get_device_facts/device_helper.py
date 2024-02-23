import logging
from napalm.base.exceptions import ModuleImportError, ConnectionException
from napalm import get_network_driver
from pythonping import ping
from pythonping.executor import SuccessOn
import ipaddress

class NetworkDeviceHelper:
    
    DEFAULT_TIMEOUT = 5
    DEFAULT_PING_COUNT = 2
    NAPALM_RUNNING_CONFIG_KEY = 'running'
    TYPE_FACTS = 1
    TYPE_RUNNING_CONFIG = 2

    logger = None
    device_driver = None
    device_connection = None
    username = None
    password = None
    device = None

    optional_args = {
                    "insecure": True
                    }
        
    def __init__(self, device):
        logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=logging.DEBUG)
        
        self.logger = logging.getLogger(__name__)

        self.device = device
        
        try:
            # Figure out the device driver
            if str(self.device.device_type.manufacturer) == 'Nokia':
                device_driver = 'srl'
                self.username = 'admin'
                self.password = 'NokiaSrl1!'
            elif str(self.device.device_type.manufacturer) == 'Arista':
                device_driver = 'eos'
                self.username = 'admin'
                self.password = 'admin'
            else:
                raise ModuleImportError(f"Unknown manufacturer {self.device.device_type.manufacturer}")
            
            # Ping the device first as some device drivers fail without throwing an exception if NAPALM can't reach the host
            if ping(self.get_device_mgmt_ip(),
                    verbose=False,
                    timeout=self.DEFAULT_TIMEOUT,
                    count=self.DEFAULT_PING_COUNT).success(option=SuccessOn.Most):
                
                # Create the NAPALM device handler
                napalm_driver = get_network_driver(device_driver)
                self.device_connection = napalm_driver(hostname=self.get_device_mgmt_ip(),
                                                       username=self.username,
                                                       password=self.password,
                                                       timeout=self.DEFAULT_TIMEOUT,
                                                       optional_args=self.optional_args)
            else:
                raise ConnectionException()

        except ModuleImportError as e:
            self.logger.debug(f"Cannot find NAPALM device_driver for {device_driver} to connect to device at {self.get_device_mgmt_ip()}. Is it installed? If you're using SR Linux , try here: https://github.com/napalm-automation-community/napalm-srlinux/blob/main/setup.py")
            raise e
        except ConnectionException as e:
            self.logger.debug(f"Could not connect to device at {self.get_device_mgmt_ip()}. {e}")
        except Exception as e:
            self.logger.debug(f"Unexpected exception of type {type(e)} caught when trying to pull config from device at {self.get_device_mgmt_ip()}. Exception: {e}")

    # Functions
    def get_device_mgmt_ip(self):
        if self.device != None:
            # Strip CIDR from the Primary IPv4 and convert to a string
            return str(ipaddress.ip_interface(str(self.device.primary_ip4)).ip)
        else:
            raise RuntimeError()

    def get_config(self, type):
        output = None
        try:
            self.device_connection.open()

            if type == self.TYPE_FACTS:
                output = self.device_connection.get_facts()
            elif type == self.TYPE_RUNNING_CONFIG:
                output = self.device_connection.get_config()[self.NAPALM_RUNNING_CONFIG_KEY]
            else:
                raise RuntimeError(f"Calls to NetworkDeviceHelper.get_config() must specify either TYPE_FACTS or TYPE_RUNNING_CONFIG.")
        except Exception as e:
            self.logger.debug(e)
        
        # SR Linux returns an empty string instead None
        if output == '':
            output = None
        return output