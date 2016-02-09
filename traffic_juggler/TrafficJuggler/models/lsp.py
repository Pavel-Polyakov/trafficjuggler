from TrafficJuggler.util import convertToGbps
import re

class LSP(object):
    def __init__(self,name,to,to_name,path,bandwidth,rbandwidth,state,output,nexthop_interface):
        self.name = name
        self.to = to
        self.to_name = to_name
        self.path = path
        self.path_formatted = self.__formattedRoute__(self.path)
        self.bandwidth = bandwidth
        self.rbandwidth = rbandwidth
        self.state = state
        self.output = output
        self.output_gbps = convertToGbps(self.output)
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
