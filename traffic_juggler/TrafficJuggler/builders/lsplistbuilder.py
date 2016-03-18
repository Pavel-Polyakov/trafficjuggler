from TrafficJuggler.models.lsp import LSP
import re

class LSPListBuilder(object):
    def __init__(self, parser):
        self.parser = parser

    def create(self):
        lsplist = []
        lsp_fromconfig = self.parser.get_lsp_config()
        path_fromconfig = self.parser.get_extended_path_config()
        lsp_state_fromcli = self.parser.get_lsp_state()
        lsp_output_fromcli = self.parser.get_lsp_output()

        for lsp in lsp_fromconfig:
            # NAME
            lsp_name = lsp['name']

            # TO
            lsp_to = lsp['to']

            # PATH
            path_name = lsp['pathname']
            if path_name != 'dynamic':
                path_route = next(p['route'] for p in path_fromconfig if p['name'] == path_name)
                if not self.__isLooseInPath__(path_route):
                    # without loose
                    lsp_path = self.__formattedPathWithoutType__(path_route)
                else:
                    # with loose in the path
                    lsp_real_path_list = self.parser.get_lsp_explicit_route(lsp_name)
                    lsp_real_path = self.__formattedPathWithoutType__(lsp_real_path_list)
                    lsp_configured_path = self.__formattedPathWithType__(path_route)
                    lsp_path = '{real} (configured: {conf})'.\
                                            format(real = lsp_real_path,
                                                   conf = lsp_configured_path)
            else:
                # dynamic path
                lsp_real_path_list = self.parser.get_lsp_explicit_route(lsp_name)
                lsp_real_path = self.__formattedPathWithoutType__(lsp_real_path_list)
                lsp_path = '{real} (dynamic)'.format(real = lsp_real_path)

            # STATE
            lsp_state = lsp_state_fromcli.get(lsp_name,'Inactive')

            # OUTPUT
            lsp_output = lsp_output_fromcli.get(lsp_name, None)
            if lsp_output != None:
                lsp_output = int(lsp_output)

            # BANDWIDTH
            lsp_bandwidth = lsp.get('bandwidth', None)
            if lsp_bandwidth != None:
                lsp_bandwidth = int(lsp_bandwidth)

            # RBANDWIDTH
            if (lsp_state != 'Inactive' and lsp_state != 'Dn' and lsp_output != None and lsp_bandwidth != None and lsp_bandwidth != 0):
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

    def __formattedPathWithType__(self,path_route):
        route = []
        for r in path_route:
            if r['type'] != None:
                route.append(r['ip']+r['type'][0].upper())
            else:
                route.append(r['ip'])
        path_formatted = self.__niceJoin__(route)
        return path_formatted

    def __formattedPathWithoutType__(self,path_route):
        route = [x['ip'] for x in path_route]
        path_formatted = self.__niceJoin__(route)
        return path_formatted

    def __niceJoin__(self,route):
        match = re.compile('(?<=\.\d\d$)')
        route = " - ".join(match.sub(' ', str(x)) for x in route)
        return route

    def __isLooseInPath__(self,path):
        if len([x for x in path if x['type'] == 'loose']) > 0:
            return True
        else:
            return False
