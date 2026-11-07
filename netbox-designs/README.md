# NetBox Designs

Designs for [NetBox Designs](https://netboxlabs.com/docs/netbox-designs/), kept here so a catalogue can read them straight from Git.

## `tutorial/`

The designs the [NetBox Designs tutorial](https://netboxlabs.com/docs/netbox-designs/tutorial/) pulls in from a repository, in the chapter [The compute rack](https://netboxlabs.com/docs/netbox-designs/tutorial/the-compute-rack/): the compute rack and the two device designs it is built from.

| File | Catalogue name | What it is |
|---|---|---|
| `tutorial/tutorial/compute_rack.yaml` | `tutorial/compute_rack` | A 42U rack: a top-of-rack switch, ten servers, and the cables between them |
| `tutorial/devices/Cisco_3850_w_module.yaml` | `devices/Cisco_3850_w_module` | The switch, with its 4x10G uplink module |
| `tutorial/devices/Dell_R640_w_module.yaml` | `devices/Dell_R640_w_module` | The server, with its 10G network card |

To use them, connect this repository in the Design Catalogue's **Repositories** with the branch `develop` and the directory `netbox-designs/tutorial`, then **Sync now**. A file's path under the directory is its catalogue name, which is the name other designs refer to it by: the rack says `design: nbd:devices/Dell_R640_w_module`.

The two designs the tutorial has you add by hand first, `tutorial/world_regions` and `tutorial/site_foundation`, are deliberately not here: a sync does not take over a design the catalogue already has by hand.

These files are copies of `docs/examples/designs/` in the NetBox Designs repository, which is where they are changed; a check there says when the two drift apart.
