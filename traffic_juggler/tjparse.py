from TrafficJuggler.builders.dbbuilder import session
from TrafficJuggler.builders.routerbuilder import RouterBuilder

HOST = 'm9-r0'
rb = RouterBuilder(HOST,session)
rb.parse()
print 'OK'
