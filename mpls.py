#!/usr/bin/env python
import re
import time
import os
from Exscript.util.interact import read_login
from Exscript.protocols import SSH2
from lxml import etree
from netaddr import IPNetwork, IPAddress
from zabbix.api import ZabbixAPI

class mRouter(object):
    def __init__(self,host,zapi):
        self.__create__(host)
        self.zapi = zapi

    def parse(self):
        lsplist = LSPList()
        lsplist.setApi(self,self.zapi)
        lsplist.parse()
        intlist = InterfaceList()
        intlist.setApi(self,lsplist)
        intlist.parse()
        self.lsplist = lsplist
        self.intlist = intlist

    def execute(self,command):
        self.conn.execute('%s | display xml | no-more' % command)
        output = self.conn.response
        rpc = re.sub('^(.|\r|\r\n)*(?=<rpc-reply)|(?<=<\/rpc-reply>)(.|\r|\r\n)*$','',output)
        rpc = re.sub('xmlns="','xmlns:junos="',rpc)
        tree = etree.fromstring(rpc)
        return tree

    def close(self):
        self.conn.send('exit\r')
        self.conn.send('exit\r')
        self.conn.close()

    def __create__(self,host):
        account = read_login()
        self.name = host
        self.conn = SSH2()
        if self.conn.connect(host):
            print 'Connected'
            self.conn.login(account)
            self.conn.execute('cli')
        else:
            print 'Does not connected. Please check your input'
            sys.exit()

class mLSP(object):
    def __init__(self,name,to,bandwidth,path,state,output,nexthop_interface,rbandwidth):
        self.name = name
        self.to = to
        self.bandwidth = bandwidth
        self.path = path
        self.state = state
        self.output = output
        self.rbandwidth = rbandwidth
        self.nexthop_interface = nexthop_interface

    def printLSP(self):
        lspout = '{state:<14s}{name:<37s}{bandwidth:>11s}{output:>14s}  {rbandwidth:<12s}{route:<10s}'
        print lspout.format(name = self.name,
                            state = self.state,
                            bandwidth = str(self.bandwidth),
                            output = str(self.output),
                            rbandwidth = str(self.rbandwidth),
                            route = self.__formattedRoute__(self.path))
    def __repr__(self):
        return "LSP "+self.name

    def __formattedRoute__(self,route):
        match = re.compile('(?<=\.\d\d$)')
        route = " - ".join(match.sub(' ', str(x)) for x in route)
        return route


class mInterface(object):
    def __init__(self,name,description,speed,output,rsvpout,ldpout):
        self.name = name
        self.description = description
        self.speed = speed
        self.output = output
        self.rsvpout = rsvpout
        self.ldpout = ldpout

    def printInterface(self):
        intout = '{name:<14s}{description:<37s}{speed:>11s}{output:>14s}  {rsvpout:<12s}{ldpout:<17s}'
        print intout.format(name = self.name,
                            description = '* '+self.description,
                            speed = '* '+re.sub('Gbps','000',self.speed),
                            output = '* '+str(self.output),
                            rsvpout = 'RSVP:'+str(self.rsvpout),
                            ldpout = 'LDP:'+str(self.ldpout))
    
    def __repr__(self):
        return "Interface "+self.name


