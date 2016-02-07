#!/usr/bin/env python
import re
import time
import os
import cPickle as pickle
import sys
from Exscript.util.interact import read_login
from Exscript.protocols import SSH2
from lxml import etree
from netaddr import IPNetwork, IPAddress
from zabbix.api import ZabbixAPI

class mExecutor(object):
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

    def get_time(self):
            return int(self.execute('show system uptime').xpath('//system-uptime-information/current-time/date-time')[0].attrib['{http://xml.juniper.net/junos/12.3R8/junos}seconds'])

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

class mRouter(object):
    def __init__(self,host):
        self.name = host

    def parse(self,executor):
        self.neighbors = self.__find_ibgp_neighbors__(executor)
        lsplist = LSPList()
        lsplist.parse(executor,self.neighbors)
        intlist = InterfaceList()
        intlist.parse(executor,lsplist)
        self.lsplist = lsplist
        self.intlist = intlist
        self.last_parse = time.asctime(time.localtime(time.time()))

    def __repr__(self):
        return "mRouter %s" % self.name

    def __find_ibgp_neighbors__(self,executor):
        result = []
        command = executor.execute('show configuration protocol bgp group ibgp')
        rootTree = command.xpath('//configuration/protocols/bgp/group/neighbor')
        for tree in rootTree:
            neighbor = {}
            neighbor['ip'] = tree.find('name').text
            neighbor['description'] = tree.find('description').text
            result.append(neighbor)
        return result

class mLSP(object):
    def __init__(self,name,to,to_name,bandwidth,path,state,output,nexthop_interface,rbandwidth):
        self.name = name
        self.to = to
        self.to_name = to_name
        self.bandwidth = bandwidth
        self.path = path
        self.path_formatted = self.__formattedRoute__(self.path)
        self.state = state
        self.output = output
        self.output_gbps = convertToGbps(self.output)
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
        self.output_gbps = convertToGbps(output)
        self.rsvpout = rsvpout
        self.ldpout = ldpout
        self.utilization = self.__getUtilization__()

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

    def __getUtilization__(self):
        if self.speed != '0Gbps':
            speed = re.sub('Gbps','000',self.speed)
            return int(round(self.output/float(speed)*100,2))
        else:
            return 0

