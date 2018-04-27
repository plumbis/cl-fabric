#!/usr/bin/env python2.7
"""   Topology Converter converts a given
topology.dot file to a Vagrantfile can use
the virtualbox or libvirt Vagrant providers
Initially written by Eric Pulvino 2015-10-19

 hosted @ https://github.com/cumulusnetworks/topology_converter
"""
# C0302 - Too many lines in module.
# Classes should probably be broken out, future work.
# Ignoring
# pylint: disable=C0302

import os
import re
import sys
import argparse
import ipaddress
import time
from collections import OrderedDict
import pydotplus
import jinja2


VERSION = "5.0.0"
VERBOSE = False


class NetworkNode(object):
    """Object that represents a specific node in the network.
    This is similar to a graphviz node.

    Many of the attributes that can be set for a node are captured
    as instance variables. Anything not explicitly managed can be
    accessed through "other_attributes".

    In general, anything that does not require additional processing
    or error checking can be managed through other_attributes.

    Attributes:
        config - The config file the node will use
        function - Function of the device
        has_pxe_interface - Bool. Does this device have a PXE interface?
        hostname - The hostname of the device
        interfaces - A dict of {"interface name": NetworkInterface()} for
            all interfaces associated with this node
        legacy - The legacy flag to support older Vagrant box images
        libvirt_local_ip - The local Tunnel IP for libvirt. Ignored for vbox providers
        memory - The amount of memory of the node
        mgmt_ip - The management (eth0) IP of the device. Used for management network DHCP
        mgmt_mac - The mac address of the management interface, if it was created
        mgmt_interface - The string name of the management interface, if it was created
        os_version - An OS version to use for the device
        other_attributes - Dict of attributes
        playbook - Ansible playbook to run as a Vagrant provisioner
        ports - The ports the device will have, even without connections. command line option
        pxehost - Bool, is this a pxehost? Related to, but not the same as has_pxe_interface
        remap - Bool, is the Vagrant remap option used?
        ssh_port - A non-standard Vagrant SSH port
        vagrant_interface - A non-standard Vagrant interface name
        vagrant_user - A non-standard Vagrant username
        vm_os - Box image name
    """

    # R0902: Too many instance attributes.
    # R0913: Too many arguments
    # R0912: Too many branches
    # R0915: Too many statements
    # pylint: disable=R0902,R0913,R0912,R0915
    def __init__(self, hostname, function, vm_os=None, memory=None,
                 config=None, os_version=None,
                 other_attributes=None, libvirt_local_ip="127.0.0.1"):

        # define default parameters for known functions.
        # all will be overridden by any provided attributes.
        defaults = {
            "fake": {
                "os": "None",
                "memory": "1"
            },
            "oob-server": {
                "os": "yk0/ubuntu-xenial",
                "memory": "512",
                "config": "./helper_scripts/auto_mgmt_network/oob_server_config_auto_mgmt.sh"
            },
            "oob-switch": {
                "os": "CumulusCommunity/cumulus-vx",
                "memory": "512",
                "config": "./helper_scripts/oob_switch_config.sh"
            },
            "host": {
                "os": "yk0/ubuntu-xenial",
                "memory": "512",
                "config": "./helper_scripts/extra_server_config.sh"
            },
            "pxehost": {
                "os": "yk0/ubuntu-xenial",
                "memory": "512",
                "config": "./helper_scripts/extra_server_config.sh"
            },
            "leaf": {
                "os": "cumuluscommunity/cumulus-vx",
                "memory": "768",
                "config": "./helper_scripts/extra_switch_config.sh"
            },
            "spine": {
                "os": "cumuluscommunity/cumulus-vx",
                "memory": "768",
                "config": "./helper_scripts/extra_switch_config.sh"
            },
            "nothing": {
                "os": "cumuluscommunity/cumulus-vx",
                "memory": "1",
                "config": "./helper_scripts/extra_switch_config.sh"
            }
        }

        # ensure the hostname is valid
        if self.check_hostname(hostname):
            self.hostname = hostname

        self.function = function

        # Set optional attribute defaults
        # If they are set, these values will be changed later
        self.pxehost = False
        self.playbook = False
        self.remap = True
        self.ports = False
        self.ssh_port = False
        self.vagrant_user = "vagrant"
        self.legacy = False
        self.vagrant_interface = "vagrant"
        self.libvirt_local_ip = libvirt_local_ip

        if VERBOSE:  # pragma: no cover
            print "Building NetworkNode " + self.hostname + ". Function set as " + self.function

        if other_attributes is None:
            if VERBOSE:  # pragma: no cover
                print "No other attributes found"
            self.other_attributes = dict()
        else:
            self.other_attributes = other_attributes

        self.mgmt_ip = self.get_node_mgmt_ip()
        self.mgmt_mac = None
        self.mgmt_interface = None

        # If the user set the mgmt IP on the oob switch, start to populate the bridge attribute
        # If they didn't set the mgmt IP this will be handled in the creation of the oob network
        # If they don't create an oob network, then we don't care about any of this.
        if self.mgmt_ip is not None and self.function == "oob-switch":
            self.mgmt_interface = "bridge"

        if "pxehost" in self.other_attributes:
            self.pxehost = self.other_attributes["pxehost"] == "True"
            if VERBOSE:  # pragma: no cover
                print "Pxehost set for " + self.hostname \
                    + ". Default OS assignment will be skipped"

        if self.function in defaults:
            if vm_os is None:
                vm_os = defaults[function]["os"]
                if VERBOSE:  # pragma: no cover
                    print "OS not found, using default of : " + vm_os

            if memory is None:
                memory = defaults[function]["memory"]
                if VERBOSE:  # pragma: no cover
                    print "No memory defined, using default of " + memory

            if config is None and function != "fake":
                config = defaults[function]["config"]
                if VERBOSE:  # pragma: no cover
                    print "No config defined, using default of " + config
                if not os.path.isfile(config):  # pragma: no cover
                    print_warning("Node \"" + hostname +
                                  " config file " + config + " does not exist")

        try:
            if int(memory) <= 0:
                print_error(
                    "Memory must be greater than 0mb on " + self.hostname)

        except (ValueError, TypeError):
            print_error("Memory value is invalid for " + self.hostname)

        if "playbook" in self.other_attributes:
            self.playbook = self.other_attributes["playbook"]
            if VERBOSE:  # pragma: no cover
                print "Found playbook " + self.playbook

        if "remap" in self.other_attributes:
            self.remap = self.other_attributes["remap"] == "True"
            if VERBOSE:  # pragma: no cover
                print "Remap found and set to " + str(self.remap)

        if "ports" in self.other_attributes:
            try:
                if int(self.other_attributes["ports"]) <= 0:
                    print_error("Ports value " + self.hostname +
                                " must be greater than 0")
            except(ValueError, TypeError):
                print_error("Ports value is invalid for " + self.hostname)

            self.ports = self.other_attributes["ports"]
            if VERBOSE:  # pragma: no cover
                print "Ports " + self.ports + " defined on " + self.hostname

        if "ssh_port" in self.other_attributes:
            try:
                if int(self.other_attributes["ssh_port"]) <= 1024:
                    print_error("SSH port value for " +
                                self.hostname + " must be greater than 1024")
            except(ValueError, TypeError):
                print_error("SSH port value is invalid for " + self.hostname)

            self.ssh_port = self.other_attributes["ssh_port"]
            if VERBOSE:  # pragma: no cover
                print "SSH port " + self.ssh_port + " defined on " + self.hostname

        if "vagrant" in self.other_attributes:
            self.vagrant_interface = self.other_attributes["vagrant"]
            if VERBOSE:  # pragma: no cover
                print "Vagrant interface " + self.vagrant_interface + " defined on " + self.hostname

        if "vagrant_user" in self.other_attributes:
            self.vagrant_user = self.other_attributes["vagrant_user"]
            if VERBOSE:  # pragma: no cover
                print "Vagrant user " + self.vagrant_user + " defined on " + self.hostname

        if "legacy" in self.other_attributes:
            self.legacy = self.other_attributes["legacy"] == "True"
            if VERBOSE:  # pragma: no cover
                print "Legacy flag set to " + self.legacy + " on " + self.hostname

        self.vm_os = vm_os
        self.memory = memory
        self.config = config
        self.interfaces = {}
        self.os_version = os_version
        self.has_pxe_interface = False

    def get_node_mgmt_ip(self):
        """Determine the management IP and return it as an IPInterface object.
        """

        # If the user builds their own management network we will not
        # create the bridge attribute or assign a mac/ip to it
        # If they define the management IP on the oob-switch
        # create the bridge attribute and populate the IP
        # The mac will be populated when it's added to the inventory
        # since the inventory tracks/owns the mac pool.
        if "mgmt_ip" in self.other_attributes:
            try:
                # Check if there is a mask on the mgmt_ip attribute
                # or assume /24
                if self.other_attributes["mgmt_ip"].find("/") < 0:
                    if VERBOSE:  # pragma: no cover
                        print "Management IP " + self.other_attributes["mgmt_ip"]\
                            + " found on " + self.hostname + " without mask. Assuming /24"
                    return ipaddress.ip_interface(unicode(self.other_attributes["mgmt_ip"] + "/24"))
                else:
                    if VERBOSE:  # pragma: no cover
                        print "Management IP " + self.other_attributes["mgmt_ip"]\
                            + " found on " + self.hostname
                    return ipaddress.ip_interface(unicode(self.other_attributes["mgmt_ip"]))

            except Exception:  # pylint: disable=W0703
                print_error("Management IP address on " +
                            self.hostname + " is invalid")

        # If the management IP wasn't set on the OOB switch
        # populate the "bridge" attribute
        elif self.function == "oob-switch":
            self.mgmt_interface = "bridge"

        return None

    @staticmethod
    def check_hostname(hostname):
        """Simple hostname validation.
        Using rules described in wikipedia article
        https://en.wikipedia.org/wiki/Hostname#Restrictions_on_valid_hostnames
        """

        # contain only the ASCII letters 'a' through 'z' (in a case-insensitive manner),
        # the digits '0' through '9', and the minus sign ('-').
        # The original specification of hostnames in RFC 952, mandated that labels could not
        # start with a digit or with a minus sign, and must not end with a minus sign.
        # However, a subsequent specification (RFC 1123) permitted hostname labels to start
        # with digits. No other symbols, punctuation characters, or white space are permitted.
        # While a hostname may not contain other characters, such as the underscore character (_)

        if len(hostname.strip()) <= 0:
            print_error("Node name is blank")

        # Hostname can only start with a letter or number
        if not re.compile('[A-Za-z0-9]').match(hostname[0]):
            print_error("Node name can only start with letters or numbers "\
                        + hostname + " is not valid!")

        # Hostname can not end with a dash
        if not re.compile('[A-Za-z0-9]').match(hostname[-1]):
            print_error("Node name can only end with letters or numbers "\
                        + hostname + " is not valid!")

        # Hostname can only contain A-Z, 0-9 and "-"
        if not re.compile('^[A-Za-z0-9\-]+$').match(hostname):  # pylint: disable=W1401
            print_error("Node name can only contain letters numbers and dash(-) "\
                        + hostname + " is not valid!")

        return True

    def get_interface(self, interface_name):
        """Returns the specificed NetworkInterface object for a given interface name.
        If the interface does not exist, returns None
        """
        if interface_name in self.interfaces:
            return self.interfaces[interface_name]

        return None

    def add_interface(self, network_interface):
        """Adds a NetworkInterface object to the interface collection.
        Returns the updated NetworkNode object.
        """

        # Check if any interface in this node is a pxe interface
        # and make sure there isn't a second interface
        # trying to be a pxe interface.
        if self.has_pxe_interface and network_interface.pxe_priority > 0:
            print_error(" Device " + self.hostname +
                        " sets pxebootinterface more than once.")

        # If this is the first time we've seen a pxe interface
        # then flip the flag on the Node
        elif network_interface.pxe_priority > 0:
            self.has_pxe_interface = True

        self.interfaces[network_interface.interface_name] = network_interface

        return self

    def __str__(self):
        """
        >> DEVICE: server03
        code: yk0/ubuntu-xenial
        memory: 512
        function: host
        mgmt_ip: 192.168.200.11
        hostname: server03
        tunnel_ip: 127.0.0.1
        config: ./helper_scripts/extra_server_config.sh
        LINK: eth0
                remote_port: 10028
                local_ip: 127.0.0.1
                local_port: 11028
                mac: 44:38:39:00:00:32
                remote_device: oob-mgmt-switch
                remote_interface: swp11
                remote_ip: 127.0.0.1"""

        # Try and guess what the provider is.
        # If the remote port is set, it's libvirt
        # Otherwise (no interfaces exist, or not set), it's the default virtualbox
        provider = "virtualbox"
        try:
            if self.interfaces.itervalues().next().remote_port is not None:
                provider = "libvirt"
        except StopIteration:
            provider = "virtualbox"

        output = []
        output.append(self.hostname)
        output.append("code: " + str(self.vm_os))
        output.append("memory: " + str(self.memory))
        output.append("function: " + str(self.function))
        output.append("mgmt_ip: " + str(self.mgmt_ip))
        for interface in self.interfaces:
            output.append("\t" + str(self.interfaces[interface].interface_name))
            if provider == "libvirt":
                output.append("\t\tlibvirt local tunnel IP: " + str(self.libvirt_local_ip))

                output.append("\t\t" + "local_port: " +
                              str(self.interfaces[interface].local_port))

                output.append("\t\t" + "remote_ip: " +
                              str(self.interfaces[interface].libvirt_remote_ip))

                output.append("\t\t" + "remote_port: " +
                              str(self.interfaces[interface].remote_port))
            else:
                output.append("\t\t" + "network: " + str(self.interfaces[interface].network))

            if self.interfaces[interface].mac is not None:
                mac = self.interfaces[interface].mac.replace("0x", "")
                output.append("\t\t" + "mac: " + str(format_mac(mac.zfill(12))))
            else:
                output.append("\t\tmac: None")

        return "\n".join(output)


