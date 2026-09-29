#!/bin/sh
''''exec "$(dirname "$0")/.venv/bin/python" "$0" "$@" #'''  # runs this file with the demo venv
"""Demo 2, step 3 (Assure): review the deviations. Assurance has no REST API, so this is a guide.

Prints the links and the order to show things in. --open opens the deviations page in your browser.
"""
import webbrowser

from common import *

url = ui("/plugins/assurance/deviations/")
if not has("netbox_assurance_plugin"):
    title("Demo 2 · 3 Assure")
    warn("Assurance (NetBox Labs) is not installed: Diode already wrote the changes into NetBox.")
    note("Run ./7_apply_check.py to see them and the change log.")
    raise SystemExit
title("Demo 2 · 3 Assure: review the deviations")
step(f"Open {url}")
for i, line in enumerate([
        "Active deviations: everything any source reported that differs from NetBox.",
        "Filter by source: discovery-sim (or your agent), then controller-sim. Two sources, one queue.",
        "Open sw-sin-01's management IP: NetBox says 10.30.0.11, discovery says 10.30.0.21. Show the Changes tab.",
        "Open ap-nyc-07: a device nobody recorded. This is the one to talk about.",
        "Leave sw-lon-01 offline open for the next step."], 1):
    print(f"  {TEAL}{i}{OFF}  {line}")
if "--open" in sys.argv:
    webbrowser.open(url)
