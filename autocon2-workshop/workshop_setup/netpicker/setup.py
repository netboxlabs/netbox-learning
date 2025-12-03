import requests
import os

# Server details constructed from environment variables
SERVER_URL = f"http://{os.getenv('MY_EXTERNAL_IP')}:{os.getenv('NETPICKER_API_PORT')}"

# Credentials
USERNAME = 'admin@admin.com'
PASSWORD = '12345678'

# Policy name and existing policies to delete
POLICY_NAME = 'autocon_workshop'
EXISTING_POLICIES = ['CIS', 'CVE', 'Integrations']

# Rule name based on the GUI's naming convention
RULE_NAME = 'rule_test_rule_1'

# Agent ID and Vault Name
AGENT_ID = '2389276829'
VAULT_NAME = 'autocon_workshop'

def get_token():
    auth_url = f'{SERVER_URL}/api/v1/auth/jwt/login'
    payload = {
        'grant_type': 'password',
        'scope': 'openid access:api',
        'username': USERNAME,
        'password': PASSWORD
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    print(f"Authenticating with {auth_url}...")
    response = requests.post(auth_url, data=payload, headers=headers)
    response.raise_for_status()
    token = response.json().get('access_token')
    if not token:
        raise Exception('Authentication failed: No access_token found in response.')
    return token

def delete_existing_policies(token):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    for policy in EXISTING_POLICIES:
        api_url = f'{SERVER_URL}/api/v1/policy/default/{policy}'
        print(f"Deleting policy '{policy}'...")
        response = requests.delete(api_url, headers=headers)
        if response.status_code == 204:
            print(f"Policy '{policy}' deleted successfully.")
        elif response.status_code == 404:
            print(f"Policy '{policy}' not found.")
        else:
            print(f"Failed to delete policy '{policy}'. Status code: {response.status_code}")
            response.raise_for_status()

def create_policy(token):
    api_url = f'{SERVER_URL}/api/v1/policy/default/'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    payload = {
        "name": POLICY_NAME,
        "description": "",
        "enabled": True,
        "id": POLICY_NAME
    }
    print(f"Creating policy {POLICY_NAME}...")
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 201:
        print(f"Policy '{POLICY_NAME}' created successfully.")
    elif response.status_code == 200:
        print(f"Policy '{POLICY_NAME}' already exists.")
    else:
        response.raise_for_status()
    return response.json()

def create_rule(token):
    api_url = f'{SERVER_URL}/api/v1/policy/default/{POLICY_NAME}/rule/'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    payload = {
        "name": RULE_NAME,
        "platform": ["nokia_srl"],
        "severity": "MEDIUM",
        "definition": {
            "code": f"""@medium(
    name='{RULE_NAME}',
    platform=['nokia_srl'],
)
def {RULE_NAME}(configuration, commands, device):
    assert f'host-name {{device.name}}' in configuration"""
        },
        "ruleset": ""  # Updated to match the curl output
    }
    print(f"Creating rule '{RULE_NAME}' in policy '{POLICY_NAME}'...")
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"Rule '{RULE_NAME}' created successfully.")
    else:
        response.raise_for_status()
    return response.json()

def create_vault(token):
    api_url = f'{SERVER_URL}/api/v1/agents/default/{AGENT_ID}/vaults/{VAULT_NAME}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    payload = {
        "ssh": {
            "username": "admin",
            "password": "NokiaSrl1!"
        },
        "secret": ""
    }
    print(f"Creating vault '{VAULT_NAME}' for agent '{AGENT_ID}'...")
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"Vault '{VAULT_NAME}' created successfully.")
    else:
        response.raise_for_status()
    return response.json()

def main():
    try:
        print(f"Using SERVER_URL: {SERVER_URL}")
        # Step 1: Authenticate and get a token
        print("Starting authentication process...")
        token = get_token()
        print('Authentication successful.')

        # Step 2: Delete existing policies
        delete_existing_policies(token)

        # Step 3: Create the policy
        #create_policy(token)

        # Step 4: Create the rule within the policy
        #create_rule(token)

        # Step 5: Create the vault
        create_vault(token)

    except requests.HTTPError as e:
        print(f'HTTP Error: {e.response.status_code} - {e.response.text}')
    except Exception as e:
        print(f'An error occurred: {str(e)}')

if __name__ == '__main__':
    main()