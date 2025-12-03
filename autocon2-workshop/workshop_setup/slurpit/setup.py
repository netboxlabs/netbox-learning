import os
import time
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings()

# -------------------------
# Step 0: Retrieve IP Address, Ports, and Subnet from Environment Variables
# -------------------------

# Retrieve the IP address from the environment variable
my_external_ip = os.getenv('MY_EXTERNAL_IP')

# Retrieve the ports from the environment variables
slurpit_port = os.getenv('SLURPIT_PORT')
netbox_port = os.getenv('NETBOX_PORT')

# Retrieve the subnet for the workshop
workshop_subnet = os.getenv('WORKSHOP_SUBNET')

# Check if the environment variables are set
if not my_external_ip:
    print('Error: The environment variable MY_EXTERNAL_IP is not set.')
    exit(1)

if not slurpit_port:
    print('Error: The environment variable SLURPIT_PORT is not set.')
    exit(1)

if not netbox_port:
    print('Error: The environment variable NETBOX_PORT is not set.')
    exit(1)

if not workshop_subnet:
    print('Error: The environment variable WORKSHOP_SUBNET is not set.')
    exit(1)

# Base URL for the Slurpit server
base_url = f'http://{my_external_ip}:{slurpit_port}'

# Create a session
session = requests.Session()

# -------------------------
# Wait for Service to Be Ready
# -------------------------

login_url = f'{base_url}/login'
timeout_seconds = 60
start_time = time.time()

while True:
    try:
        response = session.get(login_url, timeout=5)
        if response.status_code == 200:
            print("Service is available.")
            break
    except requests.exceptions.RequestException:
        pass  # Ignore connection errors and retry

    if time.time() - start_time > timeout_seconds:
        print(f"Error: Unable to connect to the service at {login_url} within {timeout_seconds} seconds.")
        exit(1)

    print("Waiting for the service to be ready...")
    time.sleep(1)

# -------------------------
# Step 1: Login to the Application
# -------------------------

# Login URL and headers
login_headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Origin': base_url,
    'Referer': f'{base_url}/',
    'User-Agent': 'Mozilla/5.0 (compatible; Python script)',
    'X-Requested-With': 'XMLHttpRequest',
}

# Login form data
login_data = {
    'invalidCredentials': '',
    'username': 'admin@admin.com',
    'password': '12345678',
}

# Prepare multipart/form-data
login_encoder = MultipartEncoder(fields=login_data)
login_headers['Content-Type'] = login_encoder.content_type

# Perform login
login_response = session.post(
    login_url,
    headers=login_headers,
    data=login_encoder,
    verify=False
)

# Check login success
if login_response.status_code == 200:
    print('Login successful.')
else:
    print('Login failed with status code:', login_response.status_code)
    print('Response:', login_response.text)
    exit(1)

# -------------------------
# Step 2: Make Authenticated Request to Add Scanner
# -------------------------

# AddScanner URL and headers
add_scanner_url = f'{base_url}/DevicesFinder/addScanner'
add_scanner_headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Origin': base_url,
    'Referer': f'{base_url}/admin/devices_finder',
    'User-Agent': 'Mozilla/5.0 (compatible; Python script)',
    'X-Requested-With': 'XMLHttpRequest',
}

# AddScanner form data
add_scanner_data = {
    'name': 'autocon_workshop',
    'version': 'snmpv3',
    'snmpv2ckey': '',
    'snmpv3username': 'snmpuser',
    'snmpv3authtype': 'sha',
    'snmpv3authkey': 'snmppassword',
    'snmpv3privtype': 'aes128',
    'snmpv3privkey': 'snmpprivpassword',
    'content': workshop_subnet,  # Use the environment variable here as well
}

# Prepare multipart/form-data
add_scanner_encoder = MultipartEncoder(fields=add_scanner_data)
add_scanner_headers['Content-Type'] = add_scanner_encoder.content_type

# Perform the addScanner request
add_scanner_response = session.post(
    add_scanner_url,
    headers=add_scanner_headers,
    data=add_scanner_encoder,
    verify=False
)

# Check if the request was successful
if add_scanner_response.status_code == 200:
    print('addScanner request successful.')
    print('Response:', add_scanner_response.text)
else:
    print('addScanner request failed with status code:', add_scanner_response.status_code)
    print('Response:', add_scanner_response.text)

# -------------------------
# Step 3: Configure NetBox Plugin in Slurpit
# -------------------------

# Plugin configuration URL and headers
plugin_config_url = f'{base_url}/Settings/update_plugin'
plugin_config_headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8,fr;q=0.7',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'DNT': '1',
    'Origin': base_url,
    'Referer': f'{base_url}/admin/settings',
    'User-Agent': 'Mozilla/5.0 (compatible; Python script)',
    'X-Requested-With': 'XMLHttpRequest',
}

# Plugin configuration data
plugin_config_data = {
    'plugin_url': f'http://{my_external_ip}:{netbox_port}',  # Use NETBOX_PORT here
    'plugin_key': '1234567890',
    'plugin_authorization': 'NetBox',
    'plugin_status': '1',
    'plugin_sync_netbox_devices': '1',
    'plugin_sync_netbox_sites': '1',
    'plugin_sync_netbox_ipam': '1',
    'plugin_sync_netbox_interfaces': '1',
    'plugin_sync_netbox_prefix': '0',
    'plugin_sync_nautobot_devices': '1',
    'plugin_sync_nautobot_sites': '1',
    'plugin_sync_nautobot_ipam': '0',
    'plugin_sync_nautobot_interfaces': '0',
    'plugin_sync_nautobot_prefix': '0',
}

# Perform the plugin configuration request
plugin_config_response = session.post(
    plugin_config_url,
    headers=plugin_config_headers,
    data=plugin_config_data,
    verify=False
)

# Check if the request was successful
if plugin_config_response.status_code == 200:
    print('Plugin configuration successful.')
    print('Response:', plugin_config_response.text)
else:
    print('Plugin configuration failed with status code:', plugin_config_response.status_code)
    print('Response:', plugin_config_response.text)

# -------------------------
# Step 4: Add a Vault to Slurpit
# -------------------------

# AddVault URL and headers
add_vault_url = f'{base_url}/vault/addVault'
add_vault_headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8,fr;q=0.7',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Origin': base_url,
    'Referer': f'{base_url}/admin/vault',
    'User-Agent': 'Mozilla/5.0 (compatible; Python script)',
    'X-Requested-With': 'XMLHttpRequest',
}

# Vault form data
add_vault_data = {
    'username': 'admin',
    'password': 'NokiaSrl1!',
    'password_confirm': 'NokiaSrl1!',
    'device_os': 'nokia_srl',
    'comment': '',
}

# Prepare multipart/form-data
add_vault_encoder = MultipartEncoder(fields=add_vault_data)
add_vault_headers['Content-Type'] = add_vault_encoder.content_type

# Perform the addVault request
add_vault_response = session.post(
    add_vault_url,
    headers=add_vault_headers,
    data=add_vault_encoder,
    verify=False
)

# Check if the request was successful
if add_vault_response.status_code == 200:
    print('Vault addition successful.')
    print('Response:', add_vault_response.text)
else:
    print('Vault addition failed with status code:', add_vault_response.status_code)
    print('Response:', add_vault_response.text)