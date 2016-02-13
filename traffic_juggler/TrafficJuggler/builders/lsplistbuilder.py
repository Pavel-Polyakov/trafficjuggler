from TrafficJuggler.models.lsplist import LSPList
from TrafficJuggler.models.lsp import LSP
import re

class LSPListBuilder(object):
    def __init__(self, parser):
        self.parser = parser

    def create(self):
        lsplist = LSPList()
        lsp_fromconfig = self.parser.get_lsp_config()
        path_fromconfig = self.parser.get_path_config()
        lsp_state_fromcli = self.parser.get_lsp_state()
        lsp_output_fromcli = self.parser.get_lsp_output()

        for lsp in lsp_fromconfig:
            lsp_name = lsp['name']
            lsp_to = lsp['to']

            path_name = lsp['pathname']
            path_route = next(p['route'] for p in path_fromconfig if p['name'] == path_name)
            lsp_path = self.__formattedRoute__(path_route)

            lsp_state = lsp_state_fromcli.get(lsp_name,'Inactive')

            lsp_output = lsp_output_fromcli.get(lsp_name, None)
            if lsp_output != None:
                lsp_output = int(lsp_output)

            lsp_bandwidth = lsp.get('bandwidth', None)
            if lsp_bandwidth != None:
                lsp_bandwidth = int(lsp_bandwidth)

            if (lsp_state != 'Inactive' and lsp_output != None and lsp_bandwidth != None):
                lsp_rbandwidth = round(float(lsp_output)/lsp_bandwidth,1)
                lsp_rbandwidth = float(lsp_rbandwidth)
            else:
                lsp_rbandwidth = None

            lsplist.append(LSP(name = lsp_name,
                                to = lsp_to,
                                path = lsp_path,
                                bandwidth = lsp_bandwidth,
                                rbandwidth = lsp_rbandwidth,
                                state = lsp_state,
                                output = lsp_output,
                                ))

        return lsplist

    def __formattedRoute__(self,route):
        match = re.compile('(?<=\.\d\d$)')
        route = " - ".join(match.sub(' ', str(x)) for x in route)
        return route
