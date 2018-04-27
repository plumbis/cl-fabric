# Created by Topology-Converter v5.0.0
#    Template Revision: v5.0.0
#    https://github.com/cumulusnetworks/topology_converter
#    using topology data from: topology.dot
#    built with the following args: ['topology.dot', '-p', 'libvirt', '-s', '9844']
#    NOTE: in order to use this Vagrantfile you will need:
#        - Vagrant(v2.0.2+) installed: http://www.vagrantup.com/downloads
#        - the "helper_scripts" directory that comes packaged with topology-converter.py
#        - Libvirt Installed -- guide to come
#        - Vagrant-Libvirt Plugin installed: $ vagrant plugin install vagrant-libvirt
#        - Start with "vagrant up --provider=libvirt --no-parallel"
#
#  Libvirt Start Port: 9844
#  Libvirt Port Gap: 1000

# Set the default provider to libvirt in the case they forget
# --provider=libvirt or if someone destroys a machine it reverts to virtualbox
ENV['VAGRANT_DEFAULT_PROVIDER'] = 'libvirt'

# Check required plugins
REQUIRED_PLUGINS_LIBVIRT = %w(vagrant-libvirt)
exit unless REQUIRED_PLUGINS_LIBVIRT.all? do |plugin|
  Vagrant.has_plugin?(plugin) || (
    puts "The #{plugin} plugin is required. Please install it with:"
    puts "$ vagrant plugin install #{plugin}"
    false
  )
end

Vagrant.require_version ">= 2.0.2"

$script = <<-SCRIPT
if grep -q -i 'cumulus' /etc/lsb-release &> /dev/null; then
    echo "### RUNNING CUMULUS EXTRA CONFIG ###"
    source /etc/lsb-release
    if [ -z /etc/app-release ]; then
        echo "  INFO: Detected NetQ TS Server"
        source /etc/app-release
        echo "  INFO: Running NetQ TS Appliance Version $APPLIANCE_VERSION"
    else
        if [[ $DISTRIB_RELEASE =~ ^2.* ]]; then
            echo "  INFO: Detected a 2.5.x Based Release"

            echo "  adding fake cl-acltool..."
            echo -e "#!/bin/bash\nexit 0" > /usr/bin/cl-acltool
            chmod 755 /usr/bin/cl-acltool

            echo "  adding fake cl-license..."
            echo -e "#!/bin/bash\nexit 0" > /usr/bin/cl-license
            chmod 755 /usr/bin/cl-license

            echo "  Disabling default remap on Cumulus VX..."
            mv -v /etc/init.d/rename_eth_swp /etc/init.d/rename_eth_swp.backup

            echo "### Rebooting to Apply Remap..."

        elif [[ $DISTRIB_RELEASE =~ ^3.* ]]; then
            echo "  INFO: Detected a 3.x Based Release"
            echo "### Disabling default remap on Cumulus VX..."
            mv -v /etc/hw_init.d/S10rename_eth_swp.sh /etc/S10rename_eth_swp.sh.backup &> /dev/null
            echo "### Disabling ZTP service..."
            systemctl stop ztp.service
            ztp -d 2>&1
            echo "### Resetting ZTP to work next boot..."
            ztp -R 2>&1
            echo "  INFO: Detected Cumulus Linux v$DISTRIB_RELEASE Release"
            if [[ $DISTRIB_RELEASE =~ ^3.[1-9].* ]]; then
                echo "### Fixing ONIE DHCP to avoid Vagrant Interface ###"
                echo "     Note: Installing from ONIE will undo these changes."
                mkdir /tmp/foo
                mount LABEL=ONIE-BOOT /tmp/foo
                sed -i 's/eth0/eth1/g' /tmp/foo/grub/grub.cfg
                sed -i 's/eth0/eth1/g' /tmp/foo/onie/grub/grub-extra.cfg
                umount /tmp/foo
            fi
            if [[ $DISTRIB_RELEASE =~ ^3.[2-9].* ]]; then
                if [[ $(grep "vagrant" /etc/netd.conf | wc -l ) == 0 ]]; then
                    echo "### Giving Vagrant User Ability to Run NCLU Commands ###"
                    sed -i 's/users_with_edit = root, cumulus/users_with_edit = root, cumulus, vagrant/g' /etc/netd.conf
                    sed -i 's/users_with_show = root, cumulus/users_with_show = root, cumulus, vagrant/g' /etc/netd.conf
                fi
            fi
        fi
    fi
