from TrafficJuggler.models.image import Image
from TrafficJuggler.models.host import Host
from TrafficJuggler.parser import Parser

from TrafficJuggler.builders.lsplistbuilder import LSPListBuilder
from TrafficJuggler.builders.interfacelistbuilder import InterfaceListBuilder
from TrafficJuggler.builders.hostbuilder import HostBuilder

from netaddr import IPNetwork, IPAddress
import re


class ImageBuilder(object):
    def __init__(self, hostname, session, parser=None):
        self.hostname = hostname
        if parser is None:
            self.parser = Parser(hostname)
        else:
            self.parser = parser
        self.session = session

    def parse(self):
        image = Image(router=self.hostname)

        hostbuilder = HostBuilder(self.parser)
        hosts = hostbuilder.create()
        for h in hosts:
            if not self.session.query(Host.ip).filter(Host.ip==h.ip).first():
                self.session.add(h)

        # firstly lets find all lsp related information
        lsplistbuilder = LSPListBuilder(self.parser)
        interfacelistbuilder = InterfaceListBuilder(self.parser)
        lsplist = lsplistbuilder.create()

        # then I will find information about interfaces, but only needed
        # so firstly I need to find its names
        nhinterfaces = self.getNextHopInterfaces(lsplist)

        # and create needed objects
        nhnames = [x['name'] for x in nhinterfaces]
        interfacelist = interfacelistbuilder.create(nhnames)

        for i in interfacelist:
            i.image = image

        # set nexthop_interface to lsps
        for l in lsplist:
            nh_name = [x['name'] for x in nhinterfaces if x['ip'] == findFirstHop(l.path)][0]
            nh_interface = [x for x in interfacelist if x.name == nh_name][0]
            l.interface = nh_interface

        for l in lsplist:
            l.image = image

        self.session.add_all(lsplist)
        self.session.add_all(interfacelist)

        self.session.commit()

    def getNextHopInterfaces(self, lsplist):
        nhinterfaces = []
        routes = self.parser.get_interfaces_config()
        for ip_nh in [findFirstHop(x.path) for x in lsplist]:
            interface_name = next(r['name'] for r in routes if IPAddress(ip_nh) in IPNetwork(r['destination']))
            nhinterfaces.append({'name': interface_name, 'ip': ip_nh})
        return nhinterfaces


def findFirstHop(route):
    return re.findall('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', route)[0]
