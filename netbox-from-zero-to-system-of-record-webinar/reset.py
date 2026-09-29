#!/bin/sh
''''exec "$(dirname "$0")/.venv/bin/python" "$0" "$@" #'''  # runs this file with the demo venv
"""Reset the demo instance to empty: every object the demos can create, every branch, and every
change request, review and policy.

Asks you to type the instance's hostname first; --yes skips that (for scripted resets).
Not covered, because there is no API for them: Assurance deviations (dismiss leftovers in the
UI) and the change log (NetBox keeps it by design).
"""
from urllib.parse import urlparse

from common import *

# Children before parents, so nothing is blocked by a reference
ORDER = [
    ("ipam", "ip-addresses"), ("ipam", "prefixes"), ("ipam", "vlans"), ("ipam", "vlan-groups"), ("ipam", "vrfs"),
    ("dcim", "cables"), ("dcim", "interfaces"), ("dcim", "devices"), ("dcim", "virtual-chassis"), ("dcim", "modules"), ("dcim", "racks"),
    ("dcim", "rack-roles"), ("dcim", "device-types"), ("dcim", "module-types"), ("dcim", "platforms"),
    ("dcim", "manufacturers"), ("dcim", "device-roles"), ("dcim", "locations"), ("dcim", "sites"),
    ("dcim", "site-groups"), ("dcim", "regions"), ("tenancy", "tenants"), ("extras", "tags"),
]

host = urlparse(NETBOX_URL).hostname
title(f"Reset {host}")
if "--yes" not in sys.argv:
    warn("This deletes every site, device, IP, type, tag and branch on the instance.")
    if input(f"  Type {host} to continue: ").strip() != host:
        fail("not confirmed; nothing deleted")
        raise SystemExit(1)

nb = netbox()
s = nb.http_session

step("Change requests, reviews and policies")
for ep, label in () if not has("netbox_changes") else (("comment-replies", "reply"), ("comments", "comment"), ("reviews", "review"),
                  ("change-requests", "change request"), ("policy-rules", "policy rule"), ("policies", "policy")):
    url = f"{NETBOX_URL}/api/plugins/changes/{ep}/"
    for o in s.get(url, params={"limit": 500}).json().get("results", []):
        s.delete(f"{url}{o['id']}/").raise_for_status()
        ok(f"deleted {label}: {o.get('display', o['id'])}")

step("Branches")
for b in (nb.plugins.branching.branches.all() if has("netbox_branching") else []):
    s.delete(f"{NETBOX_URL}/api/plugins/branching/branches/{b.id}/").raise_for_status()
    ok(f"deleted branch {b.name}")

step("Objects")
for app, ep in ORDER:
    url = f"{NETBOX_URL}/api/{app}/{ep}/"
    total = 0
    while True:
        page = s.get(url, params={"limit": 500, "brief": 1}).json().get("results", [])
        if not page:
            break
        r = s.delete(url, json=[{"id": o["id"]} for o in page])
        if r.status_code not in (200, 204):
            fail(f"{ep}: HTTP {r.status_code} {r.text[:160]}")
            break
        total += len(page)
    if total:
        ok(f"{total:4} {ep}")

left = {ep: s.get(f"{NETBOX_URL}/api/{app}/{ep}/", params={"limit": 1}).json().get("count", 0) for app, ep in ORDER}
left = {k: v for k, v in left.items() if v}
print()
if left:
    fail(f"still there: {left}")
    raise SystemExit(1)
ok("instance is empty")
note(f"Dismiss any leftover deviations at {ui('/plugins/assurance/deviations/')}")
