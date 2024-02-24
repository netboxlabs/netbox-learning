# nornir-netbox

Code for the **Getting Started with Nornir and NetBox for Network Automation Webinar** hosted by NetBox Labs in October 2023

The talk showed how to get started on your Network Automation journey with Nornir and NetBox and featured the nornir_netbox inventory plugin for Nornir.

## Getting Started

1. Clone Git repo and change into `nornir-netbox-webinar` directory
```
git clone https://github.com/netboxlabs/netbox-learning.git
cd netbox-learning/nornir-netbox-webinar
```
2. Create and activate Python 3 virtual environment
```
python3 -m venv ./venv
source venv/bin/activate
```
3. Install required Python packages
```
pip install -r requirements.txt
```
4. Set environment variables for the NetBox API token and URL
```
export NB_URL=<YOUR_NETBOX_URL> (note - must include http:// or https://) 
export NB_TOKEN=<YOUR_NETBOX_API_TOKEN>
```