class NetworkInterface(object):
    """A NetworkInterface is a single interface that can be attached
    to a NetworkNode and is part of a NetworkEdge.

    A NetworkInterface should belong to exactly one NetworkNode,
    exactly once.

    The NetworkInterface is a unique object as a way to track the
    attributes that are unique/specific to that NetworkInterface.

    Note, that NetworkInterface is for a physical interface that
    would be part of the virtual topology within the environment.
    This means a bridge or loopback can not be a NetworkInterface object.

    Attributes:
    hostname - the hostname that this interface is attached to
    interface_name - the name of the interface
    mac - the MAC address of the interface
    ip - the IP address of the interface
    network - for Virtualbox only, the network name the interface belongs to
    local_port - for Libvirt only, the libvirt local_port
    remote_port - for Libvirt only, the libvirt remote_port
    """
    # pylint: disable=R0902, R0913

    def __init__(self, hostname, interface_name, mac=None, ip=None,
                 network=None, local_port=None, remote_port=None):
        self.hostname = hostname
        self.interface_name = self.remove_interface_slash(interface_name)
        self.ip = ip  # pylint: disable=C0103
        self.mac = self.validate_mac(mac)
        self.network = network
        self.local_port = local_port
        self.remote_port = remote_port
        self.attributes = {}
        self.pxe_priority = 0
        self.remote_hostname = None
        self.remote_interface = None
        self.libvirt_remote_ip = None

    def remove_interface_slash(self, interface_name):
        """Remove a / character from an interface name and
        replace it with "-" i.e., g0/0 becomes g0-0
        """
        if "/" in interface_name:
            new_interface = interface_name.replace('/', '-')
            print_warning("Device " + str(self.hostname) + " interface"
                          " " + str(interface_name) + " contains a slash"
                          " and will be convereted to " + str(new_interface))

            return new_interface

        return interface_name

    def add_attribute(self, attribute):
        """Add an attribute dict to the existing attributes dict
        """
        self.attributes.update(attribute)

    def validate_mac(self, mac):
        """Validate that the input MAC address is valid.
        This includes filtering out things like broadcast,
        multicast and all zero mac
        """
        if mac is None:
            return None

        mac = mac.replace(":", "")
        mac = mac.replace(".", "")
        mac = mac.strip().lower()

        if len(mac) > 12:
            print_error(self.hostname + " MAC " + mac + " is too long")

        if len(mac) < 12:
            print_error(self.hostname + " MAC " + mac + " is too short")

        try:
            int(mac, 16)

        except Exception:  # pylint: disable=W0703
            print_error(self.hostname + " MAC " + mac + " could not be converted to hex. "
                        + "Perhaps there are bad characters?")

        # Broadcast
        if mac == "ffffffffffff":
            print_error(self.hostname + " MAC " +
                        mac + " is a broadcast address")

        # Invalid
        if mac == "000000000000":
            print_error(self.hostname + " MAC " + mac +
                        " is an invalid all zero MAC")

        # Multicast
        if mac[:6] == "01005e":
            print_error(self.hostname + " MAC " + mac + " is a multicast MAC")

        return hex(int(mac, 16))


