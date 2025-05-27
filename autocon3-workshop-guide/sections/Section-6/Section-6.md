# Introducing Secrets Management for NetBox Discovery

This section covers the implementation of secrets management in conjunction with NetBox Discovery. Participants will learn how to use Vault as a secret store for configuration secrets and how to update Device Discovery configurations to use these secrets.

## Instructions 

We'll be building off some of the earlier work and will explore how you can securely access sensitive information you might need in your agent configurations and policies. To get started, you'll need:
* A working environment to run an Orb agent (as per sections 3 and 4)
* A reachable Diode ingestion point and valid client credentials (as per sections 3 and 4)
* A GitHub repo populated with agent policy files (we'll be using [`netboxlabs/autocon3_workshop_config`](https://github.com/netboxlabs/autocon3_workshop_config) but you can use your own)

### Agent Configuration to Use Secrets Manager

1. Let's create an agent configuration file called `agent-vault.yaml` that add's a `secrets_manager` section to enable retrieving secrets from a vault by running the following:
```
cat > agent-vault.yaml <<EOF
orb:
  labels:
    ccc_integration: true
  secrets_manager:
    active: vault
    sources:
      vault:
        address: "https://vault.netboxlabs.tech:8200"
        namespace: "workshop"
        timeout: 60
        auth: "token"
        auth_args:
          token: \${VAULT_TOKEN}
        schedule: "*/5 * * * *"
  config_manager: 
    active: git
    sources:
      git:
        url: "https://github.com/netboxlabs/autocon3_workshop_config.git"
        schedule: "* * * * *"
        branch: develop
  backends:
    worker:
    common:
      diode:
        target: grpc://${INFRA_IP}:8080/diode
        client_id: \${DIODE_CLIENT_ID}
        client_secret: \${DIODE_CLIENT_SECRET}
        agent_name: agent-git
EOF
```

2. Take a look at the [`ccc_integration.yaml`](https://github.com/netboxlabs/autocon3_workshop_config/blob/develop/ccc_integration.yaml) policy file to see the secrets substitution syntax:
```
    worker:
      catalyst_center_worker:
        config:
          package: nbl_cisco_catalyst_center
          CCC_HOST: ${vault://kv/workshop/CCC_HOST}
          CCC_USER: ${vault://kv/workshop/CCC_USER}
          CCC_PWD: ${vault://kv/workshop/CCC_PWD}
        scope:
``` 

3. Now let's run the agent (notice we now need to pass a `VAULT_TOKEN` to be able to access the vault):
```
docker run -u root --rm -v ${PWD}:/opt/orb/ \
-e DIODE_CLIENT_ID -e DIODE_CLIENT_SECRET -e VAULT_TOKEN \
mrmrcoleman/orb-agent:with_ccc run -c /opt/orb/agent-vault.yaml
```

Look for the following log entry indicating that the agent has successfully connected to the vault:
* `{"time":"","level":"INFO","msg":"Starting vault secret polling","cron interval":"*/5 * * * *"}`

>[!TIP]
> Back in your work environment, you could also replace references to `DIODE_CLIENT_ID` and `DIODE_CLIENT_SECRET` in your agent configuation with vault secrets. Configured this way, you would only have to pass `VAULT_TOKEN` to start the agent.

### View Ingested Data in Assurance

You can look at the data that was ingested in NetBox Assurance:
- Go to your NetBox instance (`http://$INFRA_IP:8000/netbox`, username: `admin`, password: `admin`)
- In the left pane navigate to `Assurance` -> `Active Deviations`
- You should see deviations for the data that was ingested