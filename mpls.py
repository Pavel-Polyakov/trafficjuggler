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
    def __init__(self,name,to,bandwidth,path):
        self.name = name
        self.to = to
        self.bandwidth = bandwidth
        self.path = path
    def __repr__(self):
        return "LSP "+self.name


class mPath(object):
    def __init__(self,name,route):
        self.name = name
        self.route = route
    def __repr__(self):
        return "Path "+self.name
    def formattedRoute(self):
        match = re.compile('(?<=\.\d\d$)')
        route = " - ".join(match.sub(' ', str(x)) for x in self.route)
        return route

class mRoute(object):
    def __init__(self,destination,interface):
        self.destination = destination
        self.via = interface
    def __repr__(self):
        return "Route "+self.destination

class mLogicalInterface(object):
    def __init__(self,name,description,speed,output):
        self.name = name
        self.description = description
        self.speed = speed
        self.output = output
    def __repr__(self):
        return "LogicalInterface "+self.name

def findAllLSP(router):
    command = router.execute('show configuration protocol mpls')
    rootTree = command.xpath('//configuration/protocols/mpls/label-switched-path')
    lsps = []
    for tree in rootTree:
        name = tree.xpath('string(name/text())')
        to = tree.xpath('string(to/text())')
        try:
            band = tree.xpath('string(bandwidth/per-traffic-class-bandwidth/text())')
            band = __SetSameBandwidth__(band)
        except AttributeError:
            band = 0
        bandwidth = band
        path = tree.xpath('primary/name')[0].text
        lsps.append(mLSP(name,to,bandwidth,path))
    return lsps

def findAllPath(router):
    result = []
    command = router.execute('show configuration protocol mpls')
    rootTree = command.xpath('//configuration/protocols/mpls/path')
    for tree in rootTree:
        name = tree.xpath('string(name/text())')
        hops = tree.xpath('path-list')
        route = []
        for hop in hops:
            route.append(hop.xpath('string(name/text())'))
        result.append(mPath(name,route))
    return result

def findAllRoutes(router):
    result = []
    command = router.execute('show configuration interfaces')
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
                except Exception: pass
                if destination != '':
                    finalname = interfacename+'.'+unitname
                    result.append(mRoute(destination,finalname))
        except Exception: pass
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

def getLSPState(router):
    result = {}
    command = router.execute('show mpls lsp unidirectional ingress')
    rootTree = command.xpath('//mpls-lsp-information/rsvp-session-data/rsvp-session')
    for tree in rootTree:
        state = tree.xpath('string(mpls-lsp/lsp-state/text())')
        name = tree.xpath('string(mpls-lsp/name/text())')
        result[name] = state
    return result

def getLspOutput(router, account):
    result = {}
    host = router.name
    zapi = ZabbixAPI(url='http://zabbix.ihome.ru', user=account.name, password=account.password)
    hostid = ''
    for h in zapi.host.getobjects():
        if h['name'] == host:
            hostid = h['hostid']
    for item in zapi.item.get(hostids=hostid,output='extend'):
        if re.match('.*octets',item['key_']):
            key = re.sub('_octets','',item['key_'])
            if int(time.time()) > int(item['lastclock']) + 180:
                output = 0
            else:
                output = int(item['lastvalue'])/1000**2
            result[key] = output
    return result

def __SetSameBandwidth__(band):
    if re.match('m|g', band):
        band = re.sub('m','000',band)
        band = re.sub('g','000000',band)
    band = re.sub('000000$','m',band)
    band = re.sub('g$','000m',band)
    if re.match('m', band):
        re.sub('m','',band)
        band = float(band)/1000
    band = re.sub('m','',band)
    return int(band)

def collectAndSort(router,zabbixaccount):
#grab information
    lsps = findAllLSP(router)
    paths = findAllPath(router)
    routes = findAllRoutes(router)
    lints = findAllLogicalInterfaces(router)
    lspOutput = getLspOutput(router, zabbixaccount)
    lspState = getLSPState(router)

#group information
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
        l.rbandwidth = round(float(output)/l.bandwidth,1)
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

    for interface in interfaces:
        try:
            interface.rsvppercent = round((float(interface.rsvpout)/interface.output)*100,2)
            interface.ldpout = interface.output - interface.rsvpout
        except Exception:
            interface.rsvppercent = 0
            interface.ldpout = 0
    return interfaces

def printInterfaces(interfaces):
    #and print it
    intout = '{name:<14s}{description:<37s}{bandwidth:>11s}{output:>14s}  {rsvpout:<12s}{ldpout:<17s}'
    lspout = '{state:<14s}{name:<37s}{bandwidth:>11s}{output:>14s}  {rbandwidth:<12s}{route:<10s}'

    for interface in sorted(interfaces, key = lambda interface: interface.output, reverse=True):
        print intout.format(name = interface.name,
                            description = '* '+interface.description,
                            bandwidth = '* '+re.sub('Gbps','000',interface.speed),
                            output = '* '+str(interface.output),
                            rsvpout = 'RSVP:'+str(interface.rsvpout),
                            ldpout = 'LDP:'+str(interface.ldpout))
        for lsp in sorted(interface.lsplist, key = lambda lsp: lsp.bandwidth, reverse = True):
            print lspout.format(name = lsp.name,
                                state = lsp.state,
                                bandwidth = str(lsp.bandwidth)+'m',
                                output = str(lsp.output),
                                rbandwidth = str(lsp.rbandwidth)+'m',
                                route = lsp.path.formattedRoute())
        print

host = raw_input('Please enter host: ')
router = mRouter(host)
print "Please enter zabbix logo/pass: "
zabbixaccount = read_login()

value = ''
while value != 'exit':
    os.system('clear')
    print '%s MPLS information' % host
    interfaces = collectAndSort(router,zabbixaccount)
    printInterfaces(interfaces)
    value = raw_input('Type exit for stop: ')
router.close()
