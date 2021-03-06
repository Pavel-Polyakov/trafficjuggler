from TrafficJuggler.executor import Executor
from netaddr import IPNetwork
import time
import re

class Parser(object):
    def __init__(self,hostname):
        self.executor = Executor(hostname)
        self.hostname = hostname

    def close(self):
        self.executor.close()

    def get_time(self):
        h = self.executor.getXMLByCommand('show system uptime').xpath('//system-uptime-information/current-time/date-time')[0].attrib
        for p in h:
            result =  h[p]
        return result

    def get_ibgp_hosts(self):
        result = []
        command = self.executor.getXMLByCommand('show configuration protocol bgp group ibgp')
        rootTree = command.xpath('//configuration/protocols/bgp/group/neighbor')
        for tree in rootTree:
            neighbor = {}
            neighbor['ip'] = tree.find('name').text
            neighbor['description'] = tree.find('description').text
            result.append(neighbor)
        return result

    def get_itself(self):
        command = self.executor.getXMLByCommand('show configuration protocol bgp group ibgp')
        result = {}
        result['description'] = self.hostname
        result['ip'] = command.xpath('string(//configuration/protocols/bgp/group/local-address/text())')
        return result

    def get_lsp_config(self):
        result = []
        command = self.executor.getXMLByCommand('show configuration protocol mpls')
        rootTree = command.xpath('//configuration/protocols/mpls/label-switched-path')
        for tree in rootTree:
            LSP = {}
            name = tree.xpath('string(name/text())')
            to = tree.xpath('string(to/text())')
            bandwidth = tree.xpath('string(bandwidth/per-traffic-class-bandwidth/text())')
            bandwidth = self.convertBandwidthToM(bandwidth)

            try:
                path = tree.xpath('primary/name')[0].text
            except IndexError:
                path = 'dynamic'
            LSP['name'] = name
            LSP['to'] = to
            LSP['bandwidth'] = bandwidth
            LSP['pathname'] = path
            result.append(LSP)
        return result

    def get_path_config(self):
        result = []
        command = self.executor.getXMLByCommand('show configuration protocol mpls')
        rootTree = command.xpath('//configuration/protocols/mpls/path')
        for tree in rootTree:
            PATH = {}
            name = tree.xpath('string(name/text())')
            hops = tree.xpath('path-list')
            route = []
            for hop in hops:
                hop_ip = hop.xpath('string(name/text())')
                hop_type_list = hop.xpath('loose|strict')
                if len(hop_type_list) > 0:
                    hop_type = hop_type_list[0].tag
                else:
                    hop_type = None
                hop_dict = {'ip': hop_ip,
                            'type': hop_type}
                route.append(hop_dict)
            PATH['name'] = name
            PATH['route'] = route
            result.append(PATH)
        return result

    def get_ospf_db(self):
        rpc = self.executor.getXMLByCommand('show ospf database detail')
        return rpc

    def get_interfaces_config(self):
        result = []
        command = self.executor.getXMLByCommand('show configuration interfaces')
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

    def get_lsp_state(self):
        result = {}
        command = self.executor.getXMLByCommand('show mpls lsp unidirectional ingress')
        rootTree = command.xpath('//mpls-lsp-information/rsvp-session-data/rsvp-session')
        for tree in rootTree:
            state = tree.xpath('string(mpls-lsp/lsp-state/text())')
            name = tree.xpath('string(mpls-lsp/name/text())')
            result[name] = state
        return result

    def get_interfaces_state(self):
        result = []
        command = self.executor.getXMLByCommand('show interfaces detail')
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

    def get_lsp_explicit_route(self,name):
        result = []
        command = self.executor.getXMLByCommand('show mpls lsp unidirectional name {name} detail'.format(name=name))
        for address in command.xpath('//explicit-route/address'):
            hop_ip = address.text
            hop_type = address.xpath('string((following-sibling::explicit-route-type)[1]/text())')
            hop_dict = {'ip': hop_ip,
                        'type': hop_type}
            result.append(hop_dict)
        return result

    def get_lsp_output(self):
        return self.__get_average_lsp_bps__(self.__get_lsp_stat_list__())

    def get_prefixes_by_host(self):
        result = []
        ospfdb = self.executor.getXMLByCommand('show ospf database detail netsummary')
        for lsa in ospfdb.xpath('ospf-database-information/ospf-database'):
            host_ip = lsa.xpath('advertising-router')[0].text
            lsa_id = lsa.xpath('lsa-id')[0].text
            mask = lsa.xpath('ospf-summary-lsa/address-mask')[0].text
            prefix = IPNetwork(lsa_id+'/'+mask)
            result.append({'host_ip':host_ip, 'prefix':str(prefix)})
        return result

    def convertBandwidthToM(self,band):
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
        except ValueError:
            band = 0
        return band

    def __get_lsp_output_stat__(self):
        stat_time = self.get_time()
        stat_cli = self.executor.getXMLByCommand('show mpls lsp unidirectional ingress statistics')
        stat_lsps = stat_cli.xpath('//mpls-lsp-information/rsvp-session-data/rsvp-session/mpls-lsp')
        result = {}
        for lsp in stat_lsps:
            name = lsp.xpath('string(name/text())')
            bytes = lsp.xpath('string(lsp-bytes/text())')
            result[name] = bytes
        result['time'] = stat_time
        return result

    def __get_lsp_stat_list__(self,accuracy=5,latency=5):
        result = []
        for x in xrange(0,accuracy):
            result.append(self.__get_lsp_output_stat__())
            time.sleep(latency)
        return result

    def __get_average_lsp_bps__(self,lsp_stats):
        result = {}
        lsp_list = [x[0] for x in lsp_stats[0].items() if x[0] != 'time' and x[0] != 'NA']
        for lsp in lsp_list:
            s = [[int(x[lsp]),float(x['time'])] for x in lsp_stats if x[lsp] != 'NA']
            bps_list = [(s[s.index(x)+1][0]-x[0])/(s[s.index(x)+1][1]-x[1]) for x in s if s[::-1].index(x) != 0]
            if len(bps_list) != 'NA' and len(bps_list)>0:
                bps_average = sum(bps_list)/float(len(bps_list))
                result[lsp] = int((bps_average*8)/(1000**2))
        return result
