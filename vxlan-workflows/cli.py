import requests
import json
import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Get flat VXLAN objects for a specific device.")
    parser.add_argument("device_name", help="The name of the device to process.")
    args = parser.parse_args()
    device_name = args.device_name

    netbox_url = os.getenv("NETBOX_URL")
    netbox_token = os.getenv("NETBOX_TOKEN")

    if not netbox_url:
        print("Error: NETBOX_URL environment variable not set.", file=sys.stderr)
        sys.exit(1)
    
    if not netbox_token:
        print("Error: NETBOX_TOKEN environment variable not set.", file=sys.stderr)
        sys.exit(1)

    if not netbox_url.endswith('/'):
        netbox_url += '/'
    
    vtep_url = f"{netbox_url}api/plugins/custom-objects/vtep/"
    headers = {"Authorization": f"Token {netbox_token}", "Content-Type": "application/json"}

    vteps_response = requests.get(vtep_url, headers=headers)

    if vteps_response.status_code != 200:
        print(f"Error getting VTEPs: Received status code {vteps_response.status_code}", file=sys.stderr)
        sys.exit(1)
    
    try:
        vteps_json = vteps_response.json().get("results", [])
    except json.JSONDecodeError as e:
        print(f"Error parsing VTEPs response: {e}", file=sys.stderr)
        sys.exit(1)

    flat_vxlan_list = []

    for vtep in vteps_json:
        if not vtep.get('device'):
            continue

        device_response = requests.get(f"{netbox_url}api/dcim/devices/{vtep['device']}/", headers=headers)
        if device_response.status_code != 200:
            print(f"Error getting device {vtep['device']}: Status {device_response.status_code}", file=sys.stderr)
            continue
        
        device = device_response.json()
        
        if device.get("name") != device_name:
            continue

        for vxlan_id in vtep.get("vxlans", []):
            vxlan_response = requests.get(f"{netbox_url}api/plugins/custom-objects/vxlan/{vxlan_id}/", headers=headers)
            if vxlan_response.status_code != 200:
                print(f"Error getting VXLAN {vxlan_id}: Status {vxlan_response.status_code}", file=sys.stderr)
                continue
            
            vxlan = vxlan_response.json()
            
            base_vxlan_data = {
                "site": device.get("site", {}).get("name"),
                "eos_l3_mtu": vtep.get("eos_l3_mtu"),
                "arp_suppression": vxlan.get("arp_suppression"),
                "bum_mcast_group": vxlan.get("bum_mcast_group"),
                "ingress_replication": vxlan.get("ingress_replication"),
                "l3_mtu": vxlan.get("l3_mtu"),
                "name": vxlan.get("name"),
            }

            if vxlan.get('ipv4_gw_and_mask'):
                ip_response = requests.get(f"{netbox_url}api/ipam/ip-addresses/{vxlan['ipv4_gw_and_mask']}/", headers=headers)
                if ip_response.status_code == 200:
                    base_vxlan_data["ipv4_gw_and_mask"] = ip_response.json().get("address")

            if vxlan.get('ipv6_gw_and_mask'):
                ip_response = requests.get(f"{netbox_url}api/ipam/ip-addresses/{vxlan['ipv6_gw_and_mask']}/", headers=headers)
                if ip_response.status_code == 200:
                    base_vxlan_data["ipv6_gw_and_mask"] = ip_response.json().get("address")
            
            if vxlan.get('dhcp_v4_server'):
                dhcp_response = requests.get(f"{netbox_url}api/ipam/ip-addresses/{vxlan['dhcp_v4_server']}/", headers=headers)
                if dhcp_response.status_code == 200:
                    base_vxlan_data["dhcp_v4_server"] = dhcp_response.json().get("address")

            if vxlan.get('dhcp_v4_source_vlan'):
                vlan_response = requests.get(f"{netbox_url}api/ipam/vlans/{vxlan['dhcp_v4_source_vlan']}/", headers=headers)
                if vlan_response.status_code == 200:
                    base_vxlan_data["dhcp_v4_source_vlan"] = vlan_response.json().get("name")

            base_vxlan_data["interface_description"] = f"{vxlan.get('name', '')}_{base_vxlan_data.get('ipv4_gw_and_mask', '')}"

            if vxlan.get('vrf_name'):
                vrf_response = requests.get(f"{netbox_url}api/ipam/vrfs/{vxlan['vrf_name']}/", headers=headers)
                if vrf_response.status_code == 200:
                    base_vxlan_data["vrf_name"] = vrf_response.json().get("name")
            
            if vxlan.get('vni'):
                vni_response = requests.get(f"{netbox_url}api/plugins/custom-objects/vni/{vxlan['vni']}/", headers=headers)
                if vni_response.status_code == 200:
                    vni = vni_response.json()
                    base_vxlan_data["vnid"] = vni.get("vnid")
                    
                    for vlan_id in vni.get("vlans", []):
                        flat_vxlan_data = base_vxlan_data.copy()
                        vlan_response = requests.get(f"{netbox_url}api/ipam/vlans/{vlan_id}/", headers=headers)
                        if vlan_response.status_code == 200:
                            vlan_object = vlan_response.json()
                            flat_vxlan_data["vlan_id"] = vlan_object.get("vid")
                            flat_vxlan_list.append(flat_vxlan_data)
    
    print(json.dumps(flat_vxlan_list, indent=4))

if __name__ == "__main__":
    main()