#!/bin/sh
''''exec "$(dirname "$0")/.venv/bin/python" "$0" "$@" #'''  # runs this file with the demo venv
"""Demo 2, step 4 (Apply): after applying in Assurance, show that NetBox changed and logged it.

Apply one deviation (for example the serial on sw-nyc-01), bulk-apply a group, then run this.
It prints the objects the demo touches and the latest change log entries.
"""
from common import *

nb = netbox()
title("Demo 2 · 4 Apply: NetBox updated, change logged")
step("The devices changed most recently (the ones you just applied)")
# only devices touched in the last two hours: bulk-loaded rows carry no timestamp and would sort first
from datetime import datetime, timedelta, timezone
since = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
recent = nb.http_session.get(f"{NETBOX_URL}/api/dcim/devices/",
                             params={"ordering": "-last_updated", "last_updated__gte": since, "limit": 10}).json()["results"]
if not recent:
    note("no device changed in the last two hours")
for d in (nb.dcim.devices.get(r["id"]) for r in recent):
    ip = d.primary_ip4.address if d.primary_ip4 else "-"
    print(f"  {d.name:18} {d.site.name:14} status={d.status.value:8} serial={d.serial or '-':14} platform={d.platform.name if d.platform else '-':10} primary={ip}")
step("Latest change log entries")
changes = [c for c in nb.http_session.get(f"{NETBOX_URL}/api/core/object-changes/", params={"ordering": "-time", "limit": 30}).json()["results"]
           if c.get("object_repr") != "preflight-probe"][:12]  # hide the preflight write test
for c in changes:
    print(f"  {c['time'][:19]}  {c['action']['value']:7} {c['changed_object_type']:22} {str(c['object_repr'])[:28]:28} by {c.get('user_name') or '-'}")
step(f"In the UI: {ui('/core/changelog/')}")
