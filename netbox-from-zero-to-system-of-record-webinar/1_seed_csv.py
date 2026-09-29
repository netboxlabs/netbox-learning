#!/bin/sh
''''exec "$(dirname "$0")/.venv/bin/python" "$0" "$@" #'''  # runs this file with the demo venv
"""Demo 1, step 1 (Seed): CSV import in the NetBox UI.

Shows the CSV to paste, the import page to paste it into, and what to expect, including the one
row that fails on purpose. Run with --api to load the same files through the REST API instead
(the fallback if the UI misbehaves), and with --check to confirm what landed.
"""
import csv

from common import *


def show(name):
    text = (DATA / name).read_text()
    print(f"{DIM}--- data/{name} ---{OFF}")
    print(text.rstrip())
    print(f"{DIM}---{OFF}")


def check():
    nb = netbox()
    sites, locs, racks = nb.dcim.sites.count(), nb.dcim.locations.count(), nb.dcim.racks.count()
    (ok if sites == 3 else warn)(f"{sites} sites (expected 3)")
    (ok if locs == 3 else warn)(f"{locs} locations (expected 3)")
    (ok if racks == 4 else warn)(f"{racks} racks (expected 4; more means an import ran twice)")


def load_api():
    """Fallback: the same CSV rows through the REST API, with the failing row reported."""
    nb = netbox()
    for row in csv.DictReader(open(DATA / "sites.csv")):
        if nb.dcim.sites.get(slug=row["slug"]):
            note(f"site {row['name']} already there")
            continue
        nb.dcim.sites.create(**row)
        ok(f"site {row['name']}")
    for row in csv.DictReader(open(DATA / "locations.csv")):
        site = nb.dcim.sites.get(name=row["site"])
        if nb.dcim.locations.get(site_id=site.id, slug=row["slug"]):
            note(f"location {row['site']}/{row['name']} already there")
            continue
        nb.dcim.locations.create(site=site.id, name=row["name"], slug=row["slug"], status=row["status"])
        ok(f"location {row['site']}/{row['name']}")
    for row in csv.DictReader(open(DATA / "racks.csv")):
        site = nb.dcim.sites.get(name=row["site"])
        if site is None:
            fail(f"rack {row['name']} at {row['site']}: site {row['site']!r} does not exist")
            continue
        if nb.dcim.racks.get(site_id=site.id, name=row["name"]):
            note(f"rack {row['site']}/{row['name']} already there")
            continue
        loc = nb.dcim.locations.get(site_id=site.id, name=row["location"])
        nb.dcim.racks.create(site=site.id, location=loc.id, name=row["name"], status=row["status"], u_height=int(row["u_height"]), width=int(row["width"]))
        ok(f"rack {row['site']}/{row['name']}")


if "--check" in sys.argv:
    title("Seed: check")
    check()
    raise SystemExit
if "--api" in sys.argv:
    title("Seed: fallback through the REST API")
    load_api()
    check()
    raise SystemExit

title("Demo 1 · 1 Seed: CSV import in the UI")
step(f"Open {ui('/dcim/sites/import/')}")
step("Paste this, keep the format on CSV, and submit:")
show("sites.csv")
note("Names are how every later step refers to these sites, so they stay exactly like this.")
pause()

step(f"Open {ui('/dcim/locations/import/')}")
step("Paste this and submit. Racks go into a location, so a rerun cannot copy them:")
show("locations.csv")
pause()

step(f"Open {ui('/dcim/racks/import/')}")
step("Paste this and submit:")
show("racks.csv")
warn("The last row points at FRA-DC1, which does not exist. NetBox rejects the whole import and names")
warn("the row and the field. That is the point to show: nothing half-lands.")
pause("Press Enter once you have shown the error")

step("Delete the FRA-DC1 row and submit again. The corrected file is data/racks-fixed.csv:")
show("racks-fixed.csv")
pause("Press Enter once the racks are in")

step("Optional: paste the same racks again. NetBox rejects the whole import, because rack names")
step("are unique within a location. Without a location, the same file would import a second copy.")
pause()

step("Checking what landed")
check()