class LSPList(list):
    def __init__(self, *args):
        list.__init__(self, *args)
   
    def setApi(self, router,zabbixapi):
        self.router = router
        self.zabbixapi = zabbixapi
  
    def parse(self):
        lsp_fromconfig = self.__find_lsp_fromconfig__()
        path_fromconfig = self.__find_path_fromconfig__()
        routes_fromconfig = self.__find_routes_fromconfig__()
        lsp_state_fromcli = self.__find_lsp_state_fromcli__()
        lsp_output_fromzabbix = self.__find_lsp_output_fromzabbix__()
        
        for LSP in lsp_fromconfig:
            lsp_name = LSP['name']
            lsp_to = LSP['to']
            lsp_bandwidth = LSP['bandwidth']
            path_name = LSP['pathname']
            path_route = next(p['route'] for p in path_fromconfig if p['name'] == path_name)
            nexthop_ip = path_route[0]
            nexthop_interface = next(r['name'] for r in routes_fromconfig if IPAddress(nexthop_ip) in IPNetwork(r['destination']))
            lsp_state = lsp_state_fromcli.get(lsp_name,'Inactive')
            lsp_output = lsp_output_fromzabbix.get(lsp_name,'None')
            
            if (lsp_state != 'Inactive' and str(lsp_output) != 'None'):
                lsp_rbandwidth = round(float(lsp_output)/lsp_bandwidth,1)
                lsp_rbandwidth = str(lsp_rbandwidth)+"m"
            else:
                lsp_rbandwidth = "None"
            if (str(lsp_bandwidth) != "None"): 
                lsp_bandwidth = str(lsp_bandwidth)+"m"
        
            self.append(mLSP(name = lsp_name, 
                                to = lsp_to, 
                                path = path_route,
                                bandwidth = lsp_bandwidth, 
                                rbandwidth = lsp_rbandwidth,
                                state = lsp_state,
                                output = lsp_output,
                                nexthop_interface = nexthop_interface))
    
    def printLSPList(self):
        for LSP in self:
            LSP.printLSP()

    def sortByBandwidth(self):
        newlist = LSPList()
        newlist.extend(self)
        newlist.sort(key = lambda lsp: re.sub('m','',lsp.bandwidth), reverse = True)
        return newlist
        
    def sortByOutput(self):
        newlist = LSPList()
        newlist.extend(self)
        newlist.sort(key = lambda lsp: lsp.output, reverse = True)
        return newlist
        
    def getLSPByHost(self,to):
        newlist = LSPList()
        for l in self:
            if l.to == to:
                newlist.append(l)
        return newlist

    def getLSPByInterface(self,interface):
        newlist = LSPList()
        for l in self:
            if l.nexthop_interface == interface:
                newlist.append(l)
        return newlist

    def getLSPByState(self,state):
        newlist = LSPList()
        for l in self:
            if l.state == state:
                newlist.append(l)
        return newlist
    
    def getAllInterfaces(self):
        newlist = []
        for x in set([x.nexthop_interface for x in self]):
            newlist.append(x)
        return newlist
    
    def getAllHosts(self):
        newlist = []
        for x in set([x.to for x in self]):
            newlist.append(x)
        return newlist

    def getAllHostsSortedByOutput(self):
        newlist = []
        for x in set([x.to for x in self]):
            newlist.append(x)
        return sorted(newlist, key = lambda x: self.getLSPByHost(x).getSumOutput(), reverse = True)
    
    def getSumOutput(self):
        return sum(x.output for x in self if x.output != 'None')

    def getSumBandwidth(self):
        return sum([int(re.sub('m','',x.bandwidth)) for x in self if x.bandwidth != 'None'])

    def getAverageRBandwidthByHost(self,host):
        LSPByHost = [l for l in self.getLSPByHost(host) if l.rbandwidth != 'None']
        RBandwidthList = [float(re.sub('m','',l.rbandwidth)) for l in LSPByHost]
        AllLSP = len(LSPByHost)
        return round(float(sum(RBandwidthList))/AllLSP, 2)

    def __find_lsp_fromconfig__(self):
        result = []
        command = self.router.execute('show configuration protocol mpls')
        rootTree = command.xpath('//configuration/protocols/mpls/label-switched-path')
        for tree in rootTree:
            LSP = {}
            name = tree.xpath('string(name/text())')
            to = tree.xpath('string(to/text())')
            try:
                bandwidth = tree.xpath('string(bandwidth/per-traffic-class-bandwidth/text())')
                bandwidth = self.__setBandwidthInM__(bandwidth)
            except AttributeError:
                bandwidth = "None"
            path = tree.xpath('primary/name')[0].text
            LSP['name'] = name
            LSP['to'] = to
            LSP['bandwidth'] = bandwidth
            LSP['pathname'] = path
            result.append(LSP)
        return result

    def __setBandwidthInM__(self,band):
        if re.match('m|g', band):
            band = re.sub('m','000',band)
            band = re.sub('g','000000',band)
        band = re.sub('000000$','m',band)
        band = re.sub('g$','000m',band)
        if re.match('m', band):
            re.sub('m','',band)
            band = float(band)/1000
        band = re.sub('m','',band)
        try:
            band = int(band)
        except:
            band = 0
        return band

    def __find_path_fromconfig__(self):
        result = []
        command = self.router.execute('show configuration protocol mpls')
        rootTree = command.xpath('//configuration/protocols/mpls/path')
        for tree in rootTree:
            PATH = {}
            name = tree.xpath('string(name/text())')
            hops = tree.xpath('path-list')
            route = []
            for hop in hops:
                route.append(hop.xpath('string(name/text())'))
            PATH['name'] = name
            PATH['route'] = route
            result.append(PATH)
        return result

    def __find_routes_fromconfig__(self):
        result = []
        command = self.router.execute('show configuration interfaces')
        rootTree = command.xpath('//configuration/interfaces/interface')
        for interface in rootTree:
            try:
                interfacename = interface.xpath('string(name/text())')
                units = interface.xpath('unit')
                for unit in units:
                    destination = ''
                    unitname = unit.xpath('string(name/text())')
                    try:
                        destination = unit.xpath('string(family/inet/address/name/text())')
                    except Exception: 
                        pass
                    if destination != '':
                        INTERFACE = {}
                        finalname = interfacename+'.'+unitname
                        INTERFACE['name'] = finalname
                        INTERFACE['destination'] = destination
                        result.append(INTERFACE)
            except Exception: 
                pass
        return result
    
    def __find_lsp_state_fromcli__(self):
        result = {}
        command = self.router.execute('show mpls lsp unidirectional ingress')
        rootTree = command.xpath('//mpls-lsp-information/rsvp-session-data/rsvp-session')
        for tree in rootTree:
            state = tree.xpath('string(mpls-lsp/lsp-state/text())')
            name = tree.xpath('string(mpls-lsp/name/text())')
            result[name] = state
        return result
    
    def __find_lsp_output_fromzabbix__(self):
        result = {}
        router_hostid = ''
        router_name = self.router.name
        zabbix_hosts = self.zabbixapi.host.getobjects() 
        router_hostid = next(h['hostid'] for h in zabbix_hosts if h['name'] == router_name)
        zabbix_router_items = self.zabbixapi.item.get(hostids=router_hostid,output='extend')
        for item in zabbix_router_items:
            if re.match('.*octets',item['key_']):
                key = re.sub('_octets','',item['key_'])
                if int(time.time()) > int(item['lastclock']) + 180:
                    output = "None"
                else:
                    output = int(item['lastvalue'])/1000**2
                result[key] = output
        return result


