#!/bin/sh
''''exec "$(dirname "$0")/.venv/bin/python" "$0" "$@" #'''  # runs this file with the demo venv
"""Demo 1, step 2 (Script): load data/devices.csv with pynetbox, inside a NetBox branch.

Creates a branch, waits until it is ready, then in that branch gets or creates the manufacturers,
device types (with interface templates), roles, devices and management IPs. Main is untouched
until you merge. Run it twice to show that a rerun changes nothing.

  ./2_script_branch.py            load into the branch, then show the branch link
  ./2_script_branch.py --merge    merge the branch (with a change request first, if needed)
  ./2_script_branch.py --main     no branching plugin? load straight into main

Branching comes from the open-source netbox-branching plugin. If NetBox Changes (NetBox Labs) is
installed too, a branch only merges once its change request is approved: --merge opens one,
approves it and merges. In the UI that is Changes > Change requests.
"""
import csv
import time

from common import *

BRANCH = "webinar-device-load"

# The two models in the spreadsheet, with the interfaces each one ships with
TYPES = {
    ("Cisco", "C9300-48P"): {"slug": "c9300-48p", "u": 1, "mgmt": "GigabitEthernet0/0",
                             "ports": [(f"GigabitEthernet1/0/{i}", "1000base-t") for i in range(1, 49)]
                                      + [(f"TenGigabitEthernet1/1/{i}", "10gbase-x-sfpp") for i in range(1, 5)]},
    ("Arista", "DCS-7280SR-48C6"): {"slug": "dcs-7280sr-48c6", "u": 1, "mgmt": "Management1",
                                    "ports": [(f"Ethernet{i}", "10gbase-x-sfpp") for i in range(1, 49)]},
}
ROLES = {"Core Switch": ("core-switch", "00a9e0"), "Access Switch": ("access-switch", "00f2d4")}


def slug(s):
    return s.lower().replace(" ", "-")


def get_branch(nb):
    return nb.plugins.branching.branches.get(name=BRANCH)


def me(nb):
    """The user this token belongs to: the reviewer on a one-person webinar."""
    return nb.http_session.get(f"{NETBOX_URL}/api/users/tokens/", params={"limit": 1}).json()["results"][0]["user"]["id"]


def approve(nb, b):
    """Change request for the branch, approved under a one-reviewer policy. Returns the request."""
    s, A, uid = nb.http_session, f"{NETBOX_URL}/api/plugins/changes", me(nb)
    pols = s.get(f"{A}/policies/", params={"name": "Webinar review"}).json()["results"]
    if pols:
        pol = pols[0]
    else:
        pol = s.post(f"{A}/policies/", json={"name": "Webinar review", "is_default": True, "require_independent_review": False,
                                             "description": "One approval; the presenter may review their own change"}).json()
        s.post(f"{A}/policy-rules/", json={"policy": pol["id"], "name": "One approval", "enabled": True,
                                           "min_reviews": 1, "reviewers": [uid]}).raise_for_status()
        ok("policy 'Webinar review': one approval")
    crs = s.get(f"{A}/change-requests/", params={"branch_id": b.id}).json()["results"]
    if crs:
        cr = crs[0]
    else:
        r = s.post(f"{A}/change-requests/", json={"name": "Device load from the spreadsheet", "branch": b.id, "policy": pol["id"],
                                                  "priority": 3, "status": "needs-review",
                                                  "summary": "Six devices from data/devices.csv, with types, roles and management IPs"})
        r.raise_for_status()
        cr = r.json()
        ok(f"change request #{cr['id']} opened: {ui('/plugins/changes/change-requests/' + str(cr['id']) + '/')}")
    if cr["status"]["value"] != "approved":
        s.post(f"{A}/reviews/", json={"change_request": cr["id"], "user": uid, "status": "approved",
                                      "comments": "Checked against the spreadsheet."}).raise_for_status()
        s.post(f"{A}/change-requests/{cr['id']}/retrigger/")
        cr = wait_for(lambda: (x := s.get(f"{A}/change-requests/{cr['id']}/").json())["status"]["value"] == "approved" and x,
                      "the change request to be approved", timeout=60)
        ok("reviewed and approved")
    return cr


def merge():
    nb = netbox()
    title("Demo 1 · 2 Script: review and merge")
    b = get_branch(nb)
    if b is None:
        fail(f"no branch called {BRANCH}; run this script without --merge first")
        return
    if b.status.value == "merged":
        ok("already merged")
        return
    if has("netbox_changes"):
        step("Change request (NetBox Changes is installed, so the merge needs an approval)")
        approve(nb, b)
    step(f"Merging branch {BRANCH} into main")
    job = nb.http_session.post(f"{NETBOX_URL}/api/plugins/branching/branches/{b.id}/merge/", json={"commit": True})
    job.raise_for_status()
    j = wait_for(lambda: (x := nb.http_session.get(f"{NETBOX_URL}/api/core/jobs/{job.json()['id']}/").json())["status"]["value"]
                 in ("completed", "errored", "failed") and x, "the merge", timeout=300)
    if j["status"]["value"] != "completed":
        fail(f"merge {j['status']['value']}: {j.get('error')}")
        raise SystemExit(1)
    ok(f"merged. Main now has {nb.dcim.devices.count()} devices and {nb.ipam.ip_addresses.count()} IP addresses")


