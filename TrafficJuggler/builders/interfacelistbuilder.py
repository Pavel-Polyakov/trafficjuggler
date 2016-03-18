from TrafficJuggler.models.interface import Interface
import re

class InterfaceListBuilder(object):
    def __init__(self, parser):
        self.parser = parser

    def create(self,nexthop_interfaces_from_lsplist):
        interfacelist = []
        interfaces_fromcli = self.parser.get_interfaces_state()

        for interface in nexthop_interfaces_from_lsplist:
            interface_name = interface
            try:
                interface_fromcli = next(i for i in interfaces_fromcli if i['name'] == interface_name)
            except ValueError:
                interface_fromcli = {'name': 'None', 'speed': None, 'output': 0}
            interface_speed = interface_fromcli.get('speed', None)
            if interface_speed == 'Unspecified':
                interface_speed = None
            interface_output = interface_fromcli.get('output', None)
            interface_description = interface_fromcli.get('description', 'None')

            if interface_speed != None:
                interface_speed = re.sub('Gbps', '000', interface_speed)
                interface_utilization = self.__getUtilization__(speed=interface_speed,output=interface_output)
            else:
                interface_utilization = None

            interfacelist.append(Interface(name = interface_name,
                                        description = interface_description,
                                        speed = interface_speed,
                                        output = interface_output,
                                        utilization = interface_utilization,
                                        ))
        return interfacelist

    def __getUtilization__(self,speed,output):
        return int(round(output/float(speed)*100,2))