# pylint: disable=R0903
# Too few public methods.
class NetworkEdge(object):
    """A network edge is a collection of two NetworkInterface objects that share a link.
    This is a simple object to make accessing the interfaces easier.
    """

    def __init__(self, left_side, right_side):
        self.left_side = left_side
        self.right_side = right_side

        # Set the remote port information in the interfaces
        self.right_side.remote_hostname = self.left_side.hostname
        self.right_side.remote_interface = self.left_side.interface_name
        self.left_side.hostname = self.right_side.remote_hostname
        self.left_side.interface_name = self.right_side.remote_interface


class Inventory(object):
    """An Inventory represents the entire network, with all nodes and edges.
    The Inventory contains everything in the environment. All links, hosts, attributes, etc.

    The Inventory object is the final datastructure representing the dot file.
    """

    # pylint: disable=R0902
    # Too many instance attributes.
    def __init__(self, provider="virtualbox", current_libvirt_port=1025, libvirt_gap=8000):
        self.parsed_topology = None
        self.provider = provider
        self.node_collection = dict()
        self.mac_set = set()
        self.provider_offset = 1
        self.current_libvirt_port = current_libvirt_port
        self.libvirt_gap = libvirt_gap
        # current_mac default is based on Cumulus Networks mac range
        # https://support.cumulusnetworks.com/hc/en-us/articles/203837076-Reserved-MAC-Address-Range-for-Use-with-Cumulus-Linux
        self.current_mac = "0x443839000000"
        self.oob_server = None
        self.oob_switch = None
        self.mgmt_ips = set()  # This is the set of management IPs in the network
        # this is used to prevent duplicates.
        # all of the elements should be of type ipaddress.ip_interface
        # ip_interface objects are in CIDR notation (10.1.1.1/24)
        # By default if no mask is provided it will create a /32, which isn't what we want.
        self.create_mgmt_device = False

    def calculate_memory(self):
        """Look at all nodes in the Inventory
        and return the total memory they will consume
        """
        total_memory = 0

        for node in self.node_collection.itervalues():
            total_memory += int(node.memory)

        return total_memory

    def add_node(self, node):
        """Add a NetworkNode to the inventory. Returns the updated inventory
        """
        if self.provider == "libvirt":
            unsupported_images = ["boxcutter/ubuntu1604",
                                  "bento/ubuntu-16.04",
                                  "ubuntu/xenial64"]

            # There are some OS images we know do not work
            # Prevent them from being loaded.
            if node.vm_os in unsupported_images:
                print_error("Incompatible libvirt OS on " + node.hostname
                            + "\tDo not attempt to use a mutated image"
                            + " for Ubuntu16.04 on Libvirt"
                            + "\tuse an ubuntu1604 image which is natively built for libvirt"
                            + "\tlike yk0/ubuntu-xenial."
                            + "\tSee https://github.com/CumulusNetworks/topology_converter/tree/master/documentation#vagrant-box-selection"  # pylint: disable=C0301
                            + "\tSee https://github.com/vagrant-libvirt/vagrant-libvirt/issues/607"
                            + "\tSee https://github.com/vagrant-libvirt/vagrant-libvirt/issues/609")

        # Identify the oob switch and server if they exist.
        if node.function == "oob-server":
            self.oob_server = node
            if VERBOSE:  # pragma: no cover
                print "Found OOB Server " + node.hostname

        elif node.function == "oob-switch":
            bridge_mac = self.get_mac()

            # Bridge attribute would have been set when the node was
            # created with a management IP.
            node.mgmt_mac = bridge_mac

            self.oob_switch = node
            if VERBOSE:  # pragma: no cover
                print "Found OOB Switch " + node.nosthame

        # Don't allow something to be called "oob-mgmt-server"
        # if it isn't the oob-mgmt-server.
        # This could be made an option check, but is to prevent annoying
        # problems if you forget to set the function.
        if node.hostname == "oob-mgmt-server" and self.oob_server is None:
            print_error(
                "The node namded oob-mgmt-server must be set to function = \"oob-server\"")

        # Same rules for the oob-mgmt-switch as above for the oob-mgmt-server.
        if node.hostname == "oob-mgmt-switch" and self.oob_switch is None:
            print_error(
                "The node named oob-mgmt-switch must be set to function = \"oob-switch\"")

        if node.mgmt_ip is not None and node.mgmt_ip in self.mgmt_ips:
            print_error("Management IP address on " + node.hostname
                        + " is already in use. Likely it matches another static IP")
        else:
            self.mgmt_ips.add(node.mgmt_ip)

        self.node_collection[node.hostname] = node

        if VERBOSE:  # pragma: no cover
            print "Added " + node.hostname + " to inventory"

        return self

    def get_node_by_name(self, node_name):
        """Return a specific NetworkNode() in the inventory by it's name.
        If the node can not be found None is returned.
        """
        if node_name not in self.node_collection:
            return None

        return self.node_collection[node_name]

    def add_edge(self, network_edge):
        """Add a NetworkEdge to the inventory and links the
        edge to the associated NetworkNode objects.
        This assumes the NetworkNode objects have already been added to the inventory.
        This expectes a NetworkEdge() object and returns the updated inventory.

        Keyword Arguments:
        network_edge - a NetworkEdge object
        """

        for side in [network_edge.left_side, network_edge.right_side]:

            if self.get_node_by_name(side.hostname) is None:
                print_error("Host " + side.hostname + " has a connection "
                            + "but was never defined as a node")

            # Check if the interface has already been used.
            # Multiaccess interfaces are not supported.
            if self.get_node_by_name(side.hostname).get_interface(side.interface_name) is not None:
                print_error("Interface " + side.interface_name +
                            " already used on device " + side.hostname)

            else:

                # Get a MAC address for the interface, if it doesn't already have one
                if side.mac is None:
                    side.mac = self.get_mac()
                    if VERBOSE:  # pragma: no cover
                        print "Interface " + side.interface_name + " on " + side.hostname\
                              + " assigned MAC " + side.mac

        left_node = self.get_node_by_name(network_edge.left_side.hostname)
        right_node = self.get_node_by_name(network_edge.right_side.hostname)

        # Build the network links for virtualbox
        if self.provider == "virtualbox":
            network_edge.left_side.network = "network" + \
                str(self.provider_offset)
            network_edge.right_side.network = "network" + \
                str(self.provider_offset)
            if VERBOSE:  # pragma: no cover
                print network_edge.left_side.hostname + ":"\
                    + network_edge.left_side.interface_name + " -- "\
                    + network_edge.right_side.hostname + ":"\
                    + network_edge.right_side.interface_name + " assigned offset "\
                    + self.provider_offset

            self.provider_offset += 1

        # Build the local and remote ports for libvirt
        if self.provider == "libvirt":
            if self.current_libvirt_port > self.libvirt_gap:
                print_error("Configured Port_Gap: (" + str(self.libvirt_gap) + ") "
                            "exceeds the number of links in the topology. "
                            "Read the help options to fix.\n\n")

            network_edge.left_side.local_port = str(self.current_libvirt_port)
            network_edge.left_side.remote_port = str(
                self.current_libvirt_port + self.libvirt_gap)

            network_edge.right_side.local_port = str(
                self.current_libvirt_port + self.libvirt_gap)
            network_edge.right_side.remote_port = str(
                self.current_libvirt_port)

            if VERBOSE:  # pragma: no cover
                print network_edge.left_side.hostname + ":" + network_edge.left_side.interface_name\
                    + " local port: " + network_edge.left_side.local_port\
                      + " remote port: " + network_edge.left_side.remote_port
                print network_edge.right_side.hostname + ":"\
                    + network_edge.right_side.interface_name\
                    + " local port: " + network_edge.right_side.local_port\
                    + " remote port: " + network_edge.right_side.remote_port

            self.current_libvirt_port += 1

            network_edge.left_side.libvirt_remote_ip = right_node.libvirt_local_ip
            network_edge.right_side.libvirt_remote_ip = left_node.libvirt_local_ip

        network_edge.left_side.remote_hostname = network_edge.right_side.hostname
        network_edge.left_side.remote_interface = network_edge.right_side.interface_name

        network_edge.right_side.remote_hostname = network_edge.left_side.hostname
        network_edge.right_side.remote_interface = network_edge.left_side.interface_name

        left_node.add_interface(network_edge.left_side)
        right_node.add_interface(network_edge.right_side)

        # If we are connecting to the oob switch, set the mgmt_interface value for that node
        if left_node.hostname == "oob-mgmt-switch" or left_node.function == "oob-switch":
            right_node.mgmt_interface = network_edge.right_side.interface_name
            right_node.mgmt_mac = network_edge.right_side.mac

        if right_node.hostname == "oob-mgmt-switch" or right_node.function == "oob-switch":
            left_node.mgmt_interface = network_edge.left_side.interface_name
            left_node.mgmt_mac = network_edge.left_side.mac

        return self

    def get_mac(self):
        """Provides a unique mac address.

        Keyword Arguments:
        network_interface: the NetworkInterface() object to provide MAC addresses for
        """
        while self.current_mac in self.mac_set:
            # Hex is stored as strings in python
            # To add, we have to make it an int with base 16
            # But then this returns a base 10 int. wtf.
            # So we have to cast to hex() to get the 0x string back
            self.current_mac = hex(int(self.current_mac, 16) + 1)

        new_mac = self.current_mac
        self.mac_set.add(new_mac)

        self.current_mac = hex(int(self.current_mac, 16) + 1)

        return new_mac

    def add_parsed_topology(self, parsed_topology):
        """Provided with a ParseGraphvizTopology object which has
        been populated with a topology (nodes and edges).
        This will turn that collection of nodes and edges into an inventory
        """
        for node in parsed_topology.nodes:
            self.add_node(node)

        for edge in parsed_topology.edges:
            self.add_edge(edge)

        return self

    # R0912 - too many branches
    # R0915 - too many statements
    # R0914 - too many local variables
    def build_mgmt_network(self, create_mgmt_device=False):  # pylint: disable=R0912,R0915, R0914
        """Build a management network and add it to the inventory.
        This will create an oob-mgmt-switch and
        oob-mgmt-server NetworkNode if they do not exist and will
        attach every inventory device's eth0 interface to
        the oob-mgmt-server.
        If create_mgmt_device is True, the OOB server and switch will not be created
        and nothing will be attached to them.
        """

        self.create_mgmt_device = create_mgmt_device

        mgmt_switch_port_count = 1

        # Create an oob-server if the user didn't define one
        if self.oob_server is None:
            # If the OOB server isn't created we need a management IP to
            # base the rest of the network off of.
            # So enforce that the OOB server is 192.168.200.254/24
            # If the user wants something else or a larger subnet,
            # then they need to manually create the
            # OOB server and set the mgmt IP and we can do the rest
            oob_server = NetworkNode(hostname="oob-mgmt-server", function="oob-server",
                                     other_attributes={"mgmt_ip": "192.168.200.254/24"})
            self.add_node(oob_server)
            if VERBOSE:  # pragma: no cover
                print "No oob-server found, one has been created"
        else:
            oob_server = self.oob_server
            if self.oob_server.mgmt_ip is None:
                self.oob_server.mgmt_ip = ipaddress.ip_interface(
                    u'192.168.200.254/24')
                self.mgmt_ips.add(self.oob_server.mgmt_ip)

            if "eth1" in self.oob_server.interfaces and not create_mgmt_device:
                print_error("eth1 detected on OOB Server while trying to auto-build mgmt network."
                            + " Did you manually build the management network in the topology?")

        # Define the DHCP Pool settings based on the OOB IP
        # If the default IP is used, the pool will start at 192.168.200.10
        # And be of size 244. This is 256 in a /24, -2 for the network/broadcast
        # -10 for the starting offset.
        #
        # Otherwise, let's dynamically size based on the provided OOB IP
        # This allows for much larger dynamic pools if required
        dhcp_pool_size = (self.oob_server.mgmt_ip.network.num_addresses - 2)
        current_lease = 1

        if dhcp_pool_size <= 3:
            # /29 gives 6 usable hosts, allowing for oob server, switch and hosts
            print_error("OOB Server subnet is too small for a valid DHCP pool."
                        + " Minimum subnet mask is /29")

        # Everything is stored as ipaddress.IPInterface (in CIDR)
        # the .network[current_lease] returns an IPAddress without a mask
        oob_server_mask = "/" + \
            str(self.oob_server.mgmt_ip)[
                str(self.oob_server.mgmt_ip).find("/") + 1:]

        # Create an oob-switch if the user didn't define one
        if self.oob_switch is None:
            if create_mgmt_device:
                print_error("OOB Management Switch was not found in the topology."
                            + " Management switch must be manually defined for "
                            + "'create-management-device option")

            self.add_node(NetworkNode(
                hostname="oob-mgmt-switch", function="oob-switch"))

            if VERBOSE:  # pragma: no cover
                print "No oob-switch found, one has been created"

        # The management switch is a bit special
        # it's the only device with a logical management interface
        # as a result, we are going to put the IP and MAC in oob-mgmt-switch Node's attributes
        # because we can't create an edge since it's not connected to anything.
        if self.oob_switch.mgmt_ip is None:

            candidate_lease = str(
                self.oob_server.mgmt_ip.network[current_lease])
            candidate_ip_object = ipaddress.ip_interface(
                unicode(candidate_lease + oob_server_mask))

            # Check if this IP is taken, if so, keep trying until we find the next free IP
            while candidate_ip_object in self.mgmt_ips:

                current_lease += 1
                candidate_lease = str(
                    self.oob_server.mgmt_ip.network[current_lease])
                candidate_ip_object = ipaddress.ip_interface(
                    unicode(candidate_lease + oob_server_mask))

            oob_switch_ip = candidate_ip_object

            self.oob_switch.mgmt_ip = oob_switch_ip
            self.mgmt_ips.add(oob_switch_ip)

            if VERBOSE:  # pragma: no cover
                print "OOB-Switch dynamically assigned IP " + self.oob_switch.mgmt_ip

        else:
            # Verify node_ip in subnet of oob-server ip
            if not self.oob_server.mgmt_ip.network == self.oob_switch.mgmt_ip.network:
                print_error("Management IP address on the OOB Switch"
                            + " is not in the same subnet as the OOB server."
                            + " OOB Server is configured for "
                            + str(self.oob_server.mgmt_ip) + ". "
                            + "OOB Switch is configured for "
                            + str(self.oob_switch.mgmt_ip))

        # Connect the oob server and switch
        # if cmd is set, they should already have defined this connection
        if not create_mgmt_device:
            mgmt_port = "swp" + str(mgmt_switch_port_count)
            self.add_edge(NetworkEdge(NetworkInterface(hostname=self.oob_server.hostname,
                                                       interface_name="eth1",
                                                       ip=str(self.oob_server.mgmt_ip)),
                                      NetworkInterface(hostname=self.oob_switch.hostname,
                                                       interface_name=mgmt_port)))
            self.oob_server.mgmt_interface = "eth1"

            if VERBOSE:  # pragma: no cover
                print "Management Link Added: "
                print self.oob_server.hostname + ":eth1 -- " + self.oob_switch.hostname + mgmt_port
                print ""

        for hostname, node_object in self.node_collection.iteritems():
            if hostname == "oob-mgmt-server" or hostname == "oob-mgmt-switch":
                continue

            # Increment the oob switch port count
            mgmt_switch_port_count += 1

            if node_object.mgmt_ip is not None:
                # Verify node_ip in subnet of oob-server ip
                if not self.oob_server.mgmt_ip.network == node_object.mgmt_ip.network:
                    print_error("Management IP address on " + node_object.hostname
                                + " is not in the same subnet as the OOB server."
                                + " OOB Server is configured for "
                                + str(self.oob_server.mgmt_ip) + ". "
                                + node_object.hostname + " is configured for "
                                + str(node_object.mgmt_ip))

                # If they set the CMD flag, assume they connected everything
                if create_mgmt_device:
                    continue

                mgmt_port = "swp" + str(mgmt_switch_port_count)
                self.add_edge(NetworkEdge(
                    NetworkInterface(hostname=hostname, interface_name="eth0",
                                     ip=str(node_object.mgmt_ip)),
                    NetworkInterface(hostname="oob-mgmt-switch",
                                     interface_name=mgmt_port)))
                node_object.mgmt_interface = "eth0"

            else:
                candidate_lease = str(
                    self.oob_server.mgmt_ip.network[current_lease])
                candidate_ip_object = ipaddress.ip_interface(
                    unicode(candidate_lease + oob_server_mask))

                # Check if this IP is taken, if so, keep trying until we find the next free IP
                while candidate_ip_object in self.mgmt_ips:
                    # If picking the next IP exceeds the pool, exit.
                    if current_lease + 1 > dhcp_pool_size:
                        print_error("Number of devices in management "
                                    + "network exceeds DCHP pool size ("
                                    + str(dhcp_pool_size) + ")")

                    current_lease += 1
                    candidate_lease = str(
                        self.oob_server.mgmt_ip.network[current_lease])
                    candidate_ip_object = ipaddress.ip_interface(
                        unicode(candidate_lease + oob_server_mask))

                if node_object.mgmt_interface is None:
                    self.add_edge(NetworkEdge(
                        NetworkInterface(hostname=hostname, interface_name="eth0",
                                         ip=str(candidate_ip_object)),
                        NetworkInterface(hostname="oob-mgmt-switch",
                                         interface_name="swp" + str(mgmt_switch_port_count))))
                    node_object.mgmt_interface = "eth0"

                node_object.mgmt_ip = candidate_ip_object
                self.mgmt_ips.add(candidate_ip_object)
                current_lease += 1

    def validate_eth0(self):
        """Ensures every device has an eth0 interface. Otherwise Switchd will bomb even on Vx.
        If a device does not have an eth0 interface, one will be created and connected to a
        special NOTHING NetworkNode
        """
        nothing_node = NetworkNode(hostname="NOTHING", function="nothing")
        self.add_node(nothing_node)
        nothing_interface_count = 0

        for node in self.node_collection.values():
            if node.get_interface("eth0") is None:
                nothing_interface = "eth" + str(nothing_interface_count)
                self.add_edge(NetworkEdge(NetworkInterface(hostname=node.hostname,
                                                           interface_name="eth0"),
                                          NetworkInterface(hostname=nothing_node.hostname,
                                                           interface_name=(nothing_interface))))
                nothing_interface_count += 1

