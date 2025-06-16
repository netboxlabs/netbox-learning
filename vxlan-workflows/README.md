# VXLAN Configuration Fetcher

This tool fetches and flattens VXLAN configuration data from a NetBox instance for a specific device using Custom Objects.

## Setup

1.  **Create a virtual environment:**

    ```bash
    python3 -m venv venv
    ```

2.  **Activate the virtual environment:**

    ```bash
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Set the required environment variables:**

    ```bash
    export NETBOX_URL="<your_netbox_url>"
    export NETBOX_TOKEN="<your_netbox_api_token>"
    ```
    Replace `<your_netbox_url>` and `<your_netbox_api_token>` with your actual NetBox URL and API token. The URL should be the base URL of your NetBox instance (e.g., `http://netbox.example.com/`).

2.  **Run the script:**

    ```bash
    python cli.py <device_name>
    ```
    Replace `<device_name>` with the name of the device you want to query.

    **Example:**
    ```bash
    python cli.py example_vtep_leaf
    ``` 