from flask import Flask, render_template, request
from TrafficJuggler.builders.dbbuilder import session
from TrafficJuggler.models.lsp import LSP
from TrafficJuggler.models.lsplist import LSPList
from TrafficJuggler.models.interface import Interface
from TrafficJuggler.models.interfacelist import InterfaceList
from TrafficJuggler.models.host import Host
from TrafficJuggler.models.image import Image

app = Flask(__name__)

@app.route('/')
def index():
    neighbors = session.query(Host).all()
    image_id_last = session.query(Image).all()[-1].id
    
    lsplist_frombase = session.query(LSP).filter(LSP.image_id == image_id_last).all()
    lsplist = LSPList()
    lsplist.extend(lsplist_frombase)
    
    interfacelist_frombase = session.query(Interface).filter(Interface.image_id == image_id_last).all()
    interfacelist = InterfaceList()
    interfacelist.extend(interfacelist_frombase)

    hosts = [{'ip': x} for x in lsplist.getAllHostsSortedByOutput()]
    for host in hosts:
        ip = host['ip']
        host['name'] = next(x.name for x in neighbors if x.ip == ip)
        host['sumbandwidth'] = str(lsplist.getLSPByHost(ip).getSumBandwidth())
        host['sumoutput'] = lsplist.getLSPByHost(ip).getSumOutputGbps()
        host['rbandwidth'] = str(lsplist.getAverageRBandwidthByHost(ip))
        host['lsplist'] = [x.__dict__ for x in lsplist.getLSPByHost(ip).sortByOutput()]
        host['sumoutput_calculated'] = float(host['sumoutput']) + \
            sum(float(x.output_calculated_gpbs) for x in lsplist.getLSPByHost(ip) if hasattr(x, 'output_calculated_gpbs'))

    interfaces = [x.__dict__ for x in interfacelist.sortByOutput()]
    for interface in interfaces:
        interface['lsplist'] = [x.__dict__ for x in lsplist.getLSPByInterfaceId(interface['id']).sortByOutput()]
        interface['rsvpout'] = lsplist.getLSPByInterfaceId(interface['id']).getSumOutput()
        interface['ldpout'] = interface['output'] - interface['rsvpout']

    return render_template('index.html', interfaces=interfaces, hosts=hosts)

if __name__ == '__main__':
    app.run(
#        host = "127.0.0.1",
        host = "0.0.0.0",
        debug = True
    )
