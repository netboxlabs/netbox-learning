#!/bin/sh
''''exec "$(dirname "$0")/.venv/bin/python" "$0" "$@" #'''  # runs this file with the demo venv
"""Check everything the demos need, before going live: NetBox, the token, plugins, Diode, Docker."""
import shutil
import subprocess

import requests

from common import *

title("Preflight")
problems = 0
H = {"Authorization": AUTH, "Accept": "application/json"}

step(f"NetBox at {NETBOX_URL}")
try:
    st = requests.get(f"{NETBOX_URL}/api/status/", headers=H, timeout=15)
    st.raise_for_status()
    st = st.json()
    ok(f"NetBox {st['netbox-version']}, {st['rq-workers-running']} background worker(s)")
except Exception as e:
    fail(f"cannot reach the API: {e}")
    raise SystemExit(1)

step("Plugins (each one only matters for some steps)")
optional = {
    "netbox_branching": "2_script_branch.py loads into a branch (open source; without it, use --main)",
    "netbox_diode_plugin": "3_stream_diode.py and demo 2 send through Diode (open source)",
    "netbox_changes": "merges wait for an approved change request (NetBox Labs)",
    "netbox_assurance_plugin": "Diode data arrives as deviations to review (NetBox Labs)",
}
for p, what in optional.items():
    if p in st["plugins"]:
        ok(f"{p} {st['plugins'][p]}: {what}")
    else:
        note(f"-- {p} not installed: {what.split(' (')[0]} is skipped or runs without it")

step("Token can write")
r = requests.post(f"{NETBOX_URL}/api/extras/tags/", headers=H, json={"name": "preflight-probe", "slug": "preflight-probe"}, timeout=15)
if r.status_code == 201:
    requests.delete(f"{NETBOX_URL}/api/extras/tags/{r.json()['id']}/", headers=H, timeout=15)
    ok("created and deleted a test tag")
else:
    fail(f"write failed: HTTP {r.status_code} {r.text[:120]}")
    problems += 1

step("Diode credentials")
if not all(os.environ.get(k) for k in ("DIODE_TARGET", "DIODE_CLIENT_ID", "DIODE_CLIENT_SECRET")):
    warn("DIODE_TARGET, DIODE_CLIENT_ID or DIODE_CLIENT_SECRET not set in .env: the Diode steps will not run")
else:
    base = DIODE_TARGET.replace("grpcs://", "https://").replace("grpc://", "http://")
    r = requests.post(f"{base}/auth/token", timeout=15, data={
        "grant_type": "client_credentials", "client_id": os.environ["DIODE_CLIENT_ID"],
        "client_secret": os.environ["DIODE_CLIENT_SECRET"], "scope": "diode:ingest"})
    if r.ok:
        ok("Diode issued an ingest token")
    else:
        fail(f"Diode auth failed: HTTP {r.status_code}")
        problems += 1

step("What is in NetBox now")
nb = netbox()
counts = {n: e.count() for n, e in [("sites", nb.dcim.sites), ("racks", nb.dcim.racks), ("devices", nb.dcim.devices),
                                     ("IP addresses", nb.ipam.ip_addresses), ("branches", nb.plugins.branching.branches)]}
print("  " + ", ".join(f"{v} {k}" for k, v in counts.items()))
if any(counts.values()):
    warn("not empty: run ./reset.py before the webinar for a clean start")

step("Docker, for the real Orb agent (demo 2 step 1)")
if shutil.which("docker") and subprocess.run(["docker", "info"], capture_output=True).returncode == 0:
    ok("Docker is running")
else:
    warn("Docker is not running: use the simulated discovery (4_discover_simulated.py)")
import socket
from urllib.parse import urlparse


def reachable(host, port):
    try:
        socket.create_connection((host, port), timeout=5).close()
        return True
    except OSError:
        return False


step("Demo 2 sources")
if os.environ.get("LAB_DEVICE_HOST"):
    h = os.environ["LAB_DEVICE_HOST"]
    (ok if reachable(h, 22) else warn)(f"lab switch {h}: SSH {'answers' if reachable(h, 22) else 'does not answer (Tailscale connected?)'}")
elif os.environ.get("LAB_SNMP_TARGETS"):
    note("SNMP targets set; not probed (UDP)")
else:
    warn("no LAB_DEVICE_HOST or LAB_SNMP_TARGETS in .env: use ./4_discover_simulated.py")


print()
if problems:
    fail(f"{problems} problem(s) to fix before going live")
    raise SystemExit(1)
ok("ready")
