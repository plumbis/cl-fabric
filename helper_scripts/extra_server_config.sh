#!/bin/bash

echo "#################################"
echo "  Running Extra_Server_Config.sh"
echo "#################################"
sudo su

useradd cumulus -m -s /bin/bash
echo "cumulus:CumulusLinux!" | chpasswd
sed "s/PasswordAuthentication no/PasswordAuthentication yes/" -i /etc/ssh/sshd_config

# Hides "dpkg-reconfigure: unable to re-open stdin: No file or directory" error in Vagrant up
export DEBIAN_FRONTEND=noninteractive

#Test for Debian-Based Host
which apt &> /dev/null
if [ "$?" == "0" ]; then
    #These lines will be used when booting on a debian-based box
    echo -e "note: ubuntu device detected"
    #Install LLDP
    apt-get update -qy && apt-get install lldpd ntp ntpdate -qy
    echo "configure lldp portidsubtype ifname" > /etc/lldpd.d/port_info.conf

    #Replace existing network interfaces file
    echo -e "auto lo" > /etc/network/interfaces
    echo -e "iface lo inet loopback\n\n" >> /etc/network/interfaces
    echo -e  "source /etc/network/interfaces.d/*.cfg\n" >> /etc/network/interfaces

    #Add vagrant interface
    # echo -e "\n\nauto vagrant" > /etc/network/interfaces.d/vagrant.cfg
    # echo -e "iface vagrant inet dhcp\n\n" >> /etc/network/interfaces.d/vagrant.cfg

    echo -e "\n\nauto eth0" > /etc/network/interfaces.d/eth0.cfg
    echo -e "iface eth0 inet dhcp\n\n" >> /etc/network/interfaces.d/eth0.cfg

    echo "retry 1;" >> /etc/dhcp/dhclient.conf
fi

#Test for Fedora-Based Host
which yum &> /dev/null
if [ "$?" == "0" ]; then
    echo -e "note: fedora-based device detected"
    /usr/bin/dnf install python -y
    echo -e "DEVICE=vagrant\nBOOTPROTO=dhcp\nONBOOT=yes" > /etc/sysconfig/network-scripts/ifcfg-vagrant
    echo -e "DEVICE=eth0\nBOOTPROTO=dhcp\nONBOOT=yes" > /etc/sysconfig/network-scripts/ifcfg-eth0
fi

echo "cumulus ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/10_cumulus

echo "### Installing SSH Keys"
mkdir -p /home/cumulus/.ssh
chmod 700 -R /home/cumulus
chown -R cumulus:cumulus /home/cumulus
chmod 600 /home/cumulus/.ssh/*
chmod 700 /home/cumulus/.ssh
echo -e "wget http://192.168.200.254/authorized_keys -q -O /home/cumulus/.ssh/authorized_keys" > /etc/dhcp/dhclient-exit-hooks.d/get_keys


echo "### Writing NTP Data"
echo -e "Etc/UTC" > /etc/timezone
cat << EOT > /etc/ntp.conf
# /etc/ntp.conf, configuration for ntpd; see ntp.conf(5) for help
driftfile /var/lib/ntp/ntp.drift
statistics loopstats peerstats clockstats
filegen loopstats file loopstats type day enable
filegen peerstats file peerstats type day enable
filegen clockstats file clockstats type day enable
server 192.168.0.254 iburst
# By default, exchange time with everybody, but don't allow configuration.
restrict -4 default kod notrap nomodify nopeer noquery
restrict -6 default kod notrap nomodify nopeer noquery
# Local users may interrogate the ntp server more closely.
restrict 127.0.0.1
restrict ::1
# Specify interfaces, don't listen on switch ports
interface listen eth0
EOT


echo "#################################"
echo "   Finished"
echo "#################################"