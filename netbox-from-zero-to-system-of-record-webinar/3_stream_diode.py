#!/bin/sh
''''exec "$(dirname "$0")/.venv/bin/python" "$0" "$@" #'''  # runs this file with the demo venv
"""Demo 1, step 3 (Stream): the same spreadsheet through Diode, run twice, no duplicates.

Sends every row of data/devices.csv plus the two new switches in data/devices-new.csv, by name
only: no IDs, no lookups, no ordering. Diode matches what NetBox already has.

Without Assurance, Diode writes straight into NetBox: the six devices from step 2 match and are
left alone, and the two new switches are created. With Assurance (NetBox Labs), what differs
arrives as deviations to review instead. Either way, run it again: nothing is duplicated.

  ./3_stream_diode.py            send the spreadsheet through Diode
  ./3_stream_diode.py --check    each device exists exactly once
"""
import csv

from netboxlabs.diode.sdk.ingester import Device, Entity, Interface, IPAddress, Location, Rack

from common import *

APP = "xls-import"


def rows():
    for f in ("devices.csv", "devices-new.csv"):
        yield from csv.DictReader(open(DATA / f))


def entities():
    for r in rows():
        loc = Location(name=r["location"], site=r["site"])
        rack = Rack(name=r["rack"], site=r["site"], location=loc)
        yield Entity(device=Device(name=r["name"], site=r["site"], location=loc, rack=rack, position=float(r["position"]), face="front",
                                   device_type=r["model"], manufacturer=r["manufacturer"], role=r["role"], status=r["status"]))
        # the interface and IP carry the full device, not just its name: for a device NetBox does not have yet
        # (sw-lon-02, sw-sin-02, waiting in Assurance), Diode would otherwise try to create it without a type or role
        ref = Device(name=r["name"], site=r["site"], device_type=r["model"], manufacturer=r["manufacturer"], role=r["role"])
        mgmt = Interface(device=ref, name=r["mgmt_interface"], type="1000base-t", mgmt_only=True)
        yield Entity(interface=mgmt)
        yield Entity(ip_address=IPAddress(address=r["mgmt_ip"], status="active", assigned_object_interface=mgmt))


def check():
    nb = netbox()
    title("Stream: every device exactly once")
    for r in rows():
        n = len(list(nb.dcim.devices.filter(name=r["name"])))
        (ok if n == 1 else (warn if n == 0 else fail))(f"{r['name']}: {n}")
    if has("netbox_assurance_plugin"):
        note("0 for sw-lon-02 or sw-sin-02 means their deviations are not applied yet.")
    else:
        note("0 for sw-lon-02 or sw-sin-02: give the reconciler a few seconds and check again.")


if "--check" in sys.argv:
    check()
    raise SystemExit

title("Demo 1 · 3 Stream: Diode, by name")
ents = list(entities())
step(f"Sending {len(ents)} entities ({sum(1 for _ in rows())} devices with their management interface and IP) as {APP!r}")
os.environ.setdefault("DIODE_SDK_LOG_LEVEL", "WARNING")
with diode(APP) as client:
    resp = client.ingest(entities=ents)
if resp.errors:
    for e in resp.errors:
        fail(e)
    raise SystemExit(1)
ok("accepted by Diode: one call, no IDs")
print()
if has("netbox_assurance_plugin"):
    step(f"Assurance is installed, so open {ui('/plugins/assurance/deviations/')}")
    note("Filter by source xls-import. Expect creations for sw-lon-02 and sw-sin-02 only:")
    note("the six devices from step 2 already match, so they produce no deviation.")
    note("Run this script again: no new deviations. Apply the two, then run --check.")
else:
    step("Diode writes straight into NetBox: the six known devices match, the two new switches are created")
    note("Run this script again: nothing is duplicated. Then run ./3_stream_diode.py --check.")
