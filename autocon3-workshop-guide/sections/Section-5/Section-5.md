# Introducing Git-Driven Configuration Management for NetBox Discovery

This section explores how Git configuration management works with NetBox Discovery. Participants will learn about Git-based configuration management concepts and how to move agent configurations into Git repositories.

## Instructions 

We'll be building off some of the earlier work but will explore how you can manage a fleet of agents without having to configure them individually. To get started, you'll need:
* A working environment to run an Orb agent (as per sections 3 and 4)
* A reachable Diode ingestion point and valid client credentials (as per sections 3 and 4)
* A publicly accessible GitHub repository (we'll be using [`netboxlabs/autocon3_workshop_config`](https://github.com/netboxlabs/autocon3_workshop_config) but you can use your own)

### Discovery Policy Files in GitHub

Discovery policy files are similar to agent configuration files we've seen earlier but they contain the `policies` section. We've created a GitHub repository with examples at [`netboxlabs/autocon3_workshop_config`](https://github.com/netboxlabs/autocon3_workshop_config) but feel free to build your own repository with policy files.

There are 3 **Network Discovery** policy files in the repository:

[`ping_scan.yaml`](https://github.com/netboxlabs/autocon3_workshop_config/blob/develop/ping_scan.yaml) to do an ICMP (ping) scan with the following content:
```yaml
network_discovery:
  ping_scan:
    config:
    scope:
      targets:
        - 10.114.0.1-100
      ping_scan: true
      timing: 5
```

[`port_scan.yaml`](https://github.com/netboxlabs/autocon3_workshop_config/blob/develop/port_scan.yaml) to do a full port scan with the following content:
```yaml
network_discovery:
  port_scan:
    config:
    scope:
      targets:
        - 10.114.0.1-100
```

[`port_scan_fast.yaml`](https://github.com/netboxlabs/autocon3_workshop_config/blob/develop/port_scan_fast.yaml) to do a faster port scan with the following content:
```yaml
network_discovery:
  fast_port_scan:
    config:
    scope:
      targets:
        - 10.114.0.1-100
      fast_mode: true
      timing: 5
```

There is also a selector file in the repository. This file is needed by the agents to determine what policies they should run. This file **MUST** be at the root of the repository and **MUST** be named [`selector.yaml`](https://github.com/netboxlabs/autocon3_workshop_config/blob/develop/selector.yaml).
```yaml
ping_scan_selector:
  selector:
    ping_scan: true
  policies:
    default:
      path: ping_scan.yaml

port_scan_selector:
  selector:
    discovery_type: port scan
  policies:
    default:
      path: port_scan.yaml
      
port_scan_fast_selector:
  selector:
    discovery_type: fast port scan
  policies:
    default:
      path: port_scan_fast.yaml

#--- Ignore for now; will be used in section 6
ccc_integration_selector:
  selector:
    ccc_integration: true
  policies:
    default:
      path: ccc_integration.yaml
```

The repository structure should look something like this:
```
autocon3_workshop_config/
├── ccc_integration.yaml (ignore for now; will be used in section 6)
├── ping_scan.yaml
├── port_scan.yaml
├── port_scan_fast.yaml
└── selector.yaml
```

### Agent Configuration to Use GitHub

1. We are now ready to configure the agent to use the policies from the repository. We'll create an agent configuration file named `agent-git.yaml` by running the following:
```bash
cat > agent-git.yaml <<EOF
orb:
  labels:
    ping_scan: true
    discovery_type: port scan
  config_manager: 
    active: git
    sources:
      git:
        url: "https://github.com/netboxlabs/autocon3_workshop_config.git"
        schedule: "* * * * *"
        branch: develop
  backends:
    network_discovery:
    common:
      diode:
        target: grpc://${INFRA_IP}:8080/diode
        client_id: \${DIODE_CLIENT_ID}
        client_secret: \${DIODE_CLIENT_SECRET}
        agent_name: agent-git
EOF
```

This file is very similar to the previous ones with the following differences:
* new `labels` section with key/value pairs to be used to match with selectors in `selector.yaml`
* updated `config_manager` section to use git instead of local file for policies
* removed the `policies` section as it is no longer necessary

2. Now let's run the agent:
```bash
docker run -u root --rm -v ${PWD}:/opt/orb/ \
-e DIODE_CLIENT_ID -e DIODE_CLIENT_SECRET \
mrmrcoleman/orb-agent:with_ccc run -c /opt/orb/agent-git.yaml
```

Look for the following log entry indicating that the agent has successfully pulled policies from GitHub:
* `{"time":"","level":"INFO","msg":"cloning repository","url":"https://github.com/netboxlabs/autocon3_workshop_config.git","branch":"develop"}`

Look for the following types of log entries indicating successful selector matches:
* `{"time":"","level":"INFO","msg":"Selector matched","selector":"ping_scan_selector"}`
* `{"time":"","level":"INFO","msg":"Selector matched","selector":"port_scan_selector"}`
* `{"time":"","level":"INFO","msg":"Selector matched","selector":"port_scan_fast_selector"}`

Look for the following types of log entries indicating what policies were applied by the agent:
* `{"time":"","level":"INFO","msg":"policy applied successfully","policy_id":"","policy_name":"ping_scan"}`
* `{"time":"","level":"INFO","msg":"policy applied successfully","policy_id":"","policy_name":"port_scan"}`
* `{"time":"","level":"INFO","msg":"policy applied successfully","policy_id":"","policy_name":"fast_port_scan"}`

3. Try different combinations of `labels` key/value pairs to see what policies actually get applied to the agent:
* `ping_scan`: `true` versus `false`
* `discovery_type`: `port scan` versus `fast port scan`

>[!TIP]
> The key/value pairs used in the agent `labels` section and the `selector` blocks in `selector.yaml` are entirely customizable. As long as they match, the selector will apply the appropriate policy. You can experiment with label schemas (e.g., by location, agent type, or hostname) to achieve more granular policy targeting.

### View Ingested Data in Assurance

You can look at the data that was ingested in NetBox Assurance:
- Go to your NetBox instance (`http://$INFRA_IP:8000/netbox`, username: `admin`, password: `admin`)
- In the left pane navigate to `Assurance` -> `Active Deviations`
- You should see deviations for the data that was ingested