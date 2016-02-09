from TrafficJuggler.util import convertToGbps
import re

class Interface(object):
    def __init__(self,name,description,speed,output,rsvpout,ldpout):
        self.name = name
        self.description = description
        self.speed = speed
        self.output = output
        self.output_gbps = convertToGbps(output)
        self.rsvpout = rsvpout
        self.ldpout = ldpout
        self.utilization = self.GetUtilization()

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

    def GetUtilization(self):
        if self.speed != '0Gbps':
            speed = re.sub('Gbps','000',self.speed)
            return int(round(self.output/float(speed)*100,2))
        else:
            return 0