def load():
    nb = netbox()
    if "--main" in sys.argv:
        title("Demo 1 · 2 Script: pynetbox, straight into main")
        return load_into(netbox(), None)
    title("Demo 1 · 2 Script: pynetbox into a branch")
    if not has("netbox_branching"):
        fail("the netbox-branching plugin is not installed: install it, or run ./2_script_branch.py --main")
        raise SystemExit(1)

    step(f"Branch {BRANCH}")
    b = get_branch(nb)
    if b is None:
        b = nb.plugins.branching.branches.create(name=BRANCH, description="Device load from the spreadsheet")
        ok("created, provisioning")
    if b.status.value == "merged":
        warn("this branch is already merged: run ./reset.py for a fresh start")
        return
    b = wait_for(lambda: (x := get_branch(nb)) and x.status.value == "ready" and x, "the branch to be ready")
    ok(f"ready (schema {b.schema_id})")

    load_into(netbox(branch_schema_id=b.schema_id), b)  # every call lands in the branch, not in main


def load_into(br, b):
    created = 0

    step("Reference data: manufacturers, device types, roles")
    for (mfr, model), t in TYPES.items():
        m = br.dcim.manufacturers.get(slug=slug(mfr)) or br.dcim.manufacturers.create(name=mfr, slug=slug(mfr))
        dt = br.dcim.device_types.get(slug=t["slug"])
        if dt is None:
            dt = br.dcim.device_types.create(manufacturer=m.id, model=model, slug=t["slug"], u_height=t["u"])
            br.dcim.interface_templates.create([{"device_type": dt.id, "name": t["mgmt"], "type": "1000base-t", "mgmt_only": True}]
                                               + [{"device_type": dt.id, "name": p, "type": pt} for p, pt in t["ports"]])
            created += 1
            ok(f"{mfr} {model}, {len(t['ports']) + 1} interface templates")
        else:
            note(f"{mfr} {model} already there")
    for name, (s, colour) in ROLES.items():
        if br.dcim.device_roles.get(slug=s) is None:
            br.dcim.device_roles.create(name=name, slug=s, color=colour)
            created += 1
            ok(f"role {name}")

    step("Devices from data/devices.csv (get-or-create, the pattern on the slide)")
    for row in csv.DictReader(open(DATA / "devices.csv")):
        site = br.dcim.sites.get(name=row["site"])
        if site is None:
            fail(f"{row['name']}: site {row['site']} is missing; run step 1 first")
            continue
        dev = br.dcim.devices.get(name=row["name"], site_id=site.id)
        if dev is None:
            rack = br.dcim.racks.get(site_id=site.id, name=row["rack"])
            dev = br.dcim.devices.create(
                name=row["name"], site=site.id, rack=rack.id if rack else None,
                position=int(row["position"]) if rack else None, face="front" if rack else None,
                device_type={"slug": TYPES[(row["manufacturer"], row["model"])]["slug"]},
                role={"slug": ROLES[row["role"]][0]}, status=row["status"])
            created += 1
            ok(f"{row['name']} in {row['site']}/{row['rack']}")
        else:
            note(f"{row['name']} already there")

        # The interface comes from the device type's template; the IP is assigned to it, then made primary
        iface = br.dcim.interfaces.get(device_id=dev.id, name=row["mgmt_interface"])
        ip = br.ipam.ip_addresses.get(address=row["mgmt_ip"])
        if ip is None:
            ip = br.ipam.ip_addresses.create(address=row["mgmt_ip"], status="active",
                                             assigned_object_type="dcim.interface", assigned_object_id=iface.id)
            created += 1
        if not dev.primary_ip4 or dev.primary_ip4.id != ip.id:
            dev.primary_ip4 = ip.id
            dev.save()

    print()
    if not created:
        ok("nothing to create: a rerun changes nothing")
    elif b is None:
        ok(f"{created} objects created in main")
    else:
        ok(f"{created} objects created in the branch. Main still has {netbox().dcim.devices.count()} devices.")
    if b is not None:
        step(f"Show the branch and its Diff tab: {ui(f'/plugins/branching/branches/{b.id}/')}")
        step("Then: ./2_script_branch.py --merge")


if "--merge" in sys.argv:
    merge()
else:
    load()
