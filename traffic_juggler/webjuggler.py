from flask import Flask, render_template, request
from TrafficJuggler.parser import Parser
from TrafficJuggler.builders.routerbuilder import RouterBuilder
from TrafficJuggler.util import loaditems

app = Flask(__name__)

@app.route('/')
def index():
    router = builder.create()
#    router = loaditems('m9-r0')

    hosts = [{'ip': x} for x in router.lsplist.getAllHostsSortedByOutput()]
    for host in hosts:
        ip = host['ip']
        host['name'] = next(x['description'] for x in router.neighbors if x['ip'] == ip)
        host['sumbandwidth'] = str(router.lsplist.getLSPByHost(ip).getSumBandwidth())
        host['sumoutput'] = router.lsplist.getLSPByHost(ip).getSumOutputGbps()
        host['rbandwidth'] = str(router.lsplist.getAverageRBandwidthByHost(ip))
        host['lsplist'] = [x.__dict__ for x in router.lsplist.getLSPByHost(ip).sortByOutput()]
        host['sumoutput_calculated'] = float(host['sumoutput']) + sum(float(x.output_calculated_gpbs) for x in router.lsplist.getLSPByHost(ip) if hasattr(x, 'output_calculated_gpbs'))
    interfaces = [x.__dict__ for x in router.interfacelist.sortByOutput()]
    for interface in interfaces:
        interface['lsplist'] = [x.__dict__ for x in router.lsplist.getLSPByInterface(interface['name']).sortByOutput()]

    return render_template('index.html', interfaces=interfaces, hosts=hosts)

if __name__ == '__main__':
    HOST = 'm9-r0'
    parser = Parser(HOST)
    builder = RouterBuilder(HOST,parser)
    app.run(
#        host = "127.0.0.1",
        host = "0.0.0.0",
        debug = True
    )
