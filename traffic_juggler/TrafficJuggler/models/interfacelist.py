class InterfaceList(list):
    def __init__(self, *args):
        list.__init__(self, *args)

    def printInterfaceList(self):
        for interface in self:
            interface.printInterface()

    def sortByOutput(self):
        newlist = InterfaceList()
        newlist.extend(self)
        newlist.sort(key = lambda interface: interface.output, reverse = True)
        return newlist
