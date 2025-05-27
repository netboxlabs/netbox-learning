# Introduction to NetBox Labs & NetBox

This section provides an introduction to NetBox Labs and the NetBox platform. It covers the basics of NetBox and its capabilities, serving as a foundation for the workshop despite its automation focus.

## Instructions

Sit back and relax. We will introduce NetBox Labs and NetBox, and give you a guided tour of a NetBox Cloud instance with example data.

### Log in to the User Interface of your NetBox Instance

Now is a good time to check that you can access your NetBox instance, by logging into the Web UI. The details are:

- **URL:** http://$INFRA_IP:8000/netbox
- **Credentials:** admin / admin

> [!TIP]
>
> You can find your the value of your `INFRA_IP` environment variable by entering the command `env | grep INFRA_IP` in your terminal.

**Note** your NetBox instance is empty as you will be populating the database with discovered data for devices, interfaces, IP addresses etc during the rest of the workshop.