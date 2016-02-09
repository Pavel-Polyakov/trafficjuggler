from TrafficJuggler.models.lsplist import LSPList
from TrafficJuggler.models.lsp import LSP
from netaddr import IPNetwork, IPAddress

class LSPListBuilder(object):
    def __init__(self, parser):
        self.parser = parser

    def create(self):
        lsplist = LSPList()
        lsp_fromconfig = self.parser.get_lsp_config()
        path_fromconfig = self.parser.get_path_config()
        routes_fromconfig = self.parser.get_routes()
        lsp_state_fromcli = self.parser.get_lsp_state()
        lsp_output_fromcli = self.parser.get_lsp_output()
        ibgp_neighbors = self.parser.get_ibgp_neighbors()

        for lsp in lsp_fromconfig:
            lsp_name = lsp['name']
            lsp_to = lsp['to']
            lsp_to_name = next(x['description'] for x in ibgp_neighbors if x['ip'] == lsp_to)
            lsp_bandwidth = lsp['bandwidth']
            path_name = lsp['pathname']
            path_route = next(p['route'] for p in path_fromconfig if p['name'] == path_name)
            nexthop_ip = path_route[0]
            nexthop_interface = next(r['name'] for r in routes_fromconfig if IPAddress(nexthop_ip) in IPNetwork(r['destination']))
            lsp_state = lsp_state_fromcli.get(lsp_name,'Inactive')
            lsp_output = lsp_output_fromcli.get(lsp_name,'None')

            if (lsp_state != 'Inactive' and str(lsp_output) != 'None'):
                lsp_rbandwidth = round(float(lsp_output)/int(lsp_bandwidth),1)
                lsp_rbandwidth = str(lsp_rbandwidth)
            else:
                lsp_rbandwidth = "None"

            if (str(lsp_bandwidth) != "None"):
                lsp_bandwidth = str(lsp_bandwidth)

            if lsp_output == 0:
                lsp_output = "0"

            lsplist.append(LSP(name = lsp_name,
                                to = lsp_to,
                                to_name = lsp_to_name,
                                path = path_route,
                                bandwidth = lsp_bandwidth,
                                rbandwidth = lsp_rbandwidth,
                                state = lsp_state,
                                output = lsp_output,
                                nexthop_interface = nexthop_interface))
        return lsplist
