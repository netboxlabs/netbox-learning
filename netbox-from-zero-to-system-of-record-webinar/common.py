"""Shared helpers for the webinar demo scripts: settings from .env, API clients, console output."""
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
TAG = "webinar-demo"


def load_env():
    """Read demo/.env into os.environ without overriding variables already set in the shell."""
    env = HERE / ".env"
    if not env.exists():
        sys.exit(f"Missing {env}. Copy .env.example to .env and fill it in.")
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


load_env()
NETBOX_URL = os.environ["NETBOX_URL"].rstrip("/")
NETBOX_TOKEN = os.environ["NETBOX_TOKEN"]
DIODE_TARGET = os.environ.get("DIODE_TARGET", "")
# NetBox 4.5+ tokens (nbt_...) go in a Bearer header; older 40-character tokens use "Token"
AUTH = f"Bearer {NETBOX_TOKEN}" if NETBOX_TOKEN.startswith("nbt_") else f"Token {NETBOX_TOKEN}"
_PLUGINS = None


def plugins():
    """Installed NetBox plugins, from /api/status/, so each script adapts to Community NetBox, Cloud or Enterprise."""
    global _PLUGINS
    if _PLUGINS is None:
        import requests

        r = requests.get(f"{NETBOX_URL}/api/status/", headers={"Authorization": AUTH, "Accept": "application/json"}, timeout=15)
        r.raise_for_status()
        _PLUGINS = r.json().get("plugins", {})
    return _PLUGINS


def has(plugin):
    return plugin in plugins()


def netbox(branch_schema_id=None):
    """A pynetbox client. With a branch schema ID, every call is made inside that branch."""
    import pynetbox

    nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)
    nb.http_session.headers["Authorization"] = AUTH
    if branch_schema_id:
        nb.http_session.headers["X-NetBox-Branch"] = branch_schema_id
    return nb


def diode(app_name, app_version="1.0"):
    """A Diode client. Credentials come from DIODE_CLIENT_ID and DIODE_CLIENT_SECRET in .env."""
    from netboxlabs.diode.sdk import DiodeClient

    return DiodeClient(target=DIODE_TARGET, app_name=app_name, app_version=app_version)


# ---------- console output: readable on a shared screen ----------
TEAL, AMBER, RED, DIM, BOLD, OFF = "\033[96m", "\033[93m", "\033[91m", "\033[2m", "\033[1m", "\033[0m"


def title(text):
    print(f"\n{BOLD}{TEAL}== {text} =={OFF}\n")


def step(text):
    print(f"{TEAL}>{OFF} {text}")


def ok(text):
    print(f"  {TEAL}ok{OFF}  {text}")


def warn(text):
    print(f"  {AMBER}!!{OFF}  {text}")


def fail(text):
    print(f"  {RED}xx{OFF}  {text}")


def note(text):
    print(f"  {DIM}{text}{OFF}")


def pause(text="Press Enter to continue"):
    """Wait for the presenter, unless the script runs with --no-pause."""
    if "--no-pause" in sys.argv:
        return
    input(f"\n{DIM}{text}...{OFF}")


def ui(path):
    """A NetBox UI link for the presenter to open."""
    return f"{NETBOX_URL}/{path.lstrip('/')}"


def wait_for(check, what, timeout=120, every=3):
    """Poll check() until it returns something truthy."""
    end = time.time() + timeout
    while time.time() < end:
        result = check()
        if result:
            return result
        time.sleep(every)
    raise TimeoutError(f"Timed out waiting for {what}")