class LSPList(list):
    def __init__(self, *args):
        list.__init__(self, *args)

    def parse(self,router,ibgp_neighbors):
        self.__setApi__(router)
        lsp_fromconfig = self.__find_lsp_fromconfig__()
        path_fromconfig = self.__find_path_fromconfig__()
        routes_fromconfig = self.__find_routes_fromconfig__()
        lsp_state_fromcli = self.__find_lsp_state_fromcli__()
        lsp_output_fromcli = self.__find_lsp_output_fromcli__()

        for LSP in lsp_fromconfig:
            lsp_name = LSP['name']
            lsp_to = LSP['to']
            lsp_to_name = next(x['description'] for x in ibgp_neighbors if x['ip'] == lsp_to)
            lsp_bandwidth = LSP['bandwidth']
            path_name = LSP['pathname']
            path_route = next(p['route'] for p in path_fromconfig if p['name'] == path_name)
            nexthop_ip = path_route[0]
            nexthop_interface = next(r['name'] for r in routes_fromconfig if IPAddress(nexthop_ip) in IPNetwork(r['destination']))
            lsp_state = lsp_state_fromcli.get(lsp_name,'Inactive')
            lsp_output = lsp_output_fromcli.get(lsp_name,'None')

            if (lsp_state != 'Inactive' and str(lsp_output) != 'None'):
                lsp_rbandwidth = round(float(lsp_output)/lsp_bandwidth,1)
                lsp_rbandwidth = str(lsp_rbandwidth)
            else:
                lsp_rbandwidth = "None"
            if (str(lsp_bandwidth) != "None"):
                lsp_bandwidth = str(lsp_bandwidth)

            if lsp_output == 0:
                lsp_output = "Down"


            self.append(mLSP(name = lsp_name,
                                to = lsp_to,
                                to_name = lsp_to_name,
                                path = path_route,
                                bandwidth = lsp_bandwidth,
                                rbandwidth = lsp_rbandwidth,
                                state = lsp_state,
                                output = lsp_output,
                                nexthop_interface = nexthop_interface))
        for lsp in self:
            if lsp.output == "None" and lsp.state == "Up":
                lsp.output_calculated = self.getCalculatedOutputForLSP(lsp)
                lsp.output_calculated_gpbs = convertToGbps(lsp.output_calculated)
                lsp.rbandwidth_calculated = self.getAverageRBandwidthByHost(lsp.to)

        self.__unsetApi__()

    def __setApi__(self,router):
        self.router = router
        #self.zabbixapi = zabbixapi

    def __unsetApi__(self):
        self.router = None
        #self.zabbixapi = None

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
        return sum(int(x.output) for x in self if x.output != 'None' and x.output != 'Down')

    def getSumOutputGbps(self):
        return convertToGbps(self.getSumOutput())

    def getSumBandwidth(self):
        return sum([int(re.sub('m','',x.bandwidth)) for x in self if x.bandwidth != 'None'])

    def getAverageRBandwidthByHost(self,host):
        LSPByHost = [l for l in self.getLSPByHost(host) if l.output != 'None' and l.output != 'Down']
        try:
            RBandwidthList = [float(re.sub('m','',str(l.rbandwidth))) for l in LSPByHost]
        except Exception:
            pass
        AllLSP = len(LSPByHost)
        if AllLSP != 0:
            return round(float(sum(RBandwidthList))/AllLSP, 2)
        else:
            return 0

    def getCalculatedOutputForLSP(self,lsp):
        host = lsp.to
        band = lsp.bandwidth
        rband = self.getAverageRBandwidthByHost(host)
        return int(int(band)*rband)

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

    def __find_lsp_output_fromcli__(self):
        return self.__get_average_lsp_bps__(self.__get_lsp_stat_list__())

    def __get_lsp_output_stat__(self):
        stat_time = self.router.get_time()
        stat_cli = self.router.execute('show mpls lsp unidirectional ingress statistics')
        stat_lsps = stat_cli.xpath('//mpls-lsp-information/rsvp-session-data/rsvp-session/mpls-lsp')
        result = {}
        for lsp in stat_lsps:
            name = lsp.xpath('string(name/text())')
            bytes = lsp.xpath('string(lsp-bytes/text())')
            result[name] = bytes
        result['time'] = stat_time
        return result

    def __get_lsp_stat_list__(self,accuracy=5,latency=2):
        result = []
        for x in xrange(0,accuracy):
            result.append(self.__get_lsp_output_stat__())
            time.sleep(latency)
        return result

    def __get_average_lsp_bps__(self,lsp_stats):
        result = {}
        lsp_list = [x[0] for x in lsp_stats[0].items() if x[0] != 'time']
        for lsp in lsp_list:
            s = [[int(x[lsp]),float(x['time'])] for x in lsp_stats]
            bps_list = [(s[s.index(x)+1][0]-x[0])/(s[s.index(x)+1][1]-x[1]) for x in s if s[::-1].index(x) != 0]
            bps_average = sum(bps_list)/float(len(bps_list))
            result[lsp] = (bps_average*8)/(1000*1000)
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

    def parse(self,router,lsplist):
        self.__setApi__(router,lsplist)
        interfaces_fromcli = self.__find_interfaces_fromcli__()

        for interface in self.lsplist.getAllInterfaces():
            interface_name = interface
            try:
                interface_fromcli = next(i for i in interfaces_fromcli if i['name'] == interface_name)
            except Exception:
                interface_fromcli = {'name': 'None', 'speed': '0Gbps', 'output': 0}
            interface_speed = interface_fromcli.get('speed', 'None')
            interface_output = interface_fromcli.get('output', 'None')
            interface_description = interface_fromcli.get('description', 'None')
            interface_rsvpout = self.lsplist.getLSPByInterface(interface_name).getSumOutput()
            interface_ldpout = interface_output - interface_rsvpout

            self.append(mInterface(name = interface_name,
                                        description = interface_description,
                                        speed = interface_speed,
                                        output = interface_output,
                                        rsvpout = interface_rsvpout,
                                        ldpout = interface_ldpout))
        self.__unsetApi__()

    def __setApi__(self,router,lsplist):
        self.router = router
        self.lsplist = lsplist

    def __unsetApi__(self):
        self.router = None
        self.lsplist = None

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

def convertToGbps(value):
    if value != 'None' and value != 'Down':
        return str(round(float(value)/1000,2))

def getZApi():
    print "Please enter zabbix account information"
    zabbixaccount = read_login()
    zapi = ZabbixAPI(url='http://zabbix.ihome.ru', user=zabbixaccount.name, password=zabbixaccount.password)
    return zapi

def loaditems(file):
    try:
        with open('%s.pkl' % (file) ,'rb') as fr:
            items = pickle.load(fr)
        return items
    except IOError:
        return []

def writeitems(file,items):
    with open('%s.pkl' % (file),'wb') as fr:
        pickle.dump(items,fr)

if __name__ == "__main__":
    if len(sys.argv)>1 and sys.argv[1] == "load":
        router = loaditems(sys.argv[2])
    else:
        #zapi = getZApi()
        host = raw_input('Please enter host: ')
        executor = mExecutor(host)
        router = mRouter(host)
        router.parse(executor)
        executor.close()
        if len(sys.argv)>1 and sys.argv[1] == "save":
            writeitems(sys.argv[2],router)

    print "\nSummary information"
    for interface in router.intlist.sortByOutput():
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
    for interface in router.intlist.sortByOutput():
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