# A class for this may not be the best thing,
# but seems easier than stand alone methods
class ParseGraphvizTopology(object):
    """Parses a graphviz dot file and creates an object with
    a list of NetworkNode and NetworkEdge objects
    """

    def __init__(self):

        self.topology_file = None
        self.nodes = list()
        self.edges = list()

    def parse_topology(self, topology_file):
        """
        Parse the provide graphviz topology object.

        Returns a NetworkInventory() object.
        """

        # Pass through simple linter first to identify easy problems
        self.lint_topology_file(topology_file)

        # Open the .dot file and parse with graphviz
        try:
            graphviz_topology = pydotplus.graphviz.graph_from_dot_file(
                topology_file)

        except Exception:  # pragma: no cover # pylint: disable=W0703
            # Two known ways to get here:
            # 1.) The file changed or was deleted between lint_topology_file() and graphviz call
            # 2.) lint topo file should be extended to handle missed failure.
            # as a result this isn't in coverage
            print_error("Cannot parse the provided topology.dot file (%s)\n"
                        + "There is probably a syntax error of some kind "
                        + "common causes include failing to close quotation "
                        + "marks and hidden characters from copy/pasting device"
                        + "names into the topology file.")
        try:
            graphviz_nodes = graphviz_topology.get_node_list()
            graphviz_edges = graphviz_topology.get_edge_list()

        except Exception as exception:  # pragma: no cover # pylint: disable=W0703
            # Like the previous exception
            # if this is hit, it's either a corner, like file change
            # or we need to expand the linter
            print exception
            print_error("There is a syntax error in your topology file."
                        + "Read the error output above for any clues as to the source.")

        for node in graphviz_nodes:
            self.nodes.append(self.create_node_from_graphviz(node))

        for edge in graphviz_edges:
            self.edges.append(self.create_edge_from_graphviz(edge))

        return self

    @staticmethod
    def lint_topology_file(topology_file):
        """Validate the contents of the .dot topology file

        This is a simple linter for dot files to help identify
        where file errors are. This is independent of the full
        .dot file parser provided by pydot.

        This will check for:
         - ASCII encoding
         - Balanced double quotes ("")
         - Balanced single quotes/ticks ('')
         - That "--" exists to denote each side of the link

        Keyword arguments:
        topology_file - an ASCII encoded text file representing the topology
        """
        try:
            with open(topology_file, "r") as topo_file:
                line_list = topo_file.readlines()
                count = 0

                for line in line_list:
                    count += 1
                    # Try to encode into ascii
                    try:
                        line.encode('ascii', 'ignore')

                    except UnicodeDecodeError:
                        print_error("Line " + str(count) + ":\n"
                                    + str(line) + "\n"
                                    + "Has hidden unicode characters in it which"
                                    + " prevent it from being converted to ASCII"
                                    + " Try manually typing it instead of copying and pasting.")

                    if line.count("\"") % 2 == 1:
                        print_error("Line " + str(count) + ": Has an odd"
                                    + " number of quotation characters \n"
                                    + str(line))

                    if line.count("'") % 2 == 1:
                        print_error("Line " + str(count) + ": Has an odd"
                                    + " number of quotation characters \n"
                                    + str(line))

                    if line.count(":") == 2:
                        if " -- " not in line:
                            print_error("Line " + str(count) + " does not"
                                        + "contain the required \" -- \" to"
                                        + " seperate a link")

        # W0703 - Exception too broad
        except Exception:  # pylint: disable=W0703
            print_error("Problem opening file, " +
                        topology_file + " perhaps it doesn't exist?")

        return True

    @staticmethod
    def create_edge_from_graphviz(graphviz_edge):
        """Take in a graphviz edge object and
        returns a new NetworkEdge object
        """

        left_hostname = graphviz_edge.get_source().split(":")[
            0].replace('"', '')
        left_interface = graphviz_edge.get_source().split(":")[
            1].replace('"', '')
        left_mac = graphviz_edge.get("left_mac")
        left_pxe = graphviz_edge.get("left_pxebootinterface")

        right_hostname = graphviz_edge.get_destination().split(":")[
            0].replace('"', '')
        right_interface = graphviz_edge.get_destination().split(":")[
            1].replace('"', '')
        right_mac = graphviz_edge.get("right_mac")
        right_pxe = graphviz_edge.get("right_pxebootinterface")

        if left_mac:
            left_mac = left_mac.replace('"', '')

        if right_mac:
            right_mac = right_mac.replace('"', '')

        left = NetworkInterface(hostname=left_hostname,
                                interface_name=left_interface, mac=left_mac)
        right = NetworkInterface(hostname=right_hostname,
                                 interface_name=right_interface, mac=right_mac)

        if left_pxe:
            left.pxe_priority = 1

        if right_pxe:
            right.pxe_priority = 1

        # Process passthrough attributes
        for attribute in graphviz_edge.get_attributes():
            value = graphviz_edge.get(attribute).strip("\"")

            # Since we already pulled out the mac, skip it
            if attribute == "left_mac" or attribute == "right_mac":
                continue

            if attribute.startswith('left_'):
                left.add_attribute({attribute[5:]: value})

            elif attribute.startswith('right_'):
                right.add_attribute({attribute[6:]: value})

            else:
                left.add_attribute({attribute: value})
                right.add_attribute({attribute: value})

        return NetworkEdge(left, right)

    @staticmethod
    def create_node_from_graphviz(graphviz_node):
        """Returns a NetworkNode object from a graphviz node object
        """
        hostname = graphviz_node.get_name().replace('"', '')

        # get_attributes() returns the list of settings at the top of the file
        # ex. {'function': '"spine"', 'config': '"./helper_scripts/config_switch.sh"',
        #      'version': '"3.4.3"', 'os': '"CumulusCommunity/cumulus-vx"', 'memory': '"768"'}
        #
        # all the graphviz object elements are wrapped in quotes.
        # Remember to remove them before processing
        graphviz_attributes = graphviz_node.get_attributes()

        vm_os = None
        os_version = None
        function = "unknown"
        memory = None
        config = None
        other_attributes = {}
        pxehost = False
        libvirt_ip = "127.0.0.1"

        for attribute_key in graphviz_attributes.keys():
            if attribute_key == "os":
                vm_os = graphviz_attributes["os"].replace("\"", "")

            elif attribute_key == "function":
                function = graphviz_attributes["function"].replace(
                    "\"", "").lower()

            elif attribute_key == "memory":
                memory = graphviz_attributes["memory"].replace("\"", "")

            elif attribute_key == "config":
                config = graphviz_attributes["config"].replace(
                    "\"", "").lower()

            elif attribute_key == "version":
                os_version = graphviz_attributes["version"].replace(
                    "\"", "").lower()

            # For any unhandled attributes, pass them through unmodified
            else:
                other_attributes.update({attribute_key.replace("\"", ""):
                                         graphviz_attributes[attribute_key].replace("\"", "")})

            if attribute_key == "pxehost":
                pxehost = True

            if attribute_key == "libvirt_ip":
                libvirt_ip = graphviz_attributes["libvirt_ip"].replace(
                    "\"", "").lower()

        # Verify that they provided an OS for devices that aren't pxehost
        if vm_os is None and not pxehost:
            print_error("OS not provided for " + hostname)

        return NetworkNode(hostname=hostname, function=function, vm_os=vm_os, memory=memory,
                           config=config, os_version=os_version, other_attributes=other_attributes,
                           libvirt_local_ip=libvirt_ip)


