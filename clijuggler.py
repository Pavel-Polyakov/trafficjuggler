#!/usr/bin/env python
from TrafficJuggler.builders.routerbuilder import RouterBuilder
from TrafficJuggler.util import loaditems,saveitems
import re
import os
import sys

if __name__ == "__main__":
    if len(sys.argv)>1 and sys.argv[1] == "load":
        router = loaditems(sys.argv[2])
    else:
        #zapi = getZApi()
        host = raw_input('Please enter host: ')
        builder = RouterBuilder(host)
        router = builder.create()

        if len(sys.argv)>1 and sys.argv[1] == "save":
            saveitems(sys.argv[2],router)

    print "\nSummary information"
    for interface in router.interfacelist.sortByOutput():
        interface.printInterface()
        router.lsplist.getLSPByInterface(interface.name).printLSPList()
        print

    print "\nInformation related to Hosts"
    for host in router.lsplist.getAllHostsSortedByOutput():
        lsps = router.lsplist.getLSPByHost(host)
        host_name = next(x['description'] for x in router.neighbors if x['ip'] == host)
        print '{host:<15}{space:<21}{bandwidth:<12}{output:<12}{rband:<12}'.format(space = host_name,
                                                                                    host=host,
                                                                                    output=str(round(float(lsps.getSumOutput())/1000,1))+"Gbps",
                                                                                    bandwidth=str(lsps.getSumBandwidth())+"m",
                                                                                    rband=str(lsps.getAverageRBandwidthByHost(host))+"m")

    print "\nInformation related to Interface"
    for interface in router.interfacelist.sortByOutput():
        speed = re.sub('Gbps','000',interface.speed)
        output = interface.output
        try:
            utilization = str(round(output/float(speed)*100,2))+"%"
        except Exception:
            utilization = 0
        print '{name:<15}{description:<21}{speed:<12}{output:<12}{util:<15}'.format(name = interface.name,
                                                                                    description = interface.description,
                                                                                    speed = interface.speed,
                                                                                    output = str(round(float(interface.output)/1000,1))+"Gbps",
                                                                                    util = utilization)

    print "\nParse time: %s" % router.last_parse
