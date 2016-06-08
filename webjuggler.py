from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from copy import copy
import logging
import sys
import re
import numpy as np

from config import FULL_PATH, HOSTS
from TrafficJuggler.models.lsp import LSP
from TrafficJuggler.models.interface import Interface
from TrafficJuggler.models.host import Host
from TrafficJuggler.models.image import Image
from plotter import getGraph


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://tj:trafficjuggler@localhost/tj'
db = SQLAlchemy(app)
db.create_all()

session = db.session

logging.basicConfig(stream=sys.stderr)


@app.route('/')
def index():
    routers = []
    for host in HOSTS:
        r = {}

        last_parse = session.query(Image).filter(Image.router == host).all()[-1]
        last_parse_id = last_parse.id
        last_parse_time = last_parse.time
        r['name'] = host
	r['interfaces'] = getInterfacesByImageId(last_parse_id)
        r['hosts'] = getHostsByImageId(last_parse_id)
        r['last_parse'] = last_parse_time
        routers.append(r)
    devices = session.query(Host).all()
    return render_template('index.html',
                           routers=routers,
                           devices=devices)


@app.route('/<router>/lsp/<key>.png')
def plot_lsp(router, key):
    xy = session.query(LSP.output, Image.time).\
            filter(Image.router == router).\
            filter(LSP.name == key).\
            filter(LSP.image_id == Image.id).\
            filter(Image.time > datetime.now() - timedelta(days=1, hours=3)).\
            all()
    x = [k[1] for k in xy]
    y = [k[0] for k in xy]
    y = [0 if k is None else k for k in y]
    return getGraph(x, y)


@app.route('/<router>/interface/<key>.png')
def plot_interface(router, key):
    xy = session.query(Interface.output, Image.time).\
            filter(Image.router == router).\
            filter(Interface.description == key).\
            filter(Interface.image_id == Image.id).\
            filter(Image.time > datetime.now() - timedelta(days=1, hours=3)).\
            all()
    x = [k[1] for k in xy]
    y = [k[0] for k in xy]
    y = [0 if k is None else k for k in y]
    return getGraph(x, y)


@app.route('/<router>/host/<key>.png')
def plot_host(router, key):
    images = session.query(Image).\
        filter(Image.router == router).\
        filter(Image.time > datetime.now() - timedelta(days=1, hours=3)).all()
    x = [k.time for k in images]
    HostOutput = []
    for image in images:
        output = session.query(func.sum(LSP.output)).\
                filter(LSP.image_id == image.id).\
                filter(LSP.to == key).scalar()
        if output is None:
            output = 0
        HostOutput.append(output)
    y = HostOutput
    return getGraph(x, y)


@app.route('/<router>/interface/<interface>/lsplist')
def plot_interface_lsplist(router, interface):
    last_parse = session.query(Image).filter(Image.router == router).all()[-1]
    last_parse_id = last_parse.id

    interface_id = session.query(Interface.id).\
        filter(Interface.description == interface).\
        filter(Interface.image_id == last_parse_id).scalar()

    lsps = session.query(LSP).\
        filter(LSP.image_id == last_parse_id).\
        filter(LSP.interface_id == interface_id).\
        all()
    lsps = sorted(lsps, key=lambda x: x.output, reverse=True)

    elements = []
    for l in lsps:
        L = copy(l)
        L.img = url_for('plot_lsp',router=router,key=L.name)
        L.comment = L.name
        L.out = L.output
        elements.append(L)

    return render_template('list.html', elements=elements)


@app.route('/<router>/host/<host>/lsplist')
def plot_host_lsplist(router, host):
    last_parse = session.query(Image).filter(Image.router == router).all()[-1]
    last_parse_id = last_parse.id

    lsps = session.query(LSP).\
        filter(LSP.image_id == last_parse_id).\
        filter(LSP.to == host).\
        all()
    lsps = sorted(lsps, key=lambda x: x.output, reverse=True)

    elements = []
    for l in lsps:
        L = copy(l)
        L.img = url_for('plot_lsp',router=router,key=L.name)
        L.comment = L.name
        L.out = L.output
        elements.append(L)

    return render_template('list.html', elements=elements)


@app.route('/<router>/<key>')
def plot_list(router, key):
    last_parse = session.query(Image).filter(Image.router == router).all()[-1]
    last_parse_id = last_parse.id

    if key == 'interfaces':
        f = getInterfacesByImageId
        val_compared = 'description'
        val_out = 'output'
    elif key == 'hosts':
        f = getHostsByImageId
        val_compared = 'ip'
        val_out = 'sumoutput'
    elif key == 'lsps':
        f = getLSPSByImageId
        val_compared = 'name'
        val_out = 'output'

    elements = f(last_parse_id)
    for element in elements:
        element.img = '/{router}/{key}/{val}.png'.\
            format(router=router,
                   key=re.sub('s$', '', key),
                   val=getattr(element, val_compared))
        element.comment = getattr(element, val_compared)
        element.out = getattr(element, val_out)
    return render_template('list.html',
                           elements=elements)


def getHostsByImageId(id):
    result = []
    hosts = session.query(Host).\
        filter(Host.ip == LSP.to).\
        filter(LSP.image_id == id).\
        distinct(LSP.to).all()
    for host in hosts:
        H = copy(host)
        H.lsplist = session.query(LSP).\
			filter(LSP.image_id == id).\
			filter(LSP.to == host.ip).\
			order_by(LSP.output.desc()).all()
	H.sumoutput = sum([x.output for x in H.lsplist if x.output is not None])
	H.sumbandwidth = sum([x.bandwidth for x in H.lsplist if x.bandwidth is not None])
	rbandwidth = np.mean([x.rbandwidth for x in H.lsplist if x.rbandwidth is not None])
	if np.isnan(rbandwidth):
	    rbandwidth = None
	H.rbandwidth = rbandwidth
	result.append(H)

    result_sorted = sorted(result, key=lambda x: x.sumoutput, reverse=True)
    return result_sorted


def getInterfacesByImageId(id):
    result = []
    interfaces = session.query(Interface).\
        filter(Interface.image_id == id).all()
    for interface in interfaces:
        I = copy(interface)
        I.lsplist = session.query(LSP).\
			filter(LSP.image_id == id).\
			filter(LSP.interface_id == interface.id).\
			order_by(LSP.output.desc()).all()
	I.rsvpout = sum([x.output for x in I.lsplist if x.output is not None])
	if I.output and I.rsvpout:
            I.ldpout = I.output - I.rsvpout
        else:
            I.ldpout = I.output
        if I.ldpout < 100:
            I.ldpout = 0
        result.append(I)

    result_sorted = sorted(result, key=lambda x: x.output, reverse=True)
    return result_sorted


def getLSPSByImageId(id):
    lsps = session.query(LSP).\
                    filter(LSP.image_id == id).all()
    lsps = sorted(lsps, key=lambda x: x.output, reverse=True)
    return lsps


if __name__ == '__main__':

    app.run(
        host="0.0.0.0",
        debug=True
    )
