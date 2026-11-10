#!/usr/bin/env bash
set -euo pipefail

# NetBox Discovery Quickstart — macOS bootstrap
#
# This quickstart relies on ContainerLab, which has no native macOS support,
# and its Nokia SR Linux lab images, which are published x86_64-only. This
# script creates a Lima-managed Ubuntu VM that satisfies both requirements —
# a real Linux host, with a genuine x86_64 kernel so SR Linux boots cleanly
# (a native arm64 VM with per-process amd64 emulation is NOT enough; SR
# Linux's system daemons boot-loop under it) — and drops you into a shell
# inside it so you can continue with the rest of the quickstart exactly as
# documented in README.md, starting from "Clone the repo".
#
# Run this ON YOUR MAC, not inside any VM:
#   ./0_macos_create_vm.sh
#
# Override sizing if you like, e.g.:
#   VM_CPUS=6 VM_MEMORY_GIB=8 ./0_macos_create_vm.sh
# but note that fewer than ~8-10 CPUs / 12GiB RAM has been observed to cause
# Device Discovery's bulk NetBox writes to time out under emulation.

VM_NAME="${VM_NAME:-netbox-quickstart}"
VM_CPUS="${VM_CPUS:-11}"
VM_MEMORY_GIB="${VM_MEMORY_GIB:-16}"
VM_DISK_GIB="${VM_DISK_GIB:-60}"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "This script is for macOS only. On Linux, just follow the main README directly."
  exit 1
fi

if ! command -v brew &> /dev/null; then
  echo "Error: Homebrew is required (https://brew.sh) to install Lima."
  exit 1
fi

if ! command -v limactl &> /dev/null; then
  echo "--- Installing Lima ---"
  brew install lima
fi

# Apple Silicon needs the QEMU driver + additional guest agent to run an
# x86_64 guest at all (the default 'vz' driver only supports native-arch
# guests).
if [[ "$(uname -m)" == "arm64" ]]; then
  if ! brew list lima-additional-guestagents &> /dev/null; then
    echo "--- Installing lima-additional-guestagents (x86_64 guest support on Apple Silicon) ---"
    brew install lima-additional-guestagents
  fi
fi

if limactl list --format '{{.Name}}' 2>/dev/null | grep -qx "$VM_NAME"; then
  echo "--- VM '$VM_NAME' already exists, starting it ---"
  limactl start "$VM_NAME"
else
  echo "--- Creating VM '$VM_NAME' (x86_64, ${VM_CPUS} CPUs, ${VM_MEMORY_GIB}GiB RAM, ${VM_DISK_GIB}GiB disk) ---"
  limactl create --name="$VM_NAME" --arch=x86_64 \
    --cpus="$VM_CPUS" --memory="$VM_MEMORY_GIB" --disk="$VM_DISK_GIB" \
    template:ubuntu-25.04 --tty=false
  echo "--- Starting VM '$VM_NAME' ---"
  limactl start "$VM_NAME"
fi

VM_IP=$(limactl shell "$VM_NAME" -- bash -c "ip -4 addr show | grep -v '127.0.0.1' | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1")

echo
echo "--- VM ready ---"
echo "VM internal IP: $VM_IP"
echo
echo "Lima automatically forwards any port the VM listens on back to"
echo "127.0.0.1 on your Mac, so once NetBox is up later in this guide you"
echo "can always reach it at http://127.0.0.1:8000 from your Mac browser,"
echo "regardless of the IP address used inside the VM."
echo
echo "Next steps — open a shell in the VM and continue the main README from"
echo "'Clone the repo and go to the Discovery Quickstart':"
echo
echo "  limactl shell $VM_NAME"
echo "  sudo mkdir -p /opt && sudo chown \$(whoami):\$(whoami) /opt && cd /opt"
echo "  git clone https://github.com/netboxlabs/netbox-learning.git"
echo "  cd netbox-learning/netbox-discovery-quickstart"
echo "  ./0_install_host_tooling.sh"
echo
echo "When you reach 'Generate and export the necessary environment"
echo "variables', use:"
echo
echo "  export MY_EXTERNAL_IP=$VM_IP"
echo
echo "Note: the 'su - quickstart' step won't accept password input"
echo "non-interactively. If you're scripting the rest of this, grant"
echo "passwordless sudo first:"
echo
echo "  echo 'quickstart ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/quickstart-nopasswd"
echo "  sudo chmod 440 /etc/sudoers.d/quickstart-nopasswd"
