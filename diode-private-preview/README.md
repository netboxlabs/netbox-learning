# Diode Private Preview

## Diode SDK Python

### Set Up and Installation

Pre-requisites:

* Python >= 3.7

1. Create a virtual environment and activate it:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Upgrade pip:

```
python3 -m pip install --upgrade pip
```

3. Install the Diode SDK:

```bash
pip install netboxlabs-diode-sdk
```

4. Set the following environment variables:

```bash
export DIODE_API_KEY=<provided during Diode private preview program onboarding>
```

### Example scripts

All scripts have an optional flags:

```
--target TARGET  the target address of the Diode server (without http:// or https://)
--tls_verify     enable TLS verification (default: True)
--apply          apply the changes (default: False)
```

#### CSV data ingestion

Parses a CSV file and extracts information about the device and ingests it into NetBox using the Diode SDK.

```bash
python3 examples/csv/main.py [--target TARGET] [--apply]
```

#### Containerlab

Parses a Containerlab configuration file and extracts information about the device and its interfaces, including IP
addresses and ingests it into NetBox using the Diode SDK.

```bash
python3 examples/containerlab/main.py [--target TARGET] [--apply]
```

#### Cisco IOS

Parses Cisco IOS configuration file and extracts information about the device and its interfaces, including IP addresses
and ingests it into NetBox using the Diode SDK.

Requires additional dependencies:

```bash
pip install ciscoconfparse2
```

```bash
python3 examples/cisco_ios/main.py [--target TARGET] [--apply]
```
