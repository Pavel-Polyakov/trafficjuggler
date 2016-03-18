from TrafficJuggler.models.prefix import Prefix


class PrefixBuilder(object):
    def __init__(self, parser):
        self.parser = parser

    def create(self):
        result = []
        prefixes = self.parser.get_prefixes_by_host()
        for p in prefixes:
            result.append(Prefix(name = p['prefix'], host_ip = p['host_ip']))
        return result
