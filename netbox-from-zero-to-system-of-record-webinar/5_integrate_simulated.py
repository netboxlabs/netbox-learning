#!/bin/sh
''''exec "$(dirname "$0")/.venv/bin/python" "$0" "$@" #'''  # runs this file with the demo venv
"""Demo 2, step 2 (Integrate): a controller as a second source for the same review queue.

Sends as the source 'controller-sim'. If you show a real NetBox Labs controller integration
instead, skip this script; the Assurance steps are the same.
"""
from common import *
from sources import controller

APP = "controller-sim"
title("Demo 2 · 2 Integrate (controller as a second source)")
ents = controller()
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
step("What it reports that differs from NetBox:")
for line in ("sw-lon-01 status active -> offline", "uplink descriptions on sw-lon-01 and sw-nyc-01", "VLAN 100 users in LON-DC1"):
    note(line)
