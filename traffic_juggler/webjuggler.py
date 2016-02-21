from flask import Flask, render_template, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
from TrafficJuggler.models.lsp import LSP
from TrafficJuggler.models.lsplist import LSPList
from TrafficJuggler.models.interface import Interface
from TrafficJuggler.models.interfacelist import InterfaceList
from TrafficJuggler.models.host import Host
from TrafficJuggler.models.image import Image
from TrafficJuggler.parser import Parser
from TrafficJuggler.builders.imagebuilder import ImageBuilder
from pytz import timezone
from sqlalchemy.orm import sessionmaker
import logging, sys

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pyplot as PLT
from matplotlib import dates
from statsmodels.nonparametric.smoothers_lowess import lowess

import StringIO
import time
import datetime
from datetime import date, timedelta, datetime

from TrafficJuggler.config import FULL_PATH

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{path}tj.db'.format(path=FULL_PATH)
db = SQLAlchemy(app)
session = db.session

logging.basicConfig(stream=sys.stderr)

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

@app.route('/update')
def update():
    HOST = 'm9-r0'
    parser = Parser(HOST)
    rb = ImageBuilder(HOST, session, parser)
    rb.parse()
    return redirect('/')

@app.route('/lsp/<key>.png')
def plot_lsp(key):
    response = getGraph(LSP, key)
    return response

@app.route('/interface/<key>.png')
def plot_interface(key):
    response = getGraph(Interface, key)
    return response

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

def getGraph(Type, key):
    xy = session.query(Type.output, Image.time).\
            filter(Type.name == key).\
            filter(Type.image_id == Image.id).\
            filter(Image.time > datetime.now() - timedelta(days=1, hours=3)).\
            all()
    x = [k[1] for k in xy]
    y = [k[0] for k in xy]
    for yv in y:
        if str(yv) == 'None':
            y[y.index(yv)] = 0
    x = map(lambda k: k + timedelta(hours=3), x)
    x_unixtime = map(lambda k: time.mktime(k.timetuple()), x)
    xy_smooth = lowess(y, x_unixtime, frac = 0.025)
    y_smooth = xy_smooth[:,1]

    fig = Figure(figsize=(16,6), dpi=80)
    fig.autofmt_xdate()
    fig.set_facecolor('white')

    axis = fig.add_subplot(1, 1, 1)
    axis.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))
    axis.xaxis.set_major_locator(dates.HourLocator(byhour=range(0,24,1)))
    axis.plot(x, y_smooth, color='#337AB7')
    axis.fill_between(x,y_smooth, facecolor='#337AB7')
    axis.grid(True)
    # axis.set_title(key)
    axis.set_ylabel('LSP Output, MBps')
    axis.set_xlabel('\n%s - %s' % (x[0],x[-1]))
    axis.set_ylim(bottom=0)

    canvas = FigureCanvas(fig)
    output = StringIO.StringIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

if __name__ == '__main__':

    app.run(
#        host = "127.0.0.1",
        host = "0.0.0.0",
        debug = True
    )
