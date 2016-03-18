from TrafficJuggler.models.host import Host


class HostBuilder(object):
    def __init__(self, parser):
        self.parser = parser

    def create(self):
        result = []
        neighbors = self.parser.get_ibgp_hosts()
        itself = self.parser.get_itself()
        result.append(Host(name = itself['description'], ip = itself['ip']))
        for n in neighbors:
            result.append(Host(name = n['description'], ip = n['ip']))
        return result