def parse_arguments():
    """ Parse command line arguments, and return a dict of values.
    """
    parser = argparse.ArgumentParser(description="Topology Converter -- Convert \
                                     topology.dot files into Vagrantfiles")

    parser.add_argument("topology_file",
                        help="provide a topology file as input")

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="enables verbose logging mode")

    parser.add_argument("-p", "--provider", choices=["libvirt", "virtualbox"], default="virtualbox",
                        help="specifies the provider to be used in the Vagrantfile, \
                        script supports 'virtualbox' or 'libvirt', default is virtualbox.")

    parser.add_argument("-a", "--ansible-hostfile", action="store_true",
                        help="When specified, ansible hostfile will be generated \
                        from a dummy playbook run.")

    parser.add_argument("-c", "--create-mgmt-network", action="store_true",
                        help="When specified, a mgmt switch and server will be created. \
                        The default assumes a /24 subnet. If the mgmt_ip is set on the \
                        OOB server, it will be used to define the DHCP pool for the network.\
                        Any node specific mgmt_ip settings will override the OOB server pool.")

    parser.add_argument("-cco", "--create-mgmt-configs-only", action="store_true",
                        help="Calling this option does NOT regenerate the Vagrantfile \
                        but it DOES regenerate the configuration files that come \
                        packaged with the mgmt-server in the '-c' option. This option \
                        is typically used after the '-c' has been called to generate \
                        a Vagrantfile with an oob-mgmt-server and oob-mgmt-switch to \
                        modify the configuration files placed on the oob-mgmt-server \
                        device. Useful when you do not want to regenerate the \
                        vagrantfile but you do want to make changes to the \
                        OOB-mgmt-server configuration templates.")

    parser.add_argument("-cmd", "--create-mgmt-device", action="store_true",
                        help="Calling this option creates the mgmt device and runs the \
                        auto_mgmt_network template engine to load configurations on to \
                        the mgmt device but it does not create the OOB-MGMT-SWITCH or \
                        associated connections. Useful when you are manually specifying \
                        the construction of the management network but still want to have \
                        the OOB-mgmt-server created automatically.")

    parser.add_argument("-t", "--template", action="append", nargs=2,
                        help="Specify an additional jinja2 template and a destination \
                        for that file to be rendered to.")

    parser.add_argument("-s", "--start-port", type=int, default=8000,
                        help="FOR LIBVIRT PROVIDER: this option overrides \
                        the default starting-port 8000 with a new value. \
                        Use ports over 1024 to avoid permissions issues. If using \
                        this option with the virtualbox provider it will be ignored.")

    parser.add_argument("-g", "--port-gap", type=int, default=1000,
                        help="FOR LIBVIRT PROVIDER: this option overrides the \
                        default port-gap of 1000 with a new value. This number \
                        is added to the start-port value to determine the port \
                        to be used by the remote-side. Port-gap also defines the \
                        max number of links that can exist in the topology. EX. \
                        If start-port is 8000 and port-gap is 1000 the first link \
                        will use ports 8001 and 9001 for the construction of the \
                        UDP tunnel. If using this option with the virtualbox \
                        provider it will be ignored.")

    parser.add_argument("-dd", "--display-datastructures", action="store_true",
                        help="When specified, the datastructures which are passed \
                        to the template are displayed to screen. Note: Using \
                        this option does not write a Vagrantfile and \
                        supercedes other options.")

    parser.add_argument("--synced-folder", action="store_true",
                        help="Using this option enables the default Vagrant \
                        synced folder which we disable by default. \
                        See: https://www.vagrantup.com/docs/synced-folders/basic_usage.html")

    parser.add_argument("--version", action="version", version="Topology \
                        Converter version is v%s" % VERSION,
                        help="Using this option displays the version of Topology Converter")

    parser.add_argument("--vagrantfile", default="Vagrantfile",
                        help="Define a customer file to output instead of 'Vagrantfile'")

    parser.add_argument("-m", "--memory", action="store_true",
                        help="Display the estimated topology memory requirements and exits \
                         This supports the -c option and will include the management \
                         network in the memory output")

    return parser


