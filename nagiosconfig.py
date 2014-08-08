#!/usr/bin/python

"""
Overview
========
Script to generate individual Nagios host and service configuration files for
each device to be monitored.  Each configuration file should be written to its
own configuration file.   Nagios should be configured to read all configuration
within a directory(s).


Philosophy
==========
The idea behind this system is to create individal configuration files for
each device to be monitored.  This system is going to create independent
service checks for EACH host.   This may DUPLICATE lots of service checks.

Why do this?   The mains goals are:

    * Flexability: If you need the ability tweak settings for each device.
    * Simplicity: It makes it easy for everyone to understand.

Why should you not use this system?   If you have many device that could all
share a common set of configuration parameters, then I suggest you look into
Nagios Object Inheritance and Template-Based Object Configuration.

Example Usage
=============
$ ./nagiosconfig.py --hostname test1.example.com --ipaddr 1.2.3.4 --createhost \
        --parents switch1.example.com --parents switch2.example.com \
        --hostgroup server --hostgroup nss --hostgroup dns --device server \
        --parents switch2.example.com --service ping --service ssh \
        --device server --regexchange contact_groups:user@example.com

Copyright / License
===================
Copyright (C) 2014  Jason E. Murray <jemurray@wustl.edu>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import argparse
import re
import glob
import logging


# Template file locations
baseDir = '.'
hostTemplates = baseDir+'/templates/host'
serviceTemplates = baseDir+'/templates/service'
hostGroupFile = baseDir+'/hostgroups.cfg'

# Available device types.   These are used to determin the host images/icons
availableDeviceTypes = ['server', 'router', 'switch', 'unknown']

# Setup basic logging
logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)



def getArguments(hostGroupFile, availableServiceChecks):
    """
    Process arguments setup on the command line

    :param hostGroupFile: physical location of the Nagios hostgroup configuration file
    :param availableServiceChecks: list containing all the available service check templates
    :returns: list of arguments
    """

    parser = argparse.ArgumentParser(description='Script to automatically build Nagios host and service definations')
    parser.add_argument('--hostname', action='store', dest='hostname', required=True, help='The fully qualified hostname')
    parser.add_argument('--createhost', action='store_true', dest='createhost', help='Create host defination')
    parser.add_argument('--service', action='append', dest='service', choices=availableServiceChecks, help='Create service defination')
    parser.add_argument('--ipaddr', action='store', dest='ipaddr', required=True, help='Public IP address of the device')
    parser.add_argument('--parents', action='append', dest='parents', help='FQDN of the object parents, this host must already exist.  Multiple --parents can be used')
    parser.add_argument('--hostgroups', action='append', dest='hostgroups', choices=getHostGroups(hostGroupFile), help='Hostgroups the device should be a part of.  Multiple --hostgroups can be used')
    parser.add_argument('--devicetype', action='store', dest='devicetype', default='unknown', choices=availableDeviceTypes, help='Type of device')
    parser.add_argument('--regexchange', action='append', dest='regexChange', metavar='regular_expression:new_value', help='Use a regular expression to change anything in service templates')
    parser.add_argument('--version', action='version', version='%(prog)s 0.1beta')

    args = parser.parse_args()

    return args


def validateArgs(args):
    """
    There are a number of aruments that need extended validation for proper syntax, this function takes care of this.

    :param args: list of command line arguments
    """

    try:
        if args.regexChange:
            for i in args.regexChange:
                reg, value = i.split(':')
                logger.debug("validateArgs regex values: {0} {1}".format(reg, value))
    # Use an exception to catch the fact that two values are needed within the split.
    except:
        print '\nError:'
        print '\t--regexchange must have two values in the following format "regular_expression:change_value"'
        exit(-1)

    logger.debug("all command line arguments {0}".format(args))


def buildHost(args):
    """
    Build the host defination.

    TODO: I think this will get changed over to using templates.
          For now simple print lines are used in order to skip key:values
          that are not used

    :params args: list of arguments
    """

    print "define host {"
    print "\thost_name                          %s" % args.hostname
    print "\talias                              %s" % args.hostname
    print "\taddress                            %s" % args.ipaddr
    if args.parents:
        print "\tparents                            %s" % ", ".join(args.parents)
    else:
        print "\t#parents                           NONE"
    if args.hostgroups:
        print "\thostgroups                         %s " % ", ".join(args.hostgroups)
    else:
        print "\t#hostgroups                        NONE"
    print "\tnotifications_enabled              1"
    print "\tevent_handler_enabled              1"
    print "\tflap_detection_enabled             1"
    print "\tfailure_prediction_enabled         1"
    print "\tprocess_perf_data                  1"
    print "\tretain_status_information          1"
    print "\tretain_nonstatus_information       1"
    print "\tcheck_command                      check-host-alive"
    print "\tmax_check_attempts                 10"
    print "\tnotification_interval              0"
    print "\tnotification_period                24x7"
    print "\tnotification_options               d,u,r"
    print "\tcontact_groups                     admins"
    print "\ticon_image                         base/linux40.png"
    print "\ticon_image_alt                     Debian GNU/Linux"
    print "}"
    print ""

def buildService(service, serviceCheckFiles, args):
    """
    Build service configurations based on template files.

    TODO: rework system so it parses the templates into key:value pairs and
          reformats them for consistancy

    :param service: type of service template configuration to make
    :param serviceCheckFiles: list that containes physical location to server template files
    :param args: command line arguments
    """

    try:
        logger.debug("Building service template {0} from file: {1}".format(service, serviceCheckFiles[service]))
        fh = open(serviceCheckFiles[service], 'r')
        print "service {"
        for line in fh:
            # Remove the service type
            m = re.search('^#type:', line)
            if m:
                continue

            # Remove blank lines
            m = re.search('^$', line)
            if m:
                continue

            # Generate the service description
            m = re.search('^(.*)\s+(%%service_description%%)', line)
            if m:
                print "\t{0} {1}-{2}".format(m.group(1), service.upper(), args.hostname)
                continue

            # Generate the host name
            m = re.search('^(.*)\s+(%%host_name%%)', line)
            if m:
                print "\t{0} {1}".format(m.group(1), args.hostname)
                continue

            # replace all key:value pairs from the --regexchange command line argument
            if args.regexChange:
                found = False
                for i in args.regexChange:
                    reg, rvalue = i.split(':')
                    pattern = "("+reg+")\s+(.*)"
                    m = re.search(pattern, line)
                    if m:
                        print "\t{0:<32}{1:<25}".format(m.group(1), rvalue)
                        found = True
                # break the loop if a regex match is found
                if found:
                     continue

            # Nothing matched above, print the line from the template.
            print "\t{0}".format(line),

        print "}"
        print ""

    except:
        print "This should not happen, but the service template '{0}' does not exist or is broken in some way, please try again".format(service)


def getHostGroups(hostGroupFile):
    """
    Read the Nagios hostgroup configuration file and get all available hostgroups.   This is used
    to dynamically create the command line argument options.

    :param hostGroupFile: physical location of the Nagios hostgroup configuration file
    :return: list of all available host groups
    """

    availableHostGroups = []
    fh = open(hostGroupFile, 'r')
    pattern = '^\s+hostgroup_name\s+(.*)$'
    recomp = re.compile(pattern)
    for line in fh:
        result = recomp.match(line)
        if result:
            availableHostGroups.append(result.group(1))

    logger.debug("List of available hostGroups: {0} ".format(availableHostGroups))
    fh.close()
    return availableHostGroups


def getServiceTemplates(serviceTemplates):
    """
    Read all files in the services template directory in order to generate
    list of all available service checks available.

    :param serviceTemplates: physical directory location of service template files
    :return: list of all available service checks and list of all physicial template files locations
    """

    availableServiceChecks = []
    serviceCheckFiles = {}
    for file in glob.glob(serviceTemplates+'/*.t'):
        fh = open(file, 'r')
        for line in fh:
            m = re.search('^#type:\s+(\w+)$', line)
            if m:
                logger.debug("Template type: {0}".format(m.group(1)))
                availableServiceChecks.append(m.group(1))
                serviceCheckFiles[m.group(1)] = file

    fh.close()
    logger.debug("Available service templates: {0}".format(serviceCheckFiles))
    return availableServiceChecks, serviceCheckFiles



def main():
    """
    main() function is use to make sure script is called directly.
    """

    availableServiceChecks, serviceCheckFiles = getServiceTemplates(serviceTemplates)
    args = getArguments(hostGroupFile, availableServiceChecks)
    validateArgs(args)
    if args.createhost:
        buildHost(args)
    if args.service:
        for service in args.service:
            buildService(service, serviceCheckFiles, args)


if __name__ == '__main__':
    """
    Make sure script is called directly
    """
    main()