fi
echo "### DONE ###"
echo "### Rebooting Device to Apply Remap..."
nohup bash -c 'sleep 10; shutdown now -r "Rebooting to Remap Interfaces"' &
SCRIPT

Vagrant.configure("2") do |config|

  config.vm.provider :libvirt do |domain|
    # increase nic adapter count to be greater than 8 for all VMs.
    domain.nic_adapter_count = 130
  end


        
##### DEFINE VM for oob-mgmt-server #####
  config.vm.define "oob-mgmt-server" do |device|
    
    device.vm.hostname = "oob-mgmt-server"
    device.vm.box = "CumulusCommunity/vx_oob_server"
    device.vm.box_version = "1.0.4"

    device.vm.provider "libvirt" do |v|      
        v.memory = 1024    
        

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for eth1 --> oob-mgmt-switch:swp1
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:59',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1079',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9079',
        :libvirt__iface_name => 'eth1',
        auto_config: false
    # link for eth0 --> NOTHING:eth3
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:68',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1088',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9088',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    
        
    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/auto_mgmt_network/oob_server_config_auto_mgmt.sh"
    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:59 --> eth1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:59", NAME="eth1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:68 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:68", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for oob-mgmt-switch #####
  config.vm.define "oob-mgmt-switch" do |device|
    
    device.vm.hostname = "oob-mgmt-switch"
    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.3"

    device.vm.provider "libvirt" do |v|      
        v.memory = 256    
        

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for eth0 --> NOTHING:eth2
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:66',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1087',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9087',
        :libvirt__iface_name => 'eth0',
        auto_config: false
    # link for swp10 --> spine01:eth0
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:32',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9055',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1055',
        :libvirt__iface_name => 'swp10',
        auto_config: false
    # link for swp11 --> spine02:eth0
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:61',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9084',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1084',
        :libvirt__iface_name => 'swp11',
        auto_config: false
    # link for swp12 --> exit01:eth0
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:0f',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9033',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1033',
        :libvirt__iface_name => 'swp12',
        auto_config: false
    # link for swp13 --> exit02:eth0
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:4f',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9073',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1073',
        :libvirt__iface_name => 'swp13',
        auto_config: false
    # link for swp14 --> edge01:eth0
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:42',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9065',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1065',
        :libvirt__iface_name => 'swp14',
        auto_config: false
    # link for swp15 --> internet:eth0
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:38',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9059',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1059',
        :libvirt__iface_name => 'swp15',
        auto_config: false
    # link for swp16 --> netq-ts:eth1
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:3a',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9060',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1060',
        :libvirt__iface_name => 'swp16',
        auto_config: false
    # link for swp8 --> leaf03:eth0
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:2d',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9052',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1052',
        :libvirt__iface_name => 'swp8',
        auto_config: false
    # link for swp9 --> leaf04:eth0
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:37',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9058',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1058',
        :libvirt__iface_name => 'swp9',
        auto_config: false
    # link for swp2 --> server01:eth0
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:45',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9067',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1067',
        :libvirt__iface_name => 'swp2',
        auto_config: false
    # link for swp3 --> server02:eth0
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:4e',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9072',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1072',
        :libvirt__iface_name => 'swp3',
        auto_config: false
    # link for swp1 --> oob-mgmt-server:eth1
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:61',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9079',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1079',
        :libvirt__iface_name => 'swp1',
        auto_config: false
    # link for swp6 --> leaf01:eth0
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:20',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9044',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1044',
        :libvirt__iface_name => 'swp6',
        auto_config: false
    # link for swp7 --> leaf02:eth0
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:3f',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9063',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1063',
        :libvirt__iface_name => 'swp7',
        auto_config: false
    # link for swp4 --> server03:eth0
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:04',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9027',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1027',
        :libvirt__iface_name => 'swp4',
        auto_config: false
    # link for swp5 --> server04:eth0
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:50',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9074',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1074',
        :libvirt__iface_name => 'swp5',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    
        
    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/oob_switch_config.sh"
    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:66 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:66", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:32 --> swp10'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:32", NAME="swp10", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:61 --> swp11'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:61", NAME="swp11", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:0f --> swp12'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:0f", NAME="swp12", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:4f --> swp13'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:4f", NAME="swp13", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:42 --> swp14'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:42", NAME="swp14", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:38 --> swp15'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:38", NAME="swp15", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:3a --> swp16'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:3a", NAME="swp16", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:2d --> swp8'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:2d", NAME="swp8", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:37 --> swp9'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:37", NAME="swp9", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:45 --> swp2'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:45", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:4e --> swp3'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:4e", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:61 --> swp1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:61", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:20 --> swp6'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:20", NAME="swp6", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:3f --> swp7'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:3f", NAME="swp7", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:04 --> swp4'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:04", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:50 --> swp5'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:50", NAME="swp5", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for exit02 #####
  config.vm.define "exit02" do |device|
    
    device.vm.hostname = "exit02"
    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.3"

    device.vm.provider "libvirt" do |v|      
        v.memory = 768    
        

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for eth0 --> oob-mgmt-switch:swp13
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:42',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1073',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9073',
        :libvirt__iface_name => 'eth0',
        auto_config: false
    # link for swp50 --> exit01:swp50
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:17',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9038',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1038',
        :libvirt__iface_name => 'swp50',
        auto_config: false
    # link for swp51 --> spine01:swp29
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:21',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1045',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9045',
        :libvirt__iface_name => 'swp51',
        auto_config: false
    # link for swp52 --> spine02:swp29
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:57',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1078',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9078',
        :libvirt__iface_name => 'swp52',
        auto_config: false
    # link for swp49 --> exit01:swp49
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:27',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9048',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1048',
        :libvirt__iface_name => 'swp49',
        auto_config: false
    # link for swp48 --> exit02:swp47
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:36',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9057',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1057',
        :libvirt__iface_name => 'swp48',
        auto_config: false
    # link for swp1 --> edge01:eth2
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:0c',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9031',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1031',
        :libvirt__iface_name => 'swp1',
        auto_config: false
    # link for swp47 --> exit02:swp48
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:35',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1057',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9057',
        :libvirt__iface_name => 'swp47',
        auto_config: false
    # link for swp46 --> exit02:swp45
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:31',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9054',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1054',
        :libvirt__iface_name => 'swp46',
        auto_config: false
    # link for swp45 --> exit02:swp46
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:30',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1054',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9054',
        :libvirt__iface_name => 'swp45',
        auto_config: false
    # link for swp44 --> internet:swp2
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:41',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9064',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1064',
        :libvirt__iface_name => 'swp44',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:42 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:42", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:17 --> swp50'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:17", NAME="swp50", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:21 --> swp51'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:21", NAME="swp51", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:57 --> swp52'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:57", NAME="swp52", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:27 --> swp49'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:27", NAME="swp49", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:36 --> swp48'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:36", NAME="swp48", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:0c --> swp1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:0c", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:35 --> swp47'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:35", NAME="swp47", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:31 --> swp46'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:31", NAME="swp46", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:30 --> swp45'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:30", NAME="swp45", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:41 --> swp44'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:41", NAME="swp44", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = vagrant'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for exit01 #####
  config.vm.define "exit01" do |device|
    
    device.vm.hostname = "exit01"
    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.3"

    device.vm.provider "libvirt" do |v|      
        v.memory = 768    
        

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for swp1 --> edge01:eth1
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:4d',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9071',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1071',
        :libvirt__iface_name => 'swp1',
        auto_config: false
    # link for swp50 --> exit02:swp50
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:16',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1038',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9038',
        :libvirt__iface_name => 'swp50',
        auto_config: false
    # link for swp51 --> spine01:swp30
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:09',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1030',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9030',
        :libvirt__iface_name => 'swp51',
        auto_config: false
    # link for swp52 --> spine02:swp30
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:5c',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1081',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9081',
        :libvirt__iface_name => 'swp52',
        auto_config: false
    # link for swp49 --> exit02:swp49
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:26',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1048',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9048',
        :libvirt__iface_name => 'swp49',
        auto_config: false
    # link for swp48 --> exit01:swp47
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:13',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9035',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1035',
        :libvirt__iface_name => 'swp48',
        auto_config: false
    # link for swp44 --> internet:swp1
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:08',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9029',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1029',
        :libvirt__iface_name => 'swp44',
        auto_config: false
    # link for swp47 --> exit01:swp48
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:12',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1035',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9035',
        :libvirt__iface_name => 'swp47',
        auto_config: false
    # link for swp46 --> exit01:swp45
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:47',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9068',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1068',
        :libvirt__iface_name => 'swp46',
        auto_config: false
    # link for swp45 --> exit01:swp46
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:46',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1068',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9068',
        :libvirt__iface_name => 'swp45',
        auto_config: false
    # link for eth0 --> oob-mgmt-switch:swp12
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:41',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1033',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9033',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:4d --> swp1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:4d", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:16 --> swp50'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:16", NAME="swp50", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:09 --> swp51'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:09", NAME="swp51", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:5c --> swp52'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:5c", NAME="swp52", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:26 --> swp49'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:26", NAME="swp49", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:13 --> swp48'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:13", NAME="swp48", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:08 --> swp44'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:08", NAME="swp44", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:12 --> swp47'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:12", NAME="swp47", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:47 --> swp46'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:47", NAME="swp46", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:46 --> swp45'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:46", NAME="swp45", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:41 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:41", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = vagrant'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for spine02 #####
  config.vm.define "spine02" do |device|
    
    device.vm.hostname = "spine02"
    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.3"

    device.vm.provider "libvirt" do |v|      
        v.memory = 768    
        

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for swp32 --> spine01:swp32
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:3c',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9061',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1061',
        :libvirt__iface_name => 'swp32',
        auto_config: false
    # link for swp30 --> exit01:swp52
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:5d',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9081',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1081',
        :libvirt__iface_name => 'swp30',
        auto_config: false
    # link for swp31 --> spine01:swp31
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:4b',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9070',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1070',
        :libvirt__iface_name => 'swp31',
        auto_config: false
    # link for swp29 --> exit02:swp52
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:58',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9078',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1078',
        :libvirt__iface_name => 'swp29',
        auto_config: false
    # link for swp2 --> leaf02:swp52
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:60',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9083',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1083',
        :libvirt__iface_name => 'swp2',
        auto_config: false
    # link for swp3 --> leaf03:swp52
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:1c',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9041',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1041',
        :libvirt__iface_name => 'swp3',
        auto_config: false
    # link for swp1 --> leaf01:swp52
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:25',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9047',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1047',
        :libvirt__iface_name => 'swp1',
        auto_config: false
    # link for swp4 --> leaf04:swp52
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:49',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9069',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1069',
        :libvirt__iface_name => 'swp4',
        auto_config: false
    # link for eth0 --> oob-mgmt-switch:swp11
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:22',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1084',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9084',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    
        
    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"
    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:3c --> swp32'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:3c", NAME="swp32", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:5d --> swp30'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:5d", NAME="swp30", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:4b --> swp31'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:4b", NAME="swp31", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:58 --> swp29'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:58", NAME="swp29", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:60 --> swp2'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:60", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:1c --> swp3'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:1c", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:25 --> swp1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:25", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:49 --> swp4'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:49", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:22 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:22", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = vagrant'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for spine01 #####
  config.vm.define "spine01" do |device|
    
    device.vm.hostname = "spine01"
    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.3"

    device.vm.provider "libvirt" do |v|      
        v.memory = 768    
        

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for swp32 --> spine02:swp32
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:3b',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1061',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9061',
        :libvirt__iface_name => 'swp32',
        auto_config: false
    # link for swp30 --> exit01:swp51
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:0a',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9030',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1030',
        :libvirt__iface_name => 'swp30',
        auto_config: false
    # link for swp31 --> spine02:swp31
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:4a',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1070',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9070',
        :libvirt__iface_name => 'swp31',
        auto_config: false
    # link for swp29 --> exit02:swp51
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:22',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9045',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1045',
        :libvirt__iface_name => 'swp29',
        auto_config: false
    # link for swp2 --> leaf02:swp51
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:29',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9049',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1049',
        :libvirt__iface_name => 'swp2',
        auto_config: false
    # link for swp3 --> leaf03:swp51
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:52',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9075',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1075',
        :libvirt__iface_name => 'swp3',
        auto_config: false
    # link for swp1 --> leaf01:swp51
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:56',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9077',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1077',
        :libvirt__iface_name => 'swp1',
        auto_config: false
    # link for swp4 --> leaf04:swp51
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:3e',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9062',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1062',
        :libvirt__iface_name => 'swp4',
        auto_config: false
    # link for eth0 --> oob-mgmt-switch:swp10
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:21',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1055',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9055',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    
        
    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"
    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:3b --> swp32'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:3b", NAME="swp32", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:0a --> swp30'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:0a", NAME="swp30", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:4a --> swp31'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:4a", NAME="swp31", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:22 --> swp29'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:22", NAME="swp29", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:29 --> swp2'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:29", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:52 --> swp3'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:52", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:56 --> swp1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:56", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:3e --> swp4'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:3e", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:21 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:21", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = vagrant'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for leaf04 #####
  config.vm.define "leaf04" do |device|
    
    device.vm.hostname = "leaf04"
    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.3"

    device.vm.provider "libvirt" do |v|      
        v.memory = 768    
        

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for swp50 --> leaf03:swp50
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:06',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9028',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1028',
        :libvirt__iface_name => 'swp50',
        auto_config: false
    # link for swp51 --> spine01:swp4
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:3d',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1062',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9062',
        :libvirt__iface_name => 'swp51',
        auto_config: false
    # link for swp52 --> spine02:swp4
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:48',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1069',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9069',
        :libvirt__iface_name => 'swp52',
        auto_config: false
    # link for swp49 --> leaf03:swp49
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:2f',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9053',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1053',
        :libvirt__iface_name => 'swp49',
        auto_config: false
    # link for swp48 --> leaf04:swp47
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:34',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9056',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1056',
        :libvirt__iface_name => 'swp48',
        auto_config: false
    # link for swp2 --> server04:eth2
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:2c',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9051',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1051',
        :libvirt__iface_name => 'swp2',
        auto_config: false
    # link for swp1 --> server03:eth2
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:5e',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9082',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1082',
        :libvirt__iface_name => 'swp1',
        auto_config: false
    # link for swp47 --> leaf04:swp48
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:33',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1056',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9056',
        :libvirt__iface_name => 'swp47',
        auto_config: false
    # link for swp46 --> leaf04:swp45
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:1a',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9040',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1040',
        :libvirt__iface_name => 'swp46',
        auto_config: false
    # link for swp45 --> leaf04:swp46
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:19',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1040',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9040',
        :libvirt__iface_name => 'swp45',
        auto_config: false
    # link for eth0 --> oob-mgmt-switch:swp9
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:14',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1058',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9058',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    
        
    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"
    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:06 --> swp50'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:06", NAME="swp50", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:3d --> swp51'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:3d", NAME="swp51", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:48 --> swp52'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:48", NAME="swp52", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:2f --> swp49'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:2f", NAME="swp49", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:34 --> swp48'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:34", NAME="swp48", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:2c --> swp2'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:2c", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:5e --> swp1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:5e", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:33 --> swp47'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:33", NAME="swp47", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:1a --> swp46'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:1a", NAME="swp46", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:19 --> swp45'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:19", NAME="swp45", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:14 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:14", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = vagrant'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for leaf02 #####
  config.vm.define "leaf02" do |device|
    
    device.vm.hostname = "leaf02"
    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.3"

    device.vm.provider "libvirt" do |v|      
        v.memory = 768    
        

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for swp50 --> leaf01:swp50
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:02',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9025',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1025',
        :libvirt__iface_name => 'swp50',
        auto_config: false
    # link for swp51 --> spine01:swp2
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:28',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1049',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9049',
        :libvirt__iface_name => 'swp51',
        auto_config: false
    # link for swp52 --> spine02:swp2
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:5f',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1083',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9083',
        :libvirt__iface_name => 'swp52',
        auto_config: false
    # link for swp49 --> leaf01:swp49
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:11',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9034',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1034',
        :libvirt__iface_name => 'swp49',
        auto_config: false
    # link for swp48 --> leaf02:swp47
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:5b',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9080',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1080',
        :libvirt__iface_name => 'swp48',
        auto_config: false
    # link for swp2 --> server02:eth2
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:18',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9039',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1039',
        :libvirt__iface_name => 'swp2',
        auto_config: false
    # link for swp1 --> server01:eth2
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:15',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9037',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1037',
        :libvirt__iface_name => 'swp1',
        auto_config: false
    # link for swp47 --> leaf02:swp48
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:5a',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1080',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9080',
        :libvirt__iface_name => 'swp47',
        auto_config: false
    # link for swp46 --> leaf02:swp45
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:0e',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9032',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1032',
        :libvirt__iface_name => 'swp46',
        auto_config: false
    # link for swp45 --> leaf02:swp46
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:0d',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1032',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9032',
        :libvirt__iface_name => 'swp45',
        auto_config: false
    # link for eth0 --> oob-mgmt-switch:swp7
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:12',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1063',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9063',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    
        
    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"
    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:02 --> swp50'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:02", NAME="swp50", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:28 --> swp51'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:28", NAME="swp51", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:5f --> swp52'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:5f", NAME="swp52", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:11 --> swp49'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:11", NAME="swp49", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:5b --> swp48'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:5b", NAME="swp48", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:18 --> swp2'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:18", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:15 --> swp1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:15", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:5a --> swp47'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:5a", NAME="swp47", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:0e --> swp46'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:0e", NAME="swp46", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:0d --> swp45'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:0d", NAME="swp45", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:12 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:12", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = vagrant'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for leaf03 #####
  config.vm.define "leaf03" do |device|
    
    device.vm.hostname = "leaf03"
    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.3"

    device.vm.provider "libvirt" do |v|      
        v.memory = 768    
        

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for swp50 --> leaf04:swp50
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:05',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1028',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9028',
        :libvirt__iface_name => 'swp50',
        auto_config: false
    # link for swp51 --> spine01:swp3
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:51',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1075',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9075',
        :libvirt__iface_name => 'swp51',
        auto_config: false
    # link for swp52 --> spine02:swp3
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:1b',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1041',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9041',
        :libvirt__iface_name => 'swp52',
        auto_config: false
    # link for swp49 --> leaf04:swp49
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:2e',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1053',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9053',
        :libvirt__iface_name => 'swp49',
        auto_config: false
    # link for swp48 --> leaf03:swp47
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:54',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9076',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1076',
        :libvirt__iface_name => 'swp48',
        auto_config: false
    # link for swp2 --> server04:eth1
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:1f',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9043',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1043',
        :libvirt__iface_name => 'swp2',
        auto_config: false
    # link for swp1 --> server03:eth1
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:23',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9046',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1046',
        :libvirt__iface_name => 'swp1',
        auto_config: false
    # link for swp47 --> leaf03:swp48
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:53',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1076',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9076',
        :libvirt__iface_name => 'swp47',
        auto_config: false
    # link for swp46 --> leaf03:swp45
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:2b',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9050',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1050',
        :libvirt__iface_name => 'swp46',
        auto_config: false
    # link for swp45 --> leaf03:swp46
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:2a',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1050',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9050',
        :libvirt__iface_name => 'swp45',
        auto_config: false
    # link for eth0 --> oob-mgmt-switch:swp8
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:13',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1052',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9052',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    
        
    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"
    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:05 --> swp50'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:05", NAME="swp50", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:51 --> swp51'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:51", NAME="swp51", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:1b --> swp52'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:1b", NAME="swp52", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:2e --> swp49'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:2e", NAME="swp49", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:54 --> swp48'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:54", NAME="swp48", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:1f --> swp2'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:1f", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:23 --> swp1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:23", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:53 --> swp47'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:53", NAME="swp47", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:2b --> swp46'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:2b", NAME="swp46", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:2a --> swp45'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:2a", NAME="swp45", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:13 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:13", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = vagrant'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for leaf01 #####
  config.vm.define "leaf01" do |device|
    
    device.vm.hostname = "leaf01"
    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.3"

    device.vm.provider "libvirt" do |v|      
        v.memory = 768    
        

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for swp50 --> leaf02:swp50
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:01',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1025',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9025',
        :libvirt__iface_name => 'swp50',
        auto_config: false
    # link for swp51 --> spine01:swp1
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:55',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1077',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9077',
        :libvirt__iface_name => 'swp51',
        auto_config: false
    # link for swp52 --> spine02:swp1
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:24',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1047',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9047',
        :libvirt__iface_name => 'swp52',
        auto_config: false
    # link for swp49 --> leaf02:swp49
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:10',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1034',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9034',
        :libvirt__iface_name => 'swp49',
        auto_config: false
    # link for swp48 --> leaf01:swp47
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:44',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9066',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1066',
        :libvirt__iface_name => 'swp48',
        auto_config: false
    # link for swp2 --> server02:eth1
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:14',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9036',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1036',
        :libvirt__iface_name => 'swp2',
        auto_config: false
    # link for swp1 --> server01:eth1
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:03',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9026',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1026',
        :libvirt__iface_name => 'swp1',
        auto_config: false
    # link for swp47 --> leaf01:swp48
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:43',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1066',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9066',
        :libvirt__iface_name => 'swp47',
        auto_config: false
    # link for swp46 --> leaf01:swp45
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:1e',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '9042',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '1042',
        :libvirt__iface_name => 'swp46',
        auto_config: false
    # link for swp45 --> leaf01:swp46
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:1d',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1042',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9042',
        :libvirt__iface_name => 'swp45',
        auto_config: false
    # link for eth0 --> oob-mgmt-switch:swp6
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:11',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1044',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9044',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    
        
    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"
    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:01 --> swp50'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:01", NAME="swp50", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:55 --> swp51'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:55", NAME="swp51", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:24 --> swp52'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:24", NAME="swp52", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:10 --> swp49'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:10", NAME="swp49", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:44 --> swp48'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:44", NAME="swp48", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:14 --> swp2'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:14", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:03 --> swp1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:03", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:43 --> swp47'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:43", NAME="swp47", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:1e --> swp46'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:1e", NAME="swp46", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:1d --> swp45'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:1d", NAME="swp45", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:11 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:11", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = vagrant'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for edge01 #####
  config.vm.define "edge01" do |device|
    
    device.vm.hostname = "edge01"
    device.vm.box = "yk0/ubuntu-xenial"

    device.vm.provider "libvirt" do |v|      
        v.memory = 768    
        
        v.nic_model_type = 'e1000'

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for eth2 --> exit02:swp1
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:0b',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1031',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9031',
        :libvirt__iface_name => 'eth2',
        auto_config: false
    # link for eth1 --> exit01:swp1
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:4c',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1071',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9071',
        :libvirt__iface_name => 'eth1',
        auto_config: false
    # link for eth0 --> oob-mgmt-switch:swp14
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:51',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1065',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9065',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    # Shorten Boot Process - Applies to Ubuntu Only - remove \"Wait for Network\"
    device.vm.provision :shell , inline: "sed -i 's/sleep [0-9]*/sleep 1/' /etc/init/failsafe.conf 2>/dev/null || true"
        
    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_server_config.sh"
    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:0b --> eth2'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:0b", NAME="eth2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:4c --> eth1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:4c", NAME="eth1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:51 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:51", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = vagrant'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for server01 #####
  config.vm.define "server01" do |device|
    
    device.vm.hostname = "server01"
    device.vm.box = "yk0/ubuntu-xenial"

    device.vm.provider "libvirt" do |v|      
        v.memory = 512    
        
        v.nic_model_type = 'e1000'

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for eth2 --> leaf02:swp1
        device.vm.network "private_network",
        :mac => '30:01:11:10',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1037',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9037',
        :libvirt__iface_name => 'eth2',
        auto_config: false
    # link for eth1 --> leaf01:swp1
        device.vm.network "private_network",
        :mac => '30:01:11:10',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1026',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9026',
        :libvirt__iface_name => 'eth1',
        auto_config: false
    # link for eth0 --> oob-mgmt-switch:swp2
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:31',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1067',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9067',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    # Shorten Boot Process - Applies to Ubuntu Only - remove \"Wait for Network\"
    device.vm.provision :shell , inline: "sed -i 's/sleep [0-9]*/sleep 1/' /etc/init/failsafe.conf 2>/dev/null || true"
        
    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_server_config.sh"
    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 30:01:11:10 --> eth2'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="30:01:11:10", NAME="eth2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 30:01:11:10 --> eth1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="30:01:11:10", NAME="eth1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:31 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:31", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = vagrant'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for server03 #####
  config.vm.define "server03" do |device|
    
    device.vm.hostname = "server03"
    device.vm.box = "yk0/ubuntu-xenial"

    device.vm.provider "libvirt" do |v|      
        v.memory = 512    
        
        v.nic_model_type = 'e1000'

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for eth2 --> leaf04:swp1
        device.vm.network "private_network",
        :mac => '30:03:33:30',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1082',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9082',
        :libvirt__iface_name => 'eth2',
        auto_config: false
    # link for eth1 --> leaf03:swp1
        device.vm.network "private_network",
        :mac => '30:03:33:30',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1046',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9046',
        :libvirt__iface_name => 'eth1',
        auto_config: false
    # link for eth0 --> oob-mgmt-switch:swp4
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:33',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1027',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9027',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    # Shorten Boot Process - Applies to Ubuntu Only - remove \"Wait for Network\"
    device.vm.provision :shell , inline: "sed -i 's/sleep [0-9]*/sleep 1/' /etc/init/failsafe.conf 2>/dev/null || true"
        
    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_server_config.sh"
    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 30:03:33:30 --> eth2'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="30:03:33:30", NAME="eth2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 30:03:33:30 --> eth1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="30:03:33:30", NAME="eth1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:33 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:33", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = vagrant'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for server02 #####
  config.vm.define "server02" do |device|
    
    device.vm.hostname = "server02"
    device.vm.box = "yk0/ubuntu-xenial"

    device.vm.provider "libvirt" do |v|      
        v.memory = 512    
        
        v.nic_model_type = 'e1000'

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for eth2 --> leaf02:swp2
        device.vm.network "private_network",
        :mac => '30:02:22:20',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1039',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9039',
        :libvirt__iface_name => 'eth2',
        auto_config: false
    # link for eth1 --> leaf01:swp2
        device.vm.network "private_network",
        :mac => '30:02:22:20',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1036',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9036',
        :libvirt__iface_name => 'eth1',
        auto_config: false
    # link for eth0 --> oob-mgmt-switch:swp3
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:32',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1072',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9072',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    # Shorten Boot Process - Applies to Ubuntu Only - remove \"Wait for Network\"
    device.vm.provision :shell , inline: "sed -i 's/sleep [0-9]*/sleep 1/' /etc/init/failsafe.conf 2>/dev/null || true"
        
    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_server_config.sh"
    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 30:02:22:20 --> eth2'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="30:02:22:20", NAME="eth2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 30:02:22:20 --> eth1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="30:02:22:20", NAME="eth1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:32 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:32", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = vagrant'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for server04 #####
  config.vm.define "server04" do |device|
    
    device.vm.hostname = "server04"
    device.vm.box = "yk0/ubuntu-xenial"

    device.vm.provider "libvirt" do |v|      
        v.memory = 512    
        
        v.nic_model_type = 'e1000'

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for eth2 --> leaf04:swp2
        device.vm.network "private_network",
        :mac => '30:04:44:40',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1051',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9051',
        :libvirt__iface_name => 'eth2',
        auto_config: false
    # link for eth1 --> leaf03:swp2
        device.vm.network "private_network",
        :mac => '30:04:44:40',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1043',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9043',
        :libvirt__iface_name => 'eth1',
        auto_config: false
    # link for eth0 --> oob-mgmt-switch:swp5
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:34',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1074',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9074',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    # Shorten Boot Process - Applies to Ubuntu Only - remove \"Wait for Network\"
    device.vm.provision :shell , inline: "sed -i 's/sleep [0-9]*/sleep 1/' /etc/init/failsafe.conf 2>/dev/null || true"
        
    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_server_config.sh"
    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 30:04:44:40 --> eth2'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="30:04:44:40", NAME="eth2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 30:04:44:40 --> eth1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="30:04:44:40", NAME="eth1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:34 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:34", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = vagrant'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for netq-ts #####
  config.vm.define "netq-ts" do |device|
    
    device.vm.hostname = "netq-ts"
    device.vm.box = "netq/ts"

    device.vm.provider "libvirt" do |v|      
        v.memory = 1024    
        

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for eth1 --> oob-mgmt-switch:swp16
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:39',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1060',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9060',
        :libvirt__iface_name => 'eth1',
        auto_config: false
    # link for eth0 --> NOTHING:eth1
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:64',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1086',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9086',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:39 --> eth1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:39", NAME="eth1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:64 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:64", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
        
