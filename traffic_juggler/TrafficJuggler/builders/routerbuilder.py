from TrafficJuggler.models.router import Router
from TrafficJuggler.parser import Parser
from lsplistbuilder import LSPListBuilder
from interfacelistbuilder import InterfaceListBuilder

import time

class RouterBuilder(object):
    def __init__(self, hostname):
        self.hostname = hostname
        self.parser = Parser(hostname)

    def create(self):
        lsplistbuilder = LSPListBuilder(self.parser)
        interfacelistbuilder = InterfaceListBuilder(self.parser)

        lsplist = lsplistbuilder.create()
        nexthop_interfaces_from_lsplist = lsplist.getNextHopInterfaces()
        nexthop_interfaces_output = lsplist.getOutputOfNextHopInterfaces()
        interfacelist = interfacelistbuilder.create(nexthop_interfaces_from_lsplist,nexthop_interfaces_output)
        neighbors = self.parser.get_ibgp_neighbors()
        last_parse = time.asctime(time.localtime(time.time()))

        return Router(self.hostname,lsplist,interfacelist,neighbors,last_parse)