def check_files(cli_args, vagrant_template):
    """Verify that all required files can be opened.
    This includes the template file based by the command line
    and the default vagrantfile .j2 jinja template
    """

    if cli_args.template:
        custom_template = str(cli_args.template[0][0])
        if not os.path.isfile(custom_template):
            print_error("Provided template file-- \""
                        + custom_template + "\" does not exist!")

    if not os.path.isfile(vagrant_template):
        print_error("Default Vagrant Template \"" +
                    vagrant_template + "\" does not exist!")

    return True


def format_mac(mac_address):
    """Take in a mac address string like 00a22345feff0012
    and return a mac formatted as 00:a2:23:45:fe:ff:00:12
    """
    return ':'.join(map(''.join, zip(*[iter(mac_address)] * 2)))


def get_plural(input_string):
    """ Adds an "e" to English words that need to end in '-es'
    """
    es_plural_suffix = ["ss", "sh", "ch", "x", "z", "s"]

    if input_string[-2:] in es_plural_suffix or input_string[-1:] in es_plural_suffix:
        return input_string + "e"

    return input_string


def render_ansible_hostfile(inventory, topology_file, input_dir):
    """Provides the logic to build an ansible hosts file from a jinja2 template
    """
    if VERBOSE:  # pragma: no cover
        print "Generating ansible hosts file"
    hostfile_template = os.path.join(input_dir, "ansible_hostfile.j2")

    # the variables that will be passed to the template
    jinja_variables = {"version": VERSION, "topology": topology_file}

    node_dict = {}

    for node in inventory.node_collection.itervalues():
        # Don't do anything for fake devices
        if node.function == "fake":
            continue

        ansible_function = node.function
        if node.mgmt_ip is not None:
            node_mgmt_ip = str(node.mgmt_ip)[:str(node.mgmt_ip).find("/")]
        else:
            node_mgmt_ip = None


        # If the plural of the word is "es" then
        # add an e for when the jinja template adds an "s"
        # For examples, switches
        ansible_function = get_plural(node.function)

        if ansible_function in node_dict:
            node_dict[ansible_function].append({"hostname": node.hostname, "mgmt_ip": node_mgmt_ip})
        else:
            node_dict[ansible_function] = [{"hostname": node.hostname, "mgmt_ip": node_mgmt_ip}]

    jinja_variables["node_dict"] = node_dict
    template = jinja2.Template(open(hostfile_template).read())

    return template.render(jinja_variables)


