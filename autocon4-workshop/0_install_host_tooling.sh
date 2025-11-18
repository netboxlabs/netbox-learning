#!/bin/bash
set -euo pipefail

# Detect the package manager (apt or yum/dnf)
if command -v apt &> /dev/null; then
    PM="apt"
elif command -v yum &> /dev/null || command -v dnf &> /dev/null; then
    PM=$(command -v dnf || echo yum)  # Use dnf if available, fallback to yum
else
    echo "Unsupported package manager. Only apt, yum, and dnf are supported."
    exit 1
fi

echo "--- Running setup for Linux ---"

# Run package manager-specific commands
#if [[ $PM == "apt" ]]; then
#    sudo apt update
#    sudo apt install -y python3-venv net-tools snmp curl ca-certificates
#else
#    sudo $PM install -y python3-venv net-tools snmp curl ca-certificates
#fi

# Install Docker
echo "--- Installing Docker ---"
if [[ $PM == "apt" ]]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/docker-archive-keyring.gpg > /dev/null
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
    sudo $PM install -y yum-utils
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo $PM install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi

# Start Docker
sudo systemctl enable docker
sudo systemctl start docker

# Install ContainerLab
echo "--- Installing ContainerLab ---"
LATEST_RELEASE=$(curl -s https://api.github.com/repos/srl-labs/containerlab/releases/latest | grep "tag_name" | cut -d : -f 2,3 | tr -d \" | tr -d , | tr -d " ")
echo "Installing ContainerLab version: $LATEST_RELEASE"
cd /tmp
wget -q https://github.com/srl-labs/containerlab/releases/download/${LATEST_RELEASE}/containerlab_${LATEST_RELEASE#v}_linux_amd64.deb
sudo dpkg -i containerlab_${LATEST_RELEASE#v}_linux_amd64.deb
rm -f containerlab_*.deb
cd -
containerlab version

# Install Ansible
echo "--- Installing Ansible ---"
if [[ $PM == "apt" ]]; then
    sudo apt install -y ansible
else
    sudo $PM install -y ansible
fi

# Install Ansible collections
#echo "--- Installing Ansible Collections ---"
#ansible-galaxy collection install nokia.srlinux ansible.netcommon

# Creating new user and adding to the correct groups, and set the permissions on the cloned repo
USERNAME="quickstart"
sudo useradd -m -d "$(pwd)" -s /bin/bash ${USERNAME}
sudo passwd -d ${USERNAME}
sudo usermod -aG sudo ${USERNAME}
sudo usermod -aG docker ${USERNAME}
sudo chown -R ${USERNAME}:${USERNAME} .

echo "--- Setup Complete ---"