class InterfaceList(list):
    def __init__(self, *args):
        list.__init__(self, *args)

    def setApi(self, router, lsplist):
        self.router = router
        self.lsplist = lsplist

    def parse(self):
        interfaces_fromcli = self.__find_interfaces_fromcli__()

        for interface in self.lsplist.getAllInterfaces():
            interface_name = interface
            interface_fromcli = next(i for i in interfaces_fromcli if i['name'] == interface_name)
            interface_description = interface_fromcli.get('description', 'None')
            interface_speed = interface_fromcli.get('speed', 'None')
            interface_output = interface_fromcli.get('output', 'None')
            interface_rsvpout = self.lsplist.getLSPByInterface(interface_name).getSumOutput()
            interface_ldpout = interface_output - interface_rsvpout

            self.append(mInterface(name = interface_name,
                                        description = interface_description,
                                        speed = interface_speed,
                                        output = interface_output,
                                        rsvpout = interface_rsvpout,
                                        ldpout = interface_ldpout))
    def printInterfaceList(self):
        for interface in self:
            interface.printInterface()

    def sortByOutput(self):
        newlist = InterfaceList()
        newlist.extend(self)
        newlist.sort(key = lambda interface: interface.output, reverse = True)
        return newlist

    def __find_interfaces_fromcli__(self):
        result = []
        command = self.router.execute('show interfaces detail')
        rootTree = command.xpath('//interface-information/physical-interface')
        for interface in rootTree:
            for tree in interface.xpath('logical-interface'):
                try:
                    INTERFACE = {}
                    name = tree.xpath('string(name/text())')
                    description = tree.xpath('string(description/text())')
                    speed = tree.getparent().xpath('string(speed/text())')
                    if re.match('ae',name):
                        output = tree.xpath('string(lag-traffic-statistics/lag-bundle/output-bps/text())')
                    else:
                        output = tree.xpath('string(transit-traffic-statistics/output-bps/text())')
                    try:
                        output = int(output)/1000**2
                    except ValueError:
                        output = 0
                    INTERFACE['name'] = name
                    INTERFACE['description'] = description
                    INTERFACE['speed'] = speed
                    INTERFACE['output'] = output
                    result.append(INTERFACE)
                except AttributeError:
                    pass
        return result

def getZApi():
    print "Please enter zabbix account information"
    zabbixaccount = read_login()
    zapi = ZabbixAPI(url='http://zabbix.ihome.ru', user=zabbixaccount.name, password=zabbixaccount.password)
    return zapi

if __name__ == "__main__":
    zapi = getZApi() 
    host = raw_input('Please enter host: ')
    router = mRouter(host,zapi)
    router.parse()

    for interface in router.intlist.sortByOutput():
        interface.printInterface()
        router.lsplist.getLSPByInterface(interface.name).printLSPList()
        print

    router.close()