def render_dhcpd_conf(inventory, topology_file, input_dir):
    """Generate a dhcpd.conf output based on the inventory using the jinja2 template
    """

    dhcpd_conf_template = os.path.join(input_dir, "dhcpd.conf.j2")

    jinja_variables = {"version": VERSION, "topology": topology_file}

    # we wouldn't be building this if the oob-mgmt-server doesn't exist
    oob_server = inventory.oob_server

    # but check just in case
    if oob_server is None:
        print_error(
            "Something went wrong, no OOB Server exists. Failed to build dhcpd.conf")


    jinja_variables["dhcp_subnet"] = str(oob_server.mgmt_ip.network.network_address)
    jinja_variables["dhcp_netmask"] = str(oob_server.mgmt_ip.netmask)
    jinja_variables["oob_server_ip"] = str(oob_server.mgmt_ip.ip)

    jinja_variables["dhcp_start"] = str(oob_server.mgmt_ip.network.network_address + 1)
    jinja_variables["dhcp_end"] = str(oob_server.mgmt_ip.network.broadcast_address - 1)

    template = jinja2.Template(open(dhcpd_conf_template).read())

    return template.render(jinja_variables)


def render_dhcpd_hosts(inventory, topology_file, input_dir):
    """Generate the contents of a dhcpd.hosts static DHCP binding file
    based on a jinja2 template
    """
    dhcpd_hosts_template = os.path.join(input_dir, "dhcpd.hosts.j2")

    # the variables that will be passed to the template
    jinja_variables = {"version": VERSION, "topology": topology_file}

    # we wouldn't be building this if the oob-mgmt-server doesn't exist
    oob_server = inventory.oob_server

    # but check just in case
    if oob_server is None:
        print_error(
            "Something went wrong, no OOB Server exists. Failed to build dhcpd.hosts")

    jinja_variables["oob_server_ip"] = str(oob_server.mgmt_ip).split("/")[0]

    node_dict = {}

    for node in inventory.node_collection.itervalues():
        # Don't do anything for fake devices
        if node.function == "fake":
            continue

        # OOB Mgmt Server doesn't use DHCP
        if node.function == "oob-server":
            continue

        # The mac is stored as 0x...., send the substring without the 0x part to be formatted
        mac_address = format_mac(node.mgmt_mac[2:].zfill(12))
        node_dict[node.hostname] = {
            "mac": mac_address, "ip": node.mgmt_ip}

        if "ztp" in node.other_attributes:
            node_dict[node.hostname]["ztp"] = node.other_attributes["ztp"]
        else:
            if node.function in ("leaf", "spine", "oob-switch"):
                node_dict[node.hostname]["ztp"] = "ztp_oob.sh"

    jinja_variables["node_dict"] = node_dict
    template = jinja2.Template(open(dhcpd_hosts_template).read())

    return template.render(jinja_variables)


def render_hosts_file(inventory, topology_file, input_dir):
    """Generate the contents of a hosts static DNS lookup file
    based on a jinja2 template
    """
    dns_hosts = os.path.join(input_dir, "hosts.j2")

    # the variables that will be passed to the template
    jinja_variables = {"version": VERSION, "topology": topology_file}

    # we wouldn't be building this if the oob-mgmt-server doesn't exist
    oob_server = inventory.oob_server

    # but check just in case
    if oob_server is None:
        print_error(
            "Something went wrong, no OOB Server exists. Failed to build DNS hosts")

    jinja_variables["oob_server_ip"] = str(oob_server.mgmt_ip).split("/")[0]
    jinja_variables["oob_hostname"] = oob_server.hostname

    node_dict = {}

    for node in inventory.node_collection.itervalues():

        # We already have what we need for the oob server
        if node.function == "oob-server":
            continue

        # Don't do anything for fake devices
        if node.function == "fake":
            continue


        node_dict[node.hostname] = {"ip": str(node.mgmt_ip).split("/")[0]}

    jinja_variables["node_dict"] = node_dict
    template = jinja2.Template(open(dns_hosts).read())

    return template.render(jinja_variables)


def render_oob_server_sh(inventory, topology_file, input_dir):
    """Generate the contents of the oob server config.sh
    file based on a jinja2 template
    """
    oob_config = os.path.join(input_dir, "oob_server_config_auto_mgmt.sh.j2")

    # the variables that will be passed to the template
    jinja_variables = {"version": VERSION, "topology": topology_file}

    # we wouldn't be building this if the oob-mgmt-server doesn't exist
    oob_server = inventory.oob_server

    # but check just in case
    if oob_server is None:
        print_error("Something went wrong, no OOB Server exists. Failed to build"
                    + "oob_server_config_auto_mgmt.sh")

    jinja_variables["oob_server_ip"] = str(oob_server.mgmt_ip).split("/")[0]
    jinja_variables["oob_cidr"] = str(oob_server.mgmt_ip)

    if "ntp" in oob_server.other_attributes:
        jinja_variables["oob"] = {"ntp": oob_server.other_attributes["ntp"]}
    else:
        jinja_variables["oob"] = {"ntp": "pool.ntp.org"}

    if oob_server.vagrant_interface is not None:
        jinja_variables["vagrant_interface"] = oob_server.vagrant_interface

    template = jinja2.Template(open(oob_config).read())

    return template.render(jinja_variables)


def render_bridge_untagged(inventory, topology_file, input_dir):
    """Generate the untagged bridge interfaces config for the OOB server
    based on the bridge-untagged.j2 template
    """
    bridge_untagged_template = os.path.join(input_dir, "bridge-untagged.j2")

    jinja_variables = {"version": VERSION, "topology": topology_file}

    # we wouldn't be building this if the oob-mgmt-server doesn't exist
    oob_switch = inventory.oob_switch

    # but check just in case
    if oob_switch is None:
        print_error(
            "Something went wrong, no OOB Switch exists. \
            Failed to build switch interfaces configuration")

    jinja_variables["node"] = oob_switch
    jinja_variables["mgmt_ip"] = str(oob_switch.mgmt_ip.with_prefixlen)

    template = jinja2.Template(open(bridge_untagged_template).read())

    return template.render(jinja_variables)


def render_ztp_oob(inventory, topology_file, input_dir):
    """Generate the contents of the default ztp script
    based on a jinja2 template
    """
    oob_config = os.path.join(input_dir, "ztp_oob.sh.j2")

    # the variables that will be passed to the template
    jinja_variables = {"version": VERSION, "topology": topology_file}

    # we wouldn't be building this if the oob-mgmt-server doesn't exist
    oob_server = inventory.oob_server

    # but check just in case
    if oob_server is None:
        print_error(
            "Something went wrong, no OOB Server exists. Failed to build ztp_oob.sh")

    jinja_variables["oob_server_ip"] = str(oob_server.mgmt_ip).split("/")[0]

    template = jinja2.Template(open(oob_config).read())

    return template.render(jinja_variables)


