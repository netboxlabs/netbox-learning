"""What the simulated discovery and the simulated controller report, as Diode entities.

Each list describes the network as that source sees it. Differences from what demo 1 loaded are
deliberate, so Assurance has real deviations to show:

  discovery-sim   serial numbers and a platform NetBox does not have, a new SVI with an address,
                  a management IP that moved on sw-sin-01, and an access point nobody recorded
  controller-sim  sw-lon-01 reported offline, uplink descriptions, and the user VLAN in London
"""
from netboxlabs.diode.sdk.ingester import VLAN, Device, Entity, Interface, IPAddress, Platform

import csv
from pathlib import Path

# every device reference carries site, type, manufacturer and role from the spreadsheet, so Diode can
# match it, and could create it, without "Field role is required" or "Field device_type is required"
SPEC = {r["name"]: r for f in ("devices.csv", "devices-new.csv")
        for r in csv.DictReader(open(Path(__file__).parent / "data" / f))}


def dev(name, **kw):
    r = SPEC[name]
    return Device(name=name, site=r["site"], device_type=r["model"], manufacturer=r["manufacturer"], role=r["role"], **kw)


def discovery():
    iosxe = Platform(name="IOS-XE", manufacturer="Cisco")
    eos = Platform(name="EOS", manufacturer="Arista")
    return [
        # serials and platforms: fields nobody typed into the spreadsheet
        Entity(device=dev("sw-nyc-01", serial="FOC2231X0AB", platform=iosxe)),
        Entity(device=dev("sw-nyc-02", serial="FOC2231X0CD", platform=iosxe)),
        Entity(device=dev("core-nyc-01", serial="JPE21420187", platform=eos)),
        Entity(device=dev("core-lon-01", serial="JPE21420322", platform=eos)),
        # a new SVI with an address on sw-nyc-02
        Entity(interface=Interface(device=dev("sw-nyc-02"), name="Vlan20", type="virtual", description="Printers")),
        Entity(ip_address=IPAddress(address="10.10.20.1/24", status="active",
                                    assigned_object_interface=Interface(device=dev("sw-nyc-02"), name="Vlan20", type="virtual"))),
        # the management address on sw-sin-01 is not the one in the spreadsheet
        Entity(ip_address=IPAddress(address="10.30.0.21/24", status="active",
                                    assigned_object_interface=Interface(device=dev("sw-sin-01"), name="GigabitEthernet0/0", type="1000base-t"))),
        # something on the network that nobody recorded
        Entity(device=Device(name="ap-nyc-07", site="NYC-DC1", role="Access Point", device_type="C9130AXI",
                             manufacturer="Cisco", serial="KWC2508A1XY", status="active")),
    ]


def controller():
    return [
        Entity(device=dev("sw-lon-01", status="offline")),
        Entity(interface=Interface(device=dev("sw-lon-01"), name="TenGigabitEthernet1/1/1", type="10gbase-x-sfpp",
                                   description="Uplink to core-lon-01 Ethernet1")),
        Entity(interface=Interface(device=dev("sw-nyc-01"), name="TenGigabitEthernet1/1/1", type="10gbase-x-sfpp",
                                   description="Uplink to core-nyc-01 Ethernet1")),
        Entity(vlan=VLAN(vid=100, name="users", site="LON-DC1", status="active")),
    ]
