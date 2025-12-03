import os
import requests
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Update Slurpit plugin settings in NetBox.")
parser.add_argument("--slurpittoken", required=True, help="API key for Slurpit")
parser.add_argument("--netboxuser", required=True, help="NetBox username for login")
parser.add_argument("--netboxpass", required=True, help="NetBox password for login")
args = parser.parse_args()

# Get environment variables
my_external_ip = os.getenv("MY_EXTERNAL_IP")
netbox_port = os.getenv("NETBOX_PORT")
slurpit_port = os.getenv("SLURPIT_PORT")

# Construct URLs
login_url = f'http://{my_external_ip}:{netbox_port}/login/'
settings_url = f'http://{my_external_ip}:{netbox_port}/plugins/slurpit/settings/'
server_url = f'http://{my_external_ip}:{slurpit_port}'

# Debug output for constructed URLs
print(f"Connecting to NetBox at IP: {my_external_ip} and Port: {netbox_port}")
print(f"Login URL: {login_url}")
print(f"Settings URL: {settings_url}")
print(f"Server URL (for settings): {server_url}")

# Step 1: Login to NetBox to obtain a session cookie
session = requests.Session()  # Start a session to persist cookies
login_page = session.get(login_url, verify=False)  # Initial GET to retrieve CSRF token

# Extract the CSRF token from the login page
csrf_token = session.cookies.get('csrftoken')
if not csrf_token:
    print("Failed to retrieve CSRF token from login page.")
    exit(1)

# Prepare login data
login_data = {
    'csrfmiddlewaretoken': csrf_token,
    'next': '/',
    'username': args.netboxuser,
    'password': args.netboxpass
}

# Login POST request
login_headers = {
    'Referer': login_url,
    'Content-Type': 'application/x-www-form-urlencoded'
}
print("Attempting to log in to NetBox...")
login_response = session.post(login_url, headers=login_headers, data=login_data, verify=False)

# Check if login was successful
if login_response.status_code == 200 and "sessionid" in session.cookies:
    print("Login successful.")
else:
    print("Login failed. Please check your username and password, or verify that NetBox is accessible.")
    print(f"Status Code: {login_response.status_code}")
    print(f"Response: {login_response.text}")
    exit(1)

# Step 2: Retrieve CSRF token from the settings page
print("Accessing the settings page to retrieve CSRF token...")
settings_page = session.get(settings_url, headers={'Referer': login_url}, verify=False)

# Extract the new CSRF token from the settings page
csrf_token = session.cookies.get('csrftoken')
if not csrf_token:
    print("Failed to retrieve CSRF token from settings page.")
    exit(1)

# Step 3: Update the Slurpit plugin settings in NetBox using the session cookie
settings_headers = {
    'Referer': settings_url,
    'Content-Type': 'application/x-www-form-urlencoded'
}
settings_data = {
    'csrfmiddlewaretoken': csrf_token,
    'setting_id': '1',
    'server_url': server_url,
    'api_key': args.slurpittoken
}

print("Attempting to update plugin settings...")
response = session.post(settings_url, headers=settings_headers, data=settings_data, verify=False)

# Interpret response for settings update
if response.status_code == 200:
    print("Settings updated successfully in NetBox.")
elif response.status_code == 403:
    print("Failed to update settings: Access denied. Please check your permissions.")
elif response.status_code == 400:
    print("Failed to update settings: Bad request. Please verify the data being sent.")
else:
    print("An error occurred while updating settings.")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")