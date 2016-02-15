from TrafficJuggler.builders.dbbuilder import session
from TrafficJuggler.builders.imagebuilder import ImageBuilder
from TrafficJuggler.parser import Parser
import time

HOST = 'm9-r0'
parser = Parser(HOST)
rb = ImageBuilder(HOST, session, parser)
rb.parse()
print 'OK'
