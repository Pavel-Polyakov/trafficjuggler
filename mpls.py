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
    def __init__(self,host):
        self.__create__(host)
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
    def printLSP(self):
        lspout = '{state:<14s}{name:<37s}{bandwidth:>11s}{output:>14s}  {rbandwidth:<12s}{route:<10s}'
        print lspout.format(name = self.name,
                            state = self.state,
                            bandwidth = str(self.bandwidth)+'m',
                            output = str(self.output),
                            rbandwidth = str(self.rbandwidth),
                            route = self.__formattedRoute__(self.path))
    def __repr__(self):
        return "LSP "+self.name

    def __formattedRoute__(self,route):
        match = re.compile('(?<=\.\d\d$)')
        route = " - ".join(match.sub(' ', str(x)) for x in route)
        return route

class mLogicalInterface(object):
    def __init__(self,name,description,speed,output):
        self.name = name
        self.description = description
        self.speed = speed
        self.output = output
    def __repr__(self):
        return "LogicalInterface "+self.name

class LSPList(object):
    LSPs = []
    
    def __init__(self,router,zabbixapi):
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
            
            if (str(lsp_state) != 'Inactive' and str(lsp_output) != 'None'):
                lsp_rbandwidth = round(float(lsp_output)/lsp_bandwidth,1)
                lsp_rbandwidth = str(lsp_rbandwidth)+"m"
            else:
                lsp_rbandwidth = "None"
            if (str(lsp_bandwidth) != "None"): 
                lsp_bandwidth = str(lsp_bandwidth)+"m"
            self.LSPs.append(mLSP(name = lsp_name, 
                                to = lsp_to, 
                                path = path_route,
                                bandwidth = lsp_bandwidth, 
                                rbandwidth = lsp_rbandwidth,
                                state = lsp_state,
                                output = lsp_output,
                                nexthop_interface = nexthop_interface))

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


def findAllLogicalInterfaces(router):
    result = []
    command = router.execute('show interfaces detail')
    rootTree = command.xpath('//interface-information/physical-interface')
    for interface in rootTree:
        for tree in interface.xpath('logical-interface'):
            try:
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
                result.append(mLogicalInterface(name,description,speed,output))
            except AttributeError:
                pass
    return result



def collectAndSort(router,zabbixaccount):
    lsps = findAllLSP(router)
    paths = findAllPath(router)
    routes = findAllRoutes(router)
    lints = findAllLogicalInterfaces(router)
    lspOutput = getLspOutput(router, zabbixaccount)
    lspState = getLSPState(router)
    
    interfaces = []
    for l in lsps:
        path = next(x for x in paths if x.name == l.name)
        route = next(x for x in routes if IPAddress(path.route[0]) in IPNetwork(x.destination))
        lint = next(x for x in lints if x.name == route.via)
        try: state = lspState[l.name]
        except KeyError: state = 'Inactive'
        try: output = lspOutput[l.name]
        except KeyError: output = 0
        l.path = path
        l.nh = lint
        l.output = output
        l.state = state
        try:
            l.rbandwidth = round(float(output)/l.bandwidth,1)
        except Exception:
            l.rbandwidth = 0
        if not lint in interfaces:
            lint.bandwidth = l.bandwidth
            lint.rsvpout = int(l.output)
            lint.lsplist = []
            lint.lsplist.append(l)
            interfaces.append(lint)
        else:
            interfaces[interfaces.index(lint)].bandwidth += l.bandwidth
            interfaces[interfaces.index(lint)].rsvpout += int(l.output)
            interfaces[interfaces.index(lint)].lsplist.append(l)
    
    hosts = []
    for l in lsps:
        to = l.to
        if not to in [x.name for x in hosts]:
            lsplist = [x for x in lsps if x.to == to]
            output = sum([x.output for x in lsplist])
            host = mHost(to,lsplist,output)
            hosts.append(host)
        else:
            pass

    for interface in interfaces:
        try:
            interface.rsvppercent = round((float(interface.rsvpout)/interface.output)*100,2)
            interface.ldpout = interface.output - interface.rsvpout
        except Exception:
            interface.rsvppercent = 0
            interface.ldpout = 0
    return interfaces,lsps,hosts

def printInterfaces(interfaces):
    #and print it
    intout = '{name:<14s}{description:<37s}{bandwidth:>11s}{output:>14s}  {rsvpout:<12s}{ldpout:<17s}'

    for interface in sorted(interfaces, key = lambda interface: interface.output, reverse=True):
        print intout.format(name = interface.name,
                            description = '* '+interface.description,
                            bandwidth = '* '+re.sub('Gbps','000',interface.speed),
                            output = '* '+str(interface.output),
                            rsvpout = 'RSVP:'+str(interface.rsvpout),
                            ldpout = 'LDP:'+str(interface.ldpout))
        for lsp in sorted(interface.lsplist, key = lambda lsp: lsp.bandwidth, reverse = True):
            lsp.printLSP()
        print

if __name__ == "__main__":
    host = raw_input('Please enter host: ')
    router = mRouter(host)
    print "Please enter zabbix logo/pass: "
    zabbixaccount = read_login()
    zapi = ZabbixAPI(url='http://zabbix.ihome.ru', user=account.name, password=account.password)
    
    interfaces,lsps,hosts = collectAndSort(router,zabbixaccount)
    printInterfaces(interfaces)
    router.close()
