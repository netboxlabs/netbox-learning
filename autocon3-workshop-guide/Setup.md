# Workshop Setup Guide

This guide will help you set up your environment for the AutoCon3 Workshop on Linux, MacOS, or Windows using Vagrant and VirtualBox.

---

## 1. Prerequisites

### Install VirtualBox

- **MacOS & Windows:**
  - Download and install from: https://www.virtualbox.org/wiki/Downloads
- **Linux (Ubuntu/Debian):**
  - Run:
    ```sh
    sudo apt-get update
    sudo apt-get install -y virtualbox
    ```
  - For other distros, see the [VirtualBox Linux Downloads](https://www.virtualbox.org/wiki/Linux_Downloads).

### Install Vagrant

- **MacOS & Windows:**
  - Download and install from: https://www.vagrantup.com/downloads
- **MacOS (Homebrew alternative):**
  - Run:
    ```sh
    brew install --cask vagrant
    ```
- **Linux (Ubuntu/Debian):**
  - Run:
    ```sh
    sudo apt-get install -y vagrant
    ```
  - Or download the `.deb` package from https://www.vagrantup.com/downloads and install with:
    ```sh
    sudo dpkg -i vagrant_*.deb
    ```

---

## 2. Verify Installation

Check that both Vagrant and VirtualBox are installed:
```sh
vagrant --version
virtualbox --help
```

---

## 3. Clone the Workshop Repository

```sh
git clone <your-repo-url>
cd autocon3-workshop-guide
```

---

## 4. Start the Workshop VM

```sh
vagrant up
```

This will download the Ubuntu image, set up Docker and Containerlab, and sync your workshop files into the VM.

---

## 5. Access the VM

```sh
vagrant ssh
cd /home/vagrant/workshop/network
```

---

## 6. Run Your First Lab

```sh
sudo clab deploy -t 2nodes.clab.yaml
```

---

## 7. (Optional) Use VS Code with the VM

1. Install the [Remote - SSH](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh) extension in VS Code.
2. Run:
   ```sh
   vagrant ssh-config > vagrant-ssh-config
   ```
3. Add a new SSH host in VS Code using the details from `vagrant-ssh-config`.
4. Connect and work directly in the VM from VS Code.

---

## 8. Stopping and Cleaning Up

- To stop the VM (pause):
  ```sh
  vagrant halt
  ```
- To destroy the VM (remove all data):
  ```sh
  vagrant destroy
  ```

---

## Troubleshooting
- Make sure virtualization is enabled in your BIOS/firmware.
- If you have issues with permissions, try running your terminal as administrator (Windows) or with `sudo` (Linux/Mac).
- For more help, see the [Vagrant documentation](https://www.vagrantup.com/docs) and [VirtualBox documentation](https://www.virtualbox.org/manual/).

---

Happy Labbing!
