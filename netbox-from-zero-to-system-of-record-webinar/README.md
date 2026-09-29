# From Zero to System of Record: getting your data into NetBox

The code from the NetBox Labs webinar *From Zero to System of Record* (29 September 2026). Each script is one step of the live demos, so you can run the same steps against your own NetBox.

Don't have a NetBox to try it on? [NetBox Cloud Free](https://netboxlabs.com/products/free-netbox-cloud/) gives you a hosted instance at no cost, and every Community step below fits inside its limits.

## What's in here

| Step | Script | What it shows | Needs |
|---|---|---|---|
| Seed | `1_seed_csv.py` | CSV import of sites and racks in the UI, including one row that fails on purpose. `--api` loads the same files through the REST API. | Any NetBox |
| Script | `2_script_branch.py` | pynetbox loads `data/devices.csv` (types, roles, devices, management IPs) with get-or-create, so a rerun changes nothing. It loads into a branch; `--merge` merges it, and `--main` loads straight into main. | Any NetBox; branching plugin for the branch |
| Script without Python | `2b_ansible.sh` | Ansible loads the data definition file `ansible/data/ams-dc1.yml` with the `netbox.netbox` collection. Run it twice: `changed=0`. | Any NetBox |
| Stream | `3_stream_diode.py` | The same spreadsheet plus two new switches, sent through Diode by name in one call. Diode matches what NetBox already has; run it twice and nothing is duplicated. | Diode |
| Discover | `4_discover_orb.sh` | The Orb agent in Docker, running an SNMP policy (and an optional NMAP sweep) against your lab. | Diode, Docker |
| | `4_discover_simulated.py` | No lab? Sends what an agent would report, through Diode, with deliberate differences from the spreadsheet. | Diode |
| Integrate | `5_integrate_simulated.py` | A controller as a second source for the same data. | Diode |
| Assure | `6_assure.py` | Where to look in Assurance, which turns every difference into a deviation to review. | Assurance |
| Apply | `7_apply_check.py` | The devices after the changes, and the latest change log entries. | Any NetBox |

Also included:
- `0_preflight.py` checks the connection, the token, the installed plugins and the Diode credentials.
- `reset.py` empties the instance: it asks you to type the hostname first.

### Community and NetBox Labs

Most of this is open source:
- NetBox's import tools, the REST API, pynetbox and the Ansible collection
- [netbox-branching](https://github.com/netboxlabs/netbox-branching)
- [Diode](https://github.com/netboxlabs/diode)
- the [Orb agent](https://github.com/netboxlabs/orb-agent)

Assurance, the certified controller integrations and NetBox Changes (the review gate on branch merges) come from NetBox Labs. Each script checks which plugins your NetBox has and adapts: without Assurance, Diode writes straight into NetBox. Without NetBox Changes, a branch merges without a change request.

## Setup

```sh
./setup.sh      # Python 3.12 venv: pynetbox, the Diode SDK, Ansible and the netbox.netbox collection
cp .env.example .env    # setup.sh does this if .env is missing
```

Fill in `.env`:
- **NetBox:** `NETBOX_URL` and `NETBOX_TOKEN`. Tokens starting `nbt_` (NetBox 4.5 and later) and classic 40-character tokens both work.
- **Diode:** `DIODE_TARGET`, `DIODE_CLIENT_ID` and `DIODE_CLIENT_SECRET`. Create the client credentials in NetBox under Diode > Client credentials. On NetBox Cloud, the target is `grpcs://<instance>.cloud.netboxapp.com/diode`.
- **Real Orb agent (optional):** `LAB_SNMP_TARGETS`, `LAB_SNMP_COMMUNITY`, `LAB_NETWORK_TARGETS` and `LAB_SITE`.

`.env` is in `.gitignore`: keep it out of version control.

Then:

```sh
./0_preflight.py
```

The Python scripts run with the venv automatically; `./script.py` is enough.

## Run the demos

On an empty NetBox, in this order:

```sh
./1_seed_csv.py            # or: ./1_seed_csv.py --api
./2_script_branch.py       # then ./2_script_branch.py --merge   (or --main without branching)
./2b_ansible.sh            # run it twice
./3_stream_diode.py        # run it twice, then --check
./4_discover_simulated.py  # or ./4_discover_orb.sh against a lab
./5_integrate_simulated.py
./6_assure.py              # with Assurance: review and apply in the UI
./7_apply_check.py
./reset.py                 # back to empty
```

`sources.py` lists exactly what the simulated discovery and controller report, and which differences from `data/devices.csv` are deliberate:
- serial numbers and platforms
- a new SVI with an address
- a management IP that moved
- an access point nobody recorded
- a switch reported offline
- uplink descriptions
- a VLAN

## Notes

- **NetBox versions:** the scripts were tested on NetBox 4.6 with pynetbox 7.8, the Diode SDK 1.14 and `netbox.netbox` 3.23.
- **The Ansible collection** writes to main; it has no branch support.
- **What reset doesn't clear:** the change log, which NetBox keeps by design, and Assurance deviations, which you can dismiss in the UI.