##### DEFINE VM for internet #####
  config.vm.define "internet" do |device|
    
    device.vm.hostname = "internet"
    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.3"

    device.vm.provider "libvirt" do |v|      
        v.memory = 768    
        

    end
    # see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true

    # NETWORK INTERFACES
    # link for swp2 --> exit02:swp44
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:40',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1064',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9064',
        :libvirt__iface_name => 'swp2',
        auto_config: false
    # link for swp1 --> exit01:swp44
        device.vm.network "private_network",
        :mac => '44:38:39:00:00:07',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1029',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9029',
        :libvirt__iface_name => 'swp1',
        auto_config: false
    # link for eth0 --> oob-mgmt-switch:swp15
        device.vm.network "private_network",
        :mac => 'a0:00:00:00:00:50',
        :libvirt__tunnel_type => 'udp',
        :libvirt__tunnel_local_ip => '127.0.0.1',
        :libvirt__tunnel_local_port => '1059',
        :libvirt__tunnel_ip => '127.0.0.1',
        :libvirt__tunnel_port => '9059',
        :libvirt__iface_name => 'eth0',
        auto_config: false 

    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    

    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
      if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
        rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
      fi
      rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
    delete_udev_directory
    
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:40 --> swp2'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:40", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: 44:38:39:00:00:07 --> swp1'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:07", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule
    device.vm.provision :shell , :inline => <<-udev_rule
      echo '  INFO: Adding UDEV Rule: a0:00:00:00:00:50 --> eth0'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="a0:00:00:00:00:50", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
    udev_rule

    device.vm.provision :shell , :inline => <<-vagrant_interface_rule
      echo '  INFO: Adding UDEV Rule: Vagrant interface = swp48'
      echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="swp48", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
      echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
      cat /etc/udev/rules.d/70-persistent-net.rules
    vagrant_interface_rule

    # Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

  end
end
 