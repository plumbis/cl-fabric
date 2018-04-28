#!/bin/bash
# Created by Topology-Converter v5.0.0
#    Template Revision: v4.6.5

function error() {
  echo -e "\e[0;33mERROR: The Zero Touch Provisioning script failed while running the command $BASH_COMMAND at line $BASH_LINENO.\e[0m" >&2
}
trap error ERR

SSH_URL="http://192.168.200.254/authorized_keys"
#Setup SSH key authentication for Ansible
mkdir -p /home/cumulus/.ssh
wget -O /home/cumulus/.ssh/authorized_keys $SSH_URL
sed -i '/iface eth0/a \ vrf mgmt' /etc/network/interfaces
cat <<EOT >> /etc/network/interfaces
auto mgmt
iface mgmt
  address 127.0.0.1/8
  vrf-table auto
EOT

# Passwordless Sudo
echo "cumulus ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/10_cumulus

# Disable AAA lookups for APT
sed -i -e 's/#precedence ::ffff:0:0\/96  10/#precedence ::ffff:0:0\/96  100/g' /etc/gai.conf

# Update GPG keys to solve KB issue https://support.cumulusnetworks.com/hc/en-us/articles/360002663013-Updating-Expired-GPG-Keys
wget https://repo3.cumulusnetworks.com/repo/pool/cumulus/c/cumulus-archive-keyring/cumulus-archive-keyring_3-cl3u4_all.deb
sudo dpkg -i cumulus-archive-keyring_3-cl3u4_all.deb

apt-get update
apt-get install python-apt


reboot
exit 0
#CUMULUS-AUTOPROVISIONING
