from Exscript.util.interact import read_login
from Exscript.protocols import SSH2
from lxml import etree
import re

class Executor(object):
    def __init__(self,host):
        self.__create__(host)

    def getXMLByCommand(self,command):
        self.conn.execute('%s | display xml | no-more' % command)
        output = self.conn.response
        rpc = re.sub('^(.|\r|\r\n)*(?=<rpc-reply)|(?<=<\/rpc-reply>)(.|\r|\r\n)*$','',output)
        rpc = re.sub('xmlns="','xmlns:junos="',rpc)
        tree = etree.fromstring(rpc)
        return tree

    def close(self):
        self.conn.send('exit\r')
        self.conn.send('exit\r')
        self.conn.close()

    def __create__(self,host):
        account = read_login()
        self.name = host
        self.conn = SSH2()
        if self.conn.connect(host):
            print 'Connected'
            self.conn.login(account)
            self.conn.execute('cli')
        else:
            print 'Does not connected. Please check your input'
            sys.exit()
