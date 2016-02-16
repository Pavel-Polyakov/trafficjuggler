from TrafficJuggler.util import convertToGbps
import re

class LSPList(list):
    def __init__(self, *args):
        list.__init__(self, *args)

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

    def getLSPByInterfaceId(self,interface):
        newlist = LSPList()
        for l in self:
            if l.interface_id == interface:
                newlist.append(l)
        return newlist

    def getLSPByState(self,state):
        newlist = LSPList()
        for l in self:
            if l.state == state:
                newlist.append(l)
        return newlist

    def getNextHopInterfaces(self):
        newlist = []
        for x in set([x.nexthop_interface for x in self]):
            newlist.append(x)
        return newlist

    def getOutputOfNextHopInterfaces(self):
        newlist = []
        interfaces = self.getNextHopInterfaces()
        for interface in interfaces:
            newlist.append({interface: self.getLSPByInterface(interface).getSumOutput()})
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
        return sum(int(x.output) for x in self if x.output != None and x.output != 'Down')

    def getSumOutputGbps(self):
        return convertToGbps(self.getSumOutput())

    def getSumBandwidth(self):
        return sum([x.bandwidth for x in self if x.bandwidth != None])

    def getAverageRBandwidthByHost(self,host):
        LSPByHost = [l for l in self.getLSPByHost(host) if l.output != None and l.output != 'Down']
        try:
            RBandwidthList = [l.rbandwidth for l in LSPByHost]
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
