# -*- coding: utf-8 -*-
from TrafficJuggler.models.image import Image
from TrafficJuggler.models.host import Host
from TrafficJuggler.models.interface import Interface
from TrafficJuggler.models.prefix import Prefix
from TrafficJuggler.parser import Parser

from TrafficJuggler.builders.lsplistbuilder import LSPListBuilder
from TrafficJuggler.builders.interfacelistbuilder import InterfaceListBuilder
from TrafficJuggler.builders.hostbuilder import HostBuilder
from TrafficJuggler.builders.prefixbuilder import PrefixBuilder

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

        self.__parseHosts__()
        self.__parsePrefixes__()

        lsplistbuilder = LSPListBuilder(self.parser)
        lsplist = lsplistbuilder.create()

        nhinterfaces = self.__getNextHopInterfaces__(lsplist)
        nhinterfaces_names = set([x['name'] for x in nhinterfaces])

        interfacelistbuilder = InterfaceListBuilder(self.parser)
        interfacelist = interfacelistbuilder.create(nhinterfaces_names)

        for i in interfacelist:
            i.image = image

        for l in lsplist:
            l.image = image

        self.session.add_all(interfacelist)
        self.session.commit()

        for l in lsplist:
            try:
                nh_name = [x['name'] for x in nhinterfaces if x['ip'] == l.path['real'][0]['ip']][0]
                nh_interface = self.session.query(Interface).\
                                            filter(Interface.image_id == image.id).\
                                            filter(Interface.name == nh_name).first()
                l.interface_id = nh_interface.id
            except IndexError:
                l.interface_id = None
        self.session.add_all(lsplist)
        self.session.commit()

    def __getNextHopInterfaces__(self, lsplist):
        nhinterfaces = []
        routes = self.parser.get_interfaces_config()
        for ip_nh in [x.path['real'][0]['ip'] for x in lsplist]:

                interface_name = next(r['name'] for r in routes if IPAddress(ip_nh) in IPNetwork(r['destination']))
                nhinterfaces.append({'name': interface_name, 'ip': ip_nh})
        return nhinterfaces

    def __parseHosts__(self):
        # add hosts if its not exist
        hostbuilder = HostBuilder(self.parser)
        hosts = hostbuilder.create()
        for h in hosts:
            if not self.session.query(Host.ip).filter(Host.ip==h.ip).first():
                self.session.add(h)
        self.session.commit()

    def __parsePrefixes__(self):
        # add prefix if its not exis
        prefixbuilder = PrefixBuilder(self.parser)
        prefixes = prefixbuilder.create()
        for p in prefixes:
        #    if not self.session.query("'"+p.name+"'").filter(Prefix.name==p.name).first():
                host = self.session.query(Host).filter(Host.ip == p.host_ip).first();
                p.host_id = host.id
                self.session.add(p)
        self.session.commit()

def findFirstHop(route):
    return re.findall('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', route)[0]
