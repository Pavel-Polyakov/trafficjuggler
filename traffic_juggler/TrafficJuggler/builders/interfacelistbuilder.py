from TrafficJuggler.models.interfacelist import InterfaceList
from TrafficJuggler.models.interface import Interface

class InterfaceListBuilder(object):
    def __init__(self, parser):
        self.parser = parser

    def create(self,nexthop_interfaces_from_lsplist,nexthop_interfaces_output):
        interfacelist = InterfaceList()
        interfaces_fromcli = self.parser.get_interfaces_state()

        for interface in nexthop_interfaces_from_lsplist:
            interface_name = interface
            try:
                interface_fromcli = next(i for i in interfaces_fromcli if i['name'] == interface_name)
            except Exception:
                interface_fromcli = {'name': 'None', 'speed': '0Gbps', 'output': 0}
            interface_speed = interface_fromcli.get('speed', 'None')
            interface_output = interface_fromcli.get('output', 'None')
            interface_description = interface_fromcli.get('description', 'None')
            #it's very strange, need to recreate
            try:
                interface_rsvpout = next((x[interface] for x in nexthop_interfaces_output if x.get(interface) != None))
            except StopIteration:
                interface_rsvpout = 'None'
            interface_ldpout = interface_output - interface_rsvpout
            if interface_ldpout < 0 or abs(interface_ldpout) < 150:
                interface_ldpout = 0

            interfacelist.append(Interface(name = interface_name,
                                        description = interface_description,
                                        speed = interface_speed,
                                        output = interface_output,
                                        rsvpout = interface_rsvpout,
                                        ldpout = interface_ldpout))
        return interfacelist
