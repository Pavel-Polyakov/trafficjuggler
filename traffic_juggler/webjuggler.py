from flask import Flask, render_template, request
from TrafficJuggler.builders.dbbuilder import session
from TrafficJuggler.models.lsp import LSP
from TrafficJuggler.models.lsplist import LSPList
from TrafficJuggler.models.interface import Interface
from TrafficJuggler.models.interfacelist import InterfaceList
from TrafficJuggler.models.host import Host
from TrafficJuggler.models.image import Image

from pytz import timezone
app = Flask(__name__)


@app.route('/')
def index():
    neighbors = session.query(Host).all()
    last_image_id = session.query(Image).all()[-1].id
    last_parse = getLastParse()
    lsplist = getLSPListByImageId(last_image_id)
    interfacelist = getInterfaceListByImageId(last_image_id)

    for l in lsplist:
       l.to_name = next(x.name for x in neighbors if x.ip == l.to)

    hosts = [{'ip': x} for x in lsplist.getAllHostsSortedByOutput()]
    for host in hosts:
        ip = host['ip']
        host['name'] = next(x.name for x in neighbors if x.ip == ip)
        host['sumbandwidth'] = str(lsplist.getLSPByHost(ip).getSumBandwidth())
        host['sumoutput'] = lsplist.getLSPByHost(ip).getSumOutputGbps()
        host['rbandwidth'] = str(lsplist.getAverageRBandwidthByHost(ip))
        host['lsplist'] = [x.__dict__ for x in lsplist.getLSPByHost(ip).sortByOutput()]

    interfaces = [x.__dict__ for x in interfacelist.sortByOutput()]
    for interface in interfaces:
        interface['lsplist'] = [x.__dict__ for x in lsplist.getLSPByInterfaceId(interface['id']).sortByOutput()]
        interface['rsvpout'] = lsplist.getLSPByInterfaceId(interface['id']).getSumOutput()
        interface['ldpout'] = interface['output'] - interface['rsvpout']
        if interface['ldpout'] < 100:
            interface['ldpout'] = 0

    return render_template('index.html',
                            interfaces=interfaces,
                            hosts=hosts,
                            last_parse=last_parse)

def getLastParse():
    last_parse = session.query(Image).all()[-1].time
    utc = timezone('UTC')
    mow = timezone('Europe/Moscow')
    return utc.localize(last_parse).astimezone(mow).ctime()

def getLSPListByImageId(id):
    lsplist_frombase = session.query(LSP).filter(LSP.image_id == id).all()
    lsplist = LSPList()
    lsplist.extend(lsplist_frombase)
    return lsplist

def getInterfaceListByImageId(id):
    interfacelist_frombase = session.query(Interface).filter(Interface.image_id == id).all()
    interfacelist = InterfaceList()
    interfacelist.extend(interfacelist_frombase)
    return interfacelist


if __name__ == '__main__':
    app.run(
#        host = "127.0.0.1",
        host = "0.0.0.0",
        debug = True
    )
