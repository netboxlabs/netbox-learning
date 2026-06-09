import os
import time
import uuid
from urllib.parse import urlparse

import requests
from extras.scripts import Script, StringVar, ObjectVar, ChoiceVar
from dcim.models import Device
from netbox_branching.models import Branch


def _eda_default_url():
    """Derive EDA URL from the workshop-resources Data Source host."""
    import re
    try:
        from core.models import DataSource
        ds = (
            DataSource.objects.filter(name='workshop-resources').first()
            or DataSource.objects.filter(source_url__icontains='gitea').first()
        )
        if ds:
            m = re.match(r'https?://([^/:]+)', ds.source_url)
            if m:
                return f'http://{m.group(1)}:5000/endpoint'
    except Exception:
        pass
    # EDA_HOST is always injected into the NetBox container
    eda_host = os.environ.get('EDA_HOST', '')
    if eda_host:
        return f'http://{eda_host}:5000/endpoint'
    return 'http://localhost:5000/endpoint'

EDA_URL_DEFAULT = _eda_default_url()
RESULT_POLL_TIMEOUT = 60  # seconds
RESULT_POLL_INITIAL_WAIT = 2  # seconds before first poll — no playbook finishes instantly

CONFIG_PUSH_EVENT = "device.config_push"
BRANCH_SUPPORTED_EVENTS = {"device.config_push", "device.validate"}


class TriggerEDA(Script):
    class Meta:
        name = "Trigger EDA Event"
        description = (
            "Send a webhook event to Event Driven Ansible (EDA). "
            "EDA evaluates its rulebook and runs the matching Ansible playbook automatically. "
            "Results are streamed back here once the playbook completes."
        )
        commit_default = False
        field_order = ["event_type", "device", "branch", "message", "eda_url"]

    event_type = ChoiceVar(
        choices=[
            ("device.validate", "Network Validation Report"),
            ("inventory.show", "Show Inventory"),
            (CONFIG_PUSH_EVENT, "Push Device Config"),
            ("device.verify_ospf", "Verify OSPF"),
            ("device.verify_reachability", "Verify Reachability"),
            ("device.health_check", "Health Check"),
            ("device.connectivity_test", "Connectivity Test"),
            ("device.compliance_check", "Compliance Check"),
            ("device.audit", "Network Audit"),
            ("network.alert", "Network Alert → Connectivity Test"),
            ("git.sync", "Sync Playbooks from Gitea"),
            ("custom", "Custom Event (Hello World)"),
        ],
        label="Event Type",
        description="The type of event to send to EDA. Each event type maps to a specific Ansible playbook.",
    )

    device = ObjectVar(
        model=Device,
        required=False,
        label="Target Device",
        description="Scope this event to a single device. Leave blank to run across all workshop devices.",
    )

    branch = ObjectVar(
        model=Branch,
        required=False,
        label="Branch",
        description=(
            "Select a NetBox branch to read data from. "
            "Used for 'Push Device Config' and 'Network Validation Report' — ignored for all other event types."
        ),
    )

    message = StringVar(
        label="Message",
        required=False,
        default="",
        description="Optional note included in the event payload.",
    )

    eda_url = StringVar(
        label="EDA Webhook URL",
        default=EDA_URL_DEFAULT,
        description="URL of the ansible-rulebook webhook endpoint. Auto-populated from EDA_HOST if set.",
    )

    def run(self, data, commit):
        event_type = data["event_type"]
        device = data.get("device")
        message = data.get("message", "")
        eda_url = data.get("eda_url") or EDA_URL_DEFAULT
        branch = data.get("branch")

        # Warn if a branch is selected for an event type that doesn't use it
        if branch and event_type not in BRANCH_SUPPORTED_EVENTS:
            self.log_warning(
                f"A branch was selected but event type '{event_type}' does not use branch context. "
                "The branch will be ignored. Branch selection applies to 'Push Device Config' and 'Network Validation Report'."
            )

        if isinstance(branch, int):
            branch = Branch.objects.get(pk=branch)
        branch_schema_id = branch.schema_id if branch else ""

        # Build callback URL: same host as EDA, port 5001
        parsed = urlparse(eda_url)
        job_id = uuid.uuid4().hex[:12]
        callback_url = f"{parsed.scheme}://{parsed.hostname}:5001/{job_id}"

        payload = {
            "event_type": event_type,
            "source": "netbox",
            "message": message,
            "job_id": job_id,
            "callback_url": callback_url,
        }

        if branch_schema_id:
            payload["branch_schema_id"] = branch_schema_id
            self.log_info(f"Using branch: {branch.name} ({branch_schema_id})")

        if device:
            payload["device"] = {
                "id": device.pk,
                "name": device.name,
                "status": device.status,
                "site": device.site.name if device.site else None,
                "rack": device.rack.name if device.rack else None,
                "role": device.role.name if device.role else None,
                "device_type": str(device.device_type) if device.device_type else None,
                "primary_ip": str(device.primary_ip.address) if device.primary_ip else None,
                "platform": device.platform.name if device.platform else None,
                "tags": [t.name for t in device.tags.all()],
            }
            self.log_info(f"Device: {device.name} ({device.primary_ip or 'no IP'})")

        self.log_info(f"Sending event '{event_type}' to {eda_url} (job {job_id})")

        try:
            resp = requests.post(
                eda_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
        except requests.exceptions.ConnectionError:
            self.log_failure(
                f"Could not connect to EDA at {eda_url}. "
                "Make sure ansible-rulebook is running (./7_start_eda.sh) "
                "and the URL uses the host's external IP, not localhost."
            )
            return
        except requests.exceptions.Timeout:
            self.log_failure(f"Request to {eda_url} timed out after 10 seconds.")
            return
        except requests.exceptions.HTTPError as e:
            self.log_failure(f"EDA returned an error: {e}")
            return

        self.log_info(f"EDA accepted the event (HTTP {resp.status_code}). Waiting for playbook result...")

        # Brief initial wait — playbooks take at least a few seconds to start
        time.sleep(RESULT_POLL_INITIAL_WAIT)

        # Poll the result relay server for the playbook output
        deadline = time.time() + RESULT_POLL_TIMEOUT
        while time.time() < deadline:
            try:
                result_resp = requests.get(callback_url, timeout=3)
                if result_resp.status_code == 200:
                    result = result_resp.json()
                    status = result.get("status", "unknown")
                    msg = result.get("message", str(result))
                    for line in msg.splitlines():
                        if not line.strip():
                            continue
                        if "FAIL" in line:
                            self.log_warning(line)
                        else:
                            self.log_info(line)
                    if status == "success":
                        self.log_success(f"Playbook completed successfully ({event_type})")
                    else:
                        self.log_failure(f"Playbook reported failure ({event_type})")
                    return msg
            except requests.exceptions.RequestException:
                pass  # result server not ready yet; keep polling
            time.sleep(1)

        self.log_warning(
            f"Timed out after {RESULT_POLL_TIMEOUT}s waiting for playbook result. "
            "The playbook may still be running — check: tail -f eda.log"
        )
        return None
