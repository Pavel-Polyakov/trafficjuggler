from TrafficJuggler.models.host import Host


class HostBuilder(object):
    def __init__(self, parser):
        self.parser = parser

    def create(self):
        result = []
        neighbors = self.parser.get_ibgp_neighbors()
        for n in neighbors:
            result.append(Host(name = n['description'], ip = n['ip']))
        return result
