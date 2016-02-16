from TrafficJuggler.builders.dbbuilder import session
from TrafficJuggler.builders.imagebuilder import ImageBuilder
from TrafficJuggler.parser import Parser
from time import strftime, sleep

HOST = 'm9-r0'
parser = Parser(HOST)
rb = ImageBuilder(HOST, session, parser)

while True:
    rb.parse()
    print 'OK', strftime("%Y-%m-%d %H:%M:%S")
    sleep(1800)