def get_vagrantfile_variables(inventory, cli):  # pylint: disable=R0912
    """Generate the variables to pass to the Vagrantfile .j2 template.
    This is a unique function to make testing the Vagrantfile.j2 sub-templates easier.
    """
    # the variables that will be passed to the template
    jinja_variables = {"version": VERSION,
                       "topology": cli.topology_file, "cli_args": cli}

    # time.time() returns float 1518118901.04, the whole number is good enough
    jinja_variables["epoch_time"] = str(time.time()).split(".")[0]

    # Dict of all functions in the topology
    # key is the function
    # value is list of hostnames
    function_dict = {}

    # The functions we know about
    # oob-server, oob-switch, exit, superspine, spine, leaf, tor, host
    jinja_variables["known_functions"] = ["oob-server", "oob-switch", "exit", "superspine",
                                          "spine", "leaf", "tor", "host"]

    # Iterate over all of the nodes and organize them as a {function: [nodes]} dict
    for node in inventory.node_collection.itervalues():
        # Don't do anything for fake devices
        if node.function == "fake":
            continue

        # if we've seen this function before
        # append the hostname to the list
        if node.function in function_dict:
            function_dict[node.function].append(node)

        else:
            function_dict[node.function] = [node]

    # We need an ordered collection of the devices in the network
    # This allows us to bring up devices in a defined order.
    # oob-server, oob-switch, exit, superspine, spine, leaf, tor, host
    #
    # To do this, check if we have anything of that function from function_dict
    # if so, take the list of nodes with that function and put it in our OrderedDict
    node_dict = OrderedDict()

    if "oob-server" in function_dict:
        node_dict["oob-server"] = function_dict["oob-server"]

    if "oob-switch" in function_dict:
        node_dict["oob-switch"] = function_dict["oob-switch"]

    if "exit" in function_dict:
        node_dict["exit"] = function_dict["exit"]

    if "superspine" in function_dict:
        node_dict["superspine"] = function_dict["superspine"]

    if "spine" in function_dict:
        node_dict["spine"] = function_dict["spine"]

    if "leaf" in function_dict:
        node_dict["leaf"] = function_dict["leaf"]

    if "tor" in function_dict:
        node_dict["tor"] = function_dict["tor"]

    if "host" in function_dict:
        node_dict["host"] = function_dict["host"]

    # for any devices that we don't care about boot order
    # make sure we add them to the OrderedDict
    for function in function_dict:
        if function not in node_dict:
            node_dict[function] = function_dict[function]

    jinja_variables["nodes"] = node_dict
    return jinja_variables

# No Vagrantfile test cases. Most functions are covered by template tests
# But coverage for complete Vagrantfile would be a nice addition
def render_vagrantfile(inventory, input_dir, cli):  # pylint: disable=R0912
    """Renders a complete Vagrantfile from a jinja2 template
    """
    if cli.template:
        # [0] is the template
        # [1] is the file output location
        vagrant_template = cli.template[0][0]
    else:
        vagrant_template = "Vagrantfile.j2"

    jinja_variables = get_vagrantfile_variables(inventory, cli)
    jinja_variables["arguments"] = sys.argv[1:]
    # It's required to set the jinja2 environment
    # so that the {% include %} statements within the Vagrantfile.j2
    # template knows where to look.
    env = jinja2.Environment()
    env.loader = jinja2.FileSystemLoader(input_dir)

    # pass the format_mac() and get_plural() methods to jinja2 as a filter
    env.filters["format_mac"] = format_mac
    env.filters["get_plural"] = get_plural
    # Define the search path for Jinja Templates

    template = env.get_template(vagrant_template)

    return template.render(jinja_variables)


def write_file(location, contents):  # pragma: no cover
    """Writes contents to a file
    Keyword Arguments
    location - the path of the file to write
    contents - the string contents to write to the file
    """
    # No test cases. Needs to be mocked.
    try:
        with open(location, 'w') as output_file:
            output_file.write(contents)
    except:  # pylint: disable=W0702
        print_error("ERROR: Could not write file " + location)


def print_warning(warning_string):  # pragma: no cover
    """Format and print warning messages
    """
    warning_format = "\033[93m"
    bold_format = "\033[1m"
    endc = '\033[0m'
    print warning_format + bold_format + "    WARNING: " + warning_string + endc


def print_error(error_string):  # pragma: no cover
    """Format and print error messages.
    Also exit the program
    """
    error_format = "\033[91m"
    bold_format = "\033[1m"
    endc = '\033[0m'
    print error_format + bold_format + " ### ERROR -- " + error_string + endc
    exit(1)


def print_header(output_string):  # pragma: no cover
    """Format and print header messages
    """
    header_format = "\033[95m"

    print header_format + output_string


def print_blue(output_string):  # pragma: no cover
    """Print a string in blue
    """
    blue_format = "\033[94m"
    print blue_format + output_string


def print_green(output_string):  # pragma: no cover
    """Print a string in green
    """
    green_format = "\033[92m"
    print green_format + output_string


def print_underline(output_string):  # pragma: no cover
    """Print a string with an underline
    """
    underline_format = "\033[4m"
    print underline_format + output_string


def main():  # pylint: disable=R0915
    """Main point of entry to parse a topology file,
    build an inventory and product a Vagrantfile
    """
    # W0603 - use of global statement
    global VERBOSE  # pylint: disable=W0603
    vagrant_template = "./templates/Vagrantfile/Vagrantfile.j2"
    cli = parse_arguments()
    cli_args = cli.parse_args()
    check_files(cli_args, vagrant_template)

    if cli_args.verbose:  # pragma: no cover
        VERBOSE = True

    print_header("\n######################################")
    print_header("          Topology Converter")
    print_header("######################################")
    print_blue("           originally written by Eric Pulvino")

    parser = ParseGraphvizTopology()
    parsed_topology = parser.parse_topology(cli_args.topology_file)
    inventory = Inventory(provider=cli_args.provider)
    inventory.add_parsed_topology(parsed_topology)

    if cli_args.create_mgmt_network or cli_args.create_mgmt_configs_only:
        inventory.build_mgmt_network()

    if cli_args.create_mgmt_device:
        inventory.build_mgmt_network(create_mgmt_device=True)

    if cli_args.memory:
        print str(inventory.calculate_memory()) + " MB"
        exit(0)

    if cli_args.create_mgmt_network or cli_args.create_mgmt_device:
        if not os.path.exists("./helper_scripts/auto_mgmt_network/"):
            os.makedirs("./helper_scripts/auto_mgmt_network/")
        write_file("./helper_scripts/auto_mgmt_network/ansible_hostfile",
                   render_ansible_hostfile(inventory, cli_args.topology_file,
                                           "./templates/auto_mgmt_network/"))

        write_file("./helper_scripts/auto_mgmt_network/dhcpd.conf",
                   render_dhcpd_conf(inventory, cli_args.topology_file,
                                     "./templates/auto_mgmt_network/"))

        write_file("./helper_scripts/auto_mgmt_network/dhcpd.hosts",
                   render_dhcpd_hosts(inventory, cli_args.topology_file,
                                      "./templates/auto_mgmt_network/"))

        write_file("./helper_scripts/auto_mgmt_network/hosts",
                   render_hosts_file(inventory, cli_args.topology_file,
                                     "./templates/auto_mgmt_network/"))

        write_file("./helper_scripts/auto_mgmt_network/oob_server_config_auto_mgmt.sh",
                   render_oob_server_sh(inventory, cli_args.topology_file,
                                        "./templates/auto_mgmt_network/"))

        write_file("./helper_scripts/auto_mgmt_network/ztp_oob.sh",
                   render_ztp_oob(inventory, cli_args.topology_file,
                                  "./templates/auto_mgmt_network/"))

    if cli_args.create_mgmt_network:
        write_file("./helper_scripts/auto_mgmt_network/bridge-untagged",
                   render_bridge_untagged(inventory, cli_args.topology_file,
                                          "./templates/auto_mgmt_network/"))

    # Be sure everyone has an eth0 interface, create them if we must
    inventory.validate_eth0()

    if not cli_args.create_mgmt_configs_only:
        write_file("./Vagrantfile",
                   render_vagrantfile(inventory, "./templates/Vagrantfile/", cli_args))

    for node in inventory.node_collection:
        if node == "NOTHING":
            continue
        print inventory.get_node_by_name(node)

    print ""
    print_green("############")
    print_green("SUCCESS: Vagrantfile has been generated!")
    print_green("############")
    print ""
    print "\t" + str(len(inventory.node_collection)) + " under simulation"
    for node in inventory.node_collection:
        if node == "NOTHING":
            continue
        print "\t\t" + node
    print ""
    print "\t Requiring at least " + str(inventory.calculate_memory()) + " MB of memory"


if __name__ == "__main__":  # pragma: no cover
    main()
    exit(0)
