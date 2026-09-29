#!/bin/sh
''''exec "$(dirname "$0")/.venv/bin/python" "$0" "$@" #'''  # runs this file with the demo venv
"""Demo 2, step 4 (Apply): after applying in Assurance, show that NetBox changed and logged it.

Apply one deviation (for example the serial on sw-nyc-01), bulk-apply a group, then run this.
It prints the objects the demo touches and the latest change log entries.
"""
from common import *

nb = netbox()
title("Demo 2 · 4 Apply: NetBox updated, change logged")
step("What NetBox holds now")
for name in ("sw-nyc-01", "sw-nyc-02", "core-nyc-01", "core-lon-01", "sw-lon-01", "sw-sin-01", "ap-nyc-07"):
    d = nb.dcim.devices.get(name=name)
    if d is None:
        note(f"{name:12} not in NetBox")
        continue
    ip = d.primary_ip4.address if d.primary_ip4 else "-"
    print(f"  {name:12} status={d.status.value:8} serial={d.serial or '-':12} platform={d.platform.name if d.platform else '-':7} primary={ip}")
step("Latest change log entries")
changes = nb.http_session.get(f"{NETBOX_URL}/api/core/object-changes/", params={"ordering": "-time", "limit": 12}).json()["results"]
for c in changes:
    print(f"  {c['time'][:19]}  {c['action']['value']:7} {c['changed_object_type']:22} {str(c['object_repr'])[:28]:28} by {c.get('user_name') or '-'}")
step(f"In the UI: {ui('/core/changelog/')}")
