class Router(object):
    def __init__(self,hostname,lsplist,interfacelist,neighbors,last_parse):
        self.hostname = hostname
        self.lsplist = lsplist
        self.interfacelist = interfacelist
        self.neighbors = neighbors
        self.last_parse = last_parse

    def __repr__(self):
        return "mRouter %s" % self.hostname
