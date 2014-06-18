#!/usr/bin/python

import argparse
import re
import glob


##
## Global Configuration
##
availableDeviceTypes = ['server', 'router', 'switch', 'unknown']
hostTemplates = 'templates/host'
serviceTemplates = 'templates/service'
hostGroupFile = './hostgroups.cfg'




def getArguments(hostGroupFile, availableServiceChecks):
    parser = argparse.ArgumentParser(description='Script to automatically build Nagios host and service definations')
    parser.add_argument('--hostname', action='store', dest='hostname', required=True, help='The fully qualified hostname')
    parser.add_argument('--createhost', action='store_true', dest='createhost', help='Create host defination')
    parser.add_argument('--service', action='append', dest='service', choices=availableServiceChecks, help='Create service defination')
    parser.add_argument('--ipaddr', action='store', dest='ipaddr', required=True, help='Public IP address of the device')
    parser.add_argument('--parents', action='append', dest='parents', help='FQDN of the object parents, this host must already exist.  Multiple --parents can be used')
    #parser.add_argument('--hostgroups', action='append', dest='hostgroups', help='Hostgroups the device should be a part of.  Multiple --hostgroups can be used')
    parser.add_argument('--hostgroups', action='append', dest='hostgroups', choices=getHostGroups(hostGroupFile), help='Hostgroups the device should be a part of.  Multiple --hostgroups can be used')
    parser.add_argument('--devicetype', action='store', dest='devicetype', default='unknown', choices=availableDeviceTypes, help='Type of device')
    parser.add_argument('--version', action='version', version='%(prog)s 0.1beta')

    args = parser.parse_args()

    return args


##
## Validate options to arguments are valid.
##
def validateArgs(args):

    # Do nothing anymore, found the "choices" option to argparse...

    # Print all arguments while debugging
    print "DEBUG all arguments: ", args


def buildHost(args):

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


def buildService(args):
    for service in args.service:
        print "define service {"
        if service == "ping":
            print "\tservice_description             %s-ping" % args.hostname
            print "\tcheck_command                   check_ping!1000.0,20%!2000.0,60%"
        elif service == "ssh":
            print "\tservice_description             %s-ssh" % args.hostname
            print "\tcheck_command                   check_ssh"
        print "\thost_name                       %s" % args.hostname
        print "\tnotification_interval           0"
        print "\tactive_checks_enabled           1"
        print "\tpassive_checks_enabled          1"
        print "\tparallelize_check               1"
        print "\tobsess_over_service             1"
        print "\tcheck_freshness                 0"
        print "\tnotifications_enabled           1"
        print "\tevent_handler_enabled           1"
        print "\tflap_detection_enabled          1"
        print "\tfailure_prediction_enabled      1"
        print "\tprocess_perf_data               1"
        print "\tretain_status_information       1"
        print "\tretain_nonstatus_information    1"
        print "\tis_volatile                     0"
        print "\tcheck_period                    24x7"
        print "\tnormal_check_interval           5"
        print "\tretry_check_interval            1"
        print "\tmax_check_attempts              4"
        print "\tnotification_period             24x7"
        print "\tnotification_options            w,u,c,r"
        print "\tcontact_groups                  admins"
        print "}"
        print ""


##
## Get hostgroup entries
##
def getHostGroups(hostGroupFile):
    availableHostGroups = []
    hgf = open(hostGroupFile, 'r')
    pattern = '^\s+hostgroup_name\s+(\w+)$'
    recomp = re.compile(pattern)
    for line in hgf:
        result = recomp.match(line)
        if result:
            availableHostGroups.append(result.group(1))

    #print "DEBUG availableHostGroups: ", availableHostGroups
    hgf.close()
    return availableHostGroups

##
## Get template files
##
def getServiceTemplates(serviceTemplates):
    availableServiceChecks = []
    serviceCheckFiles = {}
    for file in glob.glob(serviceTemplates+'/*.t'):
        fh = open(file, 'r')
        for line in fh:
            m = re.search('^#type:\s+(\w+)$', line)
            if m:
                print "DEBUG template type: {0}".format(m.group(1))
                availableServiceChecks.append(m.group(1))
                serviceCheckFiles = { m.group(1), file }

    print "DEBUG: ", serviceCheckFiles
    return availableServiceChecks, serviceCheckFiles



def main():
    availableServiceChecks, serviceCheckFiles = getServiceTemplates(serviceTemplates)
    args = getArguments(hostGroupFile, availableServiceChecks)
    validateArgs(args)
    if args.createhost:
        buildHost(args)
    if args.service:
        buildService(args)


# main
if __name__ == '__main__':
    main()


