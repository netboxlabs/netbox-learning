# NetBox Discovery Controller Integrations

This section introduces the concept of controller integrations and Orb extensibility. Specifically, it covers the Cisco Catalyst Center integration for NetBox, and shows how to use a local configuration to run Cisco Catalyst Center discovery.

We will use the integration to interact with a Cisco Catalyst Center controller running in an always-on sandbox environment hosted by Cisco DevNet. The controller is managing four devices (sw1, sw2, sw3 and sw4), which are of model type `C9KV-UADP-8P` and running `IOS-XE`

The integration will connect to the Catalyst Center controller and discover the four switches, along with all their associated data such as the model, device_type, platform, interfaces and MAC addresses.

## Instructions

### Getting set up

First, make sure you're in the Section 4 directory. If you currently in `Section-3` then enter:

```bash
cd ../Section-4
```

#### Pull the Docker image for the Orb Agent (optional)

Next, to pull the docker image for the Orb Agent that has the Cisco Catalyst Center integration built into it, run this command:

```
docker pull mrmrcoleman/orb-agent:with_ccc
```

#### Exporting the correct environment variables

Now we need to set up the environment so that the Catalyst Center integration can access the variables it needs to connect and retrieve data. To export the Cisco Catalyst Center URL and credentials (we using a Cisco Always-On Sandbox environment), copy and paste these commands into your terminal:
```
export CCC_HOST=https://sandboxdnac.cisco.com
export CCC_USER=devnetuser
export CCC_PWD=Cisco123!
```

> [!TIP]
>
> If you are interested you can log into the Catalyst Center Controller at the above URL using the credentials to view the device data that we are going to ingest into NetBox.
> You might need to use Safari on MacOS or another browser as sometimes there are issues accessing the URL using Google Chrome

### Controller Discovery Integration

Now we are ready to try out Controller Discovery Integration. We point our controller discovery at the Catalyst Center controller, and then interact with the results in NetBox Assurance.

We'll create a configuration file called `catalyst_center_worker.yaml` in the current directory. You will see this looks very similar to the network discovery and device discovery config files you used in the previous section. Copy and paste the following into your terminal:

```
cat > catalyst_center_worker.yaml <<EOF
orb:
  config_manager:
    active: local
  backends:
    worker:
    common:
      diode:
        target: grpc://${INFRA_IP}:8080/diode
        client_id: \${DIODE_CLIENT_ID}
        client_secret: \${DIODE_CLIENT_SECRET}
        agent_name: cc-worker
  policies:
    worker:
      catalyst_center_worker:
        config:
          package: nbl_cisco_catalyst_center
          CCC_HOST: \${CCC_HOST}
          CCC_USER: \${CCC_USER}
          CCC_PWD: \${CCC_PWD}
        scope:
EOF
```

Let's highlight some key sections in the discovery configuration:

- `backends` can be thought of as different types of discovery that the agent can run. In this case we that we are including `worker` which is specific to this section and also `common` which is used in all configurations
- `policies` are used to configure the `backends` so in this case we are telling our `worker` backend to use the package called `nbl_cisco_catalyst_center` and to target the Cisco Catalyst Center controller using the values we set for `CCC_HOST`, `CCC_USER` and `CCC_PWD`.
- Note that the Diode `Target` will have the value for `INFRA_IP` pulled in from your environment variables

> [!TIP]
>
> If you need to check the value of your `INFRA_IP` enter this command in your terminal `env | grep INFRA_IP`


#### Start the Orb Agent
To start the Orb agent, copy and paste the following command into your terminal, and hit enter:

```bash
docker run -u root --rm \
  -v ${PWD}:/opt/orb/ \
  -e DIODE_CLIENT_ID \
  -e DIODE_CLIENT_SECRET \
  -e CCC_HOST \
  -e CCC_USER \
  -e CCC_PWD \
  mrmrcoleman/orb-agent:with_ccc run \
  -c /opt/orb/catalyst_center_worker.yaml
```

When we run the command, the agent will:
   - Connect to the Cisco Catalyst Center sandbox environment
   - Discover device information for the 4 devices (sw1, sw2, sw3, sw4)
   - Send the data to NetBox through the Diode ingestion service

After a minute or so you should see something like this in the logs:
```bash
{"time":"2025-05-24T07:22:01.493179688Z","level":"INFO","msg":"worker stdout","log":"INFO:worker.policy.runner:Policy catalyst_center_worker: Successful ingestion"}
{"time":"2025-05-24T07:22:01.493897606Z","level":"INFO","msg":"worker stdout","log":"INFO:apscheduler.executors.default:Job \"PolicyRunner.run (trigger: date[2025-05-24 07:21:57 UTC], next run at: 2025-05-24 07:21:57 UTC)\" executed successfully"}
```

As we are only running the agent once (as opposed to scheduling it), you should stop the agent with `Ctrl+C`.

#### Working with the discovered data

Great! Our discovery controller integration has run. Now let's go and look at what it found in NetBox Assurance.

- Go back to your NetBox instance (`http://$INFRA_IP:8000/netbox`, username: `admin`, password: `admin`)
- In the left pane navigate to `Assurance` -> `Active Deviations`
- You should see a whole bunch of deviations that were discovered
- Click on one of the deviations and explore the **Ingested Data**
- We will apply all the deviations, so navigate back to `Assurance` -> `Active Deviations`, select the first deviation, hold down shift and select the last deviation, then click `Apply Selected`, and then click `Apply 13 deviations`

Now we have successfully, discovered, inspected and applied our controller discovery results. Let's have a look at them in NetBox:

- In the left pane of your NetBox instance, navigate to `DEVICES` -> `Devices`
- You'll now see the four devices we discovered from the catalyst center controller are present in NetBox.
- Click on `sw1` and then explore the object attributes including the interfaces and MAC addresses
- Also under the `Devices` menu, explore the `Manufacturers`, `Device Types` and `Platforms` that were automatically created as part of the discovery process.

The Catalyst Center Controller managed devices have now been discovered!

**Troubleshooting Tips:**
- If you see connection errors, verify that your `INFRA_IP` is correct
- Ensure all environment variables are properly set using `env | grep -E "INFRA_IP|DIODE|CCC"`
- Check that your yaml file is properly formatted with no tab characters
