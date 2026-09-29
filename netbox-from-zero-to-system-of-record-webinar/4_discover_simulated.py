#!/bin/sh
''''exec "$(dirname "$0")/.venv/bin/python" "$0" "$@" #'''  # runs this file with the demo venv
"""Demo 2, step 1 (Discover), fallback: what an Orb agent would report, sent through Diode.

Use this when the lab is not reachable. It sends as the source 'discovery-sim'; sources.py lists
exactly what it reports and which differences from demo 1 are deliberate.
"""
from common import *
from sources import discovery

APP = "discovery-sim"
title("Demo 2 · 1 Discover (simulated agent)")
ents = discovery()
step(f"Reporting {len(ents)} observations as {APP!r}")
os.environ.setdefault("DIODE_SDK_LOG_LEVEL", "WARNING")
with diode(APP) as client:
    resp = client.ingest(entities=ents)
for e in resp.errors:
    fail(e)
if resp.errors:
    raise SystemExit(1)
ok("accepted by Diode")
if not has("netbox_assurance_plugin"):
    note("No Assurance here, so Diode writes these changes straight into NetBox; 7_apply_check.py shows them.")
step("What it reports that differs from NetBox (deviations, if Assurance is installed):")
for line in ("serial numbers and platforms on four devices", "new interface Vlan20 on sw-nyc-02, with 10.10.20.1/24",
             "a management IP on sw-sin-01 that is not in NetBox", "ap-nyc-07, an access point nobody recorded"):
    note(line)